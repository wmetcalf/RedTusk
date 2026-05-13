package io.redtusk.worker;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

import java.io.File;
import java.io.IOException;
import java.time.Instant;

/**
 * Assembles the canonical rmeta document and writes metadata.json.
 * The produced JSON satisfies the JSON Schema in src/redtusk/schema.py.
 */
public final class RmetaWriter {

    private static final ObjectMapper OM = new ObjectMapper();

    private final JobDescriptor job;
    private final ParseResult result;
    private final long durationMs;

    public RmetaWriter(JobDescriptor job, ParseResult result, long durationMs) {
        this.job = job;
        this.result = result;
        this.durationMs = durationMs;
    }

    public void write(File outputDir) throws IOException {
        outputDir.mkdirs();
        OM.writerWithDefaultPrettyPrinter()
          .writeValue(new File(outputDir, "metadata.json"), buildDocument());
    }

    private ObjectNode buildDocument() {
        ObjectNode root = OM.createObjectNode();
        root.put("redtusk_version", job.redtuskVersion());

        ObjectNode input = root.putObject("input");
        input.put("sha256", job.sha256());
        input.put("size_bytes", result.entries().isEmpty() ? 0L : result.entries().get(0).sizeBytes());
        if (job.filenameHint() != null) input.put("filename_hint", job.filenameHint());
        else input.putNull("filename_hint");
        input.put("submitted_at", Instant.now().toString());

        ObjectNode extraction = root.putObject("extraction");
        String rootContentType = result.entries().isEmpty() ? "application/octet-stream"
                                                            : result.entries().get(0).contentType();
        extraction.put("root_content_type", rootContentType);
        String rootLanguage = result.entries().isEmpty() ? null : result.entries().get(0).language();
        if (rootLanguage != null) extraction.put("root_language", rootLanguage);
        else extraction.putNull("root_language");
        extraction.put("duration_ms", durationMs);
        ArrayNode entriesNode = extraction.putArray("entries");
        for (EntryResult e : result.entries()) entriesNode.add(buildEntry(e));

        ObjectNode limits = root.putObject("limits");
        limits.put("max_recursion_depth", job.limits().maxRecursionDepth());
        limits.put("max_embedded_entries", job.limits().maxEmbeddedEntries());
        limits.put("max_extracted_bytes", job.limits().maxExtractedBytes());
        limits.put("ocr_timeout_s", job.limits().ocrTimeoutS());

        if (result.truncated() != null) {
            var t = result.truncated();
            ObjectNode tr = root.putObject("truncated");
            tr.put("reason", t.reason());
            tr.put("limit", t.limit());
            tr.put("observed", t.observed());
        } else {
            root.putNull("truncated");
        }

        ArrayNode warningsNode = root.putArray("warnings");
        for (ParseResult.WorkerWarning w : result.warnings()) {
            ObjectNode wn = warningsNode.addObject();
            wn.put("code", w.code());
            wn.put("detail", w.detail());
            if (w.entryPath() != null) wn.put("entry_path", w.entryPath());
            else wn.putNull("entry_path");
        }

        ObjectNode sandbox = root.putObject("sandbox");
        sandbox.put("profile", job.sandboxProfile());
        sandbox.put("runtime", job.sandboxRuntime());
        sandbox.put("appcds", job.appcds());
        sandbox.put("ksm", job.ksm());
        sandbox.put("crac", job.crac());

        return root;
    }

    private ObjectNode buildEntry(EntryResult e) {
        ObjectNode n = OM.createObjectNode();
        n.put("path", e.path());
        if (e.parentPath() != null) n.put("parent_path", e.parentPath());
        else n.putNull("parent_path");
        n.put("depth", e.depth());
        n.put("content_type", e.contentType());
        n.put("size_bytes", e.sizeBytes());
        if (e.sha256() != null) n.put("sha256", e.sha256()); else n.putNull("sha256");
        if (e.md5()    != null) n.put("md5",    e.md5());    else n.putNull("md5");
        if (e.sha1()   != null) n.put("sha1",   e.sha1());   else n.putNull("sha1");
        n.put("has_thumbnail", e.hasThumbnail());
        if (e.thumbnailSkipped() != null) n.put("thumbnail_skipped", e.thumbnailSkipped());
        else n.putNull("thumbnail_skipped");
        if (e.phash()    != null) n.put("phash",    e.phash());    else n.putNull("phash");
        if (e.colorhash() != null) n.put("colorhash", e.colorhash()); else n.putNull("colorhash");

        ObjectNode meta = n.putObject("metadata");
        if (e.metadata() != null) {
            e.metadata().forEach((k, v) -> meta.put(k, v == null ? null : v.toString()));
        }

        n.put("text", e.text() != null ? e.text() : "");
        if (e.language() != null) n.put("language", e.language());
        else n.putNull("language");

        // qr — always present
        ObjectNode qr = n.putObject("qr");
        ArrayNode codes = qr.putArray("codes");
        if (e.qr() != null && e.qr().codes() != null) {
            for (EntryResult.QrCode code : e.qr().codes()) {
                ObjectNode c = codes.addObject();
                c.put("data", code.data());
                if (code.format() != null) c.put("format", code.format());
                else c.putNull("format");
                if (code.rawBytes() != null) c.put("raw_bytes", code.rawBytes());
                else c.putNull("raw_bytes");
                if (code.position() != null) c.put("position", code.position());
                else c.putNull("position");
            }
        }
        String qrSkipped = e.qr() != null ? e.qr().skipped() : "disabled";
        if (qrSkipped != null) qr.put("skipped", qrSkipped);
        else qr.putNull("skipped");

        // ocr — always present
        ObjectNode ocr = n.putObject("ocr");
        if (e.ocr() != null) {
            ocr.put("text", e.ocr().text() != null ? e.ocr().text() : "");
            if (e.ocr().language() != null) ocr.put("language", e.ocr().language());
            else ocr.putNull("language");
            ocr.put("duration_ms", e.ocr().durationMs());
            if (e.ocr().skipped() != null) ocr.put("skipped", e.ocr().skipped());
            else ocr.putNull("skipped");
        } else {
            ocr.put("text", "");
            ocr.putNull("language");
            ocr.put("duration_ms", 0);
            ocr.put("skipped", "disabled");
        }

        if (e.error() != null) n.put("error", e.error());
        else n.putNull("error");

        return n;
    }
}
