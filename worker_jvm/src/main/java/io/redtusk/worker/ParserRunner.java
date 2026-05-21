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
        AutoDetectParser auto = new AutoDetectParser();
        // AutoDetectParser wraps DefaultParser (itself a CompositeParser) — recurse to find
        // the actual AbstractImageParser instances and enable perceptual hashing on each.
        enableImageHashing(auto);
        // JSoupParser.Config in ParseContext is ignored (parser reads instance field, not
        // ParseContext).  Walk the tree to set extractScripts=true on the actual instance.
        enableHtmlScriptExtraction(auto);
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
        PDFParserConfig pdfCfg = new PDFParserConfig();
        pdfCfg.setExtractMarkedContent(true);
        pdfCfg.setExtractUniqueInlineImagesOnly(false);
        context.set(PDFParserConfig.class, pdfCfg);

        // Office: surface hidden/empty rows in Excel workbooks — a common lure technique.
        OfficeParserConfig officeCfg = new OfficeParserConfig();
        officeCfg.setIncludeMissingRows(true);
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

        try (TikaInputStream stream = TikaInputStream.get(inputFile.toPath())) {
            wrapper.parse(stream, handler, rootMeta, context);
        } catch (Exception e) {
            LOG.warning("Tika parse threw [" + e.getClass().getName() + "]: " + e.getMessage()
                    + (e.getCause() != null ? " caused by " + e.getCause().getClass().getName() + ": " + e.getCause().getMessage() : ""));
            return new ParseResult(List.of(errorEntry("/", null, 0,
                guessContentType(rootMeta), inputFile.length(),
                rootSha256, e.getMessage())), List.of(), null);
        }

        List<Metadata> metaList = handler.getMetadataList();
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
            if (pass1Capture != null && i > 0) {
                // Key on the same EMBEDDED_RESOURCE_PATH string the capture
                // recorded post-delegate — survives RecursiveParserWrapperHandler's
                // cloneMetadata in endEmbeddedDocument.
                byte[] imgBytes = pass1Capture.bufferedBytesFor(path);
                if (imgBytes != null) {
                    String thumbCt = pass1Capture.contentTypeFor(path);
                    if (thumbCt == null) thumbCt = contentType;
                    pass1Thumb = writePass1Thumbnail(outDir, path, imgBytes, thumbCt);
                }
            }

            results.add(new EntryResult(
                path, parentPath, depth, contentType, sizeBytes,
                sha256, md5, sha1, pass1Thumb, null, phash, colorhash, metadata, text, language, qr, ocr, null
            ));
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

    private static Map<String, Object> extractMetadata(Metadata m) {
        Map<String, Object> result = new LinkedHashMap<>();
        for (String name : m.names()) {
            if (name.startsWith("X-TIKA:") || name.equals("Content-Type")) continue;
            String value = m.get(name);
            if (value != null) result.put(name, value);
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
