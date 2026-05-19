package io.redtusk.worker;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.File;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.HashSet;

import static org.junit.jupiter.api.Assertions.*;

class RmetaWriterTest {

    private static final ObjectMapper OM = new ObjectMapper();

    private static JobDescriptor minimalDescriptor() {
        return new JobDescriptor(
            "/scratch/in/doc.txt", "/scratch/out",
            "ae1c" + "0".repeat(60),
            "doc.txt",
            new JobDescriptor.LimitsDescriptor(10, 5000, 524288000L, 60),
            true, false, "eng", 3,
            "default", "runsc", true, true, false,
            "0.1.0",
            "/usr/local/bin/ZXingReader", "tesseract",
            2000, true, true
        );
    }

    private static EntryResult rootEntry() {
        return new EntryResult(
            "/", null, 0, "text/plain", 13L,
            "ae1c" + "0".repeat(60), null, null, false, null, null, null, Map.of(), "Hello RedTusk.", "en",
            new EntryResult.QrResult(List.of(), "no_images"),
            new EntryResult.OcrResult("", null, 0, "no_images"),
            null
        );
    }

    @Test
    void writesMetadataJsonFile(@TempDir Path tmp) throws Exception {
        Path outDir = tmp.resolve("out");
        outDir.toFile().mkdirs();

        RmetaWriter writer = new RmetaWriter(minimalDescriptor(),
            new ParseResult(List.of(rootEntry()), List.of(), null), 42L);
        writer.write(outDir.toFile());

        File metaFile = outDir.resolve("metadata.json").toFile();
        assertTrue(metaFile.exists(), "metadata.json must exist");

        JsonNode root = OM.readTree(metaFile);
        assertEquals("0.1.0", root.get("redtusk_version").asText());
        assertEquals("ae1c" + "0".repeat(60), root.get("input").get("sha256").asText());
        assertEquals("text/plain", root.get("extraction").get("root_content_type").asText());
        assertEquals(42L, root.get("extraction").get("duration_ms").asLong());
        assertEquals(1, root.get("extraction").get("entries").size());
        assertTrue(root.get("truncated").isNull());
        assertEquals(0, root.get("warnings").size());
    }

    @Test
    void topLevelKeysMatchSchema(@TempDir Path tmp) throws Exception {
        Path outDir = tmp.resolve("out");
        outDir.toFile().mkdirs();
        new RmetaWriter(minimalDescriptor(),
            new ParseResult(List.of(rootEntry()), List.of(), null), 0L).write(outDir.toFile());

        JsonNode root = OM.readTree(outDir.resolve("metadata.json").toFile());
        var expected = Set.of(
            "redtusk_version", "input", "extraction",
            "limits", "truncated", "warnings", "sandbox"
        );
        var actual = new HashSet<String>();
        root.fieldNames().forEachRemaining(actual::add);
        assertEquals(expected, actual, "top-level keys must match the JSON Schema exactly");
    }

    @Test
    void entriesAreSerialised(@TempDir Path tmp) throws Exception {
        Path outDir = tmp.resolve("out");
        outDir.toFile().mkdirs();
        EntryResult embedded = new EntryResult(
            "/embedded/img.png", "/", 1, "image/png", 512L,
            "b".repeat(64), "d41d8cd98f00b204e9800998ecf8427e", "da39a3ee5e6b4b0d3255bfef95601890afd80709",
            true, null, "a1b2c3d4e5f6a7b8", "1f0e0310000000",
            Map.of("Image-Width", "100"), "", null,
            new EntryResult.QrResult(
                List.of(new EntryResult.QrCode(
                    "https://evil.test/x", "QR_CODE", "aGVsbG8=", "0,0 50,0 50,50 0,50")),
                null
            ),
            new EntryResult.OcrResult("click here", "eng", 88, null),
            null
        );
        new RmetaWriter(minimalDescriptor(),
            new ParseResult(List.of(rootEntry(), embedded), List.of(), null), 100L)
            .write(outDir.toFile());

        JsonNode root = OM.readTree(outDir.resolve("metadata.json").toFile());
        JsonNode entries = root.get("extraction").get("entries");
        assertEquals(2, entries.size());
        JsonNode embNode = entries.get(1);
        assertEquals("/embedded/img.png", embNode.get("path").asText());
        assertEquals("/", embNode.get("parent_path").asText());
        assertEquals(1, embNode.get("depth").asInt());
        assertEquals("https://evil.test/x",
            embNode.get("qr").get("codes").get(0).get("data").asText());
        assertEquals("click here", embNode.get("ocr").get("text").asText());
    }

    @Test
    void qrAndOcrAlwaysPresentEvenWhenEmpty(@TempDir Path tmp) throws Exception {
        Path outDir = tmp.resolve("out");
        outDir.toFile().mkdirs();
        new RmetaWriter(minimalDescriptor(),
            new ParseResult(List.of(rootEntry()), List.of(), null), 0L).write(outDir.toFile());

        JsonNode entry = OM.readTree(outDir.resolve("metadata.json").toFile())
            .get("extraction").get("entries").get(0);
        assertNotNull(entry.get("qr"), "qr must always be present");
        assertNotNull(entry.get("ocr"), "ocr must always be present");
        assertEquals("no_images", entry.get("qr").get("skipped").asText());
        assertEquals("no_images", entry.get("ocr").get("skipped").asText());
    }
}
