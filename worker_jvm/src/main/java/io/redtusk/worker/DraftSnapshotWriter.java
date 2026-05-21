package io.redtusk.worker;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.apache.tika.metadata.Metadata;
import org.apache.tika.metadata.TikaCoreProperties;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Instant;
import java.util.List;
import java.util.concurrent.atomic.AtomicLong;
import java.util.logging.Logger;

/**
 * Writes / overwrites {@code outDir/metadata.json} with a partial result
 * snapshot after each entry the recursive walk produces. The snapshot is
 * marked {@code truncated.reason="in_progress"} so callers can distinguish
 * "the worker died mid-parse and this is what we got" from a complete result.
 *
 * <p>On normal completion the snapshot file is replaced by {@link RmetaWriter}'s
 * final, fully-enriched metadata.json (hashes, thumbnails, Pass-2 merge). The
 * dispatcher's timeout-salvage path picks up the in-progress snapshot when
 * the worker is SIGKILLed past job_timeout_s.</p>
 *
 * <p>Writes are atomic (tmp + rename) and throttled to at most one per
 * {@link #MIN_INTERVAL_MS}ms so a 10K-entry container doesn't generate 10K
 * fsync-equivalents. The first and last entries always flush; intermediate
 * ones obey the throttle.</p>
 */
final class DraftSnapshotWriter {

    private static final Logger LOG = Logger.getLogger(DraftSnapshotWriter.class.getName());
    private static final ObjectMapper OM = new ObjectMapper();
    /** Throttle: at most one snapshot per this many ms (ignored for the first call). */
    private static final long MIN_INTERVAL_MS = 250;

    private final JobDescriptor job;
    private final File outDir;
    private final long startMs;
    private final AtomicLong lastWriteMs = new AtomicLong(0);

    DraftSnapshotWriter(JobDescriptor job, File outDir) {
        this.job = job;
        this.outDir = outDir;
        this.startMs = System.currentTimeMillis();
    }

    /** Flush a snapshot now, regardless of throttle. Used at end-of-parse. */
    void flushNow(List<Metadata> metaList) {
        write(metaList);
    }

    /** Flush a snapshot if enough time has passed since the previous write. */
    void maybeFlush(List<Metadata> metaList) {
        long now = System.currentTimeMillis();
        long last = lastWriteMs.get();
        if (last != 0 && (now - last) < MIN_INTERVAL_MS) return;
        if (!lastWriteMs.compareAndSet(last, now)) return;  // someone else just wrote
        write(metaList);
    }

    private void write(List<Metadata> metaList) {
        try {
            File metaFile = new File(outDir, "metadata.json");
            Path tmp = Files.createTempFile(outDir.toPath(), "metadata-", ".json.tmp");
            try {
                OM.writerWithDefaultPrettyPrinter().writeValue(tmp.toFile(), buildDoc(metaList));
                Files.move(tmp, metaFile.toPath(),
                        StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
            } finally {
                Files.deleteIfExists(tmp);
            }
        } catch (Exception e) {
            // Never fail the parse over a draft-write failure — it's best-effort
            // salvage, not load-bearing for the happy path.
            LOG.fine("DraftSnapshotWriter: write failed: " + e.getMessage());
        }
    }

    /**
     * Build a schema-valid rmeta document from the metaList as-it-is right now.
     * Entry shape is intentionally minimal: path, content type, text, OCR
     * (whatever ran inline during the parse), language, and metadata. Hashes,
     * thumbnails, QR, and language-detection refinement are filled by the
     * post-parse pipeline in ParserRunner / Main and don't exist yet.
     */
    private ObjectNode buildDoc(List<Metadata> metaList) {
        ObjectNode root = OM.createObjectNode();
        root.put("redtusk_version", job.redtuskVersion());

        ObjectNode input = root.putObject("input");
        input.put("sha256", job.sha256());
        // size_bytes from the root entry if present; fall back to whatever the
        // dispatcher staged. Root entry's Content-Length isn't set by Tika so
        // 0 is acceptable for the draft schema (size is integer >= 0).
        input.put("size_bytes", rootSize(metaList));
        if (job.filenameHint() != null) input.put("filename_hint", job.filenameHint());
        else input.putNull("filename_hint");
        input.put("submitted_at", Instant.now().toString());

        ObjectNode extraction = root.putObject("extraction");
        extraction.put("root_content_type", "application/octet-stream");
        extraction.putNull("root_language");
        extraction.put("duration_ms", System.currentTimeMillis() - startMs);
        ArrayNode entries = extraction.putArray("entries");

        // Schema requires entries[0].path=="/", depth==0, parent_path==null.
        // RecursiveParserWrapperHandler only adds the root metadata to its list
        // in endDocument (at position 0) — meaning during a mid-parse snapshot
        // there is NO root yet. Synthesize a stub root so the draft validates;
        // it'll be replaced by the real root entry when the final write happens.
        entries.add(buildStubRoot());
        for (Metadata m : metaList) {
            // Skip a real root metadata if it's already in the list at index 0
            // (happens after endDocument runs). Identified by an EMBEDDED_RESOURCE_PATH
            // that's either null or "/" — both indicate the container, not a child.
            String ep = m.get(TikaCoreProperties.EMBEDDED_RESOURCE_PATH);
            if (ep == null || ep.isEmpty() || "/".equals(ep)) continue;
            entries.add(buildEntry(m));
        }

        ObjectNode limits = root.putObject("limits");
        limits.put("max_recursion_depth", job.limits().maxRecursionDepth());
        limits.put("max_embedded_entries", job.limits().maxEmbeddedEntries());
        limits.put("max_extracted_bytes", job.limits().maxExtractedBytes());
        limits.put("ocr_timeout_s", job.limits().ocrTimeoutS());

        // Sentinel: this is a mid-parse snapshot. Final write replaces this
        // with null (or a real truncation reason). Dispatcher rewrites this to
        // "job_timeout" when promoting a draft on SIGKILL.
        ObjectNode tr = root.putObject("truncated");
        tr.put("reason", "in_progress");
        tr.put("limit", 0);
        tr.put("observed", metaList.size());

        root.putArray("warnings");

        ObjectNode sandbox = root.putObject("sandbox");
        sandbox.put("profile", job.sandboxProfile());
        sandbox.put("runtime", job.sandboxRuntime());
        sandbox.put("appcds", job.appcds());
        sandbox.put("ksm", job.ksm());
        sandbox.put("crac", job.crac());

        return root;
    }

    private static long rootSize(List<Metadata> metaList) {
        if (metaList.isEmpty()) return 0;
        String s = metaList.get(0).get("Content-Length");
        if (s == null) return 0;
        try { return Long.parseLong(s.trim()); } catch (NumberFormatException e) { return 0; }
    }

    private static String firstContentType(Metadata m) {
        String ct = m.get("Content-Type");
        if (ct == null || ct.isEmpty()) return "application/octet-stream";
        int semi = ct.indexOf(';');
        return semi >= 0 ? ct.substring(0, semi).trim() : ct.trim();
    }

    /**
     * Build a schema-compliant stub root entry. Used in mid-parse drafts where
     * the real root metadata hasn't been added to the wrapper's list yet
     * (RecursiveParserWrapperHandler.endDocument is what eventually adds it at
     * position 0; until then there is no root in the list).
     */
    private ObjectNode buildStubRoot() {
        ObjectNode n = OM.createObjectNode();
        n.put("path", "/");
        n.putNull("parent_path");
        n.put("depth", 0);
        n.put("content_type", "application/octet-stream");
        n.put("size_bytes", 0);
        n.putNull("sha256");  // root sha256 set in the input block, not duplicated here
        n.putNull("md5");
        n.putNull("sha1");
        n.put("has_thumbnail", false);
        n.putNull("thumbnail_skipped");
        n.putNull("phash");
        n.putNull("colorhash");
        n.putObject("metadata");
        n.put("text", "");
        n.putNull("language");
        ObjectNode qr = n.putObject("qr");
        qr.putArray("codes");
        qr.put("skipped", "in_progress");
        ObjectNode ocr = n.putObject("ocr");
        ocr.put("text", "");
        ocr.putNull("language");
        ocr.put("duration_ms", 0);
        ocr.put("skipped", "in_progress");
        n.putNull("error");
        return n;
    }

    /** Build a schema-compliant entry from the raw Metadata (no Pass-2 enrichment). */
    private static ObjectNode buildEntry(Metadata m) {
        ObjectNode n = OM.createObjectNode();
        String embPath = m.get(TikaCoreProperties.EMBEDDED_RESOURCE_PATH);
        String path = (embPath == null || embPath.isEmpty()) ? "/" : embPath;
        n.put("path", path);
        if (!"/".equals(path)) {
            int slash = path.lastIndexOf('/');
            n.put("parent_path", slash <= 0 ? "/" : path.substring(0, slash));
        } else {
            n.putNull("parent_path");
        }
        n.put("depth", "/".equals(path) ? 0 : countDepth(path));
        n.put("content_type", firstContentType(m));
        n.put("size_bytes", parseLong(m.get("Content-Length")));
        n.putNull("sha256");
        n.putNull("md5");
        n.putNull("sha1");
        n.put("has_thumbnail", false);
        n.putNull("thumbnail_skipped");
        n.putNull("phash");
        n.putNull("colorhash");

        ObjectNode meta = n.putObject("metadata");
        for (String name : m.names()) {
            if (name.startsWith("X-TIKA:") || name.equals("Content-Type")) continue;
            String v = m.get(name);
            if (v != null) meta.put(name, v);
        }

        String text = m.get(TikaCoreProperties.TIKA_CONTENT);
        n.put("text", text == null ? "" : text);
        n.putNull("language");

        ObjectNode qr = n.putObject("qr");
        qr.putArray("codes");
        qr.put("skipped", "in_progress");

        ObjectNode ocr = n.putObject("ocr");
        // Tika populates OCR text directly into TIKA_CONTENT for image entries,
        // so the snapshot's `text` field already carries it. Keep the structured
        // ocr block as an in_progress placeholder until the final write fills
        // duration_ms / language / skipped reason.
        ocr.put("text", "");
        ocr.putNull("language");
        ocr.put("duration_ms", 0);
        ocr.put("skipped", "in_progress");

        n.putNull("error");
        return n;
    }

    private static int countDepth(String path) {
        int n = 0;
        for (char c : path.toCharArray()) if (c == '/') n++;
        return n;
    }

    private static long parseLong(String s) {
        if (s == null) return 0;
        try { return Long.parseLong(s.trim()); } catch (NumberFormatException e) { return 0; }
    }
}
