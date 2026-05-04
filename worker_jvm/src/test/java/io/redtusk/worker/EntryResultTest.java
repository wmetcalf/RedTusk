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
            "a".repeat(64), null, null, false, null, null, Map.of(), "hello", "en",
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
            "b".repeat(64), "d41d8cd98f00b204e9800998ecf8427e", "da39a3ee5e6b4b0d3255bfef95601890afd80709",
            true, "a1b2c3d4e5f6a7b8", "1f0e0310000000",
            Map.of("Image-Width", "200"), "", null,
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
            "c".repeat(64), null, null, false, null, null, Map.of(), "", null,
            new EntryResult.QrResult(List.of(), "error"),
            new EntryResult.OcrResult("", null, 0, "error"),
            "parse failed: unexpected EOF"
        );
        assertEquals("parse failed: unexpected EOF", bad.error());
        assertEquals("error", bad.qr().skipped());
    }

    @Test
    void qrCodeFields() {
        var code = new EntryResult.QrCode(
            "https://example.com", "QR_CODE", "aGVsbG8=", "0,0 100,0 100,100 0,100");
        assertEquals("https://example.com", code.data());
        assertEquals("QR_CODE", code.format());
        assertEquals("aGVsbG8=", code.rawBytes());
        assertEquals("0,0 100,0 100,100 0,100", code.position());
    }
}
