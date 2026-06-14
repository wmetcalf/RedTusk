package io.redtusk.worker;

import org.junit.jupiter.api.Test;

import java.io.File;
import java.net.URL;

import static org.junit.jupiter.api.Assertions.*;

class ParserRunnerTest {

    private static JobDescriptor.LimitsDescriptor noLimits() {
        return new JobDescriptor.LimitsDescriptor(10, 5000, 524288000L, 60);
    }

    private File fixture(String name) {
        URL url = getClass().getClassLoader().getResource(name);
        assertNotNull(url, "Test resource not found: " + name);
        return new File(url.getFile());
    }

    @Test
    void parsesPlainTextToRootEntry() throws Exception {
        ParserRunner runner = new ParserRunner(
            noLimits(), true, false, "eng", 3, 2000, true, "", "tesseract"
        );
        ParseResult result = runner.parse(
            fixture("sample.txt"), "sample.txt",
            "ae1c" + "0".repeat(60)
        );

        assertFalse(result.entries().isEmpty());
        EntryResult root = result.entries().get(0);
        assertEquals("/", root.path());
        assertNull(root.parentPath());
        assertEquals(0, root.depth());
        assertTrue(root.contentType().contains("text"),
            "content type must be text-ish, was: " + root.contentType());
        assertFalse(root.text().isBlank(), "text must not be blank for a text file");
        assertTrue(root.text().contains("Hello RedTusk"), "text must contain fixture content");
        assertNotNull(root.qr());
        assertNotNull(root.ocr());
        assertNull(root.error());
    }

    @org.junit.jupiter.api.condition.EnabledIfSystemProperty(named = "redtusk.macro.file", matches = ".+")
    @Test
    void extractsMacroEvenWhenBodyBustsWriteLimit() throws Exception {
        // Gated manual validation. Point at a real macro-bearing file whose body text exceeds
        // the 8 MB per-parse char cap (a junk-padded malspam .xls/.xlsm). Pre-fix, the
        // cumulative write-limit starved the VBA source (no text/x-vbasic entry); post-fix the
        // OfficeParser / OOXML extractor emits macros BEFORE the body, so they survive.
        //   -Dredtusk.macro.file=/path/to/truncation-case.xls
        File f = new File(System.getProperty("redtusk.macro.file"));
        assertTrue(f.isFile(), "file not found: " + f);
        ParserRunner runner = new ParserRunner(noLimits(), false, false, "eng", 3, 2000, false, "", "tesseract");
        ParseResult result = runner.parse(f, f.getName(), "0".repeat(64));
        long macroEntries = result.entries().stream()
                .filter(e -> e.contentType() != null && e.contentType().contains("vbasic"))
                .count();
        long maxText = result.entries().stream()
                .mapToLong(e -> e.text() == null ? 0 : e.text().length()).max().orElse(0);
        System.out.println("MACRO-VALIDATION file=" + f.getName()
                + " entries=" + result.entries().size()
                + " macroEntries=" + macroEntries + " maxTextLen=" + maxText);
        assertTrue(macroEntries > 0, "expected >=1 text/x-vbasic macro entry (was " + macroEntries + ")");
    }

    @Test
    void respectsMaxEmbeddedEntriesLimit() throws Exception {
        var limits = new JobDescriptor.LimitsDescriptor(10, 1, 524288000L, 60);
        ParserRunner runner = new ParserRunner(limits, false, false, "eng", 3, 2000, true, "", "tesseract");
        ParseResult result = runner.parse(
            fixture("sample.txt"), "sample.txt", "ae1c" + "0".repeat(60)
        );
        assertFalse(result.entries().isEmpty());
    }

    @Test
    void sha256IsPopulatedOnRootEntry() throws Exception {
        String expectedSha = "ae1c" + "0".repeat(60);
        ParserRunner runner = new ParserRunner(noLimits(), false, false, "eng", 3, 2000, true, "", "tesseract");
        ParseResult result = runner.parse(fixture("sample.txt"), "sample.txt", expectedSha);
        assertEquals(expectedSha, result.entries().get(0).sha256());
    }

    @Test
    void rootEntryPathIsSlash() throws Exception {
        ParserRunner runner = new ParserRunner(noLimits(), false, false, "eng", 3, 2000, true, "", "tesseract");
        ParseResult result = runner.parse(
            fixture("sample.txt"), "sample.txt", "ae1c" + "0".repeat(60)
        );
        assertEquals("/", result.entries().get(0).path());
    }

    @Test
    void respectsMaxExtractedBytesLimit() throws Exception {
        var limits = new JobDescriptor.LimitsDescriptor(10, 5000, 8L, 60);
        ParserRunner runner = new ParserRunner(limits, false, false, "eng", 3, 2000, true, "", "tesseract");
        ParseResult result = runner.parse(
            fixture("sample.txt"), "sample.txt", "ae1c" + "0".repeat(60)
        );

        int total = result.entries().stream().mapToInt(e -> e.text().getBytes(java.nio.charset.StandardCharsets.UTF_8).length).sum();
        assertTrue(total <= 8, "extracted text must be capped to max_extracted_bytes");
        assertNotNull(result.truncated());
        assertEquals("max_extracted_bytes", result.truncated().reason());
    }
}
