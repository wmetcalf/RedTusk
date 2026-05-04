package io.redtusk.worker;

import java.util.List;
import java.util.Map;

public record EntryResult(
    String path,
    String parentPath,
    int depth,
    String contentType,
    long sizeBytes,
    String sha256,
    String md5,
    String sha1,
    boolean hasThumbnail,
    String phash,
    String colorhash,
    Map<String, Object> metadata,
    String text,
    String language,
    QrResult qr,
    OcrResult ocr,
    String error
) {
    public record QrResult(
        List<QrCode> codes,
        String skipped
    ) {}

    public record QrCode(
        String data,       // barcode:value — decoded text
        String format,     // barcode:format — e.g. "QR_CODE", "EAN_13"
        String rawBytes,   // barcode:raw-bytes — base64 raw bytes; may be null
        String position    // barcode:position — bounding box string; may be null
    ) {}

    public record OcrResult(
        String text,
        String language,
        int durationMs,
        String skipped
    ) {}
}
