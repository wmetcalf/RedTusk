package io.redtusk.worker;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.crac.Core;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.logging.*;

/**
 * Entry point for the RedTusk worker JVM.
 *
 * Modes:
 *   --appcds-warmup <corpus-dir>   parse corpus files to warm parser classes (for AppCDS)
 *   --checkpoint <scratch-dir>     no-op stub (CRaC added in Plan 6)
 *   --run <scratch-dir>            production: fifo-wait → parse → write metadata.json → exit
 *
 * Exit codes: 0=success, 1=parse error, 2=fatal
 */
public final class Main {

    private static final Logger LOG = Logger.getLogger(Main.class.getName());
    private static final ObjectMapper OM = new ObjectMapper();

    public static void main(String[] args) {
        configureLogging();
        if (args.length < 2) {
            System.err.println("Usage: redtusk-worker [--appcds-warmup|--checkpoint|--run] <path>");
            System.exit(2);
        }
        String mode = args[0];
        File path = new File(args[1]);

        try {
            switch (mode) {
                case "--appcds-warmup" -> runWarmup(path);
                case "--checkpoint"    -> runCheckpoint(path);
                case "--run"           -> runJob(path);
                default -> {
                    System.err.println("Unknown mode: " + mode);
                    System.exit(2);
                }
            }
        } catch (Exception e) {
            LOG.severe("Fatal error in mode " + mode + ": " + e.getMessage());
            System.exit(2);
        }
    }

    private static void runWarmup(File corpusDir) throws Exception {
        if (!corpusDir.isDirectory()) {
            System.err.println("warmup corpus is not a directory: " + corpusDir);
            System.exit(2);
        }
        File[] files = corpusDir.listFiles();
        if (files == null || files.length == 0) {
            LOG.info("Warmup corpus is empty — exiting");
            return;
        }
        var limits = new JobDescriptor.LimitsDescriptor(10, 500, 52428800L, 30);
        var runner = new ParserRunner(limits, true, false, "eng", 3,
            2000, true, "/usr/local/bin/ZXingReader", "tesseract");
        for (File f : files) {
            if (!f.isFile()) continue;
            try {
                LOG.info("Warmup: parsing " + f.getName());
                runner.parse(f, f.getName(), "0".repeat(64));
            } catch (Exception e) {
                LOG.warning("Warmup parse failed for " + f.getName() + ": " + e.getMessage());
            }
        }
        LOG.info("Warmup complete — " + files.length + " files processed");
    }

    private static void runCheckpoint(File scratchDir) throws Exception {
        KsmHelper.markHeapMergeable();
        IpcChannel ipc = IpcChannelFactory.forScratchDir(scratchDir);
        ipc.announceReady();

        try {
            Core.checkpointRestore();
        } catch (UnsupportedOperationException e) {
            LOG.warning("CRaC checkpoint not supported on this JVM (non-CRaC JDK): " + e.getMessage());
            // On non-CRaC JVM, fall through and process the job normally (for testing).
        } catch (org.crac.RestoreException e) {
            // Restore-side notification raised — warp restored memory state but
            // one or more registered jdk.crac.Resource threw during their
            // afterRestore callback. Surface the suppressed exceptions instead
            // of letting "checkpoint failed: null" hide the real cause. Don't
            // fail the worker: the process IS restored and can still process
            // a job; we just lost some Resource's restore-time work.
            LOG.warning("CRaC restore notification raised: " + e + " ; suppressed=" + java.util.Arrays.toString(e.getSuppressed()));
            for (Throwable s : e.getSuppressed()) {
                LOG.log(java.util.logging.Level.WARNING, "  suppressed", s);
            }
        } catch (org.crac.CheckpointException e) {
            // Pre-checkpoint notification raised — execution continues in the
            // ORIGINAL instance (no restore). Only relevant at build/checkpoint
            // time; at runtime restore we don't take this branch.
            LOG.severe("CRaC checkpoint notification raised: " + e + " ; suppressed=" + java.util.Arrays.toString(e.getSuppressed()));
            System.exit(2);
        } catch (Throwable t) {
            // Anything else — log full stack trace before exiting so we can
            // see what's actually wrong instead of "null".
            LOG.log(java.util.logging.Level.SEVERE,
                    "CRaC checkpoint/restore failed unexpectedly: " + t.getClass().getName() + " / " + t.getMessage(), t);
            System.exit(2);
        }

        CapDropper.dropCheckpointRestoreCapability();

        // POST-RESTORE FIXUP: the dispatcher bind-mounts a fresh per-slot
        // scratch dir at the same path used at checkpoint time, which hides
        // the in-image control.ready we created above. Re-announce on the
        // (now-mounted) scratch dir so the dispatcher's pool poll_fifo can
        // see the ready signal and transition the slot to IDLE.
        ipc.announceReady();

        processJob(scratchDir, ipc);
    }

    /** Package-private so MainIntegrationTest can call it directly. */
    static void runJob(File scratchDir) throws Exception {
        KsmHelper.markHeapMergeable();
        IpcChannel ipc = IpcChannelFactory.forScratchDir(scratchDir);
        ipc.announceReady();
        processJob(scratchDir, ipc);
    }

    private static void processJob(File scratchDir, IpcChannel ipc) throws Exception {
        String signal = ipc.awaitGoSignal();
        LOG.info("Received signal: " + signal.trim());

        File jobFile = new File(new File(scratchDir, FifoLoop.CONTROL_DIR), "job.json");
        if (!jobFile.exists()) {
            LOG.severe("job.json not found at: " + jobFile);
            System.exit(2);
        }
        JobDescriptor job = OM.readValue(jobFile, JobDescriptor.class);

        File inputFile = new File(job.inputPath());
        File outDir = new File(job.outputDir());
        outDir.mkdirs();

        long start = System.currentTimeMillis();
        ParseResult result;
        try {
            var runner = new ParserRunner(
                job.limits(),
                job.enableQr(), job.enableOcr(),
                job.ocrLang(), job.ocrPsm(),
                job.ocrMaxImageDim(), job.ocrSkipBlank(),
                job.zxingPath(), job.tesseractPath()
            ).setOutputDir(outDir.toPath(), job.enableThumbnails())
             .setDraftSnapshot(job);
            result = runner.parse(inputFile, job.filenameHint(), job.sha256());
        } catch (Exception e) {
            LOG.severe("Parse failed: " + e.getMessage());
            System.exit(1);
            return;
        }
        long durationMs = System.currentTimeMillis() - start;

        // Second pass: save embedded file bytes to outDir/embedded/ and compute digests.
        var fileHashes = new EmbeddedFileExtractor(
            job.limits().maxRecursionDepth(),
            job.limits().maxEmbeddedEntries(),
            job.enableThumbnails()
        ).extract(inputFile, outDir.toPath());

        // Merge per-file digests (sha256/md5/sha1/size) back into the entry results.
        // Always run this loop so we can also mark image entries that Pass 2 missed
        // (fileHashes.get() == null) with a thumbnail_skipped reason — surfaces the
        // gap to the UI instead of silently showing "no thumbnail".
        {
            var updated = new java.util.ArrayList<EntryResult>(result.entries().size());
            for (EntryResult e : result.entries()) {
                var fh = fileHashes.get(e.path());
                if (fh != null) {
                    // Propagate thumbnail skip reason. "zero_byte_stream" from EmbeddedFileExtractor
                    // means Pass 2 received 0 bytes for this entry (common for deeply nested images
                    // or VBA modules whose source was stripped). If Pass 1 still produced a phash
                    // or OCR text the entry is marked so the UI can explain the missing thumbnail.
                    //
                    // NB: Pass 1's inline capture (Pass1ImageCapture) may have already written a
                    // thumbnail before we got here. In that case e.hasThumbnail() is true and we
                    // must not let Pass 2's report downgrade it (e.g. zero_byte_stream from a
                    // SavingExtractor call that received nothing because the bytes were already
                    // consumed elsewhere). OR the two flags and clear the skip reason when a
                    // thumbnail genuinely exists.
                    boolean mergedThumb = e.hasThumbnail() || fh.hasThumbnail();
                    String thumbSkipped = mergedThumb ? null : fh.thumbnailSkipped();
                    // Use Pass-2 magic-detected type when Pass-1 returned a generic type
                    // (application/x-tika-msoffice or application/octet-stream). This surfaces
                    // the actual inner payload type (e.g. PE, XML, image) for OLE-wrapped objects.
                    String contentType = e.contentType();
                    String magic = fh.detectedMagicType();
                    // Defensive copy: errorEntry() uses Map.of() (immutable); direct mutation
                    // would throw UnsupportedOperationException if fh ever matched such an entry.
                    java.util.Map<String, Object> meta = new java.util.LinkedHashMap<>(e.metadata());
                    if (magic != null) {
                        meta.put("Content-Type-Magic-Detected", magic);
                        if (contentType == null
                                || "application/octet-stream".equals(contentType)
                                || "application/x-tika-msoffice".equals(contentType)) {
                            contentType = magic;
                        }
                    }
                    // Prefer Pass-2's byte count (it actually saved the bytes).
                    // BUT if Pass-2 reported any kind of byte-stream miss while
                    // Pass-1 succeeded (mergedThumb=true), Pass-2's 0 overrides
                    // Pass-1's real size and the UI shows "0-byte image with
                    // thumbnail". Generalize the guard so any future Pass-2
                    // skip reason with sizeBytes=0 doesn't reintroduce the
                    // mismatch.
                    long mergedSize = fh.sizeBytes();
                    if (mergedThumb && fh.sizeBytes() == 0 && e.sizeBytes() > 0) {
                        mergedSize = e.sizeBytes();
                    }
                    updated.add(new EntryResult(
                        e.path(), e.parentPath(), e.depth(), contentType,
                        mergedSize,
                        fh.sha256(), fh.md5(), fh.sha1(),
                        mergedThumb,
                        thumbSkipped,
                        e.phash(), e.colorhash(),
                        meta, e.text(), e.language(),
                        e.qr(), e.ocr(), e.error()
                    ));
                } else if (job.enableThumbnails()
                        && e.contentType() != null && e.contentType().startsWith("image/")
                        && !e.hasThumbnail()
                        && e.thumbnailSkipped() == null) {
                    // Pass 2 didn't see this entry but Pass 1 detected it as an
                    // image (and possibly computed a phash). Surface why we can't
                    // show a thumbnail so the UI can render an explanation instead
                    // of silently rendering a missing-image icon. Common cause:
                    // Tika parser path differences between passes (e.g., some MSG
                    // attachment-extraction quirks where the inline image surfaces
                    // in Pass 1's recursive walk but not in Pass 2's SavingExtractor).
                    updated.add(new EntryResult(
                        e.path(), e.parentPath(), e.depth(), e.contentType(),
                        e.sizeBytes(), e.sha256(), e.md5(), e.sha1(),
                        false, "pass2_missed_entry",
                        e.phash(), e.colorhash(),
                        e.metadata(), e.text(), e.language(),
                        e.qr(), e.ocr(), e.error()
                    ));
                } else {
                    updated.add(e);
                }
            }
            result = new ParseResult(updated, result.warnings(), result.truncated());
        }

        // Generate root thumbnail when the input is an image and no thumbnail was produced yet.
        if (job.enableThumbnails()) {
            result = tryGenerateRootThumbnail(result, inputFile, outDir.toPath());
        }

        new RmetaWriter(job, result, durationMs).write(outDir);
        LOG.info("Wrote metadata.json (" + result.entries().size() + " entries, " + durationMs + " ms)");
    }

    /**
     * If the root entry (path="/") is an image type and has no thumbnail, rasterize the
     * input file and write a JPEG thumbnail to {@code outDir/thumbnail.jpg}.
     * Returns an updated ParseResult with hasThumbnail=true on the root entry on success.
     * All failures are non-fatal.
     */
    private static ParseResult tryGenerateRootThumbnail(ParseResult result, File inputFile, Path outDir) {
        if (result.entries().isEmpty()) return result;

        // Find the root entry index
        int rootIdx = -1;
        for (int i = 0; i < result.entries().size(); i++) {
            if ("/".equals(result.entries().get(i).path())) {
                rootIdx = i;
                break;
            }
        }
        if (rootIdx < 0) return result;

        EntryResult rootEntry = result.entries().get(rootIdx);
        if (rootEntry.hasThumbnail()) return result;  // already has one

        String ct = rootEntry.contentType();
        if (ct == null || !ct.startsWith("image/")) return result;

        // Skip thumbnail for large SVGs — Batik's DOM for multi-MB SVGs is expensive
        // and the first pass (trySvgOcr) already ran for phash/OCR. Small SVGs
        // (<2MB) rasterize fast enough that a second pass for the thumbnail is fine.
        if ("image/svg+xml".equals(ct) && inputFile.length() > 2L * 1024 * 1024) {
            return result;
        }

        try {
            byte[] bytes = Files.readAllBytes(inputFile.toPath());

            // Try vector/container formats first, fall back to ImageIO for raster formats
            BufferedImage img = EmbeddedFileExtractor.decodeMetafile(bytes, ct);
            if (img == null) {
                img = ImageIO.read(new ByteArrayInputStream(bytes));
            }
            if (img == null) return result;

            Path thumbPath = outDir.resolve("thumbnail.jpg");
            boolean written = EmbeddedFileExtractor.writeImageAsJpeg(img, thumbPath);
            if (!written) return result;

            // Update root entry with hasThumbnail=true.
            // phash/colorhash are computed by the Tika fork (trySvgOcr, tryHeifOcr, etc.)
            // from the full-resolution rasterization — not derived from the thumbnail.
            EntryResult updated = new EntryResult(
                rootEntry.path(), rootEntry.parentPath(), rootEntry.depth(), rootEntry.contentType(),
                rootEntry.sizeBytes(), rootEntry.sha256(), rootEntry.md5(), rootEntry.sha1(),
                true,   // hasThumbnail
                null,   // thumbnailSkipped
                rootEntry.phash(), rootEntry.colorhash(),
                rootEntry.metadata(), rootEntry.text(), rootEntry.language(),
                rootEntry.qr(), rootEntry.ocr(), rootEntry.error()
            );
            var entries = new ArrayList<>(result.entries());
            entries.set(rootIdx, updated);
            return new ParseResult(entries, result.warnings(), result.truncated());
        } catch (Exception e) {
            LOG.fine("Root thumbnail generation failed: " + e.getMessage());
            return result;
        }
    }

    private static void configureLogging() {
        Logger root = Logger.getLogger("");
        for (Handler h : root.getHandlers()) root.removeHandler(h);
        StreamHandler handler = new StreamHandler(System.err, new SimpleFormatter());
        handler.setLevel(Level.ALL);
        root.addHandler(handler);
        String level = System.getenv().getOrDefault("REDTUSK_LOG_LEVEL", "INFO");
        root.setLevel(Level.parse(level));
    }
}
