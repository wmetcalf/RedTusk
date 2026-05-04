package io.redtusk.worker;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Deserialised job.json written by the dispatcher before signalling the fifo.
 * All fields are immutable after construction (Java records).
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
    @JsonProperty("zxing_path")      String zxingPath,      // path to ZXingReader binary
    @JsonProperty("tesseract_path")   String tesseractPath,   // path to tesseract binary (default "tesseract")
    @JsonProperty("ocr_max_image_dim")    int ocrMaxImageDim,     // 0 = disabled; default 2000
    @JsonProperty("ocr_skip_blank")       boolean ocrSkipBlank,  // skip OCR on blank images via phash/colorhash
    @JsonProperty("enable_thumbnails")    boolean enableThumbnails
) {
    @JsonIgnoreProperties(ignoreUnknown = true)
    public record LimitsDescriptor(
        @JsonProperty("max_recursion_depth")    int maxRecursionDepth,
        @JsonProperty("max_embedded_entries")   int maxEmbeddedEntries,
        @JsonProperty("max_extracted_bytes")    long maxExtractedBytes,
        @JsonProperty("ocr_timeout_s")          int ocrTimeoutS
    ) {}
}
