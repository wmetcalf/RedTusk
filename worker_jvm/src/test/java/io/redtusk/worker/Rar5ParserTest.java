package io.redtusk.worker;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import java.io.File;
import java.nio.file.Path;
import static org.junit.jupiter.api.Assertions.*;

class Rar5ParserTest {
    @TempDir Path output;
    private File fixture(String name) throws Exception {
        return new File(getClass().getResource("/rar5/" + name + ".rar").toURI());
    }
    private ParserRunner runner(long byteBudget) {
        return new ParserRunner(new JobDescriptor.LimitsDescriptor(10, 20, byteBudget, 30),
            false, false, "eng", 3, 2000, false, "", "tesseract");
    }
    @Test void extractsRar5ThroughTheNormalRecursiveParser() throws Exception {
        ParseResult result = runner(1024 * 1024).parse(fixture("stored"), "sample.rar", "0".repeat(64));
        assertNull(result.entries().getFirst().error());
        assertEquals(2, result.entries().size());
        assertTrue(result.entries().getFirst().contentType().contains("rar"));
        assertFalse(result.entries().get(1).text().isBlank());
        var files = new EmbeddedFileExtractor(10, 20, false).extract(fixture("stored"), output);
        assertEquals(1, files.size());
        assertTrue(files.values().iterator().next().sizeBytes() > 0);
        assertEquals(64, files.values().iterator().next().sha256().length());
    }
    @Test void preservesUnicodeNames() throws Exception {
        ParseResult result = runner(1024 * 1024).parse(fixture("unicode"), "unicode.rar", "0".repeat(64));
        assertNull(result.entries().getFirst().error());
        assertTrue(result.entries().stream().skip(1).anyMatch(e -> e.path().chars().anyMatch(c -> c > 127)));
    }
    @Test void refusesEncryptedArchiveWithoutClaimingSuccessfulExtraction() throws Exception {
        ParseResult result = runner(1024 * 1024).parse(fixture("encrypted"), "encrypted.rar", "0".repeat(64));
        assertNotNull(result.entries().getFirst().error());
    }
    @Test void expandedByteLimitIsEnforced() throws Exception {
        ParseResult result = runner(16).parse(fixture("multiple_files"), "limited.rar", "0".repeat(64));
        assertNotNull(result.entries().getFirst().error());
        assertTrue(result.entries().getFirst().error().contains("budget"));
    }
    @Test void nestedRar5RetainsItsResourcePathAndSavedBytes() throws Exception {
        Path zip = output.resolve("outer.zip");
        try (var out = new java.util.zip.ZipOutputStream(java.nio.file.Files.newOutputStream(zip))) {
            out.putNextEntry(new java.util.zip.ZipEntry("nested.rar"));
            out.write(java.nio.file.Files.readAllBytes(fixture("stored").toPath()));
            out.closeEntry();
        }
        ParseResult result = runner(1024 * 1024).parse(zip.toFile(), "outer.zip", "0".repeat(64));
        assertEquals(3, result.entries().size());
        assertTrue(result.entries().stream().allMatch(e -> e.error() == null));
        assertTrue(result.entries().stream().anyMatch(e -> e.path().startsWith("/nested.rar/")),
            result.entries().stream().map(EntryResult::path).toList().toString());
        var files = new EmbeddedFileExtractor(10, 20, false).extract(zip.toFile(), output.resolve("saved"));
        assertEquals(2, files.size());
    }
    @Test void entryLimitStopsNativeArchiveWalk() throws Exception {
        var bounded = new ParserRunner(new JobDescriptor.LimitsDescriptor(10, 1, 1024 * 1024, 30),
            false, false, "eng", 3, 2000, false, "", "tesseract");
        ParseResult result = bounded.parse(fixture("multiple_files"), "limited.rar", "0".repeat(64));
        assertNotNull(result.entries().getFirst().error());
        assertTrue(result.entries().getFirst().error().contains("entry budget"));
    }

    @Test void refusesAmbiguousOrOversizedNativeListings() {
        assertThrows(Exception.class, () -> Rar5Parser.listedEntries("Path = one\nPath = two\nSize = 1\nFolder = -\n", 10, 1024));
        assertThrows(Exception.class, () -> Rar5Parser.listedEntries("Path = one\nSize = -1\nFolder = -\n", 10, 1024));
        assertThrows(Exception.class, () -> Rar5Parser.listedEntries("Path = one\nSize = 2048\nFolder = -\n", 10, 1024));
        assertThrows(Exception.class, () -> Rar5Parser.listedEntries("Path = one\nSize = 1\nFolder = -\nEncrypted = +\n", 10, 1024));
    }

    @Test void failedDecoderCannotPublishPartialMemberBytes() throws Exception {
        Path decoder = output.resolve("decoder");
        java.nio.file.Files.writeString(decoder, "#!/bin/sh\nif [ \"$1\" = l ]; then\n"
            + "printf 'Path = child.txt\\nSize = 6\\nFolder = -\\nEncrypted = -\\n'\nelse\n"
            + "printf poison\nexit 2\nfi\n");
        assertTrue(decoder.toFile().setExecutable(true));
        var context = new org.apache.tika.parser.ParseContext();
        var count = new java.util.concurrent.atomic.AtomicInteger();
        context.set(org.apache.tika.extractor.EmbeddedDocumentExtractor.class, new org.apache.tika.extractor.EmbeddedDocumentExtractor() {
            public boolean shouldParseEmbedded(org.apache.tika.metadata.Metadata metadata) { return true; }
            public void parseEmbedded(org.apache.tika.io.TikaInputStream stream, org.xml.sax.ContentHandler handler,
                org.apache.tika.metadata.Metadata metadata, org.apache.tika.parser.ParseContext ctx, boolean outputHtml) {
                count.incrementAndGet();
            }
        });
        try (var input = org.apache.tika.io.TikaInputStream.get(fixture("stored").toPath())) {
            assertThrows(org.apache.tika.exception.TikaException.class, () -> new Rar5Parser(decoder.toString(), Rar5Parser.DEADLINE_SECONDS, 1).parse(
                input, new org.xml.sax.helpers.DefaultHandler(), new org.apache.tika.metadata.Metadata(), context));
        }
        assertEquals(0, count.get());
    }

    // --- one decoder process per archive, not one per member ---------------------------------

    /** A fake 7zz: "l" prints LISTING; "x" of the whole archive prints STREAM; "x" of one member
     * (the archive path followed by "-- <name>") prints that member's bytes from MEMBERS. Every
     * invocation is appended to calls.log. */
    private Path fakeDecoder(String listing, String stream, String members) throws Exception {
        Path dir = output.resolve("fake-" + System.nanoTime());
        java.nio.file.Files.createDirectories(dir);
        Path log = dir.resolve("calls.log");
        Path decoder = dir.resolve("decoder");
        java.nio.file.Files.writeString(decoder, "#!/bin/sh\n"
            + "echo \"$*\" >> '" + log + "'\n"
            + "if [ \"$1\" = l ]; then printf '" + listing + "'; exit 0; fi\n"
            + "for last; do :; done\n"
            + "case \"$last\" in *.rar) printf '" + stream + "'; exit 0;; esac\n"
            + members + "\n");
        assertTrue(decoder.toFile().setExecutable(true));
        return decoder;
    }

    private java.util.Map<String, String> decodeWith(Path decoder, org.apache.tika.metadata.Metadata root)
            throws Exception {
        return decodeWithInto(decoder, new java.util.LinkedHashMap<>(), root);
    }

    private java.util.Map<String, String> decodeWithInto(Path decoder, java.util.Map<String, String> seen)
            throws Exception {
        return decodeWithInto(decoder, seen, new org.apache.tika.metadata.Metadata());
    }

    private java.util.Map<String, String> decodeWithInto(Path decoder, java.util.Map<String, String> seen,
            org.apache.tika.metadata.Metadata root) throws Exception {
        var context = new org.apache.tika.parser.ParseContext();
        context.set(org.apache.tika.extractor.EmbeddedDocumentExtractor.class, new org.apache.tika.extractor.EmbeddedDocumentExtractor() {
            public boolean shouldParseEmbedded(org.apache.tika.metadata.Metadata metadata) { return true; }
            public void parseEmbedded(org.apache.tika.io.TikaInputStream stream, org.xml.sax.ContentHandler handler,
                org.apache.tika.metadata.Metadata metadata, org.apache.tika.parser.ParseContext ctx, boolean outputHtml)
                    throws java.io.IOException {
                seen.put(metadata.get(org.apache.tika.metadata.TikaCoreProperties.RESOURCE_NAME_KEY),
                    new String(stream.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8));
            }
        });
        try (var input = org.apache.tika.io.TikaInputStream.get(fixture("stored").toPath())) {
            new Rar5Parser(decoder.toString(), Rar5Parser.DEADLINE_SECONDS, 1).parse(input, new org.xml.sax.helpers.DefaultHandler(), root, context);
        }
        return seen;
    }

    private static long calls(Path decoder) throws Exception {
        return java.nio.file.Files.readAllLines(decoder.resolveSibling("calls.log")).size();
    }

    private static final String THREE = "Path = a.txt\\nSize = 3\\nPacked Size = 3\\nFolder = -\\nCRC = 352441C2\\n\\n"
        + "Path = dir\\nSize = 0\\nFolder = +\\n\\n"
        + "Path = empty.txt\\nSize = 0\\nPacked Size = 0\\nFolder = -\\nCRC = 00000000\\n\\n"
        + "Path = dir/b.txt\\nSize = 4\\nPacked Size = 4\\nFolder = -\\nCRC = 3B6D8E59\\n";

    @Test void decodesEveryMemberWithOneDecoderRun() throws Exception {
        Path decoder = fakeDecoder(THREE, "abcdefg", "exit 9");
        var seen = decodeWith(decoder, new org.apache.tika.metadata.Metadata());
        assertEquals(java.util.Map.of("a.txt", "abc", "empty.txt", "", "dir/b.txt", "defg"), seen);
        assertEquals(3, calls(decoder), "one listing + one test + one decode, whatever the member count");
    }

    @Test void streamLongerThanItsListingIsRefused() throws Exception {
        Path decoder = fakeDecoder(THREE, "abcdefgX", "exit 9");
        var seen = new java.util.LinkedHashMap<String, String>();
        assertThrows(org.apache.tika.exception.TikaException.class,
            () -> seen.putAll(decodeWith(decoder, new org.apache.tika.metadata.Metadata())));
        assertTrue(seen.isEmpty());
    }

    @Test void streamShorterThanItsListingIsRefusedBeforeAnythingIsPublished() throws Exception {
        Path decoder = fakeDecoder(THREE, "abcdef", "exit 9");
        var seen = new java.util.LinkedHashMap<String, String>();
        assertThrows(org.apache.tika.exception.TikaException.class,
            () -> seen.putAll(decodeWith(decoder, new org.apache.tika.metadata.Metadata())));
        assertTrue(seen.isEmpty());
    }

    @Test void archiveWithLinksFallsBackToPerMemberDecoding() throws Exception {
        // 7zz writes a link's target into the -so stream, so a link-bearing archive's stream
        // need not match its listing; the legacy one-member-at-a-time path still extracts it.
        String listing = "Path = a.txt\\nSize = 3\\nFolder = -\\n\\n"
            + "Path = link\\nSize = 0\\nFolder = -\\nSymbolic Link = a.txt\\n";
        Path decoder = fakeDecoder(listing, "abca.txt", "[ \"$last\" = a.txt ] && printf abc && exit 0; exit 9");
        var root = new org.apache.tika.metadata.Metadata();
        var seen = decodeWith(decoder, root);
        assertEquals(java.util.Map.of("a.txt", "abc"), seen);
        assertTrue(String.join("|", root.getValues("X-RedTusk:archive-skipped")).contains("link"));
    }

    @Test void realMultiMemberArchiveDecodesEveryMember() throws Exception {
        ParseResult result = runner(1024 * 1024).parse(fixture("multiple_files"), "multi.rar", "0".repeat(64));
        assertNull(result.entries().getFirst().error());
        assertEquals(5, result.entries().size(), result.entries().stream().map(EntryResult::path).toList().toString());
    }

    @Test void embeddedDecisionsAreMadeInOrderAsMembersArePublished() throws Exception {
        // An extractor whose decision depends on what it has already parsed (an entry budget)
        // must see each member only after the previous one was published.
        Path decoder = fakeDecoder(THREE, "abcdefg", "exit 9");
        var seen = new java.util.ArrayList<String>();
        var context = new org.apache.tika.parser.ParseContext();
        context.set(org.apache.tika.extractor.EmbeddedDocumentExtractor.class, new org.apache.tika.extractor.EmbeddedDocumentExtractor() {
            public boolean shouldParseEmbedded(org.apache.tika.metadata.Metadata metadata) { return seen.isEmpty(); }
            public void parseEmbedded(org.apache.tika.io.TikaInputStream stream, org.xml.sax.ContentHandler handler,
                org.apache.tika.metadata.Metadata metadata, org.apache.tika.parser.ParseContext ctx, boolean outputHtml) {
                seen.add(metadata.get(org.apache.tika.metadata.TikaCoreProperties.RESOURCE_NAME_KEY));
            }
        });
        try (var input = org.apache.tika.io.TikaInputStream.get(fixture("stored").toPath())) {
            new Rar5Parser(decoder.toString(), Rar5Parser.DEADLINE_SECONDS, 1).parse(input, new org.xml.sax.helpers.DefaultHandler(),
                new org.apache.tika.metadata.Metadata(), context);
        }
        assertEquals(java.util.List.of("a.txt"), seen);
    }

    @Test void failedWholeArchiveRunFallsBackToPerMemberDecoding() throws Exception {
        // One corrupt member makes the single run fail; the members before it are still
        // published, as the one-run-per-member decoder did.
        String listing = "Path = a.txt\\nSize = 3\\nPacked Size = 3\\nFolder = -\\nCRC = 352441C2\\n\\n"
            + "Path = bad.bin\\nSize = 2\\nPacked Size = 2\\nFolder = -\\nCRC = 00000000\\n";
        Path dir = output.resolve("fake-fail");
        java.nio.file.Files.createDirectories(dir);
        Path decoder = dir.resolve("decoder");
        java.nio.file.Files.writeString(decoder, "#!/bin/sh\n"
            + "echo \"$*\" >> '" + dir.resolve("calls.log") + "'\n"
            + "if [ \"$1\" = l ]; then printf '" + listing + "'; exit 0; fi\n"
            + "for last; do :; done\n"
            + "case \"$last\" in *.rar) printf abcXY; exit 2;; a.txt) printf abc; exit 0;; esac\n"
            + "exit 2\n");
        assertTrue(decoder.toFile().setExecutable(true));
        var seen = new java.util.LinkedHashMap<String, String>();
        assertThrows(org.apache.tika.exception.TikaException.class,
            () -> seen.putAll(decodeWithInto(decoder, seen)));
        assertEquals(java.util.Map.of("a.txt", "abc"), seen);
    }

    // --- a whole-archive stream must never shift a member's bytes ------------------------------

    private java.util.Map<String, String> decodeReal(String fixture) throws Exception {
        return decodeRealInto(fixture, new java.util.LinkedHashMap<>());
    }

    private java.util.Map<String, String> decodeRealInto(String fixture, java.util.Map<String, String> seen)
            throws Exception {
        var context = new org.apache.tika.parser.ParseContext();
        context.set(org.apache.tika.extractor.EmbeddedDocumentExtractor.class, new org.apache.tika.extractor.EmbeddedDocumentExtractor() {
            public boolean shouldParseEmbedded(org.apache.tika.metadata.Metadata metadata) { return true; }
            public void parseEmbedded(org.apache.tika.io.TikaInputStream stream, org.xml.sax.ContentHandler handler,
                org.apache.tika.metadata.Metadata metadata, org.apache.tika.parser.ParseContext ctx, boolean outputHtml)
                    throws java.io.IOException {
                seen.put(metadata.get(org.apache.tika.metadata.TikaCoreProperties.RESOURCE_NAME_KEY),
                    new String(stream.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8));
            }
        });
        try (var input = org.apache.tika.io.TikaInputStream.get(fixture(fixture).toPath())) {
            new Rar5Parser(System.getenv().getOrDefault("REDTUSK_7ZZ", "7zz"), Rar5Parser.DEADLINE_SECONDS, 1).parse(input, new org.xml.sax.helpers.DefaultHandler(),
                new org.apache.tika.metadata.Metadata(), context);
        }
        return seen;
    }

    @Test void unlistedAlternateStreamCannotShiftAMembersBytes() throws Exception {
        // A decoy alternate stream (unlisted without -sns, yet written by x -so) plus a
        // data-less symlink claiming the same size keeps the whole stream's total equal to
        // the listing's while handing payload.exe the decoy's bytes.
        for (String fixture : java.util.List.of("altstream_decoy_symlink", "altstream_decoy_regular")) {
            var seen = decodeReal(fixture);
            assertEquals("MALWARE!", seen.get("payload.exe"), fixture + ": " + seen);
            assertFalse(seen.containsValue("harmless"), fixture + ": " + seen);
        }
        assertEquals("abc", decodeReal("altstream_decoy_regular").get("f1.txt"));
    }

    @Test void membersArePublishedAsTheyAreDecodedNotSpooledFirst() throws Exception {
        // The single run must not stage the whole archive before publishing: by the time the
        // first member is parsed, the private scratch must hold at most that member.
        Path decoder = fakeDecoder(THREE, "abcdefg", "exit 9");
        var tmpBefore = java.nio.file.Files.list(Path.of(System.getProperty("java.io.tmpdir")))
            .filter(p -> p.getFileName().toString().startsWith("redtusk-rar5-")).count();
        var context = new org.apache.tika.parser.ParseContext();
        var spooled = new java.util.ArrayList<Long>();
        context.set(org.apache.tika.extractor.EmbeddedDocumentExtractor.class, new org.apache.tika.extractor.EmbeddedDocumentExtractor() {
            public boolean shouldParseEmbedded(org.apache.tika.metadata.Metadata metadata) { return true; }
            public void parseEmbedded(org.apache.tika.io.TikaInputStream stream, org.xml.sax.ContentHandler handler,
                org.apache.tika.metadata.Metadata metadata, org.apache.tika.parser.ParseContext ctx, boolean outputHtml)
                    throws java.io.IOException {
                spooled.add(java.nio.file.Files.list(Path.of(System.getProperty("java.io.tmpdir")))
                    .filter(p -> p.getFileName().toString().startsWith("redtusk-rar5-")).count());
            }
        });
        try (var input = org.apache.tika.io.TikaInputStream.get(fixture("stored").toPath())) {
            new Rar5Parser(decoder.toString(), Rar5Parser.DEADLINE_SECONDS, 1).parse(input, new org.xml.sax.helpers.DefaultHandler(),
                new org.apache.tika.metadata.Metadata(), context);
        }
        assertEquals(3, spooled.size());
        assertTrue(spooled.stream().allMatch(n -> n == tmpBefore), "a whole-archive spool dir exists: " + spooled);
    }

    @Test void truncatedMemberCannotShiftLaterMembersUnderChosenCrcs() throws Exception {
        // A short member makes `7zz x -so` keep going with later members' bytes; header CRCs
        // the author chose let the shifted windows pass. Nothing may be published under a
        // name whose bytes are not its own: the archive is refused, as one-run-per-member did.
        for (String fixture : java.util.List.of("truncated_member_shuffle", "truncated_member_swap",
                "truncated_member_stored")) {
            var seen = new java.util.LinkedHashMap<String, String>();
            assertThrows(org.apache.tika.exception.TikaException.class,
                () -> seen.putAll(decodeRealInto(fixture, seen)), fixture);
            assertFalse(seen.containsKey("readme.txt") || "harmless".equals(seen.get("payload.exe")),
                fixture + ": " + seen);
        }
    }

    @Test void aSlowNestedParseAfterTheLastMemberIsNotADeadlineFailure() throws Exception {
        Path decoder = fakeDecoder("Path = a.txt\\nSize = 3\\nPacked Size = 3\\nFolder = -\\nCRC = 352441C2\\n", "abc", "exit 9");
        var context = new org.apache.tika.parser.ParseContext();
        context.set(org.apache.tika.extractor.EmbeddedDocumentExtractor.class, new org.apache.tika.extractor.EmbeddedDocumentExtractor() {
            public boolean shouldParseEmbedded(org.apache.tika.metadata.Metadata metadata) { return true; }
            public void parseEmbedded(org.apache.tika.io.TikaInputStream stream, org.xml.sax.ContentHandler handler,
                org.apache.tika.metadata.Metadata metadata, org.apache.tika.parser.ParseContext ctx, boolean outputHtml) {
                try { Thread.sleep(1500); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            }
        });
        try (var input = org.apache.tika.io.TikaInputStream.get(fixture("stored").toPath())) {
            new Rar5Parser(decoder.toString(), 1, 1).parse(input, new org.xml.sax.helpers.DefaultHandler(),
                new org.apache.tika.metadata.Metadata(), context);
        }
    }

    @Test void dataLessLinkListedAsAFileCannotShiftTheStream() throws Exception {
        // Each passes `7zz t`, yet its entry writes nothing under `x -so`. Whatever is decided,
        // the payload's bytes may only ever appear under payload.exe.
        for (String fixture : java.util.List.of("emptylink_hard_hide", "emptylink_copy_hide",
                "emptylink_symlink_mode_hide", "emptylink_symlink_empty_hide", "emptylink_redir0_hide",
                "emptylink_hard_split", "emptylink_copy_split")) {
            var seen = new java.util.LinkedHashMap<String, String>();
            try { decodeRealInto(fixture, seen); }
            catch (org.apache.tika.exception.TikaException refused) { /* refused, as origin/main */ }
            for (var e : seen.entrySet()) {
                boolean carriesPayload = e.getValue().contains("MALWARE");
                assertEquals(e.getKey().equals("payload.exe") && carriesPayload || !carriesPayload, true,
                    fixture + ": " + seen);
            }
            if (seen.containsKey("payload.exe"))
                assertTrue(seen.get("payload.exe").startsWith("MALWARE"), fixture + ": " + seen);
        }
    }

    @Test void realMultiMemberArchiveTakesTheSingleRun() throws Exception {
        Path dir = output.resolve("shim");
        java.nio.file.Files.createDirectories(dir);
        Path log = dir.resolve("calls.log");
        Path shim = dir.resolve("7zz");
        java.nio.file.Files.writeString(shim, "#!/bin/sh\necho \"$1\" >> '" + log + "'\nexec 7zz \"$@\"\n");
        assertTrue(shim.toFile().setExecutable(true));
        var seen = new java.util.ArrayList<String>();
        var context = new org.apache.tika.parser.ParseContext();
        context.set(org.apache.tika.extractor.EmbeddedDocumentExtractor.class, new org.apache.tika.extractor.EmbeddedDocumentExtractor() {
            public boolean shouldParseEmbedded(org.apache.tika.metadata.Metadata metadata) { return true; }
            public void parseEmbedded(org.apache.tika.io.TikaInputStream stream, org.xml.sax.ContentHandler handler,
                org.apache.tika.metadata.Metadata metadata, org.apache.tika.parser.ParseContext ctx, boolean outputHtml) {
                seen.add(metadata.get(org.apache.tika.metadata.TikaCoreProperties.RESOURCE_NAME_KEY));
            }
        });
        try (var input = org.apache.tika.io.TikaInputStream.get(fixture("multiple_files").toPath())) {
            new Rar5Parser(shim.toString(), Rar5Parser.DEADLINE_SECONDS, 1).parse(input, new org.xml.sax.helpers.DefaultHandler(),
                new org.apache.tika.metadata.Metadata(), context);
        }
        assertEquals(4, seen.size(), seen.toString());
        assertEquals(java.util.List.of("l", "t", "x"), java.nio.file.Files.readAllLines(log));
    }

    @Test void smallArchivesKeepThePerMemberDecode() throws Exception {
        // a `7zz t` pass plus an `x -so` pass decode the archive twice under one deadline; for a
        // few members one run each is cheaper and keeps a large single member within budget
        Path decoder = fakeDecoder(THREE, "abcdefg", "[ \"$last\" = a.txt ] && printf abc && exit 0; "
            + "[ \"$last\" = empty.txt ] && exit 0; [ \"$last\" = dir/b.txt ] && printf defg && exit 0; exit 9");
        var seen = new java.util.LinkedHashMap<String, String>();
        var context = new org.apache.tika.parser.ParseContext();
        context.set(org.apache.tika.extractor.EmbeddedDocumentExtractor.class, new org.apache.tika.extractor.EmbeddedDocumentExtractor() {
            public boolean shouldParseEmbedded(org.apache.tika.metadata.Metadata metadata) { return true; }
            public void parseEmbedded(org.apache.tika.io.TikaInputStream stream, org.xml.sax.ContentHandler handler,
                org.apache.tika.metadata.Metadata metadata, org.apache.tika.parser.ParseContext ctx, boolean outputHtml)
                    throws java.io.IOException {
                seen.put(metadata.get(org.apache.tika.metadata.TikaCoreProperties.RESOURCE_NAME_KEY),
                    new String(stream.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8));
            }
        });
        try (var input = org.apache.tika.io.TikaInputStream.get(fixture("stored").toPath())) {
            new Rar5Parser(decoder.toString()).parse(input, new org.xml.sax.helpers.DefaultHandler(),
                new org.apache.tika.metadata.Metadata(), context);
        }
        assertEquals(java.util.Map.of("a.txt", "abc", "empty.txt", "", "dir/b.txt", "defg"), seen);
        assertFalse(java.nio.file.Files.readAllLines(decoder.resolveSibling("calls.log")).stream()
            .anyMatch(line -> line.startsWith("t ")), "no whole-archive test for 3 members");
    }
}
