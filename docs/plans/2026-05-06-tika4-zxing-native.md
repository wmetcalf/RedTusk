# Plan 8 — Tika 4.0 fork + native ZXing-CPP + Tika-native OCR

**Date:** 2026-05-06
**Status:** In progress
**Depends on:** Plans 1–7 (all merged)

## Goal

Replace our hand-rolled subprocess shims with the features built into the
wmetcalf/tika `4.0-upstream-office-links` fork:

| Feature | Before | After |
|---|---|---|
| QR / barcode | `zbarimg` via `ScannerRunner` | `ZXingCPPConfig` in ParseContext → `ZXingReader` subprocess |
| OCR | `tesseract` via `ScannerRunner` | `TesseractOCRConfig` in ParseContext (Tika already does this) |
| Entry byte hash | null | `DigesterFactory` in ParseContext → `X-TIKA:digest:SHA256` |
| Embedded limits | `RecursiveParserWrapperHandler(factory, maxEntries)` | `EmbeddedLimits` in ParseContext, no-arg handler ctor |
| Tika version | 3.3.0 upstream | 4.0.0-SNAPSHOT wmetcalf fork |

`ScannerRunner.java` is deleted entirely. The worker image gains two new build
stages: one for ZXing-CPP (produces `ZXingReader` binary) and one for the Tika
fork (produces `4.0.0-SNAPSHOT` JARs in a local Maven repo).

## File targets

```
deploy/docker/
  Dockerfile.default      # add zxing-cpp + tika-fork build stages
worker_jvm/
  pom.xml                 # tika 4.0.0-SNAPSHOT, tika-parser-image-module
  src/main/java/io/redtusk/worker/
    ScannerRunner.java     # DELETE
    ParserRunner.java      # rewrite: ZXingCPPConfig, TesseractOCRConfig, DigesterFactory, EmbeddedLimits
    EntryResult.java       # update QrCode: data+format+rawBytes+position (matches Tika barcode keys)
    RmetaWriter.java       # update: read sha256 from digest metadata, QrCode from new shape
    JobDescriptor.java     # remove zbarimgBinary/tesseractBinary; add zxingPath/tesseractPath
  src/test/java/...        # update tests for new APIs
src/redtusk/
  types.py                 # update QrCode: type→format, bbox→position, add raw_bytes
  schema.py                # update QR schema to match
tests/unit/
  test_types_values.py     # update QrCode fixture
```

## Tasks

### Task 1 — `Dockerfile.default`: add ZXing-CPP and Tika-fork build stages

```dockerfile
# ── Stage 0-a: Build ZXing-CPP (produces ZXingReader binary) ─────────────────
FROM ubuntu:jammy AS zxing-build

RUN apt-get update -qq && apt-get install -y --no-install-recommends \
        git cmake build-essential libzbar-dev \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 https://github.com/zxing-cpp/zxing-cpp.git /src/zxing-cpp
RUN cmake -S /src/zxing-cpp -B /build/zxing \
        -DCMAKE_BUILD_TYPE=Release \
        -DBUILD_READERS=ON \
        -DBUILD_WRITERS=OFF \
        -DBUILD_EXAMPLES=OFF \
        -DBUILD_PYTHON_MODULE=OFF \
    && cmake --build /build/zxing --target ZXingReader -j$(nproc)
# ZXingReader binary is at /build/zxing/ZXingReader

# ── Stage 0-b: Build Tika fork (produces 4.0.0-SNAPSHOT Maven JARs) ──────────
FROM eclipse-temurin:25-jdk-jammy AS tika-build

RUN apt-get update -qq && apt-get install -y --no-install-recommends \
        git maven \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 \
        --branch 4.0-upstream-office-links \
        https://github.com/wmetcalf/tika.git \
        /src/tika

# Build all modules except gRPC (requires protoc toolchain not needed here).
# -pl '!tika-grpc' matches the fork's own build.sh script.
RUN cd /src/tika && mvn install \
        -DskipTests \
        -pl '!tika-grpc' \
        -T 2C \
        -q \
        2>&1 | tail -5
# Resulting JARs are in /root/.m2/repository/org/apache/tika/

# ── Stage 1: Build worker JAR (uses the Tika fork from stage 0-b) ────────────
FROM eclipse-temurin:25-jdk-jammy AS build

RUN apt-get update -qq && apt-get install -y --no-install-recommends \
        maven gcc libc-dev \
    && rm -rf /var/lib/apt/lists/*

# Import the Tika 4.0.0-SNAPSHOT artifacts built in stage 0-b.
COPY --from=tika-build /root/.m2/repository/org/apache/tika \
                       /root/.m2/repository/org/apache/tika

WORKDIR /build
COPY worker_jvm/ ./worker_jvm/
RUN cd worker_jvm && mvn package -DskipTests -q

# JNI native helpers
RUN JDK_HOME="${JAVA_HOME:-$(dirname $(dirname $(readlink -f $(which java))))}" && \
    gcc -fPIC -O2 -Wall -Wextra -std=c11 -D_GNU_SOURCE \
        -I"${JDK_HOME}/include" -I"${JDK_HOME}/include/linux" \
        -shared -o worker_jvm/native/libksm_helper.so \
        worker_jvm/native/ksm_helper.c && \
    gcc -fPIC -O2 -Wall -Wextra -std=c11 -D_GNU_SOURCE \
        -I"${JDK_HOME}/include" -I"${JDK_HOME}/include/linux" \
        -shared -o worker_jvm/native/libcap_dropper.so \
        worker_jvm/native/cap_dropper.c
```

Subsequent stages (appcds-dump, runtime) are unchanged except:
- Install `tesseract-ocr tesseract-ocr-eng` (still needed for Tika's TesseractOCRParser)
- Remove `zbar-tools` (no longer needed)
- Add ZXingReader binary:
  ```dockerfile
  COPY --from=zxing-build /build/zxing/ZXingReader /usr/local/bin/ZXingReader
  ```

### Task 2 — `pom.xml`: Tika 4.0.0-SNAPSHOT + image module

```xml
<properties>
    <tika.version>4.0.0-SNAPSHOT</tika.version>
    ...
</properties>

<dependencies>
    <dependency>
        <groupId>org.apache.tika</groupId>
        <artifactId>tika-core</artifactId>
        <version>${tika.version}</version>
    </dependency>
    <dependency>
        <groupId>org.apache.tika</groupId>
        <artifactId>tika-parsers-standard-package</artifactId>
        <version>${tika.version}</version>
    </dependency>
    <!-- ZXingCPPConfig for barcode scanning -->
    <dependency>
        <groupId>org.apache.tika</groupId>
        <artifactId>tika-parser-image-module</artifactId>
        <version>${tika.version}</version>
    </dependency>
    <!-- rest unchanged: jackson-databind, org-crac, junit-jupiter -->
</dependencies>
```

### Task 3 — Delete `ScannerRunner.java`

Remove the file. Remove all references in `ParserRunner.java`.

### Task 4 — `JobDescriptor.java`: replace binary paths

Remove `zbarimgBinary` and `tesseractBinary` fields (no longer passed from dispatcher).
Add `zxingPath` and `tesseractPath` with sensible defaults baked into `ParserRunner`.

```java
@JsonIgnoreProperties(ignoreUnknown = true)
public record JobDescriptor(
    @JsonProperty("input_path")      String inputPath,
    @JsonProperty("output_dir")      String outputDir,
    @JsonProperty("sha256")          String sha256,
    @JsonProperty("filename_hint")   String filenameHint,
    @JsonProperty("limits")          LimitsDescriptor limits,
    @JsonProperty("enable_qr")       boolean enableQr,
    @JsonProperty("enable_ocr")      boolean enableOcr,
    @JsonProperty("ocr_lang")        String ocrLang,
    @JsonProperty("ocr_psm")         int ocrPsm,
    @JsonProperty("zxing_path")      String zxingPath,      // default "/usr/local/bin/ZXingReader"
    @JsonProperty("tesseract_path")  String tesseractPath,  // default "tesseract"
    @JsonProperty("sandbox_profile") String sandboxProfile,
    @JsonProperty("sandbox_runtime") String sandboxRuntime,
    @JsonProperty("appcds")          boolean appcds,
    @JsonProperty("ksm")             boolean ksm,
    @JsonProperty("crac")            boolean crac,
    @JsonProperty("redtusk_version") String redtuskVersion,
    @JsonProperty("tika_version")    String tikaVersion
) { ... }
```

### Task 5 — `EntryResult.java`: updated QrCode shape

```java
public record QrCode(
    String data,       // decoded text (barcode:value)
    String format,     // barcode format e.g. "QR_CODE", "EAN_13" (barcode:format)
    String rawBytes,   // base64 raw bytes (barcode:raw-bytes); nullable
    String position    // bounding box string (barcode:position); nullable
) {}
```

Remove the old `int[] bbox` field and `type` field.

### Task 6 — `ParserRunner.java`: full rewrite

```java
public ParseResult parse(File inputFile, String filenameHint, String rootSha256)
        throws Exception {

    AutoDetectParser auto = new AutoDetectParser();
    ParseContext context = new ParseContext();

    // 1. Embedded resource limits (Tika 4.x API)
    context.set(EmbeddedLimits.class, new EmbeddedLimits.Builder()
        .setMaxEmbeddedResources(limits.maxEmbeddedEntries())
        .setMaxDepth(limits.maxRecursionDepth())
        .build());

    // 2. QR/barcode via ZXing-CPP (Tika 4.x fork feature)
    if (enableQr) {
        ZXingCPPConfig zxCfg = new ZXingCPPConfig();
        zxCfg.setEnabled(true);
        zxCfg.setZxingPath(zxingPath);  // "/usr/local/bin/ZXingReader"
        context.set(ZXingCPPConfig.class, zxCfg);
    }

    // 3. OCR via Tika's built-in TesseractOCRParser
    TesseractOCRConfig ocrCfg = new TesseractOCRConfig();
    ocrCfg.setLanguage(ocrLang);
    ocrCfg.setPSMConfiguration(ocrPsm);
    ocrCfg.setTimeout(Math.min((int)(ocrBudgetMs / 1000L), 30)); // per-call cap
    if (!enableOcr) ocrCfg.setSkipOcr(true);
    context.set(TesseractOCRConfig.class, ocrCfg);

    // 4. Byte-level digest per entry
    // DigesterFactory writes X-TIKA:digest:SHA-256 to each entry's Metadata
    context.set(DigesterFactory.class, DigesterFactory.getInstance(
        new DigestDef("SHA-256", DigestDef.EncodingType.HEX)));

    // 5. Handler with TEXT content type
    RecursiveParserWrapperHandler handler = new RecursiveParserWrapperHandler(
        new BasicContentHandlerFactory(
            BasicContentHandlerFactory.HANDLER_TYPE.TEXT, CHARS_PER_ENTRY));

    RecursiveParserWrapper wrapper = new RecursiveParserWrapper(auto);
    // ... parse, iterate metaList, build EntryResult list
```

For each entry, read:
- `sha256` from `m.get("X-TIKA:digest:SHA-256")` (note: key uses hyphen, check exact string)
- QR codes from `m.getValues(Barcode.BARCODE_VALUE)` (multi-valued), correlated with
  `m.getValues(Barcode.BARCODE_FORMAT)`, `m.getValues(Barcode.BARCODE_RAW_BYTES)`,
  `m.getValues(Barcode.BARCODE_POSITION)` — zip them by index
- OCR: for image entries (`contentType.startsWith("image/")`), `text` IS the OCR output.
  `ocr.text = text`, `ocr.skipped = null`. For non-image entries with OCR disabled, `ocr.skipped = "disabled"`. For non-image entries, `ocr.skipped = "no_images"`.
- Language: `m.get("dc:language")`

**Important implementation notes:**
- `Barcode.*` constants are in `tika-core` under `org.apache.tika.metadata.Barcode`
- `ZXingCPPConfig` is in `org.apache.tika.parser.image`
- `TesseractOCRConfig` is in `org.apache.tika.parser.ocr`
- `EmbeddedLimits` is in `org.apache.tika.config`
- `DigesterFactory` / `DigestDef` are in `org.apache.tika.digest` — check exact package in 4.x source
- Read the actual source in the fork to verify exact class paths and method names before writing code

### Task 7 — `RmetaWriter.java`: update QrCode serialization + sha256

```java
// sha256 — now from DigesterFactory
if (e.sha256() != null) n.put("sha256", e.sha256());
else n.putNull("sha256");

// qr — updated shape from Tika barcode metadata
ObjectNode qr = n.putObject("qr");
ArrayNode codes = qr.putArray("codes");
if (e.qr() != null && e.qr().codes() != null) {
    for (EntryResult.QrCode code : e.qr().codes()) {
        ObjectNode c = codes.addObject();
        c.put("data",   code.data());
        c.put("format", code.format());
        if (code.rawBytes() != null) c.put("raw_bytes", code.rawBytes());
        else c.putNull("raw_bytes");
        if (code.position() != null) c.put("position", code.position());
        else c.putNull("position");
    }
}
```

### Task 8 — Python: update `QrCode` type + schema

**`src/redtusk/types.py`:**
```python
@dataclass(frozen=True)
class QrCode:
    data: str
    format: str
    raw_bytes: str | None = None
    position: str | None = None
```

Remove `type: str` and `bbox: tuple[int, int, int, int]`.

Update `to_dict()` and `from_dict()` accordingly.

**`src/redtusk/schema.py`:** Update `_QR_CODE_SCHEMA`:
```python
_QR_CODE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["data", "format"],
    "properties": {
        "data":      {"type": "string"},
        "format":    {"type": "string"},
        "raw_bytes": {"type": ["string", "null"]},
        "position":  {"type": ["string", "null"]},
    },
}
```

### Task 9 — `worker_runtime.py`: update job.json

Remove `zbarimg_binary` and `tesseract_binary` from the job dict. Add `zxing_path`
and `tesseract_path`:

```python
job_dict = {
    ...
    "zxing_path":     "/usr/local/bin/ZXingReader",
    "tesseract_path": "tesseract",
    ...
}
```

Remove `zbarimgBinary` and `tesseractBinary` from `JobDescriptor` wiring.

### Task 10 — Update Java tests

- Remove any tests that reference `ScannerRunner`
- Update `ParserRunnerTest` to not mock scanner binaries
- Update `EntryResult`/`RmetaWriter` tests for new `QrCode` shape

### Task 11 — Update Python tests

- Update `QrCode` fixture in `test_types_values.py`
- Update `test_schema_validation.py` QR code schema assertions
- Update `test_worker_runtime.py` job.json assertions (remove zbarimg/tesseract binary fields)
- Update HTTP tests that build minimal `ExtractResult` fixtures with `QrCode`

## Acceptance criteria

- `mvn -q package -DskipTests` passes with Tika 4.0.0-SNAPSHOT
- `pytest tests/unit tests/http -q` → all passing
- `ruff check src && mypy src` clean
- Docker build completes (ZXing-CPP and Tika fork stages succeed)
- Smoke test: `PUT /detect/stream` with a text file returns the correct content type

## What this plan does NOT include

- Changes to the Python dispatcher/API/pool (untouched)
- High-density Dockerfile (deferred — requires same ZXing+Tika-fork stages to be added)
- `DigestingParser` for binary hashes of embedded bytes — that's a future Tika-fork addition per the user's plan
