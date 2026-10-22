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

/** Modern RAR decoding stays inside the existing worker sandbox. Each member is
 * bounded and published only after decoder success and an exact size check.
 * Archive paths are never extracted to disk. */
final class Rar5Parser implements Parser {
    private static final byte[] MAGIC = {'R', 'a', 'r', '!', 0x1a, 7, 1, 0};
    private static final long MAX_BYTES = 256L * 1024 * 1024;
    private static final int MAX_MEMBER_BYTES = 50 * 1024 * 1024;
    private static final ScheduledExecutorService DEADLINES = Executors.newSingleThreadScheduledExecutor(r -> {
        Thread t = new Thread(r, "rar5-deadline"); t.setDaemon(true); return t;
    });
    private final String decoder;
    Rar5Parser() { this(System.getenv().getOrDefault("REDTUSK_7ZZ", "7zz")); }
    Rar5Parser(String decoder) { this.decoder = decoder; }
    @Override public Set<MediaType> getSupportedTypes(ParseContext context) {
        return Set.of(MediaType.application("x-rar-compressed"), MediaType.application("vnd.rar"));
    }
    record Member(String path, long size, boolean skip) { }

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
            entries.add(new Member(path, size, skip)); total += size;
        }
        return entries;
    }

    private byte[] command(List<String> args, int cap, long deadline) throws IOException, TikaException {
        if (System.nanoTime() >= deadline) throw new TikaException("RAR5 decoder deadline exceeded");
        ProcessBuilder builder = new ProcessBuilder(args);
        builder.environment().put("LC_ALL", "C.UTF-8");
        Process process;
        try { process = builder.start(); }
        catch (IOException e) { throw new TikaException("RAR5 decoder unavailable: 7zz could not start", e); }
        process.getOutputStream().close();
        ScheduledFuture<?> timeout = DEADLINES.schedule(process::destroyForcibly,
            Math.max(1, deadline - System.nanoTime()), TimeUnit.NANOSECONDS);
        ByteArrayOutputStream errors = new ByteArrayOutputStream();
        Thread stderr = Thread.ofVirtual().start(() -> {
            try (InputStream stream = process.getErrorStream()) {
                byte[] block = new byte[1024]; int n;
                while ((n = stream.read(block)) >= 0)
                    errors.write(block, 0, Math.min(n, Math.max(0, 8192 - errors.size())));
            } catch (IOException ignored) { }
        });
        try (InputStream stream = process.getInputStream()) {
            byte[] bytes = stream.readNBytes(cap + 1);
            if (bytes.length > cap) throw new TikaException("RAR5 decoder exceeded its output byte budget");
            if (!process.waitFor(Math.max(1, deadline - System.nanoTime()), TimeUnit.NANOSECONDS))
                throw new TikaException("RAR5 decoder deadline exceeded");
            stderr.join(1000);
            if (process.exitValue() != 0)
                throw new TikaException("RAR5 decoder refused archive: " + errors.toString(StandardCharsets.UTF_8).strip());
            return bytes;
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt(); throw new TikaException("RAR5 decoding interrupted", e);
        } finally {
            timeout.cancel(false); process.destroyForcibly();
            try { process.getErrorStream().close(); } catch (IOException ignored) { }
        }
    }

    @Override public void parse(TikaInputStream input, ContentHandler handler, Metadata metadata,
                                ParseContext context) throws IOException, SAXException, TikaException {
        input.mark(MAGIC.length);
        byte[] magic = input.readNBytes(MAGIC.length); input.reset();
        if (!Arrays.equals(magic, MAGIC)) { new RarParser().parse(input, handler, metadata, context); return; }
        var limits = context.get(JobDescriptor.LimitsDescriptor.class);
        long budget = limits == null ? MAX_BYTES : Math.min(MAX_BYTES, Math.max(1, limits.maxExtractedBytes()));
        int maxEntries = limits == null ? 5000 : Math.max(1, limits.maxEmbeddedEntries());
        long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(60);
        String path = input.getFile().getAbsolutePath();
        byte[] listing = command(List.of(decoder, "l", "-slt", "-ba", "-sccUTF-8", "-p-", "--", path),
            4 * 1024 * 1024, deadline);
        List<Member> members = listedEntries(new String(listing, StandardCharsets.UTF_8), maxEntries, budget);
        metadata.set("X-RedTusk:archive-decoder", "7zip-rar5");
        XHTMLContentHandler xhtml = new XHTMLContentHandler(handler, metadata, context); xhtml.startDocument();
        var extractor = EmbeddedDocumentUtil.getEmbeddedDocumentExtractor(context);
        for (Member member : members) {
            if (member.skip()) { metadata.add("X-RedTusk:archive-skipped", "non-regular entry: " + member.path()); continue; }
            Metadata child = new Metadata();
            child.set(TikaCoreProperties.RESOURCE_NAME_KEY, member.path());
            child.set(Metadata.CONTENT_LENGTH, Long.toString(member.size()));
            if (!extractor.shouldParseEmbedded(child)) continue;
            byte[] bytes = command(List.of(decoder, "x", "-so", "-spd", "-y", "-p-", "-bso0", "-bsp0",
                path, "--", member.path()), (int)member.size(), deadline);
            if (bytes.length != member.size()) throw new TikaException("RAR5 decoded member size mismatch");
            try (TikaInputStream stream = TikaInputStream.get(bytes)) {
                extractor.parseEmbedded(stream, xhtml, child, context, true);
            }
        }
        xhtml.endDocument();
    }
}
