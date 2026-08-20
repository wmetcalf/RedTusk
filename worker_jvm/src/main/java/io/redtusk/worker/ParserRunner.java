package io.redtusk.worker;

import org.apache.tika.config.EmbeddedLimits;
import org.apache.tika.language.detect.LanguageDetector;
import org.apache.tika.language.detect.LanguageResult;
import org.apache.tika.io.TikaInputStream;
import org.apache.tika.metadata.Barcode;
import org.apache.tika.metadata.Metadata;
import org.apache.tika.metadata.TikaCoreProperties;
import org.apache.tika.mime.MediaType;
import org.apache.tika.parser.AutoDetectParser;
import org.apache.tika.parser.CompositeParser;
import org.apache.tika.parser.ParseContext;
import org.apache.tika.parser.Parser;
import org.apache.tika.parser.RecursiveParserWrapper;
import org.apache.tika.parser.image.AbstractImageParser;
import org.apache.tika.parser.image.UnicodeQRExtractor;
import org.apache.tika.parser.image.ZXingCPPConfig;
import org.apache.tika.parser.image.ZXingCPPScanner;
import org.apache.tika.parser.mail.RFC822Parser;
import org.apache.tika.parser.html.JSoupParser;
import org.apache.tika.parser.microsoft.OfficeParserConfig;
import org.apache.tika.parser.ocr.TesseractOCRConfig;
import org.apache.tika.parser.pdf.PDFParserConfig;
import org.apache.tika.parser.pdf.image.ImageGraphicsEngine;
import org.apache.tika.parser.pdf.image.ImageGraphicsEngineFactory;
import org.apache.tika.extractor.EmbeddedDocumentExtractor;
import org.apache.tika.sax.XHTMLContentHandler;
import org.apache.pdfbox.cos.COSStream;
import org.apache.pdfbox.pdmodel.PDPage;
import java.util.concurrent.atomic.AtomicInteger;
import org.apache.tika.sax.AbstractRecursiveParserWrapperHandler;
import org.apache.tika.sax.BasicContentHandlerFactory;
import org.apache.tika.sax.RecursiveParserWrapperHandler;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.logging.Logger;

/**
 * Drives Tika's RecursiveParserWrapper against a single document, enforces
 * extraction limits via EmbeddedLimits, and configures Tika-native QR scanning
 * (ZXingCPPConfig) and OCR (TesseractOCRConfig). Per-entry QR/OCR results are
 * read directly from the per-entry Metadata that Tika populates during parsing.
 */
public final class ParserRunner {

    private static final Logger LOG = Logger.getLogger(ParserRunner.class.getName());
    private static final int CHARS_PER_ENTRY = 8 * 1024 * 1024;
    private static final Object IMAGE_HASH_PHASH = tikaImageHashProperty("PHASH");
    private static final Object IMAGE_HASH_COLORHASH = tikaImageHashProperty("COLORHASH");

    // Install JVM-global secure JAXP defaults once at class load so even XML
    // readers constructed outside our ParseContext are hardened (XXE/SSRF).
    static {
        installGlobalSecureXml();
    }

    // Shared language detector — loaded once at startup, thread-safe for detect() calls.
    private static final LanguageDetector LANG_DETECTOR;
    static {
        LanguageDetector d = null;
        try {
            d = LanguageDetector.getDefaultLanguageDetector();
            if (d != null) d.loadModels();
        } catch (Exception e) {
            LOG.warning("Language detector unavailable: " + e.getMessage());
        }
        LANG_DETECTOR = d;
    }
    // maxExtractedBytes from job.limits() is exposed in metadata.json but does not configure
    // this constant — per-entry character limiting based on the configured value is deferred to Plan 3.

    private final JobDescriptor.LimitsDescriptor limits;
    private final boolean enableQr;
    private final boolean enableOcr;
    private final String ocrLang;
    private final int ocrPsm;
    private final int ocrMaxImageDim;
    private final boolean ocrSkipBlank;
    private final String zxingPath;
    private final String tesseractPath;
    // Optional: when set, Pass 1 captures image bytes inline and writes thumbnails.
    // Configured via setOutputDir so existing constructor + tests remain unchanged.
    private java.nio.file.Path outDir;
    private boolean enableThumbnails;
    // Optional: when set, every embedded-doc end flushes a partial metadata.json
    // snapshot to outDir so the dispatcher can salvage on SIGKILL. See DraftSnapshotWriter.
    private JobDescriptor draftJob;

    public ParserRunner(
            JobDescriptor.LimitsDescriptor limits,
            boolean enableQr, boolean enableOcr,
            String ocrLang, int ocrPsm,
            int ocrMaxImageDim, boolean ocrSkipBlank,
            String zxingPath, String tesseractPath) {
        this.limits = limits;
        this.enableQr = enableQr;
        this.enableOcr = enableOcr;
        this.ocrLang = ocrLang;
        this.ocrPsm = ocrPsm;
        this.ocrMaxImageDim = ocrMaxImageDim;
        this.ocrSkipBlank = ocrSkipBlank;
        this.zxingPath = zxingPath;
        this.tesseractPath = tesseractPath;
    }

    /**
     * Configure inline thumbnail capture during Pass 1. Optional — when called,
     * image entries observed by the recursive walk get their thumbnails written
     * directly without waiting for {@link EmbeddedFileExtractor}'s second pass.
     * Eliminates the "Pass-2 missed entry" gap (see Pass1ImageCapture javadoc).
     */
    public ParserRunner setOutputDir(java.nio.file.Path outDir, boolean enableThumbnails) {
        this.outDir = outDir;
        this.enableThumbnails = enableThumbnails;
        return this;
    }

    /**
     * Enable incremental draft-snapshot writes. Required for the dispatcher's
     * timeout-salvage path: each entry the parser walks flushes a partial
     * metadata.json to outDir, so a SIGKILLed worker leaves a usable result
     * instead of nothing. Caller must also have set outDir via {@link #setOutputDir}.
     */
    public ParserRunner setDraftSnapshot(JobDescriptor job) {
        this.draftJob = job;
        return this;
    }

    public ParseResult parse(File inputFile, String filenameHint, String rootSha256)
            throws Exception {
        AutoDetectParser auto = sharedParser();
        BasicContentHandlerFactory chFactory = new BasicContentHandlerFactory(
                BasicContentHandlerFactory.HANDLER_TYPE.TEXT, CHARS_PER_ENTRY);
        RecursiveParserWrapperHandler handler;
        DraftSnapshotWriter draftWriter = null;
        if (draftJob != null && outDir != null) {
            // Incremental draft writes — partial metadata.json after each entry so
            // a SIGKILLed worker leaves a usable salvage for the dispatcher.
            draftWriter = new DraftSnapshotWriter(draftJob, outDir.toFile());
            handler = new DraftingRecursiveHandler(chFactory, draftWriter);
            // Skeleton snapshot before any parsing starts. Covers the worst case:
            // a monolithic parser (CHM, large OLE/MSG) hangs inside its container
            // unpack and never emits a single endEmbeddedDocument before SIGKILL.
            // The skeleton has zero entries but a valid in_progress truncation
            // sentinel, so the dispatcher promotes it to a partial instead of
            // discarding the job entirely.
            draftWriter.flushNow(java.util.List.of());
        } else {
            handler = new RecursiveParserWrapperHandler(chFactory);
        }
        RecursiveParserWrapper wrapper = new RecursiveParserWrapper(auto);
        ParseContext context = new ParseContext();

        // XXE / SSRF hardening: route every JAXP factory Tika may pull from the
        // ParseContext through SafeXml so external entities, DTDs, stylesheets and
        // remote resource fetching are all disabled. Makes the README's "No remote
        // resources" guarantee real instead of relying solely on the no-network
        // namespace defense layer.
        hardenXmlParsing(context);

        // Embedded recursion / count limits (Tika-side enforcement).
        context.set(EmbeddedLimits.class, new EmbeddedLimits(
            limits.maxRecursionDepth(), false,
            limits.maxEmbeddedEntries(), false
        ));

        // ZXing-CPP barcode scanning. Only configure if enabled AND we have a binary path.
        if (enableQr && zxingPath != null && !zxingPath.isEmpty()) {
            ZXingCPPConfig zcfg = new ZXingCPPConfig();
            zcfg.setEnabled(true);
            zcfg.setZxingPath(zxingPath);
            zcfg.setTimeoutSeconds(Math.max(1, limits.ocrTimeoutS()));
            zcfg.setFormats("");  // empty = all formats
            context.set(ZXingCPPConfig.class, zcfg);
            // Enable color-aware parsing — currently honored by HTML
            // (HtmlColorQRExtractor) and PDF (PDF2XHTMLColorAware). OOXML
            // wiring is queued. Lets parsers decode CSS-color / PDF-color
            // QR codes that Tika's normal text extraction would flatten.
            context.set(org.apache.tika.parser.ColorAwareConfig.class,
                    new org.apache.tika.parser.ColorAwareConfig().setEnabled(true));
        }

        // Tesseract OCR. Always set the config so we can explicitly skip when disabled.
        TesseractOCRConfig ocrCfg = new TesseractOCRConfig();
        ocrCfg.setLanguage(ocrLang);
        ocrCfg.setPageSegMode(Integer.toString(ocrPsm));
        ocrCfg.setTimeoutSeconds(Math.max(1, limits.ocrTimeoutS()));
        ocrCfg.setSkipOcr(!enableOcr);
        context.set(TesseractOCRConfig.class, ocrCfg);
        // Per-job OCR dedup cache: TesseractOCRParser checks this before invoking
        // Tesseract so duplicate image bytes (same logo/scan repeated in a doc) are
        // only OCR'd once per parse job.
        enableOcrResultCacheIfAvailable(context, ocrMaxImageDim, ocrSkipBlank);

        // PDF: extract tagged/marked-content structure (headings, tables, lists in
        // accessibility-compliant PDFs) and all image instances, not just unique hashes
        // (duplicate images in malicious PDFs are forensically significant).
        PDFParserConfig pdfCfg = newPdfConfig();
        // ...BUT BOUNDED. Extracting every image instance is forensically right and, on a
        // current Tika, genuinely expensive: measured on an 8.4 MB PDF, the engine finds 46
        // DISTINCT images (dedup would save 6%, so this is not duplicate work) and spends ~1s
        // per image decoding and perceptual-hashing them. That took one document from 2.6s to
        // 61.9s -- a 20x throughput loss on the tier -- and it is unbounded: a PDF with a
        // thousand images costs a thousand seconds and blows through the guest budget.
        //
        // An older Tika hid this by finding almost none of them (2 hashed images vs 200 hash
        // fields on the same file), so the cap was never needed before.
        // Disable PDFParser-side per-page OCR. The default AUTO strategy
        // renders every PDF page through PDFBox into an image, then feeds
        // each rendered page to Tesseract — and bombs on a long tail of
        // real-world PDFs (corrupt color profiles, malformed XObjects,
        // PDFBox COSStream edge cases). On the mbzdls corpus 7 of 11 PDF
        // failures traced to this exact path (the same files extract
        // cleanly with OCR off). We still get OCR on actually-image-bearing
        // entries via Pass1ImageCapture → image-module's Tesseract pipeline,
        // so the only thing we lose is OCR over scanned-PDF text — and any
        // genuinely-scanned PDF surfaces its page images as embedded
        // entries that path can handle. Reflection keeps us tolerant of Tika API
        // moves (TIKA-4748); see forceNoOcr().
        forceNoOcr(pdfCfg);
        context.set(PDFParserConfig.class, pdfCfg);

        // Office: surface hidden/empty rows in Excel workbooks — a common lure technique.
        OfficeParserConfig officeCfg = newOfficeConfig();
        // Macro security: the worker NEVER executes macros — it extracts them as
        // inert embedded entries for forensic review (preserved by the standard
        // VBA/XLM extraction path that surfaces "/macros/..." entries). Set the
        // documented MacroSecurityLevel=3 (maximum) so the README claim holds.
        // No conflict with the forensic macro-as-embedded-entry behavior: this
        // POI flag only governs whether the macro project is *interpreted/run*;
        // macro *source* is still extracted as an embedded entry either way.
        applyMacroSecurity(officeCfg);
        // Enable image hashing on the vector-image POI paths (EMF / WMF). The
        // Tika fork gates rasterize-and-hash on this flag because the raster
        // costs O(image) extra memory + CPU and not every Tika user wants it.
        // We do — phash/dhash/ahash/colorhash on embedded EMFs is the whole
        // point of including them in the extraction graph. Mirrors how
        // enableImageHashingIfAvailable() flips the equivalent toggle on
        // AbstractImageParser instances for raster formats.
        enableMetafileImageHashingIfAvailable(officeCfg);
        context.set(OfficeParserConfig.class, officeCfg);

        // Email: extract all multipart/alternative bodies (plain-text AND HTML), not just
        // the preferred one. URL obfuscation tricks often differ between the two bodies.
        RFC822Parser.Config mailCfg = new RFC822Parser.Config();
        mailCfg.setExtractAllAlternatives(true);
        context.set(RFC822Parser.Config.class, mailCfg);

        // Legacy MS Works (.wps) — POI has no extractor; enable wps2text from
        // libwps-tools (installed in the worker image) to extract body text so
        // downstream URL/QR/IOC scanners can see it.
        org.apache.tika.parser.microsoft.WorksConfig worksCfg =
                new org.apache.tika.parser.microsoft.WorksConfig();
        worksCfg.setEnabled(true);
        worksCfg.setTimeoutSeconds(Math.max(5, limits.ocrTimeoutS()));
        context.set(org.apache.tika.parser.microsoft.WorksConfig.class, worksCfg);


        // Pass-1 image capture. Buffers image bytes during the recursive metadata
        // walk so we can write thumbnails AFTER the walk finishes — by then each
        // entry's Metadata carries the final, parent-prefixed
        // EMBEDDED_RESOURCE_PATH that the UI's thumbnail URL convention requires.
        // Closes the gap where MSG-style attachments surface in the recursive
        // metadata walk but get missed by EmbeddedFileExtractor's second pass.
        Pass1ImageCapture pass1Capture = null;
        if (outDir != null && enableThumbnails) {
            pass1Capture = new Pass1ImageCapture(true);
            context.set(org.apache.tika.extractor.EmbeddedDocumentExtractor.class, pass1Capture);
        }

        Metadata rootMeta = new Metadata();
        if (filenameHint != null) {
            rootMeta.set(TikaCoreProperties.RESOURCE_NAME_KEY, filenameHint);
        }

        boolean parseThrew = false;
        String parseErrorMsg = null;
        try (TikaInputStream stream = TikaInputStream.get(inputFile.toPath())) {
            wrapper.parse(stream, handler, rootMeta, context);
        } catch (Exception e) {
            LOG.warning("Tika parse threw [" + e.getClass().getName() + "]: " + e.getMessage()
                    + (e.getCause() != null ? " caused by " + e.getCause().getClass().getName() + ": " + e.getCause().getMessage() : ""));
            parseThrew = true;
            parseErrorMsg = e.getMessage();
        }

        // Copy to an ArrayList: Tika's RecursiveParserWrapperHandler returns a LinkedList, so the
        // indexed entry loop below would be O(N^2) on large containers — and the salvage path
        // below needs a guaranteed-mutable list to prepend the root. ArrayList fixes both.
        List<Metadata> metaList = new ArrayList<>(handler.getMetadataList());
        // SALVAGE on a mid-document parser crash (e.g. POI RecordFormatException on a malformed
        // BIFF body): entries emitted BEFORE the crash are still in the handler's list — notably
        // the macros, which OfficeParser/OOXML now emit ahead of the body. The root metadata is
        // only inserted (at index 0) on a clean endDocument, so on a throw the partial list holds
        // just the embedded docs; prepend the root we passed in to restore the normal
        // [root, embedded...] shape the loop below expects. The error is attached to the root
        // entry after the loop. Without this, a crash discarded the already-extracted macros.
        if (parseThrew) {
            if (metaList.isEmpty() || metaList.get(0).get(TikaCoreProperties.EMBEDDED_RESOURCE_PATH) != null) {
                metaList.add(0, rootMeta);
            }
        }
        List<EntryResult> results = new ArrayList<>(metaList.size());
        List<ParseResult.WorkerWarning> warnings = new ArrayList<>();
        // Per-job dedup cache for the Unicode-QR scan. Multipart EML with
        // matching plaintext+HTML alternatives, OOXML containers that emit
        // the same body twice through different relationships, etc. all
        // produce duplicate text bodies. Hashing once per job avoids the
        // ZXing subprocess fork for each duplicate.
        java.util.Map<String, java.util.List<String>> uqCache = new java.util.HashMap<>();

        for (int i = 0; i < metaList.size(); i++) {
            Metadata m = metaList.get(i);
            String embPath = m.get(TikaCoreProperties.EMBEDDED_RESOURCE_PATH);
            // When Tika generates a synthetic path like "/embedded-1.cls", prefer the
            // RESOURCE_NAME_KEY (actual filename from VBAMacroReader, OLE, ZIP, etc.)
            // if it's present and distinct from the synthetic basename.
            if (embPath != null && embPath.matches(".*/embedded-\\d+(\\..*)?$")) {
                String rname = m.get(TikaCoreProperties.RESOURCE_NAME_KEY);
                if (rname != null && !rname.isBlank()) {
                    String parent = embPath.substring(0, embPath.lastIndexOf('/'));
                    embPath = parent + "/" + rname;
                }
            }
            String path = (embPath == null || embPath.isEmpty()) ? "/" : embPath;
            String parentPath = deriveParentPath(path);
            int depth = countDepth(path);

            if (depth > limits.maxRecursionDepth()) continue;

            String contentType = guessContentType(m);
            long sizeBytes = (i == 0) ? inputFile.length()
                                       : parseLong(m.get("Content-Length"), 0L);
            // sha256 for embedded entries is filled in by EmbeddedFileExtractor (second pass in Main).
            // Root sha256 comes from the dispatcher which hashed the input before staging.
            String sha256 = (i == 0) ? rootSha256 : null;
            // Perceptual hashes — populated by the wmetcalf Tika fork when image hashing is available.
            String phash = metadataValue(m, IMAGE_HASH_PHASH);
            String colorhash = metadataValue(m, IMAGE_HASH_COLORHASH);
            // Byte digests / thumbnail filled in by EmbeddedFileExtractor in Main.
            String md5  = null;
            String sha1 = null;
            String text = m.get(TikaCoreProperties.TIKA_CONTENT);
            if (text == null) text = "";
            String language = m.get("dc:language");
            // Fall back to active language detection when the document has no language metadata.
            // Require at least 30 chars for reliable signal; results below MEDIUM confidence are dropped.
            // Cap input to language detector — feeding megabytes of JS/binary into
            // Optimaize can OOM; the first 10 KB is more than enough for reliable detection.
            String langSample = text.length() > 10_000 ? text.substring(0, 10_000) : text;
            if (language == null && langSample.length() >= 30 && LANG_DETECTOR != null) {
                try {
                    LanguageResult lr = LANG_DETECTOR.detect(langSample);
                    if (lr != null && lr.isReasonablyCertain()) {
                        language = lr.getLanguage();
                    }
                } catch (Exception ignored) { }
            }

            Map<String, Object> metadata = extractMetadata(m);

            // RTF IOC scan: best-effort, non-fatal.  Only run on the root entry
            // (i == 0) where inputFile is the original RTF document.  Embedded
            // RTF objects within a container are not scanned separately.
            if (i == 0) {
                try {
                    Map<String, List<String>> iocs = RtfIocScanner.scan(inputFile, contentType);
                    for (Map.Entry<String, List<String>> ioc : iocs.entrySet()) {
                        List<String> vals = ioc.getValue();
                        if (vals != null && !vals.isEmpty()) {
                            metadata.put(ioc.getKey(), vals.size() == 1 ? vals.get(0) : vals);
                        }
                    }
                } catch (Exception e) {
                    LOG.warning("RTF IOC scan error: " + e.getMessage());
                }

                // Supplement rtf:templateUrl with Tika's own extracted template path.
                // RtfIocScanner's deobfuscator interprets UNC backslashes as RTF control words,
                // truncating UNC paths. Tika's RTF parser handles this correctly for real documents.
                // Only flag remote templates (UNC or URL-based) as IOCs; local paths are benign.
                Object existingTemplate = metadata.get(RtfIocScanner.KEY_TEMPLATE_URL);
                String tikaTemplate = (String) metadata.get("extended-properties:Template");
                if (tikaTemplate != null && !tikaTemplate.isEmpty()) {
                    String lc = tikaTemplate.toLowerCase(java.util.Locale.ROOT);
                    boolean tikaIsRemote = tikaTemplate.startsWith("\\\\")
                            || lc.startsWith("http://") || lc.startsWith("https://")
                            || lc.startsWith("ftp://");
                    if (tikaIsRemote) {
                        // Tika's full path is authoritative for remote templates; override scanner.
                        metadata.put(RtfIocScanner.KEY_TEMPLATE_URL, tikaTemplate);
                    } else if (existingTemplate != null) {
                        // Tika found a local path. Only remove the scanner's value when it also
                        // looks like a truncated local path (e.g. "C:") — not if the scanner
                        // found a genuine remote URL that Tika's parser missed.
                        String existing = existingTemplate.toString();
                        String existingLc = existing.toLowerCase(java.util.Locale.ROOT);
                        boolean scannerIsRemote = existing.startsWith("\\\\")
                                || existingLc.startsWith("http://") || existingLc.startsWith("https://")
                                || existingLc.startsWith("ftp://");
                        if (!scannerIsRemote) {
                            metadata.remove(RtfIocScanner.KEY_TEMPLATE_URL);
                        }
                    }
                }
            }

            boolean isImage = isImageType(contentType);

            // ----- QR (Tika-native via ZXingCPPConfig) ---------------------------------
            EntryResult.QrResult qr;
            if (!enableQr) {
                qr = new EntryResult.QrResult(List.of(), "disabled");
            } else if (zxingPath == null || zxingPath.isEmpty()) {
                // QR enabled but no ZXingReader binary configured — treat as disabled
                qr = new EntryResult.QrResult(List.of(), "disabled");
            } else {
                // Harvest Barcode.* metadata regardless of content type — the
                // Tika fork populates these for color-aware (PDF/DOCX/PPTX/
                // XLSX/HTML) and Unicode-art QRs as well as image scans.
                String[] values    = m.getValues(Barcode.BARCODE_VALUE);
                String[] formats   = m.getValues(Barcode.BARCODE_FORMAT);
                String[] rawBytes  = m.getValues(Barcode.BARCODE_RAW_BYTES);
                String[] positions = m.getValues(Barcode.BARCODE_POSITION);
                List<EntryResult.QrCode> codes = new ArrayList<>();
                if (values != null) {
                    for (int b = 0; b < values.length; b++) {
                        codes.add(new EntryResult.QrCode(
                            values[b],
                            indexOrNull(formats, b),
                            indexOrNull(rawBytes, b),
                            indexOrNull(positions, b)
                        ));
                    }
                }
                if (codes.isEmpty() && !isImage) {
                    qr = new EntryResult.QrResult(List.of(), "no_images");
                } else {
                    qr = new EntryResult.QrResult(codes, null);
                }
            }

            // ----- Unicode-block-art QR codes embedded in extracted text --------------
            // Runs on EVERY entry's text body (post-parse) so Office docs, PDFs, ICS,
            // EML, MSG, HTML, RTF and plain text all get scanned with one hook.
            // Cheap pre-filter via UnicodeQRExtractor.countQrGlyphs() avoids the
            // bitmap-render cost when no QR-art glyphs are present.
            if (enableQr && zxingPath != null && !zxingPath.isEmpty()
                    && text != null && text.length() > 0) {
                try {
                    int glyphCount = UnicodeQRExtractor.countQrGlyphs(text);
                    // Threshold sized for the densest packing the extractor
                    // supports (sextants = 6 modules per glyph). A v1 QR
                    // (21x21) packed in sextants is ~77 glyphs; pad slightly
                    // below to keep the pre-filter useful but not exclusionary.
                    if (glyphCount >= 50) {
                        metadata.put("unicode_qr:glyph_count", Integer.toString(glyphCount));
                        // SHA-256 of the text body keys the dedup cache. Cheap
                        // vs an extra ZXing subprocess fork for duplicate bodies.
                        String textHash = sha256Hex(text);
                        java.util.List<String> decoded = uqCache.get(textHash);
                        if (decoded == null) {
                            ZXingCPPConfig zcfgLocal = context.get(ZXingCPPConfig.class);
                            ZXingCPPScanner uqScanner = new ZXingCPPScanner();
                            java.util.List<org.apache.tika.parser.image.ZXingCPPScanner.Result>
                                    uqResults = UnicodeQRExtractor.extractAndDecode(
                                            text, uqScanner, zcfgLocal, context);
                            decoded = new java.util.ArrayList<>(uqResults.size());
                            for (org.apache.tika.parser.image.ZXingCPPScanner.Result r
                                    : uqResults) {
                                String t = r.getText();
                                if (t != null && !t.isEmpty()) {
                                    decoded.add(t);
                                }
                            }
                            uqCache.put(textHash, decoded);
                        }
                        if (!decoded.isEmpty()) {
                            metadata.put("ExploitClass",
                                    "Decoded " + decoded.size()
                                  + " Unicode-art QR code(s) from extracted text "
                                  + "— invisible-to-image-scanner phishing payload");
                            // Promote Unicode-art decodes to first-class QrCode
                            // entries so the UI's QR section, metrics, and any
                            // downstream consumer iterating qr.codes sees them
                            // the same way as image-based QRs. Skip URLs that
                            // are already in qr.codes from Barcode.* harvest
                            // (Tika's UnicodeQRContentHandler also emits them
                            // via the standard channel).
                            java.util.Set<String> existing = new java.util.HashSet<>();
                            for (EntryResult.QrCode c : qr.codes()) {
                                existing.add(c.data());
                            }
                            java.util.List<EntryResult.QrCode> merged =
                                    new java.util.ArrayList<>(qr.codes());
                            for (String t : decoded) {
                                if (existing.add(t)) {
                                    merged.add(new EntryResult.QrCode(
                                            t, "QR_CODE", null, "unicode-art"));
                                }
                            }
                            qr = new EntryResult.QrResult(merged, null);
                        }
                    }
                } catch (Exception e) {
                    LOG.warning("Unicode-QR scan error on entry " + path + ": "
                            + e.getMessage());
                }
            }

            // ----- OCR (Tika-native via TesseractOCRConfig) ----------------------------
            // For image entries with OCR enabled, the extracted text IS the OCR output
            // (TesseractOCRParser writes it to TIKA_CONTENT), so we reuse `text` here.
            EntryResult.OcrResult ocr;
            if (!enableOcr) {
                ocr = new EntryResult.OcrResult("", null, 0, "disabled");
            } else if (!isImage) {
                ocr = new EntryResult.OcrResult("", null, 0, "no_images");
            } else {
                int ocrMs = (int) Math.min(
                    parseLong(m.get("X-Tika-OCR-Duration-Ms"), 0L), Integer.MAX_VALUE);
                String ocrSkippedReason = m.get("X-Tika-OCR-Skipped-Reason");
                // When OCR was skipped, use empty text — TIKA_CONTENT for image entries
                // can contain the embedded resource path written by the container parser
                // (e.g. "/docProps/thumbnail.jpeg"), not actual OCR output.
                // When OCR ran but the only content is the container-injected path prefix
                // (starts with '/' and looks like a file path), strip it — Tesseract
                // produced no real words, just the path token from the enclosing parser.
                String ocrText = ocrSkippedReason != null ? "" : stripContainerPathPrefix(text, path);
                ocr = new EntryResult.OcrResult(ocrText, language, ocrMs, ocrSkippedReason);
            }

            // hasThumbnail starts true only when Pass-1 capture buffered bytes
            // AND a thumbnail write succeeds (just below, post-walk). Root entry
            // is skipped here — Main.tryGenerateRootThumbnail handles it.
            boolean pass1Thumb = false;
            String pass1Skip = null;
            if (pass1Capture != null && i > 0) {
                // Key on the same EMBEDDED_RESOURCE_PATH string the capture
                // recorded post-delegate — survives RecursiveParserWrapperHandler's
                // cloneMetadata in endEmbeddedDocument.
                byte[] imgBytes = pass1Capture.bufferedBytesFor(path);
                if (imgBytes != null) {
                    String thumbCt = pass1Capture.contentTypeFor(path);
                    if (thumbCt == null) thumbCt = contentType;
                    pass1Thumb = writePass1Thumbnail(outDir, path, imgBytes, thumbCt);

                    // Save the source file + compute digests from the same bytes.
                    // Pass 2 (EmbeddedFileExtractor.SavingExtractor) is supposed to
                    // do this, but it misses image embeds in two cases that come up
                    // a lot in malicious-document corpora:
                    //   1. depth-1 embedded EMFs / WMFs in .xls files surfaced under
                    //      synthetic names like "/embedded-1.emf" (POI's OfficeParser
                    //      doesn't re-surface them in Pass 2's unwrapped flow), and
                    //   2. images inside embedded PDFs at depth 2 (Pass 2 doesn't
                    //      recurse into the PDF's image extractor).
                    // Pass 1 already has the bytes in memory at this point. Using
                    // them to ALSO compute sha256/md5/sha1 + size_bytes + save the
                    // raw file is essentially free, and the result wins over Pass
                    // 2's nulls below in the EmbeddedFileExtractor merge in Main.
                    Pass1Save saved = savePass1Source(outDir, path, imgBytes);
                    if (saved != null) {
                        // Override only when Pass 1 has a value to contribute. Pass 2
                        // may still fill these in for entries it does see.
                        if (sha256 == null) sha256 = saved.sha256;
                        if (md5    == null) md5    = saved.md5;
                        if (sha1   == null) sha1   = saved.sha1;
                        if (sizeBytes == 0) sizeBytes = saved.sizeBytes;
                    }
                } else if (pass1Capture.wasBufferCapped(path)) {
                    // We saw the image, recognized it as such, but dropped the
                    // buffer to stay under the per-job byte budget. Surface so
                    // the UI explains the missing thumbnail instead of falling
                    // through to pass2_missed_entry which would be misleading.
                    pass1Skip = "pass1_buffer_cap";
                }
            }

            results.add(new EntryResult(
                path, parentPath, depth, contentType, sizeBytes,
                sha256, md5, sha1, pass1Thumb, pass1Skip, phash, colorhash, metadata, text, language, qr, ocr, null
            ));
        }

        // If the parse threw mid-document, attach the error to the (salvaged) root entry and
        // warn — the partial entries (e.g. macros emitted before the crash) are preserved.
        if (parseThrew && !results.isEmpty()) {
            EntryResult r0 = results.get(0);
            results.set(0, new EntryResult(
                r0.path(), r0.parentPath(), r0.depth(), r0.contentType(), r0.sizeBytes(),
                r0.sha256(), r0.md5(), r0.sha1(), r0.hasThumbnail(), r0.thumbnailSkipped(),
                r0.phash(), r0.colorhash(), r0.metadata(), r0.text(), r0.language(),
                r0.qr(), r0.ocr(), parseErrorMsg));
            int salvaged = results.size() - 1;
            warnings.add(new ParseResult.WorkerWarning(
                "partial_extraction",
                "parser crashed mid-document; " + salvaged + " embedded entr"
                    + (salvaged == 1 ? "y" : "ies") + " salvaged: " + parseErrorMsg, "/"));
        }

        // Truncation: in Tika 4.x the root metadata gets EMBEDDED_RESOURCE_LIMIT_REACHED /
        // EMBEDDED_DEPTH_LIMIT_REACHED set when EmbeddedLimits caps were hit. Read that
        // back from metaList[0] (or rootMeta as fallback).
        ParseResult.WorkerTruncation truncated = null;
        Metadata top = metaList.isEmpty() ? rootMeta : metaList.get(0);
        if (parseBool(top.get(AbstractRecursiveParserWrapperHandler.EMBEDDED_RESOURCE_LIMIT_REACHED))) {
            truncated = new ParseResult.WorkerTruncation(
                "max_embedded_entries",
                limits.maxEmbeddedEntries(),
                metaList.size()
            );
        } else if (parseBool(top.get(AbstractRecursiveParserWrapperHandler.EMBEDDED_DEPTH_LIMIT_REACHED))) {
            truncated = new ParseResult.WorkerTruncation(
                "max_recursion_depth",
                limits.maxRecursionDepth(),
                metaList.size()
            );
        }

        if (results.isEmpty()) {
            results.add(new EntryResult(
                "/", null, 0,
                guessContentType(rootMeta), inputFile.length(),
                rootSha256, null, null, false, null, null, null, Map.of(), "", null,
                new EntryResult.QrResult(List.of(), "disabled"),
                new EntryResult.OcrResult("", null, 0, "disabled"),
                null
            ));
        }
        ParseResult capped = enforceMaxExtractedBytes(
            new ParseResult(results, warnings, truncated),
            limits.maxExtractedBytes()
        );
        return capped;
    }

    /**
     * Write a thumbnail for an entry that Pass-1 buffered, using the final
     * parent-prefixed EMBEDDED_RESOURCE_PATH from the metaList. Mirrors the
     * filesystem layout Pass-2 uses ({@code outDir/embedded/thumbnails/<rel>.jpg})
     * so the UI's deterministic URL builder finds it without any rewrite.
     */
    private static boolean writePass1Thumbnail(java.nio.file.Path outDir, String entryPath,
                                               byte[] bytes, String contentType) {
        if (outDir == null || entryPath == null || "/".equals(entryPath)) return false;
        java.nio.file.Path embRoot = outDir.resolve("embedded");
        // Reuse Pass-2's path sanitizer so the thumbnail file lands at exactly the
        // path Pass 2 would have produced for the same entry — keeps the layout
        // single-sourced and avoids divergent escaping between the two passes.
        Metadata nameOnly = new Metadata();
        java.nio.file.Path outFile = EmbeddedFileExtractor.resolveOutFile(embRoot, entryPath, nameOnly);
        if (outFile == null) return false;
        try {
            return EmbeddedFileExtractor.writeThumbnail(bytes, contentType, embRoot, outFile);
        } catch (Exception e) {
            LOG.fine("Pass-1 thumbnail write failed for " + entryPath + ": " + e.getMessage());
            return false;
        }
    }

    /** SHA-256 / MD5 / SHA-1 + size for a Pass-1-buffered embedded entry whose
     *  source bytes we just persisted to disk. */
    private record Pass1Save(String sha256, String md5, String sha1, long sizeBytes) {}

    /** Persist Pass 1's buffered bytes for an embedded entry as both a raw file
     *  under {@code embedded/<entry-path>} and a digest triple, mirroring what
     *  Pass 2's {@link EmbeddedFileExtractor.SavingExtractor} does for entries
     *  it actually saw. Returns {@code null} on path-resolution failure (e.g.
     *  the root entry, which has no embedded location). */
    private static Pass1Save savePass1Source(java.nio.file.Path outDir,
                                             String entryPath, byte[] bytes) {
        if (outDir == null || entryPath == null || "/".equals(entryPath) || bytes == null) {
            return null;
        }
        java.nio.file.Path embRoot = outDir.resolve("embedded");
        Metadata nameOnly = new Metadata();
        java.nio.file.Path outFile =
                EmbeddedFileExtractor.resolveOutFile(embRoot, entryPath, nameOnly);
        if (outFile == null) return null;
        try {
            java.nio.file.Files.createDirectories(outFile.getParent());
            java.nio.file.Files.write(outFile, bytes,
                    java.nio.file.StandardOpenOption.CREATE,
                    java.nio.file.StandardOpenOption.TRUNCATE_EXISTING);
        } catch (java.io.IOException e) {
            LOG.fine("Pass-1 source write failed for " + entryPath + ": " + e.getMessage());
            // Still compute digests + return them even if the file write failed —
            // the entry hashes are useful for similarity queries on their own.
        }
        try {
            java.security.MessageDigest dSha256 = java.security.MessageDigest.getInstance("SHA-256");
            java.security.MessageDigest dMd5    = java.security.MessageDigest.getInstance("MD5");
            java.security.MessageDigest dSha1   = java.security.MessageDigest.getInstance("SHA-1");
            dSha256.update(bytes);
            dMd5.update(bytes);
            dSha1.update(bytes);
            return new Pass1Save(hexBytes(dSha256.digest()),
                                 hexBytes(dMd5.digest()),
                                 hexBytes(dSha1.digest()),
                                 (long) bytes.length);
        } catch (java.security.NoSuchAlgorithmException e) {
            // SHA-256 / MD5 / SHA-1 are JDK-mandatory; this is unreachable in
            // practice but the API forces us to handle it.
            return new Pass1Save(null, null, null, (long) bytes.length);
        }
    }

    private static String hexBytes(byte[] b) {
        StringBuilder sb = new StringBuilder(b.length * 2);
        for (byte x : b) {
            int v = x & 0xff;
            sb.append(Character.forDigit(v >>> 4, 16))
              .append(Character.forDigit(v & 0xf, 16));
        }
        return sb.toString();
    }

    /** SHA-256 of a UTF-8 string as lowercase hex. Used to dedupe Unicode-QR
     *  scans across entries that carry the same text body (e.g. multipart EML
     *  with matching plaintext+HTML alternatives). */
    private static String sha256Hex(String s) {
        try {
            java.security.MessageDigest md = java.security.MessageDigest.getInstance("SHA-256");
            byte[] digest = md.digest(s.getBytes(java.nio.charset.StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder(digest.length * 2);
            for (byte b : digest) {
                sb.append(String.format(java.util.Locale.ROOT, "%02x", b & 0xff));
            }
            return sb.toString();
        } catch (java.security.NoSuchAlgorithmException e) {
            // SHA-256 is part of the JDK contract — fall back to identity to
            // disable the cache without crashing the entry processing.
            return s;
        }
    }

    private static ParseResult enforceMaxExtractedBytes(ParseResult result, long maxBytes) {
        if (maxBytes < 0) {
            return result;
        }
        List<EntryResult> capped = new ArrayList<>(result.entries().size());
        long remaining = maxBytes;
        long observed = 0;
        boolean truncated = false;

        for (EntryResult e : result.entries()) {
            String text = e.text() == null ? "" : e.text();
            byte[] bytes = text.getBytes(StandardCharsets.UTF_8);
            observed += bytes.length;
            String nextText = text;
            if (bytes.length > remaining) {
                truncated = true;
                nextText = truncateUtf8(text, Math.max(remaining, 0));
                remaining = 0;
            } else {
                remaining -= bytes.length;
            }
            capped.add(new EntryResult(
                e.path(), e.parentPath(), e.depth(), e.contentType(),
                e.sizeBytes(), e.sha256(), e.md5(), e.sha1(), e.hasThumbnail(),
                e.thumbnailSkipped(),
                e.phash(), e.colorhash(), e.metadata(), nextText, e.language(),
                e.qr(), e.ocr(), e.error()
            ));
        }

        if (!truncated) {
            return result;
        }

        ParseResult.WorkerTruncation truncation = new ParseResult.WorkerTruncation(
            "max_extracted_bytes",
            (int) Math.min(maxBytes, Integer.MAX_VALUE),
            (int) Math.min(observed, Integer.MAX_VALUE)
        );
        return new ParseResult(capped, result.warnings(), truncation);
    }

    private static String truncateUtf8(String text, long maxBytes) {
        if (maxBytes <= 0) {
            return "";
        }
        StringBuilder out = new StringBuilder(text.length());
        long used = 0;
        for (int offset = 0; offset < text.length(); ) {
            int cp = text.codePointAt(offset);
            int bytes = new String(Character.toChars(cp)).getBytes(StandardCharsets.UTF_8).length;
            if (used + bytes > maxBytes) {
                break;
            }
            out.appendCodePoint(cp);
            used += bytes;
            offset += Character.charCount(cp);
        }
        return out.toString();
    }

    /**
     * Install hardened JAXP factories into the {@link ParseContext} so every XML
     * read Tika performs (OOXML, ODF, RSS, XMP, SVG metadata, etc.) rejects
     * external entities, DTDs, stylesheets and remote resource loading. We set
     * the SAX/DOM/StAX/Transformer factory objects on the context AND register
     * them under the framework's string-keyed slots, because different Tika
     * parser modules look them up by type or by interface. Any factory class
     * Tika doesn't honor is harmless dead weight; the ones it does honor close
     * the XXE/SSRF hole. As a backstop, the same secure factories are installed
     * as JVM-global defaults (see {@link #installGlobalSecureXml()}).
     */
    static void hardenXmlParsing(ParseContext context) {
        try {
            context.set(javax.xml.parsers.DocumentBuilderFactory.class,
                    io.redtusk.worker.util.SafeXml.newDocumentBuilderFactory());
            context.set(javax.xml.parsers.SAXParserFactory.class,
                    io.redtusk.worker.util.SafeXml.newSAXParserFactory());
            context.set(javax.xml.stream.XMLInputFactory.class,
                    io.redtusk.worker.util.SafeXml.newXMLInputFactory());
            context.set(javax.xml.transform.TransformerFactory.class,
                    io.redtusk.worker.util.SafeXml.newTransformerFactory());
        } catch (Exception e) {
            LOG.warning("XML hardening: could not install secure JAXP factories: " + e.getMessage());
        }
    }

    /**
     * Install JVM-global secure JAXP defaults so even XML readers a parser
     * constructs directly (bypassing the ParseContext) are hardened. Idempotent
     * and best-effort: only sets a system property when it is not already set so
     * we never clobber an explicit operator override.
     */
    static void installGlobalSecureXml() {
        // jaxp.properties-style global limits: forbid all external access.
        setIfAbsent(javax.xml.XMLConstants.ACCESS_EXTERNAL_DTD, "");
        setIfAbsent(javax.xml.XMLConstants.ACCESS_EXTERNAL_SCHEMA, "");
        setIfAbsent(javax.xml.XMLConstants.ACCESS_EXTERNAL_STYLESHEET, "");
    }

    private static void setIfAbsent(String key, String value) {
        try {
            if (System.getProperty(key) == null) {
                System.setProperty(key, value);
            }
        } catch (SecurityException e) {
            LOG.fine("XML hardening: cannot set system property " + key + ": " + e.getMessage());
        }
    }

    /**
     * Set the documented MacroSecurityLevel=3 (maximum) on the OfficeParserConfig
     * if the Tika/POI API exposes it. Used reflectively so the worker still
     * compiles against Tika snapshots that lack the setter. The worker never
     * executes macros regardless — this only makes the documented hardening
     * level explicit on the config object.
     */
    /**
     * Force the PDF parser's per-page OCR strategy to NO_OCR, reflectively, so we
     * stay tolerant of Tika API moves (TIKA-4748 relocated the strategy off the flat
     * {@code PDFParserConfig.setOcrStrategy} setter into the nested {@code OcrConfig}).
     *
     * <p>Behaviour-critical: a silent failure here reverts PDF to the AUTO strategy,
     * which renders every page through PDFBox+Tesseract and bombs on a long tail of
     * malformed PDFs. So a total failure to disable OCR is logged, not swallowed.
     *
     * <p>Returns whether NO_OCR was actually applied — {@code false} means the config
     * was left at its default (AUTO). Package-private + a real return value so a test
     * can assert the reflection still lands NO_OCR against the pinned Tika, turning a
     * future API bump that breaks it into a red build instead of a silent regression.
     *
     * @return true iff NO_OCR was set on {@code pdfCfg}
     */
    static boolean forceNoOcr(PDFParserConfig pdfCfg) {
        try {
            Class<?> ocrCfgClass = Class.forName("org.apache.tika.parser.pdf.OcrConfig");
            Class<?> strategyClass = null;
            for (Class<?> c : ocrCfgClass.getDeclaredClasses()) {
                if (c.getSimpleName().equals("Strategy")) { strategyClass = c; break; }
            }
            if (strategyClass == null || !strategyClass.isEnum()) {
                return false;
            }
            Object noOcr = null;
            for (Object e : strategyClass.getEnumConstants()) {
                if ("NO_OCR".equals(((Enum<?>) e).name())) { noOcr = e; break; }
            }
            if (noOcr == null) {
                return false;
            }
            // TIKA-4748 moved the OCR strategy off the flat PDFParserConfig setter
            // into the nested OcrConfig (pdfCfg.getOcr().setStrategy). Try the nested
            // path first, fall back to the pre-4748 flat setter, so we force NO_OCR
            // against either Tika API.
            try {
                Object ocrConfig = pdfCfg.getClass().getMethod("getOcr").invoke(pdfCfg);
                if (ocrConfig == null) {
                    // getOcr() is a non-null field getter in the pinned Tika, but this
                    // block is reflective/version-tolerant by design — guard against a
                    // null return (NPE isn't a ReflectiveOperationException and would
                    // escape) and fall back to the pre-4748 flat setter.
                    throw new NoSuchMethodException("getOcr() returned null");
                }
                ocrConfig.getClass()
                         .getMethod("setStrategy", strategyClass)
                         .invoke(ocrConfig, noOcr);
            } catch (NoSuchMethodException preTika4748) {
                pdfCfg.getClass()
                      .getMethod("setOcrStrategy", strategyClass)
                      .invoke(pdfCfg, noOcr);
            }
            return true;
        } catch (ReflectiveOperationException e) {
            // Could not force NO_OCR on the PDF parser — it will fall back to the
            // AUTO strategy (per-page PDFBox render + Tesseract), which is both slow
            // and crash-prone on adversarial PDFs. Surface it instead of hiding it.
            LOG.warning("Could not disable PDF-page OCR (setOcrStrategy/getOcr unavailable): "
                    + e.getMessage() + " — PDF parsing may fall back to AUTO OCR.");
            return false;
        }
    }

    private static void applyMacroSecurity(OfficeParserConfig officeCfg) {
        // Try a few known setter shapes across Tika/POI versions.
        if (trySetIntMethod(officeCfg, "setMacroSecurityLevel", 3)) return;
        // POI exposes macro extraction without execution; if no level setter is
        // present, the default extract-don't-run behavior already satisfies the
        // "never executed" guarantee. Nothing else to do.
        LOG.fine("MacroSecurity: OfficeParserConfig exposes no macro-security setter; "
                + "relying on extract-only (non-executing) default.");
    }

    private static boolean trySetIntMethod(Object target, String method, int value) {
        try {
            target.getClass().getMethod(method, int.class).invoke(target, value);
            return true;
        } catch (NoSuchMethodException e) {
            return false;
        } catch (ReflectiveOperationException e) {
            LOG.fine("MacroSecurity: " + method + " failed: " + e.getMessage());
            return false;
        }
    }

    /**
     * The configured parser tree, built ONCE per JVM.
     *
     * {@code new AutoDetectParser()} costs ~2.1s — it resolves Tika's default config and
     * service-loads the whole parser/detector set. It was being constructed per parse and
     * discarded, which made it ~100% of a job's engine time: measured on a 43-byte HTML,
     * parse = 2165ms of which newAutoDetectParser = 2159ms. Nothing about it is job-specific
     * (both configure* helpers are static and take only the tree; the settings they apply
     * are constants), and Tika parsers are designed to be reused across parses — per-parse
     * state lives in the ParseContext and handler, which are still built fresh below.
     */
    private static volatile AutoDetectParser sharedParser;

    /**
     * Package-private, not private: EmbeddedFileExtractor's second extraction pass needs the
     * SAME instance. It used to call {@code new AutoDetectParser()} itself, which re-ran the
     * whole SPI discovery -- DefaultParser.<init> -> ServiceLoader.loadStaticServiceProviders
     * -> DefaultEncodingDetector.<init> -> the ML encoding detectors -- on EVERY JOB. Measured
     * on a 2-byte input, post-prewarm: 4314ms with the ML detectors registered vs 713ms
     * without, and a job-phase profile put the time squarely in that constructor chain.
     *
     * This is the same defect sharedParser() was introduced to fix, surviving in a second code
     * path. A warm snapshot cannot help with it: the construction happens AFTER the go-signal,
     * so no amount of prewarming captures it.
     */
    static AutoDetectParser sharedParser() {
        AutoDetectParser p = sharedParser;
        if (p != null) {
            return p;
        }
        synchronized (ParserRunner.class) {
            if (sharedParser == null) {
                AutoDetectParser built = new AutoDetectParser();
                // AutoDetectParser wraps DefaultParser (itself a CompositeParser) — recurse to
                // find the actual AbstractImageParser instances and enable perceptual hashing.
                enableImageHashing(built);
                // JSoupParser.Config in ParseContext is ignored (parser reads instance field,
                // not ParseContext). Walk the tree to set extractScripts=true on the instance.
                enableHtmlScriptExtraction(built);
                // Publish only after configuration, so no thread can observe a partly
                // configured tree through the volatile read above.
                sharedParser = built;
            }
            return sharedParser;
        }
    }

    /**
     * Office configuration, shared by both extraction passes for the same reason the PDF one is.
     *
     * includeMissingRows is the expensive one. It emits a row for every GAP in a sheet's used
     * range -- content-bearing rows are emitted either way -- so on a sparse workbook it is
     * pure padding. Measured on a 1.8 MB xlsm: 3,885,164 lines of extracted text of which
     * 3,882,321 (99.9%) were tab-only empty rows, 8 MB of output, and 203s of parse. Production
     * "finished" the same file in 67s only because it hit the 8 MiB write limit and stopped
     * before reaching the VBA -- 1 entry against this build's 44.
     *
     * DEFAULT OFF, matching Tika's own default. The forensic argument for it is row alignment
     * (knowing content sits at row 1,000,000 rather than row 5), which the row indices already
     * carry; that is not worth 3.9M blank lines on every sparse sheet. REDTUSK_INCLUDE_MISSING_ROWS=1
     * restores it for a case that needs literal row-for-row fidelity.
     */
    static OfficeParserConfig newOfficeConfig() {
        OfficeParserConfig cfg = new OfficeParserConfig();
        cfg.setIncludeMissingRows(includeMissingRows());
        return cfg;
    }

    /** Package-private for testing: System.getenv() cannot be set in-process. */
    static boolean parseIncludeMissingRows(String raw) {
        return raw != null && (raw.equals("1") || raw.equalsIgnoreCase("true"));
    }

    static boolean includeMissingRows() {
        return parseIncludeMissingRows(System.getenv("REDTUSK_INCLUDE_MISSING_ROWS"));
    }

    /**
     * The PDF configuration BOTH extraction passes must use.
     *
     * Shared, not copy-pasted, because copy-paste already failed here twice: pass 2
     * (EmbeddedFileExtractor) built its own PDFParserConfig with the same two flags and a
     * comment claiming it "carries the same config as the first pass". When pass 1 gained the
     * inline-image cap, pass 2 silently did not — so a capped pass 1 was followed by an
     * UNBOUNDED pass 2 over the same document, and a job-phase profile put 55 of 60 samples in
     * EmbeddedFileExtractor.extract even with the cap set to 1. (The same divergence, in the
     * same two methods, previously left pass 2 constructing its own AutoDetectParser.)
     *
     * Anything PDF-shaped belongs here, so the two passes cannot drift again.
     */
    static PDFParserConfig newPdfConfig() {
        PDFParserConfig cfg = new PDFParserConfig();
        cfg.setExtractMarkedContent(true);
        // Every image INSTANCE, not just unique ones: duplicates in a malicious PDF are
        // forensically significant. Bounded by the factory below -- on a current Tika this
        // finds 600 image instances in one 8.4 MB document.
        cfg.setExtractUniqueInlineImagesOnly(false);
        cfg.setImageGraphicsEngineFactory(new BoundedImageGraphicsEngineFactory(maxInlineImages()));
        return cfg;
    }

    /**
     * Per-document ceiling on PDF inline images that are decoded + hashed.
     *
     * Env, not a job limit, deliberately: it needs no change to the host/guest job JSON
     * contract, so it can be tuned on a running fleet the same way REDTUSK_PREWARM is. 0 or
     * negative means unbounded (the pre-cap behaviour), for an operator who would rather have
     * the complete image inventory than a bounded parse.
     */
    static int maxInlineImages() {
        return parseMaxInlineImages(System.getenv("REDTUSK_MAX_INLINE_IMAGES"));
    }

    /** Package-private for testing: System.getenv() cannot be set in-process. */
    static int parseMaxInlineImages(String raw) {
        if (raw == null || raw.isBlank()) {
            return DEFAULT_MAX_INLINE_IMAGES;
        }
        try {
            return Integer.parseInt(raw.trim());
        } catch (NumberFormatException e) {
            LOG.warning("Bad REDTUSK_MAX_INLINE_IMAGES=" + raw + "; using "
                        + DEFAULT_MAX_INLINE_IMAGES);
            return DEFAULT_MAX_INLINE_IMAGES;
        }
    }

    /**
     * Re-measured after the pass-2 fix, on the pinned Tika, 8.4 MB PDF (600 image instances):
     *
     *     cap=0 (unbounded)  114.1s   600 hash fields
     *     cap=32              55.5s   192
     *     cap=8               19.3s    48
     *     cap=4               ~13s     24   <- default
     *     cap=2                9.9s    12
     *     cap=1               10.4s     8
     *
     * ~1.6s per image above a ~10s floor. The earlier default of 8 was chosen from a sweep taken
     * while pass 2 was still uncapped, so those numbers were measuring the wrong thing.
     *
     * 4 is the balance point: production's Tika surfaces 2 image-hash fields on this document,
     * so 24 is an order of magnitude more forensic coverage, for ~13s on the worst PDF in the
     * corpus while ordinary documents run 3-3.7x FASTER than production. Raise it with
     * REDTUSK_MAX_INLINE_IMAGES when a case needs the full inventory; <=0 disables the bound.
     *
     * The ~10s floor is NOT images and is not yet explained -- production does this document in
     * 3.3s. Do not read a faster tier as "the Tika drift is fixed".
     */
    static final int DEFAULT_MAX_INLINE_IMAGES = 4;

    /** How many trailing pages keep their own image allowance. */
    static final int TAIL_PAGES = 2;

    /** Bound on the page-tree walk in totalPages(); a cyclic /Parent chain must not spin. */
    static final int MAX_PAGE_TREE_DEPTH = 64;

    /**
     * Stops handing out image engines once the document's image budget is spent.
     *
     * The counter is Tika's own per-document {@code imageCounter}, so the budget is per
     * DOCUMENT rather than per page -- a thousand-image PDF cannot spend it a page at a time.
     */
    static final class BoundedImageGraphicsEngineFactory extends ImageGraphicsEngineFactory {
        private final int cap;

        BoundedImageGraphicsEngineFactory(int cap) {
            this.cap = cap;
        }

        @Override
        public ImageGraphicsEngine newEngine(PDPage page, int pageNumber,
                EmbeddedDocumentExtractor extractor, PDFParserConfig cfg,
                Map<COSStream, Integer> processedInlineImages, AtomicInteger imageCounter,
                XHTMLContentHandler xhtml, Metadata parentMetadata, ParseContext parseContext) {
            if (cap <= 0) {             // explicitly unbounded
                return super.newEngine(page, pageNumber, extractor, cfg, processedInlineImages,
                        imageCounter, xhtml, parentMetadata, parseContext);
            }
            return new BoundedImageGraphicsEngine(page, pageNumber, extractor, cfg,
                    processedInlineImages, imageCounter, xhtml, parentMetadata, parseContext, cap);
        }
    }

    /** Skips its page's images once the document-wide budget is spent. */
    static final class BoundedImageGraphicsEngine extends ImageGraphicsEngine {
        private final AtomicInteger counter;
        private final int cap;
        private final int tailAllowance;
        private final boolean inTail;

        BoundedImageGraphicsEngine(PDPage page, int pageNumber,
                EmbeddedDocumentExtractor extractor, PDFParserConfig cfg,
                Map<COSStream, Integer> processedInlineImages, AtomicInteger imageCounter,
                XHTMLContentHandler xhtml, Metadata parentMetadata, ParseContext parseContext,
                int cap) {
            super(page, pageNumber, extractor, cfg, processedInlineImages, imageCounter, xhtml,
                  parentMetadata, parseContext);
            this.counter = imageCounter;
            this.cap = cap;
            this.tailAllowance = Math.max(1, cap / 2);
            this.inTail = isTailPage(page, pageNumber);
        }

        /**
         * True for the last {@link #TAIL_PAGES} pages of the document.
         *
         * A pure first-N budget only ever sees the FRONT of a document -- page-one logos and
         * letterhead -- while the payload in a weaponised PDF is as likely to sit at the end.
         * Reserving an allowance for the tail costs one extra page-walk per document and buys
         * coverage of both ends.
         *
         * The total page count is not handed to the factory, but it is reachable: a PDPage's
         * parent /Pages node carries /Count. Best-effort -- any structural surprise (a damaged
         * page tree, a missing parent) means "not a tail page", i.e. the plain cap, never an
         * exception on a hostile file.
         */
        private static boolean isTailPage(PDPage page, int pageNumber) {
            int total = totalPages(page);
            // A tail window only means anything when there is a middle to skip. Without this,
            // a 1- or 2-page PDF -- the commonest shape there is -- has EVERY page classified
            // as tail, which hands the whole document the inflated allowance and disables the
            // page-level skip entirely.
            if (total <= TAIL_PAGES * 2) {
                return false;
            }
            return pageNumber > total - TAIL_PAGES;
        }

        /**
         * Total pages in the document, by walking the page tree to its ROOT.
         *
         * The immediate /Parent is NOT the answer: per PDF 7.7.3.2 an intermediate /Pages node's
         * /Count is only its own leaf descendants, and Acrobat/InDesign routinely emit balanced
         * trees of ~10 kids. Reading the immediate parent on a 100-page file yields total=10 for
         * every page, so pages 9-100 all look like "tail" -- 92% of the document gets the
         * inflated limit and never short-circuits, reinstating exactly the per-page decode this
         * cap exists to prevent.
         *
         * Bounded walk: a malformed or cyclic page tree must not spin here.
         */
        private static int totalPages(PDPage page) {
            try {
                org.apache.pdfbox.cos.COSDictionary node = page.getCOSObject();
                int best = -1;
                for (int hops = 0; hops < MAX_PAGE_TREE_DEPTH; hops++) {
                    org.apache.pdfbox.cos.COSBase parent =
                            node.getDictionaryObject(org.apache.pdfbox.cos.COSName.PARENT);
                    if (!(parent instanceof org.apache.pdfbox.cos.COSDictionary pages)) {
                        break;
                    }
                    int count = pages.getInt(org.apache.pdfbox.cos.COSName.COUNT, -1);
                    if (count > best) {
                        best = count;       // the root carries the largest /Count
                    }
                    node = pages;
                }
                return best;
            } catch (RuntimeException e) {
                return -1;                  // hostile structure: no tail window, plain cap
            }
        }

        /**
         * The budget for THIS page. run() and drawImage() must agree: when run() tested `cap`
         * while drawImage() allowed `cap + tailAllowance`, a tail page never skipped its content
         * stream even after its allowance was spent -- so it decoded every image and discarded
         * all but the allowance, losing the page-level skip that is where the time actually goes
         * (113.6s vs 34.0s).
         */
        private int effectiveLimit() {
            return inTail ? cap + tailAllowance : cap;
        }

        @Override
        public void run() throws java.io.IOException {
            if (counter.get() >= effectiveLimit()) {
                // Budget spent by earlier pages and this is not a reserved tail page: skip the
                // whole content stream. This is where the time is actually saved -- measured
                // 113.6s unbounded vs 34.0s, because it avoids the per-image decode PDFBox does
                // before drawImage() ever gets a say.
                return;
            }
            super.run();
        }

        @Override
        public void drawImage(org.apache.pdfbox.pdmodel.graphics.image.PDImage pdImage)
                throws java.io.IOException {
            // PER IMAGE, not just per page: checking only in run() enforces the cap at PAGE
            // boundaries, so one page carrying hundreds of images still decodes all of them
            // (measured: a cap of 32 let 152 through and saved 6s of 61s).
            //
            // Tail pages get their own allowance so the budget cannot be exhausted by the front
            // of the document.
            if (counter.get() >= effectiveLimit()) {
                return;
            }
            super.drawImage(pdImage);
        }
    }

    private static void enableHtmlScriptExtraction(Parser root) {
        Set<Parser> seen = new java.util.HashSet<>();
        java.util.Deque<Parser> queue = new java.util.ArrayDeque<>();
        queue.add(root);
        while (!queue.isEmpty()) {
            Parser p = queue.poll();
            if (!seen.add(p)) {
                continue;
            }
            if (p instanceof JSoupParser jsp) {
                jsp.setExtractScripts(true);
            } else if (p instanceof CompositeParser cp) {
                queue.addAll(cp.getParsers().values());
            }
        }
    }

    private static void enableImageHashing(Parser root) {
        Set<Parser> seen = new java.util.HashSet<>();
        java.util.Deque<Parser> queue = new java.util.ArrayDeque<>();
        queue.add(root);
        while (!queue.isEmpty()) {
            Parser p = queue.poll();
            if (!seen.add(p)) continue;
            if (p instanceof AbstractImageParser aip) {
                enableImageHashingIfAvailable(aip);
            } else if (p instanceof CompositeParser cp) {
                queue.addAll(cp.getParsers().values());
            }
        }
    }

    @SuppressWarnings({"rawtypes", "unchecked"})
    private static void enableOcrResultCacheIfAvailable(
            ParseContext context, int maxImageDim, boolean skipBlank) {
        try {
            Class cacheClass = Class.forName("org.apache.tika.parser.ocr.OcrResultCache");
            Object cache = cacheClass
                .getConstructor(int.class, boolean.class)
                .newInstance(maxImageDim, skipBlank);
            context.set(cacheClass, cache);
        } catch (ClassNotFoundException | NoSuchMethodException e) {
            // Upstream Tika snapshots do not expose the fork-only OCR cache.
        } catch (ReflectiveOperationException e) {
            LOG.fine("OCR cache unavailable: " + e.getMessage());
        }
    }

    private static void enableImageHashingIfAvailable(AbstractImageParser parser) {
        try {
            parser.getClass().getMethod("setImageHashingEnabled", boolean.class).invoke(parser, true);
        } catch (NoSuchMethodException e) {
            // Upstream Tika snapshots do not expose the fork-only image hashing toggle.
        } catch (ReflectiveOperationException e) {
            LOG.fine("Image hashing unavailable: " + e.getMessage());
        }
    }

    /**
     * Flip {@code imageHashingEnabled} on the OfficeParserConfig if the fork
     * exposes it. EMFParser / WMFParser in the wmetcalf Tika fork gate their
     * rasterize-and-hash branch on this; without it set, embedded EMFs and
     * WMFs come back with no {@code image:phash} / {@code image:dhash} /
     * {@code image:ahash} / {@code image:colorhash}. Upstream Tika does not
     * have the field, so we use reflection and swallow the absence.
     */
    private static void enableMetafileImageHashingIfAvailable(OfficeParserConfig officeCfg) {
        try {
            officeCfg.getClass().getMethod("setImageHashingEnabled", boolean.class)
                    .invoke(officeCfg, true);
        } catch (NoSuchMethodException e) {
            // Older Tika or upstream Tika — fork-only toggle absent.
        } catch (ReflectiveOperationException e) {
            LOG.fine("OfficeParserConfig image hashing unavailable: " + e.getMessage());
        }
    }

    private static Object tikaImageHashProperty(String fieldName) {
        try {
            Class<?> imageHash = Class.forName("org.apache.tika.metadata.ImageHash");
            return imageHash.getField(fieldName).get(null);
        } catch (ReflectiveOperationException e) {
            return null;
        }
    }

    private static String metadataValue(Metadata metadata, Object property) {
        if (property == null) {
            return null;
        }
        try {
            return (String) Metadata.class
                .getMethod("get", property.getClass())
                .invoke(metadata, property);
        } catch (ReflectiveOperationException | ClassCastException e) {
            return metadata.get(property.toString());
        }
    }

    private static String indexOrNull(String[] arr, int i) {
        return (arr != null && i < arr.length) ? arr[i] : null;
    }

    private static boolean parseBool(String s) {
        return s != null && Boolean.parseBoolean(s);
    }

    private static boolean isImageType(String contentType) {
        return contentType != null && contentType.startsWith("image/");
    }

    private static String guessContentType(Metadata m) {
        String ct = m.get("Content-Type");
        if (ct == null || ct.isEmpty()) return "application/octet-stream";
        int semi = ct.indexOf(';');
        return (semi >= 0) ? ct.substring(0, semi).trim() : ct.trim();
    }

    private static String deriveParentPath(String path) {
        if ("/".equals(path)) return null;
        int lastSlash = path.lastIndexOf('/');
        if (lastSlash <= 0) return "/";
        return path.substring(0, lastSlash);
    }

    private static int countDepth(String path) {
        if ("/".equals(path)) return 0;
        int count = 0;
        for (char c : path.toCharArray()) if (c == '/') count++;
        return count;
    }

    private static long parseLong(String s, long defaultVal) {
        if (s == null) return defaultVal;
        try { return Long.parseLong(s.trim()); } catch (NumberFormatException e) { return defaultVal; }
    }

    /**
     * Strip a container-injected path prefix from OCR text.
     * OOXML/ODF parsers write the zip entry path (e.g. "/docProps/thumbnail.jpeg")
     * into the content handler before Tesseract runs. When Tesseract finds no real
     * words in the image, that path string is the entire TIKA_CONTENT. Detect this
     * by checking whether the text, stripped of whitespace, is a single path token
     * that shares a basename with the entry path — if so, return empty string.
     */
    private static String stripContainerPathPrefix(String text, String entryPath) {
        if (text == null || text.isBlank()) return "";
        // Quick path: if there's substantial content beyond path-like characters, keep it.
        String trimmed = text.strip();
        if (trimmed.isEmpty()) return "";
        // Extract the first non-whitespace token
        int end = 0;
        while (end < trimmed.length() && !Character.isWhitespace(trimmed.charAt(end))) {
            end++;
        }
        String firstToken = trimmed.substring(0, end);
        // If the first token looks like a file path (starts with '/', contains '.')
        // and shares a basename with the entry path, strip it.
        if (firstToken.startsWith("/") && firstToken.contains(".")) {
            String tokenBase = firstToken.substring(firstToken.lastIndexOf('/') + 1);
            String entryBase = (entryPath != null && entryPath.contains("/"))
                    ? entryPath.substring(entryPath.lastIndexOf('/') + 1)
                    : (entryPath != null ? entryPath : "");
            if (!entryBase.isEmpty() && tokenBase.equalsIgnoreCase(entryBase)) {
                // The remaining text after the path token
                String rest = trimmed.substring(end).strip();
                return rest;
            }
        }
        return text;
    }

    /**
     * Tika metadata key carrying the FULL extracted body of an entry.
     *
     * Current Tika's output-provenance work puts the whole entry text into the metadata map as
     * well as handing it to the content handler. RedTusk already stores those exact bytes in
     * the entry's `text` field, so copying this through stores every document twice: measured
     * on a 1.4 MB XLSX, metadata.json went 13.0 MB -> 26.1 MB and the job 10.1s -> 18.5s, with
     * one VBA module's metadata weighing 67,092 B against a text field of 66,309 B -- the same
     * content, byte for byte.
     *
     * The OTHER tk: provenance keys (tk:parsed-by, tk:encoding-detection-trace,
     * tk:encoding-detector, tk:content-handler) are small and forensically useful, so only this
     * one is dropped rather than the whole namespace.
     */
    static final String TIKA_CONTENT_KEY = TikaCoreProperties.TIKA_CONTENT.getName();

    /**
     * Bulk internals that are not forensic signal.
     *
     * `tk:chunks` is the chunked copy of the body, i.e. the same duplication as tk:content by
     * another name. The rest of the tk: namespace is KEPT on purpose -- tk:signature:*,
     * tk:has-signature, tk:digest:*, tk:num-images and tk:embedded-resource-type are exactly the
     * kind of thing this engine exists to surface.
     */
    private static final java.util.Set<String> SUPPRESSED_BULK_KEYS =
            java.util.Set.of(TikaCoreProperties.TIKA_CONTENT.getName(), "tk:chunks");

    /**
     * Keys that must never reach the rmeta.
     *
     * Package-private and separate from the loop ON PURPOSE: `Metadata.set("tk:...")` is
     * SILENTLY DROPPED by Tika (the namespace is computed, not settable), so a test that builds
     * a Metadata and asserts the key is absent passes whether or not the filter exists. The
     * first version of this test did exactly that. Testing the predicate directly is the only
     * honest unit-level check.
     */
    static boolean isSuppressedMetadataKey(String name) {
        // X-TIKA: is retained for older pins only. On the current pin the whole namespace was
        // renamed to tk:, so this branch matches NOTHING there -- keeping it costs nothing and
        // means the filter does not silently invert if the pin moves back.
        if (name.startsWith("X-TIKA:") || name.equals("Content-Type")) {
            return true;
        }
        // The entry's full body (and its chunked twin), duplicated into the metadata map by
        // current Tika's output-provenance work. RedTusk already stores those exact bytes in
        // `text`. Names come from TikaCoreProperties, not string literals: the rename that
        // created this bug (X-TIKA:content -> tk:content) is proof the name moves, and a literal
        // would silently start double-storing every body at the next pin bump.
        return SUPPRESSED_BULK_KEYS.contains(name);
    }

    static Map<String, Object> extractMetadata(Metadata m) {
        Map<String, Object> result = new LinkedHashMap<>();
        for (String name : m.names()) {
            if (isSuppressedMetadataKey(name)) continue;
            // Preserve ALL values of multi-valued keys (dc:creator, relationship
            // targets, ...). m.get() kept only the first; m.getValues() keeps them
            // all. Emit a scalar for a single value, a list for several (the
            // schema's metadata object is unconstrained and the Python
            // engine._coerce_metadata_value accepts list[scalar]).
            String[] values = m.getValues(name);
            if (values == null || values.length == 0) continue;
            if (values.length == 1) {
                if (values[0] != null) result.put(name, values[0]);
            } else {
                result.put(name, java.util.Arrays.asList(values));
            }
        }
        return result;
    }

    private static EntryResult errorEntry(
            String path, String parentPath, int depth,
            String contentType, long sizeBytes, String sha256, String errorMsg) {
        return new EntryResult(
            path, parentPath, depth, contentType, sizeBytes, sha256, null, null, false, null, null, null,
            Map.of(), "", null,
            new EntryResult.QrResult(List.of(), "error"),
            new EntryResult.OcrResult("", null, 0, "error"),
            errorMsg
        );
    }
}
