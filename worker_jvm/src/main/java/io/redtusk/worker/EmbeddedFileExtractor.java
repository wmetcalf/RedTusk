package io.redtusk.worker;

import org.apache.tika.extractor.EmbeddedDocumentExtractor;
import org.apache.tika.io.TikaInputStream;
import org.apache.tika.metadata.Metadata;
import org.apache.tika.metadata.TikaCoreProperties;
import org.apache.tika.mime.MediaType;
import org.apache.tika.mime.MimeTypes;
import org.apache.tika.parser.AutoDetectParser;
import org.apache.tika.parser.ParseContext;
import org.apache.tika.parser.Parser;
import org.apache.tika.parser.mail.RFC822Parser;
import org.apache.tika.parser.microsoft.OfficeParserConfig;
import org.apache.tika.parser.ocr.TesseractOCRConfig;
import org.apache.tika.parser.pdf.PDFParserConfig;
import org.xml.sax.ContentHandler;
import org.xml.sax.SAXException;
import org.xml.sax.helpers.DefaultHandler;

import javax.imageio.IIOImage;
import javax.imageio.ImageIO;
import javax.imageio.ImageWriteParam;
import javax.imageio.ImageWriter;
import javax.imageio.stream.MemoryCacheImageOutputStream;
import java.awt.*;
import java.awt.geom.Dimension2D;
import java.awt.geom.Rectangle2D;
import java.awt.image.BufferedImage;
import java.io.*;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;
import java.util.logging.Logger;

/**
 * Second-pass extractor: saves raw embedded file bytes to outDir/embedded/ and
 * computes SHA-256, MD5, and SHA-1 digests for each file.
 *
 * Tika has native digest infrastructure (CommonsDigesterFactory + InputStreamDigester)
 * but threading it through RecursiveParserWrapper for embedded entries requires
 * configuring TikaConfig XML. Since we already hold the raw bytes here, computing
 * digests inline with MessageDigest is simpler and equally correct.
 *
 * Non-fatal: per-file errors are logged and skipped.
 */
public final class EmbeddedFileExtractor {

    private static final Logger LOG = Logger.getLogger(EmbeddedFileExtractor.class.getName());
    static final long MAX_FILE_BYTES = 50L * 1024 * 1024; // 50 MB per-file cap
    /**
     * Aggregate extracted-bytes budget for a single Pass-2 extraction. Without
     * this, a zip/embed bomb (many entries × {@link #MAX_FILE_BYTES} each) can
     * amplify to tens of GB of disk writes (~25 GB at the default 500-entry
     * limit). Mirrors {@code Pass1ImageCapture.MAX_BUFFER_BUDGET_BYTES} (256 MB).
     * Once the running total exceeds this, further entries are skipped.
     */
    static final long MAX_EXTRACTED_BUDGET_BYTES = 256L * 1024 * 1024;

    private final int maxDepth;
    private final int maxFiles;
    private final boolean enableThumbnails;
    private final long maxFileBytes;
    private final long budgetBytes;
    /**
     * Size-cap events of the last {@link #extract} (a file cut at {@link #maxFileBytes}, entries
     * skipped past {@link #budgetBytes}). They used to reach only the worker log, so a capped
     * result looked complete; Main merges these into the result's warnings.
     */
    private final List<ParseResult.WorkerWarning> warnings =
            Collections.synchronizedList(new ArrayList<>());

    public EmbeddedFileExtractor(int maxDepth, int maxFiles, boolean enableThumbnails) {
        this(maxDepth, maxFiles, enableThumbnails, MAX_FILE_BYTES, MAX_EXTRACTED_BUDGET_BYTES);
    }

    /**
     * The job's limits, given to every pass-2 parse context exactly as pass 1 gets them, so
     * Rar5Parser's all-or-nothing entry/byte checks agree between the passes (otherwise pass 1
     * can refuse an archive whose members pass 2 then saves, or the reverse). Null in tests:
     * then a descriptor is built from this extractor's own caps.
     */
    private JobDescriptor.LimitsDescriptor jobLimits;

    /** Use the job's limits for every pass-2 parse context (see {@link #jobLimits}). */
    public EmbeddedFileExtractor useJobLimits(JobDescriptor.LimitsDescriptor limits) {
        this.jobLimits = limits;
        return this;
    }

    private JobDescriptor.LimitsDescriptor limitsForContext() {
        return jobLimits != null ? jobLimits
                : new JobDescriptor.LimitsDescriptor(maxDepth, maxFiles, budgetBytes, 30);
    }

    /**
     * The per-format configs pass 1 uses (PDF inline-image cap, Office, mail), set on EVERY
     * pass-2 context: the top-level one AND each nested container re-parse. A nested context
     * without them parsed a PDF inside a zip with an unbounded inline-image engine.
     */
    static void applySharedConfig(ParseContext context) {
        context.set(PDFParserConfig.class, ParserRunner.newPdfConfig());
        context.set(OfficeParserConfig.class, ParserRunner.newOfficeConfig());
        RFC822Parser.Config mailCfg = new RFC822Parser.Config();
        mailCfg.setExtractAllAlternatives(true);
        context.set(RFC822Parser.Config.class, mailCfg);
        TesseractOCRConfig noOcr = new TesseractOCRConfig();
        noOcr.setSkipOcr(true);
        context.set(TesseractOCRConfig.class, noOcr);
    }

    /** Test seam: the production caps are the 3-arg constructor's. */
    EmbeddedFileExtractor(int maxDepth, int maxFiles, boolean enableThumbnails,
                          long maxFileBytes, long budgetBytes) {
        this.maxDepth = maxDepth;
        this.maxFiles = maxFiles;
        this.enableThumbnails = enableThumbnails;
        this.maxFileBytes = maxFileBytes;
        this.budgetBytes = budgetBytes;
    }

    long maxFileBytes() { return maxFileBytes; }

    long budgetBytes() { return budgetBytes; }

    /** Warnings from the last {@link #extract} call (a copy). */
    public List<ParseResult.WorkerWarning> warnings() {
        synchronized (warnings) {
            return List.copyOf(warnings);
        }
    }

    static final int THUMB_MAX_PX  = 256;  // max dimension of thumbnail
    static final float THUMB_QUALITY = 0.82f; // JPEG quality

    /** SHA-256 / MD5 / SHA-1 digests, thumbnail flag, and magic-detected type for a saved embedded file. */
    public record FileHashes(String sha256, String md5, String sha1,
                             long sizeBytes, boolean hasThumbnail,
                             String thumbnailSkipped, String detectedMagicType) {}

    /**
     * Parse {@code inputFile}, write embedded content to {@code outDir/embedded/},
     * and return a map of (embedded-resource-path → FileHashes).
     */
    public Map<String, FileHashes> extract(File inputFile, Path outDir) {
        Map<String, FileHashes> hashes = new ConcurrentHashMap<>();
        warnings.clear();
        if (!inputFile.exists() || inputFile.length() == 0) return hashes;

        Path embDir = outDir.resolve("embedded");
        try {
            Files.createDirectories(embDir);
        } catch (IOException e) {
            LOG.warning("EmbeddedFileExtractor: cannot create dir: " + e.getMessage());
            return hashes;
        }

        // THE SHARED instance, not a fresh one. `new AutoDetectParser()` here re-ran full SPI
        // discovery on every job -- and on a current Tika that chain builds the ML encoding
        // detectors, costing ~3.6s on a 2-BYTE input (4314ms -> 713ms with them unregistered).
        // It is paid after the go-signal, so the warm snapshot cannot absorb it.
        //
        // Sharing is safe for the same reason it is safe in pass 1: the parser tree is
        // immutable once configured, and per-job state lives in the ParseContext and handler,
        // both still built fresh below. sharedParser() already applies enableImageHashing().
        AutoDetectParser parser = ParserRunner.sharedParser();

        ParseContext context = new ParseContext();
        // XXE / SSRF hardening — same secure JAXP factories Pass-1 uses, so the
        // second extraction pass also rejects external entities, DTDs,
        // stylesheets and remote-resource loading.
        ParserRunner.hardenXmlParsing(context);

        // Embedded recursion / count limits (Tika-side enforcement). Pass-1's
        // RecursiveParserWrapper enforced these; Pass-2 drives AutoDetectParser
        // directly, so without an explicit EmbeddedLimits a malicious container
        // could declare far more nested entries than Pass-1 allowed. Mirror
        // Pass-1's limits here (recursion depth + entry count).
        context.set(org.apache.tika.config.EmbeddedLimits.class,
                new org.apache.tika.config.EmbeddedLimits(maxDepth, false, maxFiles, false));

        AtomicInteger fileCount = new AtomicInteger(0);
        AtomicLong extractedBytesTotal = new AtomicLong(0);
        AtomicInteger budgetSkipped = new AtomicInteger(0);
        AtomicInteger countSkipped = new AtomicInteger(0);
        context.set(EmbeddedDocumentExtractor.class,
                new SavingExtractor(parser, embDir, maxDepth, maxFiles, enableThumbnails,
                        fileCount, extractedBytesTotal, hashes,
                        maxFileBytes, budgetBytes, budgetSkipped, countSkipped, warnings, "", 1));
        context.set(Parser.class, parser);
        // OCR already ran in the first pass (ParserRunner). Skip it here to avoid
        // running Tesseract a second time on every file in the extraction pass.
        TesseractOCRConfig noOcr = new TesseractOCRConfig();
        noOcr.setSkipOcr(true);
        context.set(TesseractOCRConfig.class, noOcr);

        // THE SAME config object pass 1 uses, from one factory method -- not a second copy of
        // the same two lines. The old comment here said it carried the same config; it did not.
        // Pass 1 gained the inline-image cap and this did not, so a capped first pass was
        // followed by an UNBOUNDED second pass over the same document.
        applySharedConfig(context);
        context.set(JobDescriptor.LimitsDescriptor.class, limitsForContext());

        try (TikaInputStream tis = TikaInputStream.get(inputFile.toPath())) {
            parser.parse(tis, new DefaultHandler(), new Metadata(), context);
        } catch (Exception e) {
            LOG.warning("EmbeddedFileExtractor: parse error on "
                    + inputFile.getName() + ": " + e.getClass().getSimpleName()
                    + ": " + e.getMessage());
            // Pass 2 stops at the first member a container parser cannot read, so every later
            // member goes unsaved. Say so: pass 1 may have no entry for those members at all.
            String msg = String.valueOf(e.getMessage());
            warnings.add(new ParseResult.WorkerWarning(
                    "partial_extraction",
                    ("embedded-file pass stopped after " + fileCount.get() + " file(s): "
                            + e.getClass().getSimpleName() + ": "
                            + msg.substring(0, Math.min(msg.length(), 500))),
                    null));
        }
        int capped = countSkipped.get();
        if (capped > 0) {
            warnings.add(new ParseResult.WorkerWarning(
                    "embedded_entries_capped",
                    capped + " embedded entr" + (capped == 1 ? "y" : "ies")
                            + " not written: the per-job limit of " + maxFiles
                            + " embedded files was reached",
                    null));
        }
        int skipped = budgetSkipped.get();
        if (skipped > 0) {
            // One warning per pass, not per entry: a bomb skips thousands.
            warnings.add(new ParseResult.WorkerWarning(
                    "extracted_bytes_budget",
                    skipped + " embedded entr" + (skipped == 1 ? "y" : "ies")
                            + " not written: the per-pass extracted-bytes budget of "
                            + budgetBytes + " bytes was reached",
                    null));
        }
        return hashes;
    }

    // ── helpers ───────────────────────────────────────────────────────────

    /**
     * Decode a vector/container image format (EMF, WMF, HEIC/HEIF, SVG) into a
     * {@link BufferedImage} for thumbnail or hashing purposes.
     * Returns null if the content type is not supported or decoding fails.
     */
    static BufferedImage decodeMetafile(byte[] bytes, String ct) {
        try {
            if ("image/emf".equals(ct) || "image/x-emf".equals(ct)) {
                org.apache.poi.hemf.usermodel.HemfPicture emf =
                    new org.apache.poi.hemf.usermodel.HemfPicture(new ByteArrayInputStream(bytes));
                Dimension2D size = emf.getSize();
                double pw = size.getWidth(), ph = size.getHeight();
                if (pw <= 0 || ph <= 0) return null;
                double scale = Math.min(THUMB_MAX_PX / pw, THUMB_MAX_PX / ph);
                int w = Math.max(1, (int)(pw * scale)), h = Math.max(1, (int)(ph * scale));
                BufferedImage img = new BufferedImage(w, h, BufferedImage.TYPE_INT_ARGB);
                Graphics2D g = img.createGraphics();
                g.setColor(Color.WHITE);
                g.fillRect(0, 0, w, h);
                emf.draw(g, new Rectangle2D.Double(0, 0, w, h));
                g.dispose();
                return img;
            } else if ("image/wmf".equals(ct) || "image/x-wmf".equals(ct)) {
                org.apache.poi.hwmf.usermodel.HwmfPicture wmf =
                    new org.apache.poi.hwmf.usermodel.HwmfPicture(new ByteArrayInputStream(bytes));
                Dimension2D size = wmf.getSize();
                double pw = size.getWidth(), ph = size.getHeight();
                if (pw <= 0 || ph <= 0) return null;
                double scale = Math.min(THUMB_MAX_PX / pw, THUMB_MAX_PX / ph);
                int w = Math.max(1, (int)(pw * scale)), h = Math.max(1, (int)(ph * scale));
                BufferedImage img = new BufferedImage(w, h, BufferedImage.TYPE_INT_ARGB);
                Graphics2D g = img.createGraphics();
                g.setColor(Color.WHITE);
                g.fillRect(0, 0, w, h);
                wmf.draw(g, new Rectangle2D.Double(0, 0, w, h));
                g.dispose();
                return img;
            } else if ("image/heic".equals(ct) || "image/heif".equals(ct) ||
                       "image/heic-sequence".equals(ct) || "image/heif-sequence".equals(ct)) {
                java.nio.file.Path tmpIn  = java.nio.file.Files.createTempFile("redtusk-heif-in-",  ".heic");
                java.nio.file.Path tmpOut = java.nio.file.Files.createTempFile("redtusk-heif-out-", ".png");
                try {
                    java.nio.file.Files.write(tmpIn, bytes);
                    Process proc = new ProcessBuilder(
                            "heif-convert", "-q", "90", tmpIn.toString(), tmpOut.toString())
                        .redirectErrorStream(true).start();
                    boolean done = proc.waitFor(30, java.util.concurrent.TimeUnit.SECONDS);
                    if (!done) { proc.destroyForcibly(); return null; }
                    // heif-convert may produce numbered output for multi-frame files
                    java.nio.file.Path actual = tmpOut;
                    if (!java.nio.file.Files.exists(tmpOut) || java.nio.file.Files.size(tmpOut) == 0) {
                        String base = tmpOut.toString().replaceFirst("\\.png$", "");
                        actual = java.nio.file.Path.of(base + "-1.png");
                    }
                    if (java.nio.file.Files.exists(actual) && java.nio.file.Files.size(actual) > 0) {
                        return ImageIO.read(actual.toFile());
                    }
                } finally {
                    java.nio.file.Files.deleteIfExists(tmpIn);
                    java.nio.file.Files.deleteIfExists(tmpOut);
                    String base = tmpOut.toString().replaceFirst("\\.png$", "");
                    for (int i = 1; i <= 10; i++)
                        java.nio.file.Files.deleteIfExists(java.nio.file.Path.of(base + "-" + i + ".png"));
                }
            } else if ("image/svg+xml".equals(ct)) {
                // Untrusted SVG → Batik. Install a deny-all security policy so a
                // malicious SVG cannot fetch external resources (SSRF, e.g. via
                // <image href="http://..."> or external CSS) or run scripts.
                org.apache.batik.transcoder.image.PNGTranscoder transcoder = newSecureSvgTranscoder();
                transcoder.addTranscodingHint(
                    org.apache.batik.transcoder.image.ImageTranscoder.KEY_MAX_WIDTH, (float) THUMB_MAX_PX);
                transcoder.addTranscodingHint(
                    org.apache.batik.transcoder.image.ImageTranscoder.KEY_MAX_HEIGHT, (float) THUMB_MAX_PX);
                java.io.ByteArrayOutputStream pngOut = new java.io.ByteArrayOutputStream();
                // Write bytes to temp file so Batik can read as URI
                java.nio.file.Path tmp = java.nio.file.Files.createTempFile("redtusk-svg-", ".svg");
                try {
                    java.nio.file.Files.write(tmp, bytes);
                    transcoder.transcode(
                        new org.apache.batik.transcoder.TranscoderInput(tmp.toUri().toString()),
                        new org.apache.batik.transcoder.TranscoderOutput(pngOut));
                } finally {
                    java.nio.file.Files.deleteIfExists(tmp);
                }
                byte[] pngBytes = pngOut.toByteArray();
                if (pngBytes.length > 0) {
                    return javax.imageio.ImageIO.read(new java.io.ByteArrayInputStream(pngBytes));
                }
            }
        } catch (Exception e) {
            LOG.fine("EmbeddedFileExtractor: metafile decode failed (" + ct + "): " + e.getMessage());
        }
        return null;
    }

    /**
     * Build a {@link org.apache.batik.transcoder.image.PNGTranscoder} hardened
     * against untrusted SVG. We override the transcoder's UserAgent so that:
     * <ul>
     *   <li>{@code getExternalResourceSecurity} returns
     *       {@code NoLoadExternalResourceSecurity} — every external resource
     *       (remote {@code <image>}, external CSS/DTD, {@code use href},
     *       {@code xlink:href}) is denied, killing the SSRF vector
     *       (CVE-2022-44729 / CVE-2022-44730 class).</li>
     *   <li>{@code getScriptSecurity} returns {@code NoLoadScriptSecurity} —
     *       no SVG {@code <script>} or event-handler script executes.</li>
     * </ul>
     * We also set {@code KEY_ALLOW_EXTERNAL_RESOURCES=false},
     * {@code KEY_CONSTRAIN_SCRIPT_ORIGIN=true} and {@code KEY_EXECUTE_ONLOAD=false}
     * as belt-and-suspenders TranscodingHints. Thumbnailing of benign SVG (which
     * needs no external resources or scripts) is unaffected.
     */
    static org.apache.batik.transcoder.image.PNGTranscoder newSecureSvgTranscoder() {
        org.apache.batik.transcoder.image.PNGTranscoder transcoder =
            new org.apache.batik.transcoder.image.PNGTranscoder() {
                @Override
                protected org.apache.batik.bridge.UserAgent createUserAgent() {
                    // UserAgentAdapter is the public, version-stable UserAgent
                    // base. Its defaults allow (relaxed) external resources and
                    // scripts; override the two security hooks to deny-all.
                    return new org.apache.batik.bridge.UserAgentAdapter() {
                        @Override
                        public org.apache.batik.bridge.ExternalResourceSecurity
                                getExternalResourceSecurity(org.apache.batik.util.ParsedURL resourceURL,
                                                            org.apache.batik.util.ParsedURL docURL) {
                            // Deny ALL external resource loading (SSRF guard).
                            return new org.apache.batik.bridge.NoLoadExternalResourceSecurity();
                        }

                        @Override
                        public org.apache.batik.bridge.ScriptSecurity
                                getScriptSecurity(String scriptType,
                                                  org.apache.batik.util.ParsedURL scriptURL,
                                                  org.apache.batik.util.ParsedURL docURL) {
                            // Deny ALL script execution.
                            return new org.apache.batik.bridge.NoLoadScriptSecurity(scriptType);
                        }
                    };
                }
            };
        // Belt-and-suspenders TranscodingHints.
        transcoder.addTranscodingHint(
            org.apache.batik.transcoder.SVGAbstractTranscoder.KEY_CONSTRAIN_SCRIPT_ORIGIN, Boolean.TRUE);
        transcoder.addTranscodingHint(
            org.apache.batik.transcoder.SVGAbstractTranscoder.KEY_EXECUTE_ONLOAD, Boolean.FALSE);
        setHintIfPresent(transcoder, "KEY_ALLOW_EXTERNAL_RESOURCES", Boolean.FALSE);
        return transcoder;
    }

    /** Set a TranscodingHint by reflective key name so the worker still compiles
     *  against Batik builds that lack a given KEY constant (e.g. the
     *  CVE-2022-44729 KEY_ALLOW_EXTERNAL_RESOURCES hint added in newer Batik). */
    private static void setHintIfPresent(org.apache.batik.transcoder.Transcoder t,
                                         String keyFieldName, Object value) {
        try {
            java.lang.reflect.Field f =
                org.apache.batik.transcoder.SVGAbstractTranscoder.class.getField(keyFieldName);
            Object key = f.get(null);
            if (key instanceof org.apache.batik.transcoder.TranscodingHints.Key k) {
                t.addTranscodingHint(k, value);
            }
        } catch (ReflectiveOperationException | RuntimeException e) {
            LOG.fine("Batik hint " + keyFieldName + " unavailable: " + e.getMessage());
        }
    }

    /**
     * Scale {@code src} to at most {@link #THUMB_MAX_PX} on the longest side and
     * write as a JPEG to {@code destPath}.  Returns true on success.
     */
    static boolean writeImageAsJpeg(BufferedImage src, Path destPath) {
        try {
            int w = src.getWidth(), h = src.getHeight();
            double scale = Math.min((double) THUMB_MAX_PX / w, (double) THUMB_MAX_PX / h);
            int tw = Math.max(1, (int) (w * scale));
            int th = Math.max(1, (int) (h * scale));

            BufferedImage thumb = new BufferedImage(tw, th, BufferedImage.TYPE_INT_RGB);
            Graphics2D g = thumb.createGraphics();
            g.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BILINEAR);
            g.setColor(Color.WHITE);
            g.fillRect(0, 0, tw, th);
            g.drawImage(src, 0, 0, tw, th, null);
            g.dispose();

            Files.createDirectories(destPath.getParent());
            Iterator<ImageWriter> writers = ImageIO.getImageWritersByFormatName("jpeg");
            if (!writers.hasNext()) return false;
            ImageWriter writer = writers.next();
            ImageWriteParam param = writer.getDefaultWriteParam();
            param.setCompressionMode(ImageWriteParam.MODE_EXPLICIT);
            param.setCompressionQuality(THUMB_QUALITY);
            try (OutputStream os = Files.newOutputStream(destPath);
                 MemoryCacheImageOutputStream ios = new MemoryCacheImageOutputStream(os)) {
                writer.setOutput(ios);
                writer.write(null, new IIOImage(thumb, null, null), param);
            } finally {
                writer.dispose();
            }
            return true;
        } catch (Exception e) {
            LOG.fine("EmbeddedFileExtractor: writeImageAsJpeg failed: " + e.getMessage());
            return false;
        }
    }

    /**
     * Write a JPEG thumbnail of {@code bytes} to {@code root/thumbnails/<rel-to-root>.jpg}.
     * Returns true if the thumbnail was written successfully.
     * Supports JPEG/PNG/GIF/BMP via ImageIO, plus EMF/WMF via Apache POI scratchpad.
     */
    static boolean writeThumbnail(byte[] bytes, String contentType, Path root, Path originalFile) {
        try {
            BufferedImage src = ImageIO.read(new ByteArrayInputStream(bytes));
            if (src == null) src = decodeMetafile(bytes, contentType);
            if (src == null) return false;

            // Scale proportionally, longest side → THUMB_MAX_PX
            int w = src.getWidth(), h = src.getHeight();
            double scale = Math.min((double) THUMB_MAX_PX / w, (double) THUMB_MAX_PX / h);
            int tw = Math.max(1, (int) (w * scale));
            int th = Math.max(1, (int) (h * scale));

            BufferedImage thumb = new BufferedImage(tw, th, BufferedImage.TYPE_INT_RGB);
            Graphics2D g = thumb.createGraphics();
            g.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BILINEAR);
            g.setColor(Color.WHITE);
            g.fillRect(0, 0, tw, th);
            g.drawImage(src, 0, 0, tw, th, null);
            g.dispose();

            // Mirror the relative path under thumbnails/, append .jpg
            Path rel = root.relativize(originalFile);
            Path thumbPath = root.resolve(THUMBNAILS_DIR).resolve(rel + ".jpg");
            Files.createDirectories(thumbPath.getParent());

            // Write JPEG at configured quality
            Iterator<ImageWriter> writers = ImageIO.getImageWritersByFormatName("jpeg");
            if (!writers.hasNext()) return false;
            ImageWriter writer = writers.next();
            ImageWriteParam param = writer.getDefaultWriteParam();
            param.setCompressionMode(ImageWriteParam.MODE_EXPLICIT);
            param.setCompressionQuality(THUMB_QUALITY);
            try (OutputStream os = Files.newOutputStream(thumbPath);
                 MemoryCacheImageOutputStream ios = new MemoryCacheImageOutputStream(os)) {
                writer.setOutput(ios);
                writer.write(null, new IIOImage(thumb, null, null), param);
            } finally {
                writer.dispose();
            }
            return true;
        } catch (Exception e) {
            LOG.fine("EmbeddedFileExtractor: thumbnail failed: " + e.getMessage());
            return false;
        }
    }

    private static String hex(byte[] b) {
        StringBuilder sb = new StringBuilder(b.length * 2);
        for (byte x : b) sb.append(String.format("%02x", x));
        return sb.toString();
    }

    /**
     * Resolve where to save bytes for an embedded entry, sanitizing path components
     * and refusing escapes outside {@code root}. Package-private so Pass-1 capture
     * (Pass1ImageCapture) writes to the same paths Pass 2 would use, keeping the
     * thumbnail artifact tree consistent regardless of which pass produced the file.
     */
    /** Top-level directory under the embedded root that only {@link #writeThumbnail} writes. */
    static final String THUMBNAILS_DIR = "thumbnails";

    /** Per-pass cap on individual resource_path_collision warnings (a hostile archive repeats). */
    static final int MAX_COLLISION_WARNINGS = 50;

    static Path resolveOutFile(Path root, String embPath, Metadata metadata) {
        String rel;
        if (embPath != null && !embPath.isEmpty()) {
            rel = embPath.startsWith("/") ? embPath.substring(1) : embPath;
        } else {
            String name = metadata.get(TikaCoreProperties.RESOURCE_NAME_KEY);
            if (name == null || name.isEmpty()) return null;
            rel = name;
        }
        // Resource names are provenance, not filesystem structure. A container
        // named nested.rar and its child nested.rar/hello.txt must both be files.
        // Stable hashed directories also bound hostile name lengths and prevent
        // lossy Unicode sanitization from overwriting another resource. Every entry
        // lands under objects/, so none can reach THUMBNAILS_DIR, which belongs to
        // writeThumbnail.
        try {
            String digest = hex(MessageDigest.getInstance("SHA-256")
                .digest(rel.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            return root.resolve("objects").resolve(digest).resolve("content");
        } catch (java.security.NoSuchAlgorithmException impossible) {
            throw new IllegalStateException("SHA-256 is required", impossible);
        }
    }

    private static void enableImageHashing(Parser root) {
        java.util.Set<Parser> seen = new java.util.HashSet<>();
        java.util.Deque<Parser> queue = new java.util.ArrayDeque<>();
        queue.add(root);
        while (!queue.isEmpty()) {
            Parser p = queue.poll();
            if (!seen.add(p)) continue;
            if (p instanceof org.apache.tika.parser.image.AbstractImageParser aip)
                enableImageHashingIfAvailable(aip);
            else if (p instanceof org.apache.tika.parser.CompositeParser cp)
                queue.addAll(cp.getParsers().values());
            else if (p instanceof org.apache.tika.parser.ParserDecorator pd)
                queue.add(pd.getWrappedParser());
        }
    }

    private static void enableImageHashingIfAvailable(org.apache.tika.parser.image.AbstractImageParser parser) {
        try {
            parser.getClass().getMethod("setImageHashingEnabled", boolean.class).invoke(parser, true);
        } catch (NoSuchMethodException e) {
            // Upstream Tika snapshots do not expose the fork-only image hashing toggle.
        } catch (ReflectiveOperationException e) {
            LOG.fine("EmbeddedFileExtractor: image hashing unavailable: " + e.getMessage());
        }
    }

    // ── per-entry saver ───────────────────────────────────────────────────

    private static final class SavingExtractor implements EmbeddedDocumentExtractor {

        private final String parentPath;
        /**
         * Container depth of the entries this extractor receives: 1 for the submitted file's
         * own members, +1 per nested container this pass recursed into. Directory components
         * inside an archive member's name ("documents/report.txt") are NOT containers, so
         * depth is tracked here rather than by counting slashes in provenance names.
         */
        private final int depth;
        private final AutoDetectParser parser;
        private final Path root;
        private final int maxDepth;
        private final int maxFiles;
        private final boolean enableThumbnails;
        private final AtomicInteger fileCount;
        /** Running total of bytes extracted in this pass; aborts past the budget. */
        private final AtomicLong extractedBytesTotal;
        private final Map<String, FileHashes> hashes;
        private final long maxFileBytes;
        private final long budgetBytes;
        private final AtomicInteger budgetSkipped;
        /** Entries refused because maxFiles was reached; reported once per pass by extract(). */
        private final AtomicInteger countSkipped;
        private final List<ParseResult.WorkerWarning> warnings;

        SavingExtractor(AutoDetectParser parser, Path root, int maxDepth,
                        int maxFiles, boolean enableThumbnails,
                        AtomicInteger fileCount, AtomicLong extractedBytesTotal,
                        Map<String, FileHashes> hashes,
                        long maxFileBytes, long budgetBytes, AtomicInteger budgetSkipped,
                        AtomicInteger countSkipped,
                        List<ParseResult.WorkerWarning> warnings, String parentPath, int depth) {
            this.maxFileBytes        = maxFileBytes;
            this.budgetBytes         = budgetBytes;
            this.budgetSkipped       = budgetSkipped;
            this.countSkipped        = countSkipped;
            this.warnings            = warnings;
            this.parentPath          = parentPath;
            this.depth               = depth;
            this.parser              = parser;
            this.root                = root;
            this.maxDepth            = maxDepth;
            this.maxFiles            = maxFiles;
            this.enableThumbnails    = enableThumbnails;
            this.fileCount           = fileCount;
            this.extractedBytesTotal = extractedBytesTotal;
            this.hashes              = hashes;
        }

        @Override
        public boolean shouldParseEmbedded(Metadata metadata) {
            if (fileCount.get() >= maxFiles) {
                countSkipped.incrementAndGet();
                return false;
            }
            String p = metadata.get(TikaCoreProperties.EMBEDDED_RESOURCE_PATH);
            return depth <= maxDepth;
        }

        @Override
        public void parseEmbedded(TikaInputStream stream, ContentHandler handler,
                                   Metadata metadata, ParseContext context, boolean outputHtml)
                throws SAXException, IOException {

            if (fileCount.get() >= maxFiles) {
                countSkipped.incrementAndGet();
                return;
            }
            // The SAME identity ResourcePaths.resolve gives the entry in pass 1: the container's
            // path + "/" + the normalised resource name (RESOURCE_NAME_KEY, else INTERNAL_PATH,
            // else the last segment of the parser's path). Main merges pass-2 bytes and hashes
            // onto pass-1 entries by this path, and the stored object is keyed by it.
            String raw = metadata.get(TikaCoreProperties.EMBEDDED_RESOURCE_PATH);
            String name = metadata.get(TikaCoreProperties.RESOURCE_NAME_KEY);
            if (name == null || name.isBlank()) name = metadata.get(TikaCoreProperties.INTERNAL_PATH);
            if ((name == null || name.isBlank()) && raw != null && !raw.isBlank())
                name = raw.substring(raw.lastIndexOf('/') + 1);
            if (name == null || name.isBlank()) return;
            String declared = parentPath + "/" + ResourcePaths.normalizeName(name);
            metadata.set(TikaCoreProperties.EMBEDDED_RESOURCE_PATH, declared);
            if (depth > maxDepth) return;
            // Aggregate extracted-bytes budget — abort further extraction once a
            // zip/embed bomb has already amplified past the cap.
            if (extractedBytesTotal.get() >= budgetBytes) {
                LOG.warning("EmbeddedFileExtractor: extracted-bytes budget exceeded ("
                        + extractedBytesTotal.get() + " >= " + budgetBytes
                        + "); skipping remaining embedded entries");
                budgetSkipped.incrementAndGet();
                return;
            }

            // Buffer bytes with size cap
            int cap = (int) Math.min(maxFileBytes, Integer.MAX_VALUE);
            byte[] bytes = stream.readNBytes(cap);
            // A full buffer is ambiguous (exactly cap bytes, or more): probe one byte so only a
            // real cut is reported.
            boolean cut = bytes.length == cap && stream.read() != -1;
            if (bytes.length == 0) {
                String embPath0 = metadata.get(TikaCoreProperties.EMBEDDED_RESOURCE_PATH);
                String hashKey0;
                if (embPath0 != null && !embPath0.isEmpty()) {
                    hashKey0 = embPath0;
                } else {
                    String rname = metadata.get(TikaCoreProperties.RESOURCE_NAME_KEY);
                    hashKey0 = "/" + (rname != null && !rname.isEmpty() ? rname : "unknown");
                }
                hashes.put(hashKey0, new FileHashes(null, null, null, 0, false, "zero_byte_stream", null));
                return;
            }

            String embPath = metadata.get(TikaCoreProperties.EMBEDDED_RESOURCE_PATH);
            if (embPath != null && hashes.containsKey(embPath)) {
                // Two entries with one identity (e.g. "a\\b" and "a/b", or a repeated name)
                // would share a storage path: the second write would destroy the first's bytes
                // and its hashes would be attributed to both. Keep both, under distinct keys.
                String original = embPath;
                int n = 2;
                while (hashes.containsKey(original + "#" + n)) n++;
                embPath = original + "#" + n;
                metadata.set(TikaCoreProperties.EMBEDDED_RESOURCE_PATH, embPath);
                if (warnings.stream().filter(w -> "resource_path_collision".equals(w.code())).count()
                        < MAX_COLLISION_WARNINGS) {
                    warnings.add(new ParseResult.WorkerWarning("resource_path_collision",
                            "two embedded entries share the identity " + original
                                    + "; the later one is kept as " + embPath, original));
                }
            }
            Path outFile = EmbeddedFileExtractor.resolveOutFile(root, embPath, metadata);
            if (outFile == null) return;

            // Re-check the aggregate budget WITH this entry's size before writing.
            // The pre-read guard above runs before bytes are buffered, so it
            // can't see this entry's length; without this check a single entry
            // could push extractedBytesTotal past MAX_EXTRACTED_BUDGET_BYTES
            // (bounded by MAX_FILE_BYTES, but still an overshoot of the cap).
            if (extractedBytesTotal.get() + bytes.length > budgetBytes) {
                LOG.warning("EmbeddedFileExtractor: extracted-bytes budget would be exceeded ("
                        + extractedBytesTotal.get() + " + " + bytes.length + " > "
                        + budgetBytes + "); skipping entry");
                budgetSkipped.incrementAndGet();
                return;
            }

            // Save file
            try {
                Files.createDirectories(outFile.getParent());
                Files.write(outFile, bytes,
                        StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);
                fileCount.incrementAndGet();
                extractedBytesTotal.addAndGet(bytes.length);
                if (cut) {
                    String where = embPath != null && !embPath.isEmpty() ? embPath
                            : "/" + root.relativize(outFile).toString().replace(File.separatorChar, '/');
                    warnings.add(new ParseResult.WorkerWarning(
                            "embedded_file_truncated",
                            "embedded file truncated to the " + cap + "-byte per-file cap; "
                                    + "hashes and size describe the truncated bytes",
                            where));
                }
            } catch (IOException e) {
                LOG.warning("EmbeddedFileExtractor: write failed " + outFile + ": " + e.getMessage());
                return;
            }

            // Compute SHA-256, MD5, SHA-1 from the same byte array.
            // Key must match the EMBEDDED_RESOURCE_PATH format from RecursiveParserWrapper
            // (e.g. "/image-0.png").  In the second pass, embPath is null because
            // AutoDetectParser doesn't set it — use the resource name with a leading /.
            String hashKey;
            if (embPath != null && !embPath.isEmpty()) {
                hashKey = embPath;
            } else {
                String rname = metadata.get(TikaCoreProperties.RESOURCE_NAME_KEY);
                hashKey = "/" + (rname != null && !rname.isEmpty()
                                 ? rname : outFile.getFileName().toString());
            }
            boolean thumb = false;
            String ct = metadata.get(Metadata.CONTENT_TYPE);

            // Re-detect content type from raw bytes only (no filename hint).
            // Passing the resource name would let NameDetector override magic=octet-stream
            // with the extension type, misclassifying unknown binaries as document types.
            String detectedMagicType = null;
            try (TikaInputStream detectStream = TikaInputStream.get(bytes)) {
                MediaType mt = parser.getDetector().detect(detectStream, new Metadata(), new ParseContext());
                if (mt != null && !MediaType.OCTET_STREAM.equals(mt)) {
                    detectedMagicType = mt.toString();
                }
            } catch (Exception ignore) {}

            try {
                // Single-pass digest: update all three from the same byte array
                MessageDigest dSha256 = MessageDigest.getInstance("SHA-256");
                MessageDigest dMd5    = MessageDigest.getInstance("MD5");
                MessageDigest dSha1   = MessageDigest.getInstance("SHA-1");
                dSha256.update(bytes);
                dMd5.update(bytes);
                dSha1.update(bytes);
                String sha256 = hex(dSha256.digest());
                String md5    = hex(dMd5.digest());
                String sha1   = hex(dSha1.digest());
                // Use detected type for thumbnail check when Pass-1 reported a generic type
                String thumbCt = isGenericType(ct) && detectedMagicType != null ? detectedMagicType : ct;
                if (enableThumbnails && thumbCt != null && thumbCt.startsWith("image/")) {
                    thumb = writeThumbnail(bytes, thumbCt, root, outFile);
                }
                hashes.put(hashKey, new FileHashes(sha256, md5, sha1, bytes.length, thumb, null, detectedMagicType));
            } catch (Exception ex) {
                LOG.warning("EmbeddedFileExtractor: hash/thumb failed: " + ex.getMessage());
                hashes.put(hashKey, new FileHashes(null, null, null, bytes.length, false, null, detectedMagicType));
            }

            // Recurse into nested embedded content
            if (embPath != null && depth < maxDepth) {
                ParseContext nested = new ParseContext();
                ParserRunner.hardenXmlParsing(nested);
                nested.set(EmbeddedDocumentExtractor.class,
                        new SavingExtractor(parser, root, maxDepth, maxFiles, enableThumbnails,
                                fileCount, extractedBytesTotal, hashes,
                                maxFileBytes, budgetBytes, budgetSkipped, countSkipped, warnings,
                                hashKey, depth + 1));
                nested.set(Parser.class, parser);
                // Same per-format configs and job limits as pass 1 and the top-level pass-2
                // context. The file count and byte budget are still enforced across nesting by
                // the shared fileCount / extractedBytesTotal counters.
                applySharedConfig(nested);
                JobDescriptor.LimitsDescriptor nestedLimits =
                        context.get(JobDescriptor.LimitsDescriptor.class);
                if (nestedLimits == null) {
                    nestedLimits = new JobDescriptor.LimitsDescriptor(maxDepth, maxFiles, budgetBytes, 30);
                }
                nested.set(JobDescriptor.LimitsDescriptor.class, nestedLimits);
                nested.set(org.apache.tika.config.EmbeddedLimits.class,
                        new org.apache.tika.config.EmbeddedLimits(maxDepth, false, maxFiles, false));
                try (TikaInputStream tis = TikaInputStream.get(bytes)) {
                    parser.parse(tis, new DefaultHandler(), new Metadata(), nested);
                } catch (Exception e) {
                    // non-fatal — nested parse errors are common for binary blobs
                }
            }
        }

        private static boolean isGenericType(String ct) {
            return ct == null
                || "application/octet-stream".equals(ct)
                || "application/x-tika-msoffice".equals(ct);
        }
    }
}
