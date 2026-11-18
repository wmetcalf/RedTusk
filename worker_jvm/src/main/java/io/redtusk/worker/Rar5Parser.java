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
 * (alternate streams included) and, when the listing describes the decoded stream exactly,
 * decoded once (one 7zz stream read member by member, each checked against its listed size
 * and CRC32 before it is published); otherwise one bounded 7zz run per member. Each member is
 * bounded, held in memory one at a time, and never extracted to disk by archive path. */
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
    /** crc is the listed CRC32 of the member's data, or null when the archive gives none. */
    record Member(String path, long size, boolean skip, boolean folder, Long crc) { }

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
            Long crc = null;
            String listedCrc = fields.getOrDefault("CRC", "");
            if (listedCrc.matches("[0-9A-Fa-f]{8}")) crc = Long.parseLong(listedCrc, 16);
            entries.add(new Member(path, size, skip, "+".equals(folder), crc)); total += size;
        }
        return entries;
    }

    @FunctionalInterface
    private interface StdoutReader<T> { T read(InputStream stdout) throws IOException, TikaException, SAXException; }

    /** What one decoder run produced: the reader's value, whether stdout ended where the reader
     * stopped (false = more output followed, so the process was killed), and the exit status. */
    private record Run<T>(T value, boolean drained, int exit, String errors) { }

    /** Runs the decoder once under the shared deadline. A deadline overrun always throws; a
     * non-zero exit or undrained stdout is reported to the caller, which decides. */
    private <T> Run<T> run(List<String> args, long deadline, StdoutReader<T> reader)
            throws IOException, TikaException, SAXException {
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
        Run<byte[]> run;
        try { run = run(args, deadline, stdout -> stdout.readNBytes(cap + 1)); }
        catch (SAXException e) { throw new TikaException("RAR5 decoder output unreadable", e); }
        if (run.value().length > cap || !run.drained())
            throw new TikaException("RAR5 decoder exceeded its output byte budget");
        if (run.exit() != 0) throw new TikaException("RAR5 decoder refused archive: " + run.errors());
        return run.value();
    }

    /** The per-member decode: one bounded 7zz run for this member only. */
    private byte[] decodeMember(String path, Member member, long deadline) throws IOException, TikaException {
        byte[] bytes = command(List.of(decoder, "x", "-so", "-spd", "-sns-", "-y", "-p-", "-bso0", "-bsp0",
            path, "--", member.path()), (int) member.size(), deadline);
        if (bytes.length != member.size()) throw new TikaException("RAR5 decoded member size mismatch");
        return bytes;
    }

    /** Offers a decoded member to the extractor, asked in order right before publishing, so an
     * extractor that counts what it has parsed (an entry budget) sees each decision after the
     * last. */
    private static void publish(Member member, byte[] bytes, org.apache.tika.extractor.EmbeddedDocumentExtractor extractor,
                                XHTMLContentHandler xhtml, ParseContext context) throws IOException, SAXException {
        Metadata child = new Metadata();
        child.set(TikaCoreProperties.RESOURCE_NAME_KEY, member.path());
        child.set(Metadata.CONTENT_LENGTH, Long.toString(member.size()));
        if (!extractor.shouldParseEmbedded(child)) return;
        try (TikaInputStream stream = TikaInputStream.get(bytes)) {
            extractor.parseEmbedded(stream, xhtml, child, context, true);
        }
    }

    private static long crc32(byte[] bytes) {
        var crc = new java.util.zip.CRC32(); crc.update(bytes); return crc.getValue();
    }

    /**
     * Decodes and publishes the archive with ONE decoder run where that is safe: {@code 7zz x
     * -so -sns-} writes every non-folder member's data in listing order, and each member is read
     * by its listed size (at most 50 MiB, held in memory one at a time as before), checked
     * against its listed CRC32, then published. Nothing is staged on disk.
     *
     * Only for archives whose listing describes the stream exactly: every entry a regular file
     * or folder (no links or alternate streams, whose -so bytes their listed size does not
     * describe) and every regular member carrying a CRC. Otherwise, or when the run stops
     * matching (short stream, CRC mismatch, non-zero exit), the remaining members are decoded
     * one 7zz run each, as before.
     *
     * @return the index of the first member NOT yet handled (members.size() when all were)
     */
    private int decodeOnce(String path, List<Member> members, long deadline,
                           org.apache.tika.extractor.EmbeddedDocumentExtractor extractor,
                           XHTMLContentHandler xhtml, ParseContext context)
            throws IOException, TikaException, SAXException {
        for (Member member : members)
            if ((member.skip() && !member.folder()) || (!member.skip() && member.crc() == null)) return 0;
        int[] next = {0};
        Run<Boolean> run = run(List.of(decoder, "x", "-so", "-spd", "-sns-", "-y", "-p-", "-bso0", "-bsp0", "--", path),
            deadline, stdout -> {
                for (; next[0] < members.size(); next[0]++) {
                    Member member = members.get(next[0]);
                    if (member.folder()) continue;
                    byte[] bytes = stdout.readNBytes((int) member.size());
                    if (bytes.length != member.size() || crc32(bytes) != member.crc()) return false;
                    publish(member, bytes, extractor, xhtml, context);
                }
                return true;
            });
        if (run.value() && run.drained() && run.exit() == 0) return members.size();
        if (next[0] >= members.size())
            throw new TikaException("RAR5 decoder wrote more than its member listing describes");
        return next[0];
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
        byte[] listing = command(List.of(decoder, "l", "-slt", "-ba", "-sns", "-sccUTF-8", "-p-", "--", path),
            4 * 1024 * 1024, deadline);
        List<Member> members = listedEntries(new String(listing, StandardCharsets.UTF_8), maxEntries, budget);
        metadata.set("X-RedTusk:archive-decoder", "7zip-rar5");
        XHTMLContentHandler xhtml = new XHTMLContentHandler(handler, metadata, context); xhtml.startDocument();
        var extractor = EmbeddedDocumentUtil.getEmbeddedDocumentExtractor(context);
        for (Member member : members)
            if (member.skip()) metadata.add("X-RedTusk:archive-skipped", "non-regular entry: " + member.path());
        int first = decodeOnce(path, members, deadline, extractor, xhtml, context);
        for (int i = first; i < members.size(); i++) {
            Member member = members.get(i);
            if (member.skip()) continue;
            Metadata probe = new Metadata();
            probe.set(TikaCoreProperties.RESOURCE_NAME_KEY, member.path());
            probe.set(Metadata.CONTENT_LENGTH, Long.toString(member.size()));
            if (!extractor.shouldParseEmbedded(probe)) continue;
            byte[] bytes = decodeMember(path, member, deadline);
            try (TikaInputStream stream = TikaInputStream.get(bytes)) {
                extractor.parseEmbedded(stream, xhtml, probe, context, true);
            }
        }
        xhtml.endDocument();
    }
}
