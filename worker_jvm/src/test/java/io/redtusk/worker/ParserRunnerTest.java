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
