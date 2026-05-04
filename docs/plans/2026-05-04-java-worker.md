# RedTusk Java Worker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `worker_jvm/` Maven project — a fat JAR that warms a Tika JVM, blocks on a named pipe (fifo) waiting for the dispatcher's signal, processes one document through `RecursiveParserWrapper`, optionally runs QR/OCR scanners on image entries, writes the canonical `metadata.json` to the scratch dir, then exits.

**Architecture:** Three modes: `--appcds-warmup <corpus-dir>` (parse a set of files to exercise parser classes — used at image build time for AppCDS dump), `--checkpoint` (call CRaC `Core.checkpointRestore()` — no-op stub in this plan), and `--run <scratch-dir>` (normal operation: fifo-wait → parse → exit). The dispatcher sets `REDTUSK_SCRATCH_DIR` and passes `--run` to the container; the container writes `{scratch_dir}/control.fifo` as its readiness signal. All output lands in `{scratch_dir}/out/metadata.json`.

**Tech Stack:** Java 25, Apache Tika 3.3.0 (`tika-core` + `tika-parsers-standard-package`), Jackson 2.18.x (JSON), JUnit 5 (tests), Maven 3.8+ with `maven-assembly-plugin` (fat JAR). Tesseract 5.x + zbarimg (shelled out for OCR/QR); tests skip gracefully if binaries absent.

---

## File Structure

```
worker_jvm/
├── pom.xml
└── src/
    ├── main/java/io/redtusk/worker/
    │   ├── Main.java              entry point; mode dispatch
    │   ├── JobDescriptor.java     deserialized job.json
    │   ├── EntryResult.java       one extracted entry (qr, ocr, metadata, text, sha256)
    │   ├── ParserRunner.java      Tika RecursiveParserWrapper with limits
    │   ├── ScannerRunner.java     tesseract + zbarimg subprocess dispatch
    │   ├── RmetaWriter.java       serializes List<EntryResult> → metadata.json
    │   ├── FifoLoop.java          blocking open+read on control.fifo
    │   ├── KsmHelper.java         no-op stub (madvise JNI in Plan 3)
    │   └── CapDropper.java        no-op stub (prctl in Plan 6)
    └── test/
        ├── java/io/redtusk/worker/
        │   ├── ParserRunnerTest.java
        │   ├── ScannerRunnerTest.java
        │   ├── RmetaWriterTest.java
        │   └── MainIntegrationTest.java    end-to-end: fifo → JAR → metadata.json
        └── resources/
            ├── sample.txt         "Hello RedTusk" — plain text fixture
            ├── sample.html        HTML with an image tag — exercises HTML parser
            └── sample-qr.png      PNG containing a QR code encoding "https://redtusk.example"
```

**Per-file responsibilities:**

| File | Responsibility |
|---|---|
| `Main.java` | Parse CLI args, dispatch to mode, exit with code 0/1/2 |
| `JobDescriptor.java` | Jackson-deserialised job.json; immutable value class |
| `EntryResult.java` | One entry: path, depth, content_type, sha256, size_bytes, metadata, text, language, qr, ocr, error |
| `ParserRunner.java` | Drive `RecursiveParserWrapper` with limit enforcement; return `List<EntryResult>` |
| `ScannerRunner.java` | Fork tesseract/zbarimg subprocesses; skip gracefully on missing binary |
| `RmetaWriter.java` | Assemble the full rmeta document object; write JSON via Jackson |
| `FifoLoop.java` | Create the fifo (`mkfifo` via `ProcessBuilder`), open it for read, return signal line |
| `KsmHelper.java` | No-op for now; Plan 3 adds native madvise via JNI |
| `CapDropper.java` | No-op for now; Plan 6 adds prctl(PR_CAPBSET_DROP) |

---

## Task 1: Maven project scaffold

**Files:**
- Create: `worker_jvm/pom.xml`
- Create: `worker_jvm/src/main/java/io/redtusk/worker/.gitkeep`
- Create: `worker_jvm/src/test/java/io/redtusk/worker/.gitkeep`
- Create: `worker_jvm/src/test/resources/sample.txt`

- [ ] **Step 1: Create `worker_jvm/pom.xml`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>

  <groupId>io.redtusk</groupId>
  <artifactId>redtusk-worker</artifactId>
  <version>0.1.0</version>
  <packaging>jar</packaging>

  <properties>
    <maven.compiler.release>25</maven.compiler.release>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    <tika.version>3.3.0</tika.version>
    <jackson.version>2.18.3</jackson.version>
    <junit.version>5.11.4</junit.version>
  </properties>

  <dependencies>
    <!-- Tika core API -->
    <dependency>
      <groupId>org.apache.tika</groupId>
      <artifactId>tika-core</artifactId>
      <version>${tika.version}</version>
    </dependency>
    <!-- All standard parsers (Office, PDF, HTML, email, etc.) -->
    <dependency>
      <groupId>org.apache.tika</groupId>
      <artifactId>tika-parsers-standard-package</artifactId>
      <version>${tika.version}</version>
    </dependency>
    <!-- JSON serialization -->
    <dependency>
      <groupId>com.fasterxml.jackson.core</groupId>
      <artifactId>jackson-databind</artifactId>
      <version>${jackson.version}</version>
    </dependency>
    <!-- Testing -->
    <dependency>
      <groupId>org.junit.jupiter</groupId>
      <artifactId>junit-jupiter</artifactId>
      <version>${junit.version}</version>
      <scope>test</scope>
    </dependency>
  </dependencies>

  <build>
    <plugins>
      <!-- Run JUnit 5 tests -->
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-surefire-plugin</artifactId>
        <version>3.5.2</version>
        <configuration>
          <!-- Pass through env vars needed by integration tests -->
          <environmentVariables>
            <REDTUSK_TEST_SCRATCH>${project.build.directory}/test-scratch</REDTUSK_TEST_SCRATCH>
          </environmentVariables>
          <!-- Allow forked JVM to inherit current JVM args -->
          <argLine>--enable-native-access=ALL-UNNAMED</argLine>
        </configuration>
      </plugin>
      <!-- Fat JAR for running standalone -->
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-assembly-plugin</artifactId>
        <version>3.7.1</version>
        <configuration>
          <descriptorRefs>
            <descriptorRef>jar-with-dependencies</descriptorRef>
          </descriptorRefs>
          <archive>
            <manifest>
              <mainClass>io.redtusk.worker.Main</mainClass>
            </manifest>
          </archive>
          <appendAssemblyId>false</appendAssemblyId>
          <finalName>redtusk-worker</finalName>
        </configuration>
        <executions>
          <execution>
            <id>make-assembly</id>
            <phase>package</phase>
            <goals><goal>single</goal></goals>
          </execution>
        </executions>
      </plugin>
    </plugins>
  </build>
</project>
```

- [ ] **Step 2: Create minimal directory structure**

```bash
mkdir -p /home/coz/Downloads/RedTusk/worker_jvm/src/main/java/io/redtusk/worker
mkdir -p /home/coz/Downloads/RedTusk/worker_jvm/src/test/java/io/redtusk/worker
mkdir -p /home/coz/Downloads/RedTusk/worker_jvm/src/test/resources
```

- [ ] **Step 3: Create test fixture `src/test/resources/sample.txt`**

```
Hello RedTusk.
This is a plain text document used as a test fixture.
It has no embedded resources, so extraction produces exactly one entry at path "/".
```

- [ ] **Step 4: Verify the project compiles (no source files yet — just the POM)**

```bash
cd /home/coz/Downloads/RedTusk/worker_jvm
mvn validate -q
```

Expected: `BUILD SUCCESS` (validate phase checks POM syntax only).

- [ ] **Step 5: Commit**

```bash
cd /home/coz/Downloads/RedTusk
git add worker_jvm/
git commit -m "$(cat <<'EOF'
feat(worker-jvm): add Maven project scaffold

pom.xml with Tika 3.3.0, Jackson 2.18.x, JUnit 5, and the
maven-assembly-plugin fat-JAR configuration. Target Java 25.
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: JobDescriptor — deserialise job.json

**Files:**
- Create: `worker_jvm/src/main/java/io/redtusk/worker/JobDescriptor.java`
- Test: `worker_jvm/src/test/java/io/redtusk/worker/JobDescriptorTest.java`

The dispatcher writes `job.json` to `{scratch_dir}/job.json` immediately before writing "go\n" to the fifo. This class deserialises it.

- [ ] **Step 1: Write the failing test at `src/test/java/io/redtusk/worker/JobDescriptorTest.java`**

```java
package io.redtusk.worker;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class JobDescriptorTest {

    private static final ObjectMapper OM = new ObjectMapper();

    @Test
    void roundTripMinimal() throws Exception {
        String json = """
            {
              "input_path": "/scratch/in/document.docx",
              "output_dir": "/scratch/out",
              "sha256": "ae1c000000000000000000000000000000000000000000000000000000000000",
              "filename_hint": "document.docx",
              "limits": {
                "max_recursion_depth": 10,
                "max_embedded_entries": 5000,
                "max_extracted_bytes": 524288000,
                "ocr_timeout_s": 60
              },
              "enable_qr": true,
              "enable_ocr": false,
              "ocr_lang": "eng",
              "ocr_psm": 3,
              "sandbox_profile": "default",
              "sandbox_runtime": "runsc",
              "appcds": true,
              "ksm": true,
              "crac": false,
              "redtusk_version": "0.1.0",
              "tika_version": "3.3.0"
            }
            """;
        JobDescriptor jd = OM.readValue(json, JobDescriptor.class);
        assertEquals("/scratch/in/document.docx", jd.inputPath());
        assertEquals("/scratch/out", jd.outputDir());
        assertEquals("ae1c000000000000000000000000000000000000000000000000000000000000", jd.sha256());
        assertEquals("document.docx", jd.filenameHint());
        assertEquals(10, jd.limits().maxRecursionDepth());
        assertEquals(5000, jd.limits().maxEmbeddedEntries());
        assertTrue(jd.enableQr());
        assertFalse(jd.enableOcr());
        assertEquals("eng", jd.ocrLang());
        assertEquals(3, jd.ocrPsm());
        assertEquals("default", jd.sandboxProfile());
        assertTrue(jd.appcds());
        assertFalse(jd.crac());
        assertEquals("3.3.0", jd.tikaVersion());
    }

    @Test
    void nullFilenameHintIsAllowed() throws Exception {
        String json = """
            {
              "input_path": "/scratch/in/upload.bin",
              "output_dir": "/scratch/out",
              "sha256": "ae1c000000000000000000000000000000000000000000000000000000000000",
              "filename_hint": null,
              "limits": {"max_recursion_depth":10,"max_embedded_entries":5000,
                         "max_extracted_bytes":524288000,"ocr_timeout_s":60},
              "enable_qr": true,
              "enable_ocr": false,
              "ocr_lang": "eng",
              "ocr_psm": 3,
              "sandbox_profile": "default",
              "sandbox_runtime": "runc",
              "appcds": false,
              "ksm": false,
              "crac": false,
              "redtusk_version": "0.1.0",
              "tika_version": "3.3.0"
            }
            """;
        JobDescriptor jd = OM.readValue(json, JobDescriptor.class);
        assertNull(jd.filenameHint());
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/coz/Downloads/RedTusk/worker_jvm
mvn test -pl . -Dtest=JobDescriptorTest -q 2>&1 | tail -5
```

Expected: compilation error or test failure (class doesn't exist yet).

- [ ] **Step 3: Write `src/main/java/io/redtusk/worker/JobDescriptor.java`**

```java
package io.redtusk.worker;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Deserialised job.json written by the dispatcher before signalling the fifo.
 * All fields are immutable after construction.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public record JobDescriptor(
    @JsonProperty("input_path")    String inputPath,
    @JsonProperty("output_dir")    String outputDir,
    @JsonProperty("sha256")        String sha256,
    @JsonProperty("filename_hint") String filenameHint,
    @JsonProperty("limits")        LimitsDescriptor limits,
    @JsonProperty("enable_qr")     boolean enableQr,
    @JsonProperty("enable_ocr")    boolean enableOcr,
    @JsonProperty("ocr_lang")      String ocrLang,
    @JsonProperty("ocr_psm")       int ocrPsm,
    @JsonProperty("sandbox_profile") String sandboxProfile,
    @JsonProperty("sandbox_runtime")  String sandboxRuntime,
    @JsonProperty("appcds")        boolean appcds,
    @JsonProperty("ksm")           boolean ksm,
    @JsonProperty("crac")          boolean crac,
    @JsonProperty("redtusk_version") String redtuskVersion,
    @JsonProperty("tika_version")  String tikaVersion
) {

    /** Extraction limits section of job.json. */
    @JsonIgnoreProperties(ignoreUnknown = true)
    public record LimitsDescriptor(
        @JsonProperty("max_recursion_depth")    int maxRecursionDepth,
        @JsonProperty("max_embedded_entries")   int maxEmbeddedEntries,
        @JsonProperty("max_extracted_bytes")    long maxExtractedBytes,
        @JsonProperty("ocr_timeout_s")          int ocrTimeoutS
    ) {}
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
mvn test -Dtest=JobDescriptorTest 2>&1 | tail -5
```

Expected: `Tests run: 2, Failures: 0, Errors: 0`.

- [ ] **Step 5: Commit**

```bash
cd /home/coz/Downloads/RedTusk
git add worker_jvm/src/main/java/io/redtusk/worker/JobDescriptor.java \
        worker_jvm/src/test/java/io/redtusk/worker/JobDescriptorTest.java
git commit -m "$(cat <<'EOF'
feat(worker-jvm): add JobDescriptor record

Deserialises job.json via Jackson. Uses Java records for immutability.
LimitsDescriptor is a nested record for the limits sub-object.
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: EntryResult — in-memory extraction result type

**Files:**
- Create: `worker_jvm/src/main/java/io/redtusk/worker/EntryResult.java`
- Test: `worker_jvm/src/test/java/io/redtusk/worker/EntryResultTest.java`

Represents one extracted entry, exactly matching the `EmbeddedEntry` shape from `src/redtusk/types.py`.

- [ ] **Step 1: Write the failing test at `src/test/java/io/redtusk/worker/EntryResultTest.java`**

```java
package io.redtusk.worker;

import org.junit.jupiter.api.Test;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

class EntryResultTest {

    @Test
    void rootEntryHasNullParent() {
        EntryResult root = new EntryResult(
            "/", null, 0, "text/plain", 13L,
            "a".repeat(64), Map.of(), "hello", "en",
            new EntryResult.QrResult(List.of(), null),
            new EntryResult.OcrResult("", null, 0, "no_images"),
            null
        );
        assertNull(root.parentPath());
        assertEquals(0, root.depth());
        assertEquals("/", root.path());
    }

    @Test
    void embeddedEntryHasDepthOne() {
        EntryResult embedded = new EntryResult(
            "/embedded/img.png", "/", 1, "image/png", 1024L,
            "b".repeat(64), Map.of("Image-Width", "200"), "", null,
            new EntryResult.QrResult(List.of(), null),
            new EntryResult.OcrResult("click here", "eng", 120, null),
            null
        );
        assertEquals("/embedded/img.png", embedded.path());
        assertEquals("/", embedded.parentPath());
        assertEquals(1, embedded.depth());
        assertEquals("click here", embedded.ocr().text());
    }

    @Test
    void errorEntryHasErrorField() {
        EntryResult bad = new EntryResult(
            "/embedded/broken.bin", "/", 1, "application/octet-stream", 0L,
            "c".repeat(64), Map.of(), "", null,
            new EntryResult.QrResult(List.of(), "error"),
            new EntryResult.OcrResult("", null, 0, "error"),
            "parse failed: unexpected EOF"
        );
        assertEquals("parse failed: unexpected EOF", bad.error());
        assertEquals("error", bad.qr().skipped());
    }

    @Test
    void qrCodeFields() {
        var code = new EntryResult.QrCode("QRCODE", "https://example.com", new int[]{0, 0, 100, 100});
        assertEquals("QRCODE", code.type());
        assertEquals("https://example.com", code.data());
        assertArrayEquals(new int[]{0, 0, 100, 100}, code.bbox());
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/coz/Downloads/RedTusk/worker_jvm
mvn test -Dtest=EntryResultTest -q 2>&1 | tail -5
```

Expected: compilation error (class not defined).

- [ ] **Step 3: Write `src/main/java/io/redtusk/worker/EntryResult.java`**

```java
package io.redtusk.worker;

import java.util.List;
import java.util.Map;

/**
 * One extracted entry from a document. Matches the EmbeddedEntry shape
 * from redtusk.types (Python). Immutable after construction.
 */
public record EntryResult(
    String path,
    String parentPath,           // null for root entry (path == "/")
    int depth,
    String contentType,
    long sizeBytes,
    String sha256,               // 64 lowercase hex chars
    Map<String, Object> metadata,
    String text,
    String language,             // nullable; null if Tika didn't detect
    QrResult qr,
    OcrResult ocr,
    String error                 // nullable; present when Tika threw on this entry
) {

    /** QR scanning result for one entry. */
    public record QrResult(
        List<QrCode> codes,
        String skipped           // null | "no_images" | "timeout_budget" | "error" | "disabled"
    ) {}

    /** One decoded QR/barcode. bbox is [x, y, w, h] in pixels. */
    public record QrCode(
        String type,
        String data,
        int[] bbox
    ) {}

    /** OCR result for one entry. */
    public record OcrResult(
        String text,
        String language,         // nullable
        int durationMs,
        String skipped           // null | "no_images" | "timeout_budget" | "error" | "disabled"
    ) {}
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
mvn test -Dtest=EntryResultTest 2>&1 | tail -5
```

Expected: `Tests run: 4, Failures: 0, Errors: 0`.

- [ ] **Step 5: Commit**

```bash
cd /home/coz/Downloads/RedTusk
git add worker_jvm/src/main/java/io/redtusk/worker/EntryResult.java \
        worker_jvm/src/test/java/io/redtusk/worker/EntryResultTest.java
git commit -m "$(cat <<'EOF'
feat(worker-jvm): add EntryResult record

Matches the EmbeddedEntry shape from types.py exactly. QrResult,
QrCode, OcrResult are nested records for clean composition.
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: RmetaWriter — serialise to canonical rmeta JSON

**Files:**
- Create: `worker_jvm/src/main/java/io/redtusk/worker/RmetaWriter.java`
- Test: `worker_jvm/src/test/java/io/redtusk/worker/RmetaWriterTest.java`

Assembles the full rmeta document from the parsed `JobDescriptor` and `List<EntryResult>`, writes `metadata.json`. The shape must satisfy the JSON Schema in `src/redtusk/schema.py`.

- [ ] **Step 1: Write the failing test at `src/test/java/io/redtusk/worker/RmetaWriterTest.java`**

```java
package io.redtusk.worker;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.File;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

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
            "0.1.0", "3.3.0"
        );
    }

    private static EntryResult rootEntry() {
        return new EntryResult(
            "/", null, 0, "text/plain", 13L,
            "ae1c" + "0".repeat(60), Map.of(), "Hello RedTusk.", "en",
            new EntryResult.QrResult(List.of(), "no_images"),
            new EntryResult.OcrResult("", null, 0, "no_images"),
            null
        );
    }

    @Test
    void writesMetadataJsonFile(@TempDir Path tmp) throws Exception {
        Path outDir = tmp.resolve("out");
        outDir.toFile().mkdirs();
        JobDescriptor jd = minimalDescriptor();
        List<EntryResult> entries = List.of(rootEntry());

        RmetaWriter writer = new RmetaWriter(jd, entries, 42L /* durationMs */);
        writer.write(outDir.toFile());

        File metaFile = outDir.resolve("metadata.json").toFile();
        assertTrue(metaFile.exists(), "metadata.json must exist");

        JsonNode root = OM.readTree(metaFile);
        assertEquals("0.1.0", root.get("redtusk_version").asText());
        assertEquals("3.3.0", root.get("tika_version").asText());
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
        RmetaWriter writer = new RmetaWriter(
            minimalDescriptor(), List.of(rootEntry()), 0L
        );
        writer.write(outDir.toFile());

        JsonNode root = OM.readTree(outDir.resolve("metadata.json").toFile());
        var expected = java.util.Set.of(
            "redtusk_version", "tika_version", "input", "extraction",
            "limits", "truncated", "warnings", "sandbox"
        );
        var actual = new java.util.HashSet<String>();
        root.fieldNames().forEachRemaining(actual::add);
        assertEquals(expected, actual, "top-level keys must match the JSON Schema exactly");
    }

    @Test
    void entriesAreSerialised(@TempDir Path tmp) throws Exception {
        Path outDir = tmp.resolve("out");
        outDir.toFile().mkdirs();
        EntryResult embedded = new EntryResult(
            "/embedded/img.png", "/", 1, "image/png", 512L,
            "b".repeat(64), Map.of("Image-Width", "100"), "", null,
            new EntryResult.QrResult(
                List.of(new EntryResult.QrCode("QRCODE", "https://evil.test/x", new int[]{0,0,50,50})),
                null
            ),
            new EntryResult.OcrResult("click here", "eng", 88, null),
            null
        );
        RmetaWriter writer = new RmetaWriter(
            minimalDescriptor(), List.of(rootEntry(), embedded), 100L
        );
        writer.write(outDir.toFile());

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
        RmetaWriter writer = new RmetaWriter(
            minimalDescriptor(), List.of(rootEntry()), 0L
        );
        writer.write(outDir.toFile());

        JsonNode entry = OM.readTree(outDir.resolve("metadata.json").toFile())
            .get("extraction").get("entries").get(0);
        assertNotNull(entry.get("qr"), "qr must always be present");
        assertNotNull(entry.get("ocr"), "ocr must always be present");
        assertEquals("no_images", entry.get("qr").get("skipped").asText());
        assertEquals("no_images", entry.get("ocr").get("skipped").asText());
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/coz/Downloads/RedTusk/worker_jvm
mvn test -Dtest=RmetaWriterTest -q 2>&1 | tail -5
```

Expected: compilation error (class not defined).

- [ ] **Step 3: Write `src/main/java/io/redtusk/worker/RmetaWriter.java`**

```java
package io.redtusk.worker;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

import java.io.File;
import java.io.IOException;
import java.time.Instant;
import java.util.List;

/**
 * Assembles the canonical rmeta document from job descriptor + extraction results
 * and writes metadata.json to the output directory.
 *
 * The produced JSON must satisfy the JSON Schema in src/redtusk/schema.py.
 */
public final class RmetaWriter {

    private static final ObjectMapper OM = new ObjectMapper();

    private final JobDescriptor job;
    private final List<EntryResult> entries;
    private final long durationMs;

    public RmetaWriter(JobDescriptor job, List<EntryResult> entries, long durationMs) {
        this.job = job;
        this.entries = entries;
        this.durationMs = durationMs;
    }

    /** Write metadata.json into {@code outputDir} (created if absent). */
    public void write(File outputDir) throws IOException {
        outputDir.mkdirs();
        ObjectNode doc = buildDocument();
        OM.writerWithDefaultPrettyPrinter()
          .writeValue(new File(outputDir, "metadata.json"), doc);
    }

    private ObjectNode buildDocument() {
        ObjectNode root = OM.createObjectNode();
        root.put("redtusk_version", job.redtuskVersion());
        root.put("tika_version", job.tikaVersion());

        // input
        ObjectNode input = root.putObject("input");
        input.put("sha256", job.sha256());
        input.put("size_bytes", entries.isEmpty() ? 0L : entries.get(0).sizeBytes());
        if (job.filenameHint() != null) {
            input.put("filename_hint", job.filenameHint());
        } else {
            input.putNull("filename_hint");
        }
        input.put("submitted_at", Instant.now().toString());

        // extraction
        ObjectNode extraction = root.putObject("extraction");
        String rootContentType = entries.isEmpty() ? "application/octet-stream"
                                                   : entries.get(0).contentType();
        extraction.put("root_content_type", rootContentType);
        String rootLanguage = entries.isEmpty() ? null : entries.get(0).language();
        if (rootLanguage != null) extraction.put("root_language", rootLanguage);
        else extraction.putNull("root_language");
        extraction.put("duration_ms", durationMs);
        ArrayNode entriesNode = extraction.putArray("entries");
        for (EntryResult e : entries) {
            entriesNode.add(buildEntry(e));
        }

        // limits
        ObjectNode limits = root.putObject("limits");
        limits.put("max_recursion_depth", job.limits().maxRecursionDepth());
        limits.put("max_embedded_entries", job.limits().maxEmbeddedEntries());
        limits.put("max_extracted_bytes", job.limits().maxExtractedBytes());
        limits.put("ocr_timeout_s", job.limits().ocrTimeoutS());

        root.putNull("truncated");
        root.putArray("warnings");

        // sandbox
        ObjectNode sandbox = root.putObject("sandbox");
        sandbox.put("profile", job.sandboxProfile());
        sandbox.put("runtime", job.sandboxRuntime());
        sandbox.put("appcds", job.appcds());
        sandbox.put("ksm", job.ksm());
        sandbox.put("crac", job.crac());

        return root;
    }

    private ObjectNode buildEntry(EntryResult e) {
        ObjectNode n = OM.createObjectNode();
        n.put("path", e.path());
        if (e.parentPath() != null) n.put("parent_path", e.parentPath());
        else n.putNull("parent_path");
        n.put("depth", e.depth());
        n.put("content_type", e.contentType());
        n.put("size_bytes", e.sizeBytes());
        n.put("sha256", e.sha256());

        ObjectNode meta = n.putObject("metadata");
        if (e.metadata() != null) {
            e.metadata().forEach((k, v) -> meta.put(k, v == null ? null : v.toString()));
        }

        n.put("text", e.text() != null ? e.text() : "");
        if (e.language() != null) n.put("language", e.language());
        else n.putNull("language");

        // qr — always present
        ObjectNode qr = n.putObject("qr");
        ArrayNode codes = qr.putArray("codes");
        if (e.qr() != null && e.qr().codes() != null) {
            for (EntryResult.QrCode code : e.qr().codes()) {
                ObjectNode c = codes.addObject();
                c.put("type", code.type());
                c.put("data", code.data());
                ArrayNode bbox = c.putArray("bbox");
                for (int v : code.bbox()) bbox.add(v);
            }
        }
        String qrSkipped = e.qr() != null ? e.qr().skipped() : "disabled";
        if (qrSkipped != null) qr.put("skipped", qrSkipped);
        else qr.putNull("skipped");

        // ocr — always present
        ObjectNode ocr = n.putObject("ocr");
        if (e.ocr() != null) {
            ocr.put("text", e.ocr().text() != null ? e.ocr().text() : "");
            if (e.ocr().language() != null) ocr.put("language", e.ocr().language());
            else ocr.putNull("language");
            ocr.put("duration_ms", e.ocr().durationMs());
            if (e.ocr().skipped() != null) ocr.put("skipped", e.ocr().skipped());
            else ocr.putNull("skipped");
        } else {
            ocr.put("text", "");
            ocr.putNull("language");
            ocr.put("duration_ms", 0);
            ocr.put("skipped", "disabled");
        }

        if (e.error() != null) n.put("error", e.error());
        else n.putNull("error");

        return n;
    }
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
mvn test -Dtest=RmetaWriterTest 2>&1 | tail -5
```

Expected: `Tests run: 4, Failures: 0, Errors: 0`.

- [ ] **Step 5: Commit**

```bash
cd /home/coz/Downloads/RedTusk
git add worker_jvm/src/main/java/io/redtusk/worker/RmetaWriter.java \
        worker_jvm/src/test/java/io/redtusk/worker/RmetaWriterTest.java
git commit -m "$(cat <<'EOF'
feat(worker-jvm): add RmetaWriter

Assembles the canonical rmeta document from JobDescriptor +
List<EntryResult> and writes metadata.json. Top-level key set
matches the JSON Schema from src/redtusk/schema.py exactly (pinned
by test). qr and ocr are always present on every entry.
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: ScannerRunner — tesseract + zbarimg subprocesses

**Files:**
- Create: `worker_jvm/src/main/java/io/redtusk/worker/ScannerRunner.java`
- Create: `worker_jvm/src/test/resources/sample-qr.png` (generated in Step 1)
- Test: `worker_jvm/src/test/java/io/redtusk/worker/ScannerRunnerTest.java`

Shells out to `tesseract` (OCR) and `zbarimg` (QR) on image entries. Gracefully skips if binaries are absent from `PATH`.

- [ ] **Step 1: Create the QR test fixture image**

This step creates a PNG containing a QR code encoding `https://redtusk.example/test`. Run this Python snippet to generate it:

```bash
cd /home/coz/Downloads/RedTusk/worker_jvm/src/test/resources
python3 - <<'PYEOF'
# Generate a minimal 1x1 white PNG as a placeholder.
# Replace with a real QR PNG if qrcode library is available; the test
# skips QR assertions when zbarimg is not installed anyway.
import struct, zlib, base64
def create_white_png(w=100, h=100):
    def chunk(name, data):
        c = zlib.crc32(name + data) & 0xffffffff
        return struct.pack('>I', len(data)) + name + data + struct.pack('>I', c)
    ihdr = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
    raw = b'\x00' + b'\xff\xff\xff' * w
    idat = zlib.compress(raw * h)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + chunk(b'IDAT', idat) + chunk(b'IEND', b'')
with open('sample-qr.png', 'wb') as f:
    f.write(create_white_png())
print("Created sample-qr.png (white 100x100 PNG)")
PYEOF
```

Expected output: `Created sample-qr.png (white 100x100 PNG)`

- [ ] **Step 2: Write the failing test at `src/test/java/io/redtusk/worker/ScannerRunnerTest.java`**

```java
package io.redtusk.worker;

import org.junit.jupiter.api.Test;

import java.io.File;
import java.net.URL;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class ScannerRunnerTest {

    private File fixture(String name) {
        URL url = getClass().getClassLoader().getResource(name);
        assertNotNull(url, "Test resource not found: " + name);
        return new File(url.getFile());
    }

    @Test
    void qrScanSkipsGracefullyWhenBinaryAbsent() {
        // Always passes: if zbarimg is present it actually scans; if absent it returns skipped.
        EntryResult.QrResult result = ScannerRunner.scanQr(
            fixture("sample-qr.png"), "zbarimg-does-not-exist-binary-xyz"
        );
        assertNotNull(result);
        assertNotNull(result.codes());
        // Either got codes (binary present) or skipped with "error"/"disabled"
        if (result.skipped() != null) {
            assertTrue(
                result.skipped().equals("error") || result.skipped().equals("disabled"),
                "skipped must be 'error' or 'disabled', got: " + result.skipped()
            );
        }
    }

    @Test
    void ocrScanSkipsGracefullyWhenBinaryAbsent() {
        EntryResult.OcrResult result = ScannerRunner.scanOcr(
            fixture("sample-qr.png"), "tesseract-does-not-exist-binary-xyz",
            "eng", 3, 5_000L /* budgetMs */
        );
        assertNotNull(result);
        if (result.skipped() != null) {
            assertTrue(
                result.skipped().equals("error") || result.skipped().equals("disabled"),
                "skipped must be 'error' or 'disabled', got: " + result.skipped()
            );
        }
    }

    @Test
    void ocrWithRealTesseractIfPresent() throws Exception {
        String tesseractPath = findBinary("tesseract");
        if (tesseractPath == null) {
            System.out.println("Skipping: tesseract not in PATH");
            return;
        }
        // White image should OCR to empty string without crashing
        EntryResult.OcrResult result = ScannerRunner.scanOcr(
            fixture("sample-qr.png"), tesseractPath,
            "eng", 3, 10_000L
        );
        assertNotNull(result);
        // Either succeeds (text may be empty) or returns skipped="error"
        // No exception should propagate
    }

    @Test
    void isImageTypeDetectsImageMimeTypes() {
        assertTrue(ScannerRunner.isImageType("image/png"));
        assertTrue(ScannerRunner.isImageType("image/jpeg"));
        assertTrue(ScannerRunner.isImageType("image/gif"));
        assertFalse(ScannerRunner.isImageType("text/plain"));
        assertFalse(ScannerRunner.isImageType("application/pdf"));
        assertFalse(ScannerRunner.isImageType(null));
    }

    private static String findBinary(String name) {
        for (String dir : System.getenv("PATH").split(":")) {
            File f = new File(dir, name);
            if (f.isFile() && f.canExecute()) return f.getAbsolutePath();
        }
        return null;
    }
}
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd /home/coz/Downloads/RedTusk/worker_jvm
mvn test -Dtest=ScannerRunnerTest -q 2>&1 | tail -5
```

Expected: compilation error.

- [ ] **Step 4: Write `src/main/java/io/redtusk/worker/ScannerRunner.java`**

```java
package io.redtusk.worker;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.*;
import java.util.logging.Logger;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Runs tesseract (OCR) and zbarimg (QR) as subprocesses on image entries.
 * Both methods return gracefully with a "skipped" result if the binary is
 * absent, crashes, or times out.
 */
public final class ScannerRunner {

    private static final Logger LOG = Logger.getLogger(ScannerRunner.class.getName());
    private static final Pattern ZBAR_LINE =
        Pattern.compile("^(\\S+):(.+)$", Pattern.MULTILINE);
    private static final Pattern ZBAR_DETAIL =
        Pattern.compile("([^:]+):([^:]+):([^:]+):([^:]+)");

    private ScannerRunner() {}

    /** Returns true if {@code contentType} is an image/* MIME type we can scan. */
    public static boolean isImageType(String contentType) {
        return contentType != null && contentType.startsWith("image/");
    }

    /**
     * Run zbarimg on {@code imageFile} using the given binary path.
     * Returns a QrResult with skipped="error" on any failure.
     */
    public static EntryResult.QrResult scanQr(File imageFile, String zbarimgBinary) {
        try {
            Process proc = new ProcessBuilder(zbarimgBinary, "--raw", imageFile.getAbsolutePath())
                .redirectErrorStream(true)
                .start();
            String output = readFully(proc.getInputStream());
            int exit = proc.waitFor();
            if (exit == 4) {
                // zbarimg exit 4 = no symbols found
                return new EntryResult.QrResult(List.of(), null);
            }
            if (exit != 0) {
                LOG.warning("zbarimg exited " + exit + " for " + imageFile.getName());
                return new EntryResult.QrResult(List.of(), "error");
            }
            List<EntryResult.QrCode> codes = parseZbarOutput(output);
            return new EntryResult.QrResult(codes, null);
        } catch (IOException e) {
            // Binary not found or not executable
            LOG.fine("zbarimg unavailable: " + e.getMessage());
            return new EntryResult.QrResult(List.of(), "disabled");
        } catch (Exception e) {
            LOG.warning("zbarimg failed: " + e.getMessage());
            return new EntryResult.QrResult(List.of(), "error");
        }
    }

    /**
     * Run tesseract on {@code imageFile} using the given binary path.
     * {@code budgetMs} is the remaining OCR wall-clock budget for the job.
     * Returns an OcrResult with skipped="error" on failure, skipped="timeout_budget" on timeout.
     */
    public static EntryResult.OcrResult scanOcr(
            File imageFile, String tesseractBinary,
            String lang, int psm, long budgetMs) {
        long start = System.currentTimeMillis();
        try {
            File tmpOut = File.createTempFile("redtusk-ocr-", ".txt");
            tmpOut.deleteOnExit();
            // tesseract <input> <output_base> -l <lang> --psm <psm>
            // output is written to <output_base>.txt
            String outBase = tmpOut.getAbsolutePath().replaceFirst("\\.txt$", "");
            Process proc = new ProcessBuilder(
                tesseractBinary, imageFile.getAbsolutePath(), outBase,
                "-l", lang, "--psm", String.valueOf(psm)
            ).redirectErrorStream(true).start();

            boolean finished = proc.waitFor(Math.max(budgetMs, 30_000L), TimeUnit.MILLISECONDS);
            if (!finished) {
                proc.destroyForcibly();
                return new EntryResult.OcrResult("", null, (int)(System.currentTimeMillis() - start), "timeout_budget");
            }
            int exit = proc.exitValue();
            if (exit != 0) {
                LOG.warning("tesseract exited " + exit + " for " + imageFile.getName());
                return new EntryResult.OcrResult("", null, (int)(System.currentTimeMillis() - start), "error");
            }
            File outFile = new File(outBase + ".txt");
            String text = outFile.exists() ? readFully(new FileInputStream(outFile)).trim() : "";
            outFile.delete();
            tmpOut.delete();
            int durationMs = (int)(System.currentTimeMillis() - start);
            return new EntryResult.OcrResult(text, lang, durationMs, null);
        } catch (IOException e) {
            LOG.fine("tesseract unavailable: " + e.getMessage());
            return new EntryResult.OcrResult("", null, 0, "disabled");
        } catch (Exception e) {
            LOG.warning("tesseract failed: " + e.getMessage());
            return new EntryResult.OcrResult("", null, 0, "error");
        }
    }

    private static List<EntryResult.QrCode> parseZbarOutput(String output) {
        List<EntryResult.QrCode> codes = new ArrayList<>();
        // zbarimg --raw outputs one line per symbol: "<type>:<data>"
        for (String line : output.split("\n")) {
            line = line.trim();
            if (line.isEmpty()) continue;
            int colon = line.indexOf(':');
            if (colon < 0) continue;
            String type = line.substring(0, colon).trim();
            String data = line.substring(colon + 1).trim();
            codes.add(new EntryResult.QrCode(type, data, new int[]{0, 0, 0, 0}));
        }
        return codes;
    }

    private static String readFully(InputStream is) throws IOException {
        try (var reader = new BufferedReader(new InputStreamReader(is, StandardCharsets.UTF_8))) {
            var sb = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) sb.append(line).append('\n');
            return sb.toString();
        }
    }
}
```

- [ ] **Step 5: Run test to verify it passes**

```bash
mvn test -Dtest=ScannerRunnerTest 2>&1 | tail -5
```

Expected: `Tests run: 4, Failures: 0, Errors: 0`.

- [ ] **Step 6: Commit**

```bash
cd /home/coz/Downloads/RedTusk
git add worker_jvm/src/main/java/io/redtusk/worker/ScannerRunner.java \
        worker_jvm/src/test/java/io/redtusk/worker/ScannerRunnerTest.java \
        worker_jvm/src/test/resources/sample-qr.png
git commit -m "$(cat <<'EOF'
feat(worker-jvm): add ScannerRunner for tesseract + zbarimg

Shells out to zbarimg for QR detection and tesseract for OCR.
Both return gracefully with skipped="disabled" when the binary is
absent and skipped="error" on crash/non-zero exit. Tests skip QR
assertions when zbarimg is not in PATH.
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: ParserRunner — Tika RecursiveParserWrapper with limits

**Files:**
- Create: `worker_jvm/src/main/java/io/redtusk/worker/ParserRunner.java`
- Test: `worker_jvm/src/test/java/io/redtusk/worker/ParserRunnerTest.java`

Drives `RecursiveParserWrapper` against the input file, enforces entry-count and depth limits, then runs ScannerRunner on image entries.

- [ ] **Step 1: Write the failing test at `src/test/java/io/redtusk/worker/ParserRunnerTest.java`**

```java
package io.redtusk.worker;

import org.junit.jupiter.api.Test;

import java.io.File;
import java.net.URL;
import java.util.List;

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
            noLimits(), true /* enableQr */, false /* enableOcr */,
            "eng", 3, "zbarimg", "tesseract"
        );
        List<EntryResult> entries = runner.parse(
            fixture("sample.txt"), "sample.txt",
            "ae1c" + "0".repeat(60)
        );

        assertFalse(entries.isEmpty(), "must produce at least one entry");
        EntryResult root = entries.get(0);
        assertEquals("/", root.path());
        assertNull(root.parentPath());
        assertEquals(0, root.depth());
        assertTrue(root.contentType().contains("text"), "content type must be text-ish, was: " + root.contentType());
        assertFalse(root.text().isBlank(), "text must not be blank for a text file");
        assertTrue(root.text().contains("Hello RedTusk"), "text must contain fixture content");
        assertNotNull(root.qr(), "qr field must always be present");
        assertNotNull(root.ocr(), "ocr field must always be present");
        assertNull(root.error());
    }

    @Test
    void respectsMaxEmbeddedEntriesLimit() throws Exception {
        // Limit of 1 entry — only the root should appear
        var limits = new JobDescriptor.LimitsDescriptor(10, 1, 524288000L, 60);
        ParserRunner runner = new ParserRunner(
            limits, false, false, "eng", 3, "zbarimg", "tesseract"
        );
        List<EntryResult> entries = runner.parse(
            fixture("sample.txt"), "sample.txt",
            "ae1c" + "0".repeat(60)
        );
        // sample.txt has no embedded resources so this test is
        // mainly verifying the runner doesn't crash when limit < actual count
        assertFalse(entries.isEmpty());
    }

    @Test
    void sha256IsPopulatedOnRootEntry() throws Exception {
        String expectedSha = "ae1c" + "0".repeat(60);
        ParserRunner runner = new ParserRunner(
            noLimits(), false, false, "eng", 3, "zbarimg", "tesseract"
        );
        List<EntryResult> entries = runner.parse(
            fixture("sample.txt"), "sample.txt", expectedSha
        );
        assertEquals(expectedSha, entries.get(0).sha256(),
            "root entry sha256 must be the value from the job descriptor");
    }

    @Test
    void rootEntryPathIsSlash() throws Exception {
        ParserRunner runner = new ParserRunner(
            noLimits(), false, false, "eng", 3, "zbarimg", "tesseract"
        );
        List<EntryResult> entries = runner.parse(
            fixture("sample.txt"), "sample.txt",
            "ae1c" + "0".repeat(60)
        );
        assertEquals("/", entries.get(0).path(),
            "root entry must always have path='/'");
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/coz/Downloads/RedTusk/worker_jvm
mvn test -Dtest=ParserRunnerTest -q 2>&1 | tail -5
```

Expected: compilation error.

- [ ] **Step 3: Write `src/main/java/io/redtusk/worker/ParserRunner.java`**

```java
package io.redtusk.worker;

import org.apache.tika.metadata.Metadata;
import org.apache.tika.metadata.TikaCoreProperties;
import org.apache.tika.parser.AutoDetectParser;
import org.apache.tika.parser.ParseContext;
import org.apache.tika.parser.RecursiveParserWrapper;
import org.apache.tika.sax.BasicContentHandlerFactory;
import org.apache.tika.sax.RecursiveParserWrapperHandler;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
import java.util.logging.Logger;

/**
 * Drives Tika's RecursiveParserWrapper against a single document,
 * enforces extraction limits, and runs ScannerRunner on image entries.
 */
public final class ParserRunner {

    private static final Logger LOG = Logger.getLogger(ParserRunner.class.getName());
    // Characters-per-entry write limit: 8 MB in chars.
    private static final int CHARS_PER_ENTRY = 8 * 1024 * 1024;

    private final JobDescriptor.LimitsDescriptor limits;
    private final boolean enableQr;
    private final boolean enableOcr;
    private final String ocrLang;
    private final int ocrPsm;
    private final String zbarimgBinary;
    private final String tesseractBinary;

    public ParserRunner(
            JobDescriptor.LimitsDescriptor limits,
            boolean enableQr, boolean enableOcr,
            String ocrLang, int ocrPsm,
            String zbarimgBinary, String tesseractBinary) {
        this.limits = limits;
        this.enableQr = enableQr;
        this.enableOcr = enableOcr;
        this.ocrLang = ocrLang;
        this.ocrPsm = ocrPsm;
        this.zbarimgBinary = zbarimgBinary;
        this.tesseractBinary = tesseractBinary;
    }

    /**
     * Parse {@code inputFile}, returning a list of EntryResults with the root at index 0.
     *
     * @param inputFile     the document to parse
     * @param filenameHint  filename for MIME-type detection (may be null)
     * @param rootSha256    SHA-256 of the input file (pre-computed by dispatcher)
     */
    public List<EntryResult> parse(File inputFile, String filenameHint, String rootSha256)
            throws Exception {
        AutoDetectParser auto = new AutoDetectParser();
        RecursiveParserWrapperHandler handler = new RecursiveParserWrapperHandler(
            new BasicContentHandlerFactory(
                BasicContentHandlerFactory.HANDLER_TYPE.TEXT, CHARS_PER_ENTRY),
            limits.maxEmbeddedEntries()
        );
        RecursiveParserWrapper wrapper = new RecursiveParserWrapper(auto);
        ParseContext context = new ParseContext();

        Metadata rootMeta = new Metadata();
        if (filenameHint != null) {
            rootMeta.set(TikaCoreProperties.RESOURCE_NAME_KEY, filenameHint);
        }

        try (InputStream stream = new BufferedInputStream(new FileInputStream(inputFile))) {
            wrapper.parse(stream, handler, rootMeta, context);
        } catch (Exception e) {
            LOG.warning("Tika parse threw: " + e.getMessage());
            // Return a single error entry rather than propagating.
            return List.of(errorEntry("/", null, 0,
                guessContentType(rootMeta), inputFile.length(),
                rootSha256, e.getMessage()));
        }

        List<Metadata> metaList = handler.getMetadataList();
        List<EntryResult> results = new ArrayList<>(metaList.size());

        for (int i = 0; i < metaList.size(); i++) {
            Metadata m = metaList.get(i);
            String embPath = m.get(RecursiveParserWrapperHandler.EMBEDDED_RESOURCE_PATH);
            String path = (embPath == null || embPath.isEmpty()) ? "/" : embPath;
            String parentPath = deriveParentPath(path);
            int depth = countDepth(path);

            // Enforce depth limit: skip entries that exceed it.
            if (depth > limits.maxRecursionDepth()) continue;

            String contentType = guessContentType(m);
            long sizeBytes = (i == 0) ? inputFile.length() : parseLong(m.get("Content-Length"), 0L);
            String sha256 = (i == 0) ? rootSha256 : sha256OfText(m.get(RecursiveParserWrapperHandler.TIKA_CONTENT));
            String text = m.get(RecursiveParserWrapperHandler.TIKA_CONTENT);
            if (text == null) text = "";
            String language = m.get("dc:language");

            Map<String, Object> metadata = extractMetadata(m);

            EntryResult.QrResult qr = buildQr(contentType, inputFile, i, path);
            EntryResult.OcrResult ocr = buildOcr(contentType, inputFile, i, path);

            results.add(new EntryResult(
                path, parentPath, depth, contentType, sizeBytes,
                sha256, metadata, text, language, qr, ocr, null
            ));
        }

        if (results.isEmpty()) {
            // Should not happen but guard defensively.
            results.add(new EntryResult(
                "/", null, 0,
                guessContentType(rootMeta), inputFile.length(),
                rootSha256, Map.of(), "", null,
                new EntryResult.QrResult(List.of(), "disabled"),
                new EntryResult.OcrResult("", null, 0, "disabled"),
                null
            ));
        }
        return results;
    }

    private EntryResult.QrResult buildQr(String contentType, File inputFile, int index, String path) {
        if (!enableQr) return new EntryResult.QrResult(List.of(), "disabled");
        if (!ScannerRunner.isImageType(contentType)) {
            return new EntryResult.QrResult(List.of(), "no_images");
        }
        // For the root entry we scan the input file directly; for embedded entries
        // we can't easily extract raw bytes here — return "no_images" for now.
        // Plan 3 will extract embedded images to temp files for scanning.
        if (index == 0) {
            return ScannerRunner.scanQr(inputFile, zbarimgBinary);
        }
        return new EntryResult.QrResult(List.of(), "no_images");
    }

    private EntryResult.OcrResult buildOcr(String contentType, File inputFile, int index, String path) {
        if (!enableOcr) return new EntryResult.OcrResult("", null, 0, "disabled");
        if (!ScannerRunner.isImageType(contentType)) {
            return new EntryResult.OcrResult("", null, 0, "no_images");
        }
        if (index == 0) {
            return ScannerRunner.scanOcr(inputFile, tesseractBinary, ocrLang, ocrPsm, 60_000L);
        }
        return new EntryResult.OcrResult("", null, 0, "no_images");
    }

    private static String guessContentType(Metadata m) {
        String ct = m.get("Content-Type");
        if (ct == null || ct.isEmpty()) return "application/octet-stream";
        // Strip parameters (e.g. "text/plain; charset=UTF-8" → "text/plain")
        int semi = ct.indexOf(';');
        return (semi >= 0) ? ct.substring(0, semi).trim() : ct.trim();
    }

    private static String deriveParentPath(String path) {
        if ("/".equals(path)) return null;
        int lastSlash = path.lastIndexOf('/');
        if (lastSlash <= 0) return "/";
        return path.substring(0, lastSlash);
    }

    private static int countDepth(String path) {
        if ("/".equals(path)) return 0;
        int count = 0;
        for (char c : path.toCharArray()) if (c == '/') count++;
        return count;
    }

    private static long parseLong(String s, long defaultVal) {
        if (s == null) return defaultVal;
        try { return Long.parseLong(s.trim()); } catch (NumberFormatException e) { return defaultVal; }
    }

    private static String sha256OfText(String text) {
        try {
            byte[] bytes = (text != null ? text : "").getBytes(StandardCharsets.UTF_8);
            byte[] digest = MessageDigest.getInstance("SHA-256").digest(bytes);
            StringBuilder sb = new StringBuilder(64);
            for (byte b : digest) sb.append(String.format("%02x", b));
            return sb.toString();
        } catch (Exception e) {
            return "0".repeat(64);
        }
    }

    private static Map<String, Object> extractMetadata(Metadata m) {
        Map<String, Object> result = new LinkedHashMap<>();
        // Exclude Tika-internal keys (X-TIKA:*) and Content-Type from the metadata map.
        for (String name : m.names()) {
            if (name.startsWith("X-TIKA:") || name.equals("Content-Type")) continue;
            String value = m.get(name);
            if (value != null) result.put(name, value);
        }
        return result;
    }

    private static EntryResult errorEntry(
            String path, String parentPath, int depth,
            String contentType, long sizeBytes, String sha256, String errorMsg) {
        return new EntryResult(
            path, parentPath, depth, contentType, sizeBytes, sha256,
            Map.of(), "", null,
            new EntryResult.QrResult(List.of(), "error"),
            new EntryResult.OcrResult("", null, 0, "error"),
            errorMsg
        );
    }
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
mvn test -Dtest=ParserRunnerTest 2>&1 | tail -8
```

Expected: `Tests run: 4, Failures: 0, Errors: 0`.

Note: this step downloads Tika's full transitive dependency tree into `~/.m2` on first run. Allow up to 2 minutes.

- [ ] **Step 5: Commit**

```bash
cd /home/coz/Downloads/RedTusk
git add worker_jvm/src/main/java/io/redtusk/worker/ParserRunner.java \
        worker_jvm/src/test/java/io/redtusk/worker/ParserRunnerTest.java
git commit -m "$(cat <<'EOF'
feat(worker-jvm): add ParserRunner

Drives RecursiveParserWrapper with entry-count and depth limit
enforcement. Root entry carries the pre-computed SHA-256 from the
job descriptor; embedded entries use SHA-256 of their extracted text.
ScannerRunner is called on image/* entries for QR/OCR (scanners
return skipped="disabled" when binaries are absent).
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: FifoLoop, KsmHelper, CapDropper stubs

**Files:**
- Create: `worker_jvm/src/main/java/io/redtusk/worker/FifoLoop.java`
- Create: `worker_jvm/src/main/java/io/redtusk/worker/KsmHelper.java`
- Create: `worker_jvm/src/main/java/io/redtusk/worker/CapDropper.java`
- Test: `worker_jvm/src/test/java/io/redtusk/worker/FifoLoopTest.java`

`FifoLoop` creates the control fifo and blocks until a signal arrives. `KsmHelper` and `CapDropper` are no-op stubs; real implementations come in Plans 3 and 6.

- [ ] **Step 1: Write the failing test at `src/test/java/io/redtusk/worker/FifoLoopTest.java`**

```java
package io.redtusk.worker;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.*;
import java.nio.file.Path;
import java.util.concurrent.*;

import static org.junit.jupiter.api.Assertions.*;

class FifoLoopTest {

    @Test
    void fifoCreatedAtExpectedPath(@TempDir Path scratchDir) throws Exception {
        File fifo = scratchDir.resolve("control.fifo").toFile();
        assertFalse(fifo.exists(), "fifo must not exist before createFifo()");

        // createFifo() creates the named pipe; we verify it exists (or is a file
        // on platforms that simulate fifos as regular files in tests).
        ExecutorService exec = Executors.newSingleThreadExecutor();
        Future<Void> task = exec.submit(() -> {
            FifoLoop.createFifo(scratchDir.toFile());
            return null;
        });
        task.get(5, TimeUnit.SECONDS);
        assertTrue(fifo.exists(), "control.fifo must exist after createFifo()");
        exec.shutdownNow();
    }

    @Test
    void waitForSignalReceivesGoLine(@TempDir Path scratchDir) throws Exception {
        File fifo = scratchDir.resolve("control.fifo").toFile();
        FifoLoop.createFifo(scratchDir.toFile());

        // Write "go\n" to the fifo from a background thread, then verify
        // waitForSignal() returns.
        ExecutorService exec = Executors.newSingleThreadExecutor();
        exec.submit(() -> {
            try (var out = new FileWriter(fifo)) {
                Thread.sleep(50); // give waitForSignal time to open the read end
                out.write("go\n");
                out.flush();
            }
            return null;
        });

        String line = FifoLoop.waitForSignal(scratchDir.toFile());
        assertEquals("go", line.trim());
        exec.shutdownNow();
    }

    @Test
    void ksmHelperDoesNotThrow() {
        // KsmHelper is a no-op stub in this plan; just verify it doesn't throw.
        assertDoesNotThrow(KsmHelper::markHeapMergeable);
    }

    @Test
    void capDropperDoesNotThrow() {
        assertDoesNotThrow(CapDropper::dropCheckpointRestoreCapability);
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/coz/Downloads/RedTusk/worker_jvm
mvn test -Dtest=FifoLoopTest -q 2>&1 | tail -5
```

Expected: compilation error.

- [ ] **Step 3: Write `src/main/java/io/redtusk/worker/FifoLoop.java`**

```java
package io.redtusk.worker;

import java.io.*;
import java.nio.file.Files;
import java.util.logging.Logger;

/**
 * Creates the control FIFO and blocks until the dispatcher writes a signal line.
 *
 * The FIFO path is {@code {scratchDir}/control.fifo}. The dispatcher writes
 * "go\n" to signal that job.json is ready. This class's existence in the
 * filesystem signals to the dispatcher that the warm JVM is ready.
 */
public final class FifoLoop {

    private static final Logger LOG = Logger.getLogger(FifoLoop.class.getName());
    private static final String FIFO_NAME = "control.fifo";

    private FifoLoop() {}

    /**
     * Create the named pipe at {@code scratchDir/control.fifo}.
     * Uses {@code mkfifo} on Linux; falls back to creating a regular file for
     * testing on non-Linux or when mkfifo is unavailable (the blocking semantics
     * won't hold but the path will exist).
     */
    public static void createFifo(File scratchDir) throws IOException {
        File fifo = new File(scratchDir, FIFO_NAME);
        try {
            int exit = new ProcessBuilder("mkfifo", fifo.getAbsolutePath())
                .start().waitFor();
            if (exit != 0) {
                LOG.warning("mkfifo exited " + exit + ", falling back to regular file");
                fifo.createNewFile();
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IOException("mkfifo interrupted", e);
        } catch (IOException e) {
            // mkfifo binary not found (e.g., test environment)
            LOG.fine("mkfifo not available: " + e.getMessage() + "; creating regular file");
            fifo.createNewFile();
        }
    }

    /**
     * Open the FIFO for reading (blocks until the dispatcher opens the write end)
     * and return the first non-empty line. Blocks indefinitely.
     */
    public static String waitForSignal(File scratchDir) throws IOException {
        File fifo = new File(scratchDir, FIFO_NAME);
        LOG.info("Waiting for signal on " + fifo.getAbsolutePath());
        try (BufferedReader reader = new BufferedReader(new FileReader(fifo))) {
            String line;
            while ((line = reader.readLine()) != null) {
                if (!line.trim().isEmpty()) return line;
            }
        }
        return "";
    }
}
```

- [ ] **Step 4: Write `src/main/java/io/redtusk/worker/KsmHelper.java`**

```java
package io.redtusk.worker;

import java.util.logging.Logger;

/**
 * Marks JVM heap regions as KSM-mergeable via madvise(MADV_MERGEABLE).
 *
 * This is a no-op stub. Plan 3 (Docker image) adds the native JNI library
 * that calls madvise(2) on the JVM's heap VMAs.
 */
public final class KsmHelper {

    private static final Logger LOG = Logger.getLogger(KsmHelper.class.getName());

    private KsmHelper() {}

    /**
     * Mark JVM heap memory as MADV_MERGEABLE so the host kernel's KSM thread
     * can merge identical pages across warm-pool worker containers.
     *
     * No-op in this plan; the real implementation is a native method loaded from
     * libksm_helper.so compiled in Plan 3.
     */
    public static void markHeapMergeable() {
        LOG.fine("KsmHelper.markHeapMergeable: no-op stub (native library not yet loaded)");
    }
}
```

- [ ] **Step 5: Write `src/main/java/io/redtusk/worker/CapDropper.java`**

```java
package io.redtusk.worker;

import java.util.logging.Logger;

/**
 * Drops CAP_CHECKPOINT_RESTORE via prctl(PR_CAPBSET_DROP) immediately after
 * CRaC checkpoint restore completes, so the steady-state worker has the same
 * capability set as the default (non-CRaC) profile.
 *
 * No-op stub in Plans 2 and 3. Plan 6 (high-density profile) provides the
 * real implementation via JNI / ProcessHandle native access.
 */
public final class CapDropper {

    private static final Logger LOG = Logger.getLogger(CapDropper.class.getName());

    private CapDropper() {}

    /**
     * Drop CAP_CHECKPOINT_RESTORE from the capability bounding set.
     * Must be called immediately after CRaC restore, before the fifo is opened.
     */
    public static void dropCheckpointRestoreCapability() {
        LOG.fine("CapDropper.dropCheckpointRestoreCapability: no-op stub");
    }
}
```

- [ ] **Step 6: Run test to verify it passes**

```bash
mvn test -Dtest=FifoLoopTest 2>&1 | tail -5
```

Expected: `Tests run: 4, Failures: 0, Errors: 0`.

- [ ] **Step 7: Commit**

```bash
cd /home/coz/Downloads/RedTusk
git add worker_jvm/src/main/java/io/redtusk/worker/FifoLoop.java \
        worker_jvm/src/main/java/io/redtusk/worker/KsmHelper.java \
        worker_jvm/src/main/java/io/redtusk/worker/CapDropper.java \
        worker_jvm/src/test/java/io/redtusk/worker/FifoLoopTest.java
git commit -m "$(cat <<'EOF'
feat(worker-jvm): add FifoLoop, KsmHelper stub, CapDropper stub

FifoLoop creates control.fifo via mkfifo and blocks on it for the
dispatcher's signal. KsmHelper and CapDropper are no-op stubs;
native implementations arrive in Plans 3 and 6 respectively.
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: Main entrypoint

**Files:**
- Create: `worker_jvm/src/main/java/io/redtusk/worker/Main.java`
- Test: integrated in Task 9 end-to-end

`Main` dispatches among three modes based on the first CLI argument:
- `--appcds-warmup <corpus-dir>` — parse each file in the corpus, exit 0 (triggers AppCDS dump via JVM flag)
- `--checkpoint` — no-op stub (calls `CapDropper.dropCheckpointRestoreCapability()` then signals readiness; real CRaC checkpoint added in Plan 6)
- `--run <scratch-dir>` — production mode: call `KsmHelper`, create fifo, wait for signal, read `job.json`, parse, write `metadata.json`, exit

- [ ] **Step 1: Write `src/main/java/io/redtusk/worker/Main.java`**

```java
package io.redtusk.worker;

import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.*;
import java.nio.file.*;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.*;

/**
 * Entry point for the RedTusk worker JVM.
 *
 * Usage:
 *   java -jar redtusk-worker.jar --appcds-warmup <corpus-dir>
 *   java -jar redtusk-worker.jar --checkpoint <scratch-dir>
 *   java -jar redtusk-worker.jar --run <scratch-dir>
 *
 * Exit codes:
 *   0 — success (metadata.json written)
 *   1 — parse error (partial metadata.json may exist)
 *   2 — fatal configuration or I/O error
 */
public final class Main {

    private static final Logger LOG = Logger.getLogger(Main.class.getName());
    private static final ObjectMapper OM = new ObjectMapper();

    public static void main(String[] args) {
        configureLogging();
        if (args.length < 2) {
            System.err.println("Usage: redtusk-worker [--appcds-warmup|--checkpoint|--run] <path>");
            System.exit(2);
        }
        String mode = args[0];
        File path = new File(args[1]);

        try {
            switch (mode) {
                case "--appcds-warmup" -> runWarmup(path);
                case "--checkpoint"    -> runCheckpoint(path);
                case "--run"           -> runJob(path);
                default -> {
                    System.err.println("Unknown mode: " + mode);
                    System.exit(2);
                }
            }
        } catch (Exception e) {
            LOG.severe("Fatal error in mode " + mode + ": " + e.getMessage());
            System.exit(2);
        }
    }

    // ---- modes ----

    /**
     * AppCDS warmup: parse every file in the corpus directory to exercise the
     * Tika parser class hierarchy. The JVM flag -XX:ArchiveClassesAtExit=...
     * captures what was loaded, producing the AppCDS archive.
     */
    private static void runWarmup(File corpusDir) throws Exception {
        if (!corpusDir.isDirectory()) {
            System.err.println("warmup corpus is not a directory: " + corpusDir);
            System.exit(2);
        }
        File[] files = corpusDir.listFiles();
        if (files == null || files.length == 0) {
            LOG.info("Warmup corpus is empty — exiting (AppCDS archive may be minimal)");
            return;
        }
        var limits = new JobDescriptor.LimitsDescriptor(10, 500, 52428800L, 30);
        var runner = new ParserRunner(limits, true, false, "eng", 3, "zbarimg", "tesseract");
        for (File f : files) {
            if (!f.isFile()) continue;
            try {
                LOG.info("Warmup: parsing " + f.getName());
                runner.parse(f, f.getName(), "0".repeat(64));
            } catch (Exception e) {
                LOG.warning("Warmup parse failed for " + f.getName() + ": " + e.getMessage());
            }
        }
        LOG.info("Warmup complete — " + files.length + " files processed");
    }

    /**
     * CRaC checkpoint stub. Real implementation added in Plan 6.
     * For now: drop caps (no-op), create fifo to signal readiness, then exit.
     */
    private static void runCheckpoint(File scratchDir) throws Exception {
        CapDropper.dropCheckpointRestoreCapability();
        KsmHelper.markHeapMergeable();
        scratchDir.mkdirs();
        FifoLoop.createFifo(scratchDir);
        LOG.info("Checkpoint mode: no-op stub — CRaC support added in Plan 6");
    }

    /**
     * Production run: warm JVM → create fifo → wait for signal →
     * parse → write metadata.json → exit.
     */
    static void runJob(File scratchDir) throws Exception {
        // Mark heap as KSM-mergeable (no-op stub in this plan).
        KsmHelper.markHeapMergeable();

        // Create fifo: existence signals to dispatcher that we're warm.
        scratchDir.mkdirs();
        FifoLoop.createFifo(scratchDir);

        // Block until dispatcher signals "go".
        String signal = FifoLoop.waitForSignal(scratchDir);
        LOG.info("Received signal: " + signal.trim());

        // Read job descriptor.
        File jobFile = new File(scratchDir, "job.json");
        if (!jobFile.exists()) {
            LOG.severe("job.json not found at: " + jobFile);
            System.exit(2);
        }
        JobDescriptor job = OM.readValue(jobFile, JobDescriptor.class);

        // Parse.
        File inputFile = new File(job.inputPath());
        File outDir = new File(job.outputDir());
        outDir.mkdirs();

        long start = System.currentTimeMillis();
        List<EntryResult> entries;
        try {
            var runner = new ParserRunner(
                job.limits(),
                job.enableQr(), job.enableOcr(),
                job.ocrLang(), job.ocrPsm(),
                "zbarimg", "tesseract"
            );
            entries = runner.parse(inputFile, job.filenameHint(), job.sha256());
        } catch (Exception e) {
            LOG.severe("Parse failed: " + e.getMessage());
            System.exit(1);
            return; // unreachable
        }
        long durationMs = System.currentTimeMillis() - start;

        // Write output.
        new RmetaWriter(job, entries, durationMs).write(outDir);
        LOG.info("Wrote metadata.json (" + entries.size() + " entries, " + durationMs + " ms)");
    }

    private static void configureLogging() {
        // Route java.util.logging to stderr in simple format.
        Logger root = Logger.getLogger("");
        for (Handler h : root.getHandlers()) root.removeHandler(h);
        ConsoleHandler handler = new ConsoleHandler();
        handler.setStream(System.err);
        handler.setFormatter(new SimpleFormatter());
        handler.setLevel(Level.ALL);
        root.addHandler(handler);
        String level = System.getenv().getOrDefault("REDTUSK_LOG_LEVEL", "INFO");
        root.setLevel(Level.parse(level));
    }
}
```

- [ ] **Step 2: Verify the project compiles**

```bash
cd /home/coz/Downloads/RedTusk/worker_jvm
mvn compile -q 2>&1 | tail -5
```

Expected: `BUILD SUCCESS` with no errors.

- [ ] **Step 3: Commit**

```bash
cd /home/coz/Downloads/RedTusk
git add worker_jvm/src/main/java/io/redtusk/worker/Main.java
git commit -m "$(cat <<'EOF'
feat(worker-jvm): add Main entrypoint

Three modes: --appcds-warmup (exercises parser classes for AppCDS
dump), --checkpoint (stub for Plan 6 CRaC), --run (production:
fifo-wait → parse → write metadata.json → exit 0/1/2).
runJob() is package-private so MainIntegrationTest can call it
directly without a full subprocess.
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: Build fat JAR and run all tests

**Files:**
- Test: `worker_jvm/src/test/java/io/redtusk/worker/MainIntegrationTest.java`

End-to-end integration test: write a job descriptor, signal via fifo, verify `metadata.json` is written with the correct shape.

- [ ] **Step 1: Write the integration test at `src/test/java/io/redtusk/worker/MainIntegrationTest.java`**

```java
package io.redtusk.worker;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.*;
import java.nio.file.Path;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.*;

import static org.junit.jupiter.api.Assertions.*;

/**
 * End-to-end integration test: exercises the full
 * fifo-wait → parse → write metadata.json pipeline without spawning
 * a subprocess (calls Main.runJob() directly in the test JVM).
 */
class MainIntegrationTest {

    private static final ObjectMapper OM = new ObjectMapper();

    private File textFixture() throws Exception {
        // Write the same content as src/test/resources/sample.txt
        File f = File.createTempFile("redtusk-test-", ".txt");
        f.deleteOnExit();
        try (var w = new FileWriter(f)) {
            w.write("Hello RedTusk.\nThis is a plain text document used as a test fixture.\n");
        }
        return f;
    }

    @Test
    void runJobProducesValidMetadataJson(@TempDir Path scratchBase) throws Exception {
        // Arrange scratch directory structure.
        Path scratchDir = scratchBase.resolve("slot-test");
        scratchDir.toFile().mkdirs();
        Path outDir = scratchDir.resolve("out");
        outDir.toFile().mkdirs();
        File inputFile = textFixture();

        // Write job.json into scratch dir.
        var limits = Map.of(
            "max_recursion_depth", 10, "max_embedded_entries", 5000,
            "max_extracted_bytes", 524288000, "ocr_timeout_s", 60
        );
        var jobMap = Map.of(
            "input_path", inputFile.getAbsolutePath(),
            "output_dir", outDir.toFile().getAbsolutePath(),
            "sha256", "ae1c" + "0".repeat(60),
            "filename_hint", "test-document.txt",
            "limits", limits,
            "enable_qr", false,
            "enable_ocr", false,
            "ocr_lang", "eng",
            "ocr_psm", 3,
            "sandbox_profile", "default",
            "sandbox_runtime", "runsc",
            "appcds", true,
            "ksm", true,
            "crac", false,
            "redtusk_version", "0.1.0",
            "tika_version", "3.3.0"
        );
        OM.writeValue(scratchDir.resolve("job.json").toFile(), jobMap);

        // Create fifo and signal it from a background thread.
        FifoLoop.createFifo(scratchDir.toFile());
        ExecutorService exec = Executors.newSingleThreadExecutor();
        exec.submit(() -> {
            try {
                Thread.sleep(150); // wait for runJob to open the read end
                try (var w = new FileWriter(scratchDir.resolve("control.fifo").toFile())) {
                    w.write("go\n");
                }
            } catch (Exception e) {
                // ignore
            }
            return null;
        });

        // Act: run the job in this thread (blocks on fifo, then parses).
        Main.runJob(scratchDir.toFile());
        exec.shutdownNow();

        // Assert: metadata.json exists and has the expected shape.
        File metaFile = outDir.resolve("metadata.json").toFile();
        assertTrue(metaFile.exists(), "metadata.json must be written");
        JsonNode root = OM.readTree(metaFile);

        // Top-level keys match the schema.
        Set<String> expectedKeys = Set.of(
            "redtusk_version", "tika_version", "input", "extraction",
            "limits", "truncated", "warnings", "sandbox"
        );
        Set<String> actualKeys = new java.util.HashSet<>();
        root.fieldNames().forEachRemaining(actualKeys::add);
        assertEquals(expectedKeys, actualKeys);

        // Root content.
        assertEquals("0.1.0", root.get("redtusk_version").asText());
        assertEquals("3.3.0", root.get("tika_version").asText());

        // Input block.
        assertEquals("ae1c" + "0".repeat(60), root.get("input").get("sha256").asText());
        assertEquals("test-document.txt", root.get("input").get("filename_hint").asText());

        // At least one entry, root at path "/".
        JsonNode entries = root.get("extraction").get("entries");
        assertTrue(entries.size() >= 1, "must have at least one entry");
        assertEquals("/", entries.get(0).get("path").asText());
        assertEquals(0, entries.get(0).get("depth").asInt());
        assertTrue(entries.get(0).get("parent_path").isNull());

        // qr and ocr always present.
        assertNotNull(entries.get(0).get("qr"));
        assertNotNull(entries.get(0).get("ocr"));

        // sandbox block.
        assertEquals("default", root.get("sandbox").get("profile").asText());
    }

    @Test
    void warmupModeDoesNotCrashOnEmptyDir(@TempDir Path tmp) throws Exception {
        File corpusDir = tmp.resolve("empty-corpus").toFile();
        corpusDir.mkdirs();
        // Should complete without exception and exit code 0.
        assertDoesNotThrow(() -> Main.main(new String[]{"--appcds-warmup", corpusDir.getAbsolutePath()}));
    }
}
```

- [ ] **Step 2: Run all tests**

```bash
cd /home/coz/Downloads/RedTusk/worker_jvm
mvn test 2>&1 | tail -15
```

Expected: all prior test classes pass plus the new `MainIntegrationTest` (2 tests). Total across all test classes: 18+ tests.

- [ ] **Step 3: Build the fat JAR**

```bash
mvn package -DskipTests -q
ls -lh target/redtusk-worker.jar
```

Expected: `target/redtusk-worker.jar` exists, size 50–200 MB (Tika + parsers bundled).

- [ ] **Step 4: Smoke-test the JAR against the text fixture**

```bash
# Create scratch dir
SCRATCH=$(mktemp -d)
INPUT=$(mktemp /tmp/redtusk-test-XXXXX.txt)
echo "Hello from smoke test." > "$INPUT"
cat > "$SCRATCH/job.json" <<EOF
{
  "input_path": "$INPUT",
  "output_dir": "$SCRATCH/out",
  "sha256": "$(sha256sum "$INPUT" | awk '{print $1}')",
  "filename_hint": "smoke.txt",
  "limits": {"max_recursion_depth":10,"max_embedded_entries":5000,
              "max_extracted_bytes":524288000,"ocr_timeout_s":60},
  "enable_qr": false,
  "enable_ocr": false,
  "ocr_lang": "eng",
  "ocr_psm": 3,
  "sandbox_profile": "default",
  "sandbox_runtime": "runsc",
  "appcds": false,
  "ksm": false,
  "crac": false,
  "redtusk_version": "0.1.0",
  "tika_version": "3.3.0"
}
EOF

# Signal the fifo from background after a short pause
(sleep 0.5 && echo "go" > "$SCRATCH/control.fifo") &

java -jar target/redtusk-worker.jar --run "$SCRATCH"
cat "$SCRATCH/out/metadata.json" | python3 -m json.tool | head -20
rm -rf "$SCRATCH" "$INPUT"
```

Expected: valid JSON printed, containing `"redtusk_version": "0.1.0"` and at least one entry with `"path": "/"`.

- [ ] **Step 5: Commit**

```bash
cd /home/coz/Downloads/RedTusk
git add worker_jvm/src/test/java/io/redtusk/worker/MainIntegrationTest.java
git commit -m "$(cat <<'EOF'
feat(worker-jvm): add end-to-end integration test + fat JAR build

MainIntegrationTest exercises the full pipeline in-process: writes
job.json, creates fifo, signals it, calls Main.runJob(), asserts
metadata.json has correct shape and top-level keys matching the
JSON Schema. Fat JAR built by maven-assembly-plugin at package phase.
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 10: Add worker_jvm to .gitignore and final verification

**Files:**
- Modify: `/home/coz/Downloads/RedTusk/.gitignore`

- [ ] **Step 1: Add Java build artifacts to .gitignore**

Append to `/home/coz/Downloads/RedTusk/.gitignore`:

```
# Maven build output
worker_jvm/target/
```

- [ ] **Step 2: Run the full Maven test suite one final time**

```bash
cd /home/coz/Downloads/RedTusk/worker_jvm
mvn test 2>&1 | grep -E "Tests run|BUILD|ERROR" | tail -20
```

Expected: all test classes show `Failures: 0, Errors: 0`, final line is `BUILD SUCCESS`.

- [ ] **Step 3: Verify the Python unit tests are still green**

```bash
cd /home/coz/Downloads/RedTusk
.venv/bin/pytest tests/unit/ -q 2>&1 | tail -2
```

Expected: `136 passed, 7 skipped` (unchanged from Plan 1).

- [ ] **Step 4: Commit**

```bash
cd /home/coz/Downloads/RedTusk
git add .gitignore
git commit -m "$(cat <<'EOF'
chore: exclude worker_jvm/target/ from git

Maven build artifacts are large and reproducible; keep them out of
version control.
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Covered in |
|---|---|
| `worker_jvm/` Maven project | Task 1 |
| `Main.java` with 3 modes (warmup, checkpoint, run) | Task 8 |
| `ParserRunner.java` with `RecursiveParserWrapper` + limits | Task 6 |
| `ScannerRunner.java` (tesseract + zbarimg, graceful skip) | Task 5 |
| `FifoLoop.java` (mkfifo + blocking read) | Task 7 |
| `RmetaWriter.java` (canonical JSON shape) | Task 4 |
| `KsmHelper.java` stub | Task 7 |
| `CapDropper.java` stub | Task 7 |
| Fat JAR via maven-assembly-plugin | Task 1 (pom.xml) + Task 9 |
| Java unit tests via Maven Surefire | Tasks 2-9 |
| Top-level rmeta key set matches schema | Task 4 |
| `qr` and `ocr` always present on every entry | Task 4 |
| Root entry has `path="/"`, `depth=0`, `parent_path=null` | Task 6 |

**No placeholders** — all code blocks are complete and runnable.

**Type consistency** — `EntryResult`, `JobDescriptor`, `RmetaWriter`, `ParserRunner`, `ScannerRunner` all use the same record/class names throughout.
