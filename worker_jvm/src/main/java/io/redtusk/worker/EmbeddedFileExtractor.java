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
import java.util.Iterator;
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

    public EmbeddedFileExtractor(int maxDepth, int maxFiles, boolean enableThumbnails) {
        this.maxDepth = maxDepth;
        this.maxFiles = maxFiles;
        this.enableThumbnails = enableThumbnails;
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
        if (!inputFile.exists() || inputFile.length() == 0) return hashes;

        Path embDir = outDir.resolve("embedded");
        try {
            Files.createDirectories(embDir);
        } catch (IOException e) {
            LOG.warning("EmbeddedFileExtractor: cannot create dir: " + e.getMessage());
            return hashes;
        }

        AutoDetectParser parser = new AutoDetectParser();
        enableImageHashing(parser);

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
        context.set(EmbeddedDocumentExtractor.class,
                new SavingExtractor(parser, embDir, maxDepth, maxFiles, enableThumbnails,
                        fileCount, extractedBytesTotal, hashes));
        context.set(Parser.class, parser);
        // OCR already ran in the first pass (ParserRunner). Skip it here to avoid
        // running Tesseract a second time on every file in the extraction pass.
        TesseractOCRConfig noOcr = new TesseractOCRConfig();
        noOcr.setSkipOcr(true);
        context.set(TesseractOCRConfig.class, noOcr);

        // Carry the same PDF and Office config as the first pass so embedded
        // PDFs/Office docs get consistent extraction (marked content, missing rows).
        PDFParserConfig pdfCfg = new PDFParserConfig();
        pdfCfg.setExtractMarkedContent(true);
        pdfCfg.setExtractUniqueInlineImagesOnly(false);
        context.set(PDFParserConfig.class, pdfCfg);
        OfficeParserConfig officeCfg = new OfficeParserConfig();
        officeCfg.setIncludeMissingRows(true);
        context.set(OfficeParserConfig.class, officeCfg);
        RFC822Parser.Config mailCfg = new RFC822Parser.Config();
        mailCfg.setExtractAllAlternatives(true);
        context.set(RFC822Parser.Config.class, mailCfg);

        try (TikaInputStream tis = TikaInputStream.get(inputFile.toPath())) {
            parser.parse(tis, new DefaultHandler(), new Metadata(), context);
        } catch (Exception e) {
            LOG.warning("EmbeddedFileExtractor: parse error on "
                    + inputFile.getName() + ": " + e.getClass().getSimpleName()
                    + ": " + e.getMessage());
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
            Path thumbPath = root.resolve("thumbnails").resolve(rel + ".jpg");
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
    static Path resolveOutFile(Path root, String embPath, Metadata metadata) {
        String rel;
        if (embPath != null && !embPath.isEmpty()) {
            rel = embPath.startsWith("/") ? embPath.substring(1) : embPath;
        } else {
            String name = metadata.get(TikaCoreProperties.RESOURCE_NAME_KEY);
            if (name == null || name.isEmpty()) return null;
            rel = name;
        }
        Path result = root;
        boolean lossy = false;
        String[] parts = rel.split("/");
        for (int idx = 0; idx < parts.length; idx++) {
            String original = parts[idx];
            String part = original.replaceAll("[^a-zA-Z0-9._+\\- ]", "_").trim();
            if (part.isEmpty() || part.equals(".") || part.equals("..")) part = "_";
            // Sanitization is lossy when it changed the component — distinct
            // raw names (e.g. "résumé.doc" vs "resume_.doc", or "a/b" vs "a_b")
            // can collapse to the same sanitized path and silently overwrite
            // each other's saved bytes, desyncing hashes/forensics. When the
            // LAST (filename) component was altered, disambiguate it with a
            // short, deterministic hash of the original relative path so the
            // mapping is stable across Pass-1 and Pass-2 for the same entry.
            if (!part.equals(original)) {
                lossy = true;
            }
            if (lossy && idx == parts.length - 1) {
                part = disambiguate(part, rel);
            }
            result = result.resolve(part);
        }
        if (!result.normalize().startsWith(root.normalize())) return null;
        return result;
    }

    /**
     * Append a short hash of the entry's original relative path to a sanitized
     * filename component so two distinct entries whose names sanitize to the
     * same string land at distinct paths. Deterministic per entry, so Pass-1 and
     * Pass-2 compute the same disambiguated path for the same entry. The hash is
     * inserted before the file extension to keep the suffix recognizable.
     */
    private static String disambiguate(String sanitized, String originalRel) {
        String tag = shortHash(originalRel);
        int dot = sanitized.lastIndexOf('.');
        if (dot > 0) {
            return sanitized.substring(0, dot) + "_" + tag + sanitized.substring(dot);
        }
        return sanitized + "_" + tag;
    }

    /** First 8 hex chars of SHA-256(s); falls back to hashCode hex if unavailable. */
    private static String shortHash(String s) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] d = md.digest(s.getBytes(java.nio.charset.StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder(8);
            for (int i = 0; i < 4; i++) sb.append(String.format("%02x", d[i]));
            return sb.toString();
        } catch (Exception e) {
            return Integer.toHexString(s.hashCode());
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

        private final AutoDetectParser parser;
        private final Path root;
        private final int maxDepth;
        private final int maxFiles;
        private final boolean enableThumbnails;
        private final AtomicInteger fileCount;
        /** Running total of bytes extracted in this pass; aborts past the budget. */
        private final AtomicLong extractedBytesTotal;
        private final Map<String, FileHashes> hashes;

        SavingExtractor(AutoDetectParser parser, Path root, int maxDepth,
                        int maxFiles, boolean enableThumbnails,
                        AtomicInteger fileCount, AtomicLong extractedBytesTotal,
                        Map<String, FileHashes> hashes) {
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
            if (fileCount.get() >= maxFiles) return false;
            String p = metadata.get(TikaCoreProperties.EMBEDDED_RESOURCE_PATH);
            return p == null || countSlashes(p) < maxDepth;
        }

        @Override
        public void parseEmbedded(TikaInputStream stream, ContentHandler handler,
                                   Metadata metadata, ParseContext context, boolean outputHtml)
                throws SAXException, IOException {

            if (fileCount.get() >= maxFiles) return;
            // Aggregate extracted-bytes budget — abort further extraction once a
            // zip/embed bomb has already amplified past the cap.
            if (extractedBytesTotal.get() >= MAX_EXTRACTED_BUDGET_BYTES) {
                LOG.warning("EmbeddedFileExtractor: extracted-bytes budget exceeded ("
                        + extractedBytesTotal.get() + " >= " + MAX_EXTRACTED_BUDGET_BYTES
                        + "); skipping remaining embedded entries");
                return;
            }

            // Buffer bytes with size cap
            byte[] bytes = stream.readNBytes((int) Math.min(MAX_FILE_BYTES, Integer.MAX_VALUE));
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

            // Determine output path — prefer RESOURCE_NAME_KEY over synthetic embedded-N paths.
            String embPath = metadata.get(TikaCoreProperties.EMBEDDED_RESOURCE_PATH);
            if (embPath != null && embPath.matches(".*/embedded-\\d+(\\..*)?$")) {
                String rname = metadata.get(TikaCoreProperties.RESOURCE_NAME_KEY);
                if (rname != null && !rname.isBlank()) {
                    String parent = embPath.substring(0, embPath.lastIndexOf('/'));
                    embPath = parent + "/" + rname;
                }
            }
            Path outFile = EmbeddedFileExtractor.resolveOutFile(root, embPath, metadata);
            if (outFile == null) return;

            // Re-check the aggregate budget WITH this entry's size before writing.
            // The pre-read guard above runs before bytes are buffered, so it
            // can't see this entry's length; without this check a single entry
            // could push extractedBytesTotal past MAX_EXTRACTED_BUDGET_BYTES
            // (bounded by MAX_FILE_BYTES, but still an overshoot of the cap).
            if (extractedBytesTotal.get() + bytes.length > MAX_EXTRACTED_BUDGET_BYTES) {
                LOG.warning("EmbeddedFileExtractor: extracted-bytes budget would be exceeded ("
                        + extractedBytesTotal.get() + " + " + bytes.length + " > "
                        + MAX_EXTRACTED_BUDGET_BYTES + "); skipping entry");
                return;
            }

            // Save file
            try {
                Files.createDirectories(outFile.getParent());
                Files.write(outFile, bytes,
                        StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);
                fileCount.incrementAndGet();
                extractedBytesTotal.addAndGet(bytes.length);
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
            if (embPath != null && countSlashes(embPath) < maxDepth - 1) {
                ParseContext nested = new ParseContext();
                ParserRunner.hardenXmlParsing(nested);
                nested.set(EmbeddedDocumentExtractor.class,
                        new SavingExtractor(parser, root, maxDepth, maxFiles, enableThumbnails,
                                fileCount, extractedBytesTotal, hashes));
                nested.set(Parser.class, parser);
                TesseractOCRConfig noOcr = new TesseractOCRConfig();
                noOcr.setSkipOcr(true);
                nested.set(TesseractOCRConfig.class, noOcr);
                try (TikaInputStream tis = TikaInputStream.get(bytes)) {
                    parser.parse(tis, new DefaultHandler(), new Metadata(), nested);
                } catch (Exception e) {
                    // non-fatal — nested parse errors are common for binary blobs
                }
            }
        }

        private static int countSlashes(String s) {
            if (s == null || s.isEmpty() || s.equals("/")) return 0;
            int n = 0;
            for (char c : s.toCharArray()) if (c == '/') n++;
            return n;
        }

        private static boolean isGenericType(String ct) {
            return ct == null
                || "application/octet-stream".equals(ct)
                || "application/x-tika-msoffice".equals(ct);
        }
    }
}
