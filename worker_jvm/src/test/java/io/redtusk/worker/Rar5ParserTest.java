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
            assertThrows(org.apache.tika.exception.TikaException.class, () -> new Rar5Parser(decoder.toString()).parse(
                input, new org.xml.sax.helpers.DefaultHandler(), new org.apache.tika.metadata.Metadata(), context));
        }
        assertEquals(0, count.get());
    }
}
