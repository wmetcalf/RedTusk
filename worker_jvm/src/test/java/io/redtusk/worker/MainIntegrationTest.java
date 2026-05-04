package io.redtusk.worker;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.*;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.*;

import static org.junit.jupiter.api.Assertions.*;

class MainIntegrationTest {

    private static final ObjectMapper OM = new ObjectMapper();

    private File textFixture() throws Exception {
        File f = File.createTempFile("redtusk-test-", ".txt");
        f.deleteOnExit();
        try (var w = new FileWriter(f)) {
            w.write("Hello RedTusk.\nThis is a plain text document used as a test fixture.\n");
        }
        return f;
    }

    @Test
    void runJobProducesValidMetadataJson(@TempDir Path scratchBase) throws Exception {
        Path scratchDir = scratchBase.resolve("slot-test");
        scratchDir.toFile().mkdirs();
        Path outDir = scratchDir.resolve("out");
        outDir.toFile().mkdirs();
        File inputFile = textFixture();

        // Write job.json
        var limits = Map.of(
            "max_recursion_depth", 10, "max_embedded_entries", 5000,
            "max_extracted_bytes", 524288000, "ocr_timeout_s", 60
        );
        // Map.of() only supports up to 10 entries; use ofEntries for the full job descriptor
        var jobMap = Map.ofEntries(
            Map.entry("input_path", inputFile.getAbsolutePath()),
            Map.entry("output_dir", outDir.toFile().getAbsolutePath()),
            Map.entry("sha256", "ae1c" + "0".repeat(60)),
            Map.entry("filename_hint", "test-document.txt"),
            Map.entry("limits", limits),
            Map.entry("enable_qr", false),
            Map.entry("enable_ocr", false),
            Map.entry("ocr_lang", "eng"),
            Map.entry("ocr_psm", 3),
            Map.entry("sandbox_profile", "default"),
            Map.entry("sandbox_runtime", "runsc"),
            Map.entry("appcds", true),
            Map.entry("ksm", true),
            Map.entry("crac", false),
            Map.entry("redtusk_version", "0.1.0"),
            Map.entry("tika_version", "3.3.0")
        );
        OM.writeValue(scratchDir.resolve("job.json").toFile(), jobMap);

        // Create ready file and signal from background thread by creating control.go
        FifoLoop.createFifo(scratchDir.toFile());
        ExecutorService exec = Executors.newSingleThreadExecutor();
        exec.submit(() -> {
            try {
                Thread.sleep(200);
                scratchDir.resolve("control.go").toFile().createNewFile();
            } catch (Exception ignored) {}
            return null;
        });

        // Act
        Main.runJob(scratchDir.toFile());
        exec.shutdownNow();

        // Assert
        File metaFile = outDir.resolve("metadata.json").toFile();
        assertTrue(metaFile.exists(), "metadata.json must be written");
        JsonNode root = OM.readTree(metaFile);

        Set<String> expectedKeys = Set.of(
            "redtusk_version", "tika_version", "input", "extraction",
            "limits", "truncated", "warnings", "sandbox"
        );
        Set<String> actualKeys = new HashSet<>();
        root.fieldNames().forEachRemaining(actualKeys::add);
        assertEquals(expectedKeys, actualKeys);

        assertEquals("0.1.0", root.get("redtusk_version").asText());
        assertEquals("3.3.0", root.get("tika_version").asText());
        assertEquals("ae1c" + "0".repeat(60), root.get("input").get("sha256").asText());
        assertEquals("test-document.txt", root.get("input").get("filename_hint").asText());

        JsonNode entries = root.get("extraction").get("entries");
        assertTrue(entries.size() >= 1);
        assertEquals("/", entries.get(0).get("path").asText());
        assertEquals(0, entries.get(0).get("depth").asInt());
        assertTrue(entries.get(0).get("parent_path").isNull());
        assertNotNull(entries.get(0).get("qr"));
        assertNotNull(entries.get(0).get("ocr"));

        assertEquals("default", root.get("sandbox").get("profile").asText());
    }

    @Test
    void warmupModeDoesNotCrashOnEmptyDir(@TempDir Path tmp) {
        File corpusDir = tmp.resolve("empty-corpus").toFile();
        corpusDir.mkdirs();
        assertDoesNotThrow(() ->
            Main.main(new String[]{"--appcds-warmup", corpusDir.getAbsolutePath()}));
    }
}
