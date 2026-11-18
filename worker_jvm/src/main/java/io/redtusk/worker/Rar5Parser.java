package io.redtusk.worker;

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
import java.util.*;
import java.util.concurrent.*;

/** Modern RAR decoding stays inside the existing worker sandbox. The archive is listed once
 * and decoded once (one 7zz stream split by the listed sizes); each member is bounded and
 * published only after decoder success and an exact size check. Archive paths are never
 * extracted to disk: decoded bytes are spooled to index-named files in a private scratch dir. */
final class Rar5Parser implements Parser {
    private static final byte[] MAGIC = {'R', 'a', 'r', '!', 0x1a, 7, 1, 0};
    private static final long MAX_BYTES = 256L * 1024 * 1024;
    private static final int MAX_MEMBER_BYTES = 50 * 1024 * 1024;
    static final long DEADLINE_SECONDS = 40;
    private static final ScheduledExecutorService DEADLINES = Executors.newSingleThreadScheduledExecutor(r -> {
        Thread t = new Thread(r, "rar5-deadline"); t.setDaemon(true); return t;
    });
    private final String decoder;
    Rar5Parser() { this(System.getenv().getOrDefault("REDTUSK_7ZZ", "7zz")); }
    Rar5Parser(String decoder) { this.decoder = decoder; }
    @Override public Set<MediaType> getSupportedTypes(ParseContext context) {
        return Set.of(MediaType.application("x-rar-compressed"), MediaType.application("vnd.rar"));
    }
    record Member(String path, long size, boolean skip, boolean folder) { }

    static List<Member> listedEntries(String listing, int maxEntries, long budget) throws TikaException {
        List<Member> entries = new ArrayList<>();
        Set<String> names = new HashSet<>();
        long total = 0;
        for (String block : listing.replace("\r\n", "\n").split("\n\n+")) {
            if (block.isBlank()) continue;
            Map<String, String> fields = new LinkedHashMap<>();
            for (String line : block.split("\n")) {
                int separator = line.indexOf(" = ");
                if (separator < 1 || line.length() > 8192 || line.chars().anyMatch(c -> c < 32))
                    throw new TikaException("RAR5 decoder returned an ambiguous member listing");
                if (fields.putIfAbsent(line.substring(0, separator), line.substring(separator + 3)) != null)
                    throw new TikaException("RAR5 decoder returned duplicate member metadata");
            }
            String path = fields.get("Path");
            if (path == null || path.isBlank() || path.length() > 4096 || !names.add(path))
                throw new TikaException("RAR5 decoder returned invalid or duplicate member names");
            if (entries.size() >= maxEntries) throw new TikaException("RAR5 archive entry budget exceeded");
            String folder = fields.get("Folder");
            if (!Set.of("+", "-").contains(folder == null ? "" : folder))
                throw new TikaException("RAR5 decoder returned invalid member type");
            long size;
            try { size = Long.parseLong(fields.getOrDefault("Size", "")); }
            catch (NumberFormatException e) { throw new TikaException("RAR5 member size unavailable", e); }
            if (size < 0 || size > MAX_MEMBER_BYTES || size > budget - total)
                throw new TikaException("RAR5 expanded byte budget exceeded");
            if ("+".equals(fields.get("Encrypted"))) throw new TikaException("RAR5 encrypted member requires a password");
            if ("+".equals(fields.get("Split Before")) || "+".equals(fields.get("Split After")))
                throw new TikaException("RAR5 split member is incomplete");
            boolean skip = "+".equals(folder) || "+".equals(fields.get("Alternate Stream"))
                || !fields.getOrDefault("Symbolic Link", "").isEmpty()
                || !fields.getOrDefault("Hard Link", "").isEmpty()
                || !fields.getOrDefault("Copy Link", "").isEmpty();
            entries.add(new Member(path, size, skip, "+".equals(folder))); total += size;
        }
        return entries;
    }

    @FunctionalInterface
    private interface StdoutReader<T> { T read(InputStream stdout) throws IOException, TikaException; }

    /** What one decoder run produced: the reader's value, whether stdout ended where the reader
     * stopped (false = more output followed, so the process was killed), and the exit status. */
    private record Run<T>(T value, boolean drained, int exit, String errors) { }

    /** Runs the decoder once under the shared deadline. A deadline overrun always throws; a
     * non-zero exit or undrained stdout is reported to the caller, which decides. */
    private <T> Run<T> run(List<String> args, long deadline, StdoutReader<T> reader)
            throws IOException, TikaException {
        if (System.nanoTime() >= deadline) throw new TikaException("RAR5 decoder deadline exceeded");
        ProcessBuilder builder = new ProcessBuilder(args);
        builder.environment().put("LC_ALL", "C.UTF-8");
        Process process;
        try { process = builder.start(); }
        catch (IOException e) { throw new TikaException("RAR5 decoder unavailable: 7zz could not start", e); }
        process.getOutputStream().close();
        var timedOut = new java.util.concurrent.atomic.AtomicBoolean();
        ScheduledFuture<?> timeout = DEADLINES.schedule(() -> { timedOut.set(true); process.destroyForcibly(); },
            Math.max(1, deadline - System.nanoTime()), TimeUnit.NANOSECONDS);
        ByteArrayOutputStream errors = new ByteArrayOutputStream();
        Thread stderr = Thread.ofVirtual().start(() -> {
            try (InputStream stream = process.getErrorStream()) {
                byte[] block = new byte[1024]; int n;
                while ((n = stream.read(block)) >= 0)
                    synchronized (errors) { errors.write(block, 0, Math.min(n, Math.max(0, 8192 - errors.size()))); }
            } catch (IOException ignored) { }
        });
        try (InputStream stream = process.getInputStream()) {
            T value = reader.read(stream);
            boolean drained = stream.read() < 0;
            if (!drained) process.destroyForcibly();
            boolean exited = process.waitFor(Math.max(1, deadline - System.nanoTime()), TimeUnit.NANOSECONDS);
            if (!exited || timedOut.get()) throw new TikaException("RAR5 decoder deadline exceeded");
            stderr.join(1000);
            String message;
            synchronized (errors) { message = errors.toString(StandardCharsets.UTF_8).strip(); }
            return new Run<>(value, drained, process.exitValue(), message);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt(); throw new TikaException("RAR5 decoding interrupted", e);
        } catch (IOException e) {
            if (timedOut.get()) throw new TikaException("RAR5 decoder deadline exceeded", e);
            throw e;
        } finally {
            timeout.cancel(false); process.destroyForcibly();
            try { process.getErrorStream().close(); } catch (IOException ignored) { }
        }
    }

    /** Captures at most cap bytes of stdout; anything more refuses the archive. */
    private byte[] command(List<String> args, int cap, long deadline) throws IOException, TikaException {
        Run<byte[]> run = run(args, deadline, stdout -> stdout.readNBytes(cap + 1));
        if (run.value().length > cap || !run.drained())
            throw new TikaException("RAR5 decoder exceeded its output byte budget");
        if (run.exit() != 0) throw new TikaException("RAR5 decoder refused archive: " + run.errors());
        return run.value();
    }

    /** Copies exactly n bytes of in to out (null = discard); false if in ends first. */
    private static boolean copyExactly(InputStream in, OutputStream out, long n) throws IOException {
        byte[] block = new byte[64 * 1024];
        while (n > 0) {
            int r = in.read(block, 0, (int) Math.min(block.length, n));
            if (r < 0) return false;
            if (out != null) out.write(block, 0, r);
            n -= r;
        }
        return true;
    }

    /**
     * Decodes the whole archive with ONE decoder run ({@code 7zz x -so} writes every non-folder
     * member's data to stdout, in listing order) and splits that stream by the listed sizes
     * into files named by member index in a private scratch directory -- never by archive
     * paths. Nothing is published until the decoder exits 0 and the stream matched the listing
     * exactly, so a CRC failure or a lying listing refuses the archive as before.
     *
     * @return one file per selected member (null where not selected), or null when the stream
     *     did not match and the archive has link or alternate-stream entries, whose -so bytes
     *     are not described by their listed size; the caller then decodes member by member
     */
    private List<java.nio.file.Path> decodeOnce(String path, List<Member> members, boolean[] selected,
                                                long deadline, java.nio.file.Path scratch)
            throws IOException, TikaException {
        List<java.nio.file.Path> files = new ArrayList<>(Collections.nCopies(members.size(), null));
        Run<Boolean> run = run(List.of(decoder, "x", "-so", "-spd", "-y", "-p-", "-bso0", "-bsp0", "--", path),
            deadline, stdout -> {
                for (int i = 0; i < members.size(); i++) {
                    Member member = members.get(i);
                    if (member.folder()) continue;
                    if (!selected[i]) {
                        if (!copyExactly(stdout, null, member.size())) return false;
                        continue;
                    }
                    java.nio.file.Path file = scratch.resolve(i + ".bin");
                    try (OutputStream out = java.nio.file.Files.newOutputStream(file,
                            java.nio.file.StandardOpenOption.CREATE_NEW)) {
                        if (!copyExactly(stdout, out, member.size())) return false;
                    }
                    files.set(i, file);
                }
                return true;
            });
        boolean matched = run.value() && run.drained() && run.exit() == 0;
        if (matched) return files;
        if (members.stream().anyMatch(m -> m.skip() && !m.folder())) return null;
        if (run.exit() != 0 && run.drained())
            throw new TikaException("RAR5 decoder refused archive: " + run.errors());
        throw new TikaException("RAR5 decoded stream does not match its member listing");
    }

    private static void deleteTree(java.nio.file.Path dir) {
        try (var walk = java.nio.file.Files.walk(dir)) {
            walk.sorted(Comparator.reverseOrder()).forEach(p -> {
                try { java.nio.file.Files.deleteIfExists(p); } catch (IOException ignored) { }
            });
        } catch (IOException ignored) { }
    }

    @Override public void parse(TikaInputStream input, ContentHandler handler, Metadata metadata,
                                ParseContext context) throws IOException, SAXException, TikaException {
        input.mark(MAGIC.length);
        byte[] magic = input.readNBytes(MAGIC.length); input.reset();
        if (!Arrays.equals(magic, MAGIC)) { new RarParser().parse(input, handler, metadata, context); return; }
        var limits = context.get(JobDescriptor.LimitsDescriptor.class);
        long budget = limits == null ? MAX_BYTES : Math.min(MAX_BYTES, Math.max(1, limits.maxExtractedBytes()));
        int maxEntries = limits == null ? 5000 : Math.max(1, limits.maxEmbeddedEntries());
        // Each pass (and each nesting level) decodes the archive again with its own deadline, so
        // two of them must fit the engine's default 120 s job budget with room for the rest
        // of the job; a deadline overrun refuses only this archive, not the job.
        long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(DEADLINE_SECONDS);
        String path = input.getFile().getAbsolutePath();
        byte[] listing = command(List.of(decoder, "l", "-slt", "-ba", "-sccUTF-8", "-p-", "--", path),
            4 * 1024 * 1024, deadline);
        List<Member> members = listedEntries(new String(listing, StandardCharsets.UTF_8), maxEntries, budget);
        metadata.set("X-RedTusk:archive-decoder", "7zip-rar5");
        XHTMLContentHandler xhtml = new XHTMLContentHandler(handler, metadata, context); xhtml.startDocument();
        var extractor = EmbeddedDocumentUtil.getEmbeddedDocumentExtractor(context);
        boolean[] selected = new boolean[members.size()];
        List<Metadata> children = new ArrayList<>(Collections.nCopies(members.size(), null));
        for (int i = 0; i < members.size(); i++) {
            Member member = members.get(i);
            if (member.skip()) { metadata.add("X-RedTusk:archive-skipped", "non-regular entry: " + member.path()); continue; }
            Metadata child = new Metadata();
            child.set(TikaCoreProperties.RESOURCE_NAME_KEY, member.path());
            child.set(Metadata.CONTENT_LENGTH, Long.toString(member.size()));
            if (!extractor.shouldParseEmbedded(child)) continue;
            selected[i] = true;
            children.set(i, child);
        }
        boolean any = false;
        for (boolean b : selected) any |= b;
        if (any) {
            java.nio.file.Path scratch = java.nio.file.Files.createTempDirectory("redtusk-rar5-");
            try {
                List<java.nio.file.Path> decoded = decodeOnce(path, members, selected, deadline, scratch);
                for (int i = 0; i < members.size(); i++) {
                    if (!selected[i]) continue;
                    if (decoded != null) {
                        try (TikaInputStream stream = TikaInputStream.get(decoded.get(i))) {
                            extractor.parseEmbedded(stream, xhtml, children.get(i), context, true);
                        }
                        java.nio.file.Files.deleteIfExists(decoded.get(i));
                    } else {
                        // Link-bearing archive whose stream did not match: one member per run.
                        Member member = members.get(i);
                        byte[] bytes = command(List.of(decoder, "x", "-so", "-spd", "-y", "-p-", "-bso0", "-bsp0",
                            path, "--", member.path()), (int) member.size(), deadline);
                        if (bytes.length != member.size()) throw new TikaException("RAR5 decoded member size mismatch");
                        try (TikaInputStream stream = TikaInputStream.get(bytes)) {
                            extractor.parseEmbedded(stream, xhtml, children.get(i), context, true);
                        }
                    }
                }
            } finally {
                deleteTree(scratch);
            }
        }
        xhtml.endDocument();
    }
}
