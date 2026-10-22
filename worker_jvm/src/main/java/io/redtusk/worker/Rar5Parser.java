package io.redtusk.worker;

import org.apache.commons.compress.archivers.tar.TarArchiveInputStream;
import org.apache.commons.io.input.CloseShieldInputStream;
import org.apache.tika.exception.TikaException;
import org.apache.tika.extractor.EmbeddedDocumentUtil;
import org.apache.tika.io.TikaInputStream;
import org.apache.tika.metadata.Metadata;
import org.apache.tika.metadata.TikaCoreProperties;
import org.apache.tika.mime.MediaType;
import org.apache.tika.parser.ParseContext;
import org.apache.tika.parser.Parser;
import org.apache.tika.parser.pkg.RarParser;
import org.apache.tika.sax.XHTMLContentHandler;
import org.xml.sax.ContentHandler;
import org.xml.sax.SAXException;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Set;
import java.util.concurrent.*;

/** RAR5 decoding stays inside the worker's existing sandbox. libarchive copies
 * entries to a bounded TAR stream; it never extracts archive paths to the filesystem.
 * Tika's normal recursive extractor handles the entries and records their provenance. */
final class Rar5Parser implements Parser {
    private static final byte[] MAGIC = {'R', 'a', 'r', '!', 0x1a, 7, 1, 0};
    private static final long MAX_BYTES = 256L * 1024 * 1024;
    private static final ScheduledExecutorService DEADLINES = Executors.newSingleThreadScheduledExecutor(r -> {
        Thread t = new Thread(r, "rar5-deadline"); t.setDaemon(true); return t;
    });

    @Override public Set<MediaType> getSupportedTypes(ParseContext context) {
        return Set.of(MediaType.application("x-rar-compressed"), MediaType.application("vnd.rar"));
    }

    @Override public void parse(TikaInputStream input, ContentHandler handler, Metadata metadata,
                                ParseContext context) throws IOException, SAXException, TikaException {
        input.mark(MAGIC.length);
        byte[] magic = input.readNBytes(MAGIC.length);
        input.reset();
        if (!Arrays.equals(magic, MAGIC)) {
            new RarParser().parse(input, handler, metadata, context);
            return;
        }
        var limits = context.get(JobDescriptor.LimitsDescriptor.class);
        long budget = limits == null ? MAX_BYTES : Math.min(MAX_BYTES, Math.max(1, limits.maxExtractedBytes()));
        int maxEntries = limits == null ? 5000 : Math.max(1, limits.maxEmbeddedEntries());
        ProcessBuilder builder = new ProcessBuilder("bsdtar", "-c", "--format=pax", "-f", "-",
            "@" + input.getFile().getAbsolutePath());
        builder.environment().put("LC_ALL", "C.UTF-8");
        Process process;
        try { process = builder.start(); }
        catch (IOException e) { throw new TikaException("RAR5 decoder unavailable: bsdtar could not start", e); }
        process.getOutputStream().close(); // No password prompts or interactive input.
        ScheduledFuture<?> deadline = DEADLINES.schedule(process::destroyForcibly, 60, TimeUnit.SECONDS);
        ByteArrayOutputStream errors = new ByteArrayOutputStream();
        Thread stderr = Thread.ofVirtual().start(() -> {
            try (InputStream stream = process.getErrorStream()) {
                byte[] block = new byte[1024]; int n;
                while ((n = stream.read(block)) >= 0) {
                    int keep = Math.min(n, Math.max(0, 8192 - errors.size()));
                    errors.write(block, 0, keep);
                }
            } catch (IOException ignored) { /* Process teardown closes the pipe. */ }
        });
        try (var archive = new TarArchiveInputStream(new BudgetInputStream(process.getInputStream(), budget))) {
            metadata.set("X-RedTusk:archive-decoder", "libarchive-rar5");
            XHTMLContentHandler xhtml = new XHTMLContentHandler(handler, metadata, context);
            xhtml.startDocument();
            var extractor = EmbeddedDocumentUtil.getEmbeddedDocumentExtractor(context);
            int count = 0;
            for (var entry = archive.getNextEntry(); entry != null; entry = archive.getNextEntry()) {
                if (++count > maxEntries) throw new TikaException("RAR5 archive entry budget exceeded");
                if (!entry.isFile() || entry.isSymbolicLink() || entry.isLink()) {
                    if (!entry.isDirectory()) metadata.add("X-RedTusk:archive-skipped", "non-regular entry: " + entry.getName());
                    continue;
                }
                if (entry.getSize() > budget) throw new TikaException("RAR5 expanded byte budget exceeded");
                Metadata child = new Metadata();
                child.set(TikaCoreProperties.RESOURCE_NAME_KEY, entry.getName());
                child.set(Metadata.CONTENT_LENGTH, Long.toString(entry.getSize()));
                if (extractor.shouldParseEmbedded(child)) {
                    try (TikaInputStream member = TikaInputStream.get(CloseShieldInputStream.wrap(archive))) {
                        extractor.parseEmbedded(member, xhtml, child, context, true);
                    }
                }
            }
            // Drain archive padding so the child cannot block while we wait for exit.
            byte[] remainder = new byte[4096];
            while (archive.read(remainder) >= 0) { }
            if (!process.waitFor(2, TimeUnit.SECONDS)) {
                throw new TikaException("RAR5 decoder did not finish within its deadline");
            }
            stderr.join(1000);
            if (process.exitValue() != 0) {
                throw new TikaException("RAR5 decoder refused archive: " + errors.toString(StandardCharsets.UTF_8).strip());
            }
            xhtml.endDocument();
        } catch (IOException e) {
            throw new TikaException("RAR5 decoding failed: " + e.getMessage(), e);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new TikaException("RAR5 decoding interrupted", e);
        } finally {
            deadline.cancel(false);
            process.destroyForcibly();
            try { process.getErrorStream().close(); } catch (IOException ignored) { }
            try { process.waitFor(1, TimeUnit.SECONDS); }
            catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        }
    }

    /** Includes archive headers and skipped members, not just bytes handed to Tika. */
    private static final class BudgetInputStream extends FilterInputStream {
        private long remaining;
        BudgetInputStream(InputStream stream, long budget) { super(stream); remaining = budget; }
        private void used(long count) throws IOException {
            if (count > 0 && (remaining -= count) < 0) throw new IOException("RAR5 expanded byte budget exceeded");
        }
        @Override public int read() throws IOException { int b = in.read(); used(b < 0 ? 0 : 1); return b; }
        @Override public int read(byte[] b, int off, int len) throws IOException {
            int n = in.read(b, off, (int)Math.min(len, remaining + 1)); used(n); return n;
        }
        @Override public long skip(long n) throws IOException {
            long skipped = in.skip(Math.min(n, remaining + 1)); used(skipped); return skipped;
        }
    }
}
