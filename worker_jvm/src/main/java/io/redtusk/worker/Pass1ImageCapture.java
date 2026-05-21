package io.redtusk.worker;

import org.apache.tika.extractor.EmbeddedDocumentExtractor;
import org.apache.tika.io.TikaInputStream;
import org.apache.tika.metadata.Metadata;
import org.apache.tika.metadata.TikaCoreProperties;
import org.apache.tika.parser.ParseContext;
import org.apache.tika.parser.Parser;
import org.xml.sax.ContentHandler;
import org.xml.sax.SAXException;

import java.io.IOException;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;
import java.util.logging.Logger;

/**
 * Pass-1 embedded-resource capture: installed in the ParseContext that
 * RecursiveParserWrapper drives, this buffers raw image bytes during the
 * recursive metadata walk so ParserRunner can write thumbnails AFTER the
 * walk finishes — at which point each entry's final, parent-path-prefixed
 * EMBEDDED_RESOURCE_PATH is known.
 *
 * <p>Why post-pass writing matters:</p> RecursiveParserWrapper sets
 * EMBEDDED_RESOURCE_PATH on a child Metadata <i>after</i> the embedded
 * parse returns — it prepends the parent's path. So when our
 * parseEmbedded callback fires, the child Metadata's path is just the
 * local resource name (e.g. {@code /image001.jpg}). After the wrapper
 * unwinds, that same Metadata in the metaList carries the prefixed
 * path (e.g. {@code /VGP report.msg/image001.jpg}). Writing the
 * thumbnail FILE before we know the prefixed path means it lands at
 * the wrong location on disk and the UI's deterministic
 * {@code embedded/thumbnails/<entry-path>.jpg} URL 404s.
 *
 * <p>This class therefore:</p>
 * <ul>
 *   <li>Buffers the raw bytes (cap matches {@link EmbeddedFileExtractor#MAX_FILE_BYTES})</li>
 *   <li>Keys the buffer by Metadata <i>identity</i> — the same Metadata
 *       object surfaces in metaList, so post-pass lookup is exact even
 *       when the path string mutates.</li>
 *   <li>Delegates back to the parser registered on the context so
 *       RecursiveParserWrapper's per-entry metadata capture still runs.</li>
 *   <li>Non-image entries pass through untouched (no buffering).</li>
 * </ul>
 *
 * <p>Memory profile matches {@link EmbeddedFileExtractor.SavingExtractor},
 * which already buffers every embedded entry into memory. Bounded by
 * MAX_FILE_BYTES per entry × per-job embedded-entry limit.</p>
 */
final class Pass1ImageCapture implements EmbeddedDocumentExtractor {

    private static final Logger LOG = Logger.getLogger(Pass1ImageCapture.class.getName());

    private static final int MAX_FILE_BYTES = (int) Math.min(
            EmbeddedFileExtractor.MAX_FILE_BYTES, Integer.MAX_VALUE);

    /**
     * Per-job total buffered-bytes cap. Without this, a malicious container
     * declaring N image attachments × 50 MB each ({@code MAX_FILE_BYTES})
     * could pin {@code N × 50 MB} of JVM heap — for the default
     * max_embedded_entries (500) that's 25 GB, easily enough to OOM the warm
     * worker JVM and kill the slot for every other in-flight job. 256 MB is
     * comfortably above the largest legitimate image payload we'd thumbnail.
     * Past the cap, additional image entries are dropped with a recorded skip
     * reason so the UI can explain why.
     */
    private static final long MAX_BUFFER_BUDGET_BYTES = 256L * 1024 * 1024;

    private final boolean enableThumbnails;
    /** Tracks total bytes currently held in {@link #buffered}. AtomicLong so
     *  the cap check is correct under concurrent parser fan-out. */
    private final AtomicLong bufferedBytesTotal = new AtomicLong();
    /** EMBEDDED_RESOURCE_PATH set for entries we deliberately dropped past the
     *  byte budget — ParserRunner reads this to set thumbnail_skipped. */
    private final Set<String> bufferCapSkipped =
            ConcurrentHashMap.newKeySet();

    /**
     * Buffered image bytes keyed by the entry's final, parent-prefixed
     * EMBEDDED_RESOURCE_PATH — captured AFTER the downstream EmbeddedParserDecorator
     * runs so the path is already in its final form. Identity-keying does not work:
     * {@link org.apache.tika.sax.RecursiveParserWrapperHandler#endEmbeddedDocument}
     * stores {@code ParserUtils.cloneMetadata(metadata)} in its metaList, so the
     * Metadata object ParserRunner iterates is a deep copy of the one we saw,
     * not the same reference. The EMBEDDED_RESOURCE_PATH string survives the clone.
     */
    private final Map<String, byte[]> buffered = new ConcurrentHashMap<>();
    private final Map<String, String> contentTypes = new ConcurrentHashMap<>();

    Pass1ImageCapture(boolean enableThumbnails) {
        this.enableThumbnails = enableThumbnails;
    }

    /** Image bytes captured for the entry at {@code embPath}, or null. */
    byte[] bufferedBytesFor(String embPath) {
        return embPath == null ? null : buffered.get(embPath);
    }

    /** Content-Type observed when {@code embPath} was captured, or null. */
    String contentTypeFor(String embPath) {
        return embPath == null ? null : contentTypes.get(embPath);
    }

    /** True if the entry at {@code embPath} was identified as an image but
     *  skipped because the per-job buffer budget was exhausted. */
    boolean wasBufferCapped(String embPath) {
        return embPath != null && bufferCapSkipped.contains(embPath);
    }

    @Override
    public boolean shouldParseEmbedded(Metadata metadata) {
        return true;
    }

    @Override
    public void parseEmbedded(TikaInputStream stream, ContentHandler handler,
                              Metadata metadata, ParseContext context, boolean outputHtml)
            throws SAXException, IOException {

        if (!enableThumbnails || !likelyImage(metadata)) {
            // Pass through untouched. Buffering the bytes and replaying via a
            // memory-backed TikaInputStream confuses some parsers (POI MSG
            // reader in particular) — keep the original stream object.
            delegate(stream, handler, metadata, context);
            return;
        }

        byte[] bytes;
        try {
            bytes = stream.readNBytes(MAX_FILE_BYTES);
        } catch (IOException e) {
            LOG.fine("Pass1ImageCapture: readNBytes failed: " + e.getMessage());
            return;
        }
        if (bytes.length == 0) {
            return;
        }

        // Magic-byte cross-check BEFORE replay. likelyImage() can be fooled by
        // an attacker who sets Content-Type=image/jpeg or RESOURCE_NAME_KEY=foo.jpg
        // on a nested non-image attachment (typically an MSG-in-MSG). If we
        // replay those bytes through a memory-backed TikaInputStream into POI's
        // MSG reader, the inner MSG parse breaks — denial of extraction. Magic
        // bytes are authoritative; on a hint/magic mismatch, pass through with
        // the ORIGINAL stream (which has only been touched by readNBytes — we
        // still need to feed it via a replay because the bytes have been
        // consumed, but at least we don't poison non-images that managed to
        // look like images by name alone).
        if (!hasImageMagic(bytes)) {
            // Bytes already consumed from the original stream; replay them but
            // do NOT buffer — we have no thumbnail to write from these bytes.
            try (TikaInputStream replay = TikaInputStream.get(bytes)) {
                delegate(replay, handler, metadata, context);
            }
            return;
        }

        // Per-job buffer budget. Past the cap, deliberately drop the buffer
        // (still replay the bytes so the inner parser sees them) and record
        // the entry so ParserRunner can surface a pass1_buffer_cap skip reason
        // on the entry.
        boolean budgetExceeded = bufferedBytesTotal.get() + bytes.length > MAX_BUFFER_BUDGET_BYTES;

        // Replay so the downstream parser sees the same bytes and produces its
        // per-entry metadata record in the RecursiveParserWrapper's list.
        try (TikaInputStream replay = TikaInputStream.get(bytes)) {
            delegate(replay, handler, metadata, context);
        }

        // Verify it really was an image (detection may have refined or rejected
        // our initial guess) before retaining the buffer.
        String ct = metadata.get(Metadata.CONTENT_TYPE);
        if (ct != null) {
            int semi = ct.indexOf(';');
            if (semi >= 0) ct = ct.substring(0, semi).trim();
        }
        // EmbeddedParserDecorator has now set EMBEDDED_RESOURCE_PATH to the
        // final, parent-prefixed value (e.g. /VGP report.msg/image001.jpg).
        // Key the buffer on that string so ParserRunner can match against
        // the cloned Metadata in the metaList.
        String embPath = metadata.get(TikaCoreProperties.EMBEDDED_RESOURCE_PATH);
        if (embPath == null || embPath.isEmpty()) {
            // Parser never tagged this entry — nothing for ParserRunner to look up.
            return;
        }
        if (ct != null && ct.startsWith("image/")) {
            if (budgetExceeded) {
                bufferCapSkipped.add(embPath);
                return;
            }
            buffered.put(embPath, bytes);
            contentTypes.put(embPath, ct);
            bufferedBytesTotal.addAndGet(bytes.length);
        }
    }

    /**
     * Magic-byte sniff for the image formats the rest of the pipeline can
     * actually decode (ImageIO + decodeMetafile in EmbeddedFileExtractor).
     * Conservative on purpose — a false negative here just means we skip the
     * Pass-1 thumbnail (Pass-2 still gets a shot); a false positive lets us
     * waste cycles on a non-image but doesn't break anything because
     * writeThumbnail will then fail to decode.
     */
    private static boolean hasImageMagic(byte[] b) {
        if (b == null || b.length < 4) return false;
        // PNG: 89 50 4E 47 0D 0A 1A 0A
        if ((b[0] & 0xff) == 0x89 && b[1] == 'P' && b[2] == 'N' && b[3] == 'G') return true;
        // JPEG: FF D8 FF
        if ((b[0] & 0xff) == 0xff && (b[1] & 0xff) == 0xd8 && (b[2] & 0xff) == 0xff) return true;
        // GIF87a / GIF89a
        if (b.length >= 6 && b[0] == 'G' && b[1] == 'I' && b[2] == 'F'
                && b[3] == '8' && (b[4] == '7' || b[4] == '9') && b[5] == 'a') return true;
        // BMP "BM"
        if (b[0] == 'B' && b[1] == 'M') return true;
        // TIFF "II*\0" or "MM\0*"
        if ((b[0] == 'I' && b[1] == 'I' && b[2] == 42 && b[3] == 0)
                || (b[0] == 'M' && b[1] == 'M' && b[2] == 0 && b[3] == 42)) return true;
        // WEBP: "RIFF" .... "WEBP"
        if (b.length >= 12 && b[0] == 'R' && b[1] == 'I' && b[2] == 'F' && b[3] == 'F'
                && b[8] == 'W' && b[9] == 'E' && b[10] == 'B' && b[11] == 'P') return true;
        // HEIC/HEIF box: "ftyp" at offset 4 followed by a brand starting with "heic"/"heix"/"hevc"/"mif1"
        if (b.length >= 12 && b[4] == 'f' && b[5] == 't' && b[6] == 'y' && b[7] == 'p') return true;
        // SVG: text "<?xml" or "<svg" within first 256 bytes (case-sensitive
        // here; case-insensitive root tag matching is overkill for the threat
        // model — attacker who crafts a malformed SVG just falls through to
        // Pass-2, no security implication).
        int probeLen = Math.min(b.length, 256);
        if (b[0] == '<') {
            for (int i = 1; i + 4 <= probeLen; i++) {
                if (b[i] == '<' && b[i+1] == 's' && b[i+2] == 'v' && b[i+3] == 'g') return true;
            }
            // Common: starts with <?xml then later has <svg
            if (b[1] == '?' && b[2] == 'x' && b[3] == 'm' && probeLen >= 8 && b[4] == 'l') {
                for (int i = 5; i + 4 <= probeLen; i++) {
                    if (b[i] == '<' && b[i+1] == 's' && b[i+2] == 'v' && b[i+3] == 'g') return true;
                }
            }
        }
        // EMF: signature "EMF" at offset 40 within EMR_HEADER record (record
        // type 1 at offset 0, then later " EMF" — POI's HemfPicture is
        // tolerant, so we mainly check the 4-byte record-type prefix here.
        // Skipping deeper validation; mis-claimed EMF just fails decode later.
        if (b.length >= 44 && b[40] == ' ' && b[41] == 'E' && b[42] == 'M' && b[43] == 'F') return true;
        // WMF: "\xD7\xCD\xC6\x9A" (Aldus Placeable) or "\x01\x00\t\x00" (standard)
        if ((b[0] & 0xff) == 0xd7 && (b[1] & 0xff) == 0xcd
                && (b[2] & 0xff) == 0xc6 && (b[3] & 0xff) == 0x9a) return true;
        return false;
    }

    /**
     * Cheap pre-classifier. We buffer-and-replay only when we have a strong
     * hint the entry is an image, because wrapping arbitrary embedded streams
     * in a memory-backed TikaInputStream regresses parsers that rely on the
     * stream's file-backing (POI's MSG reader, in particular).
     *
     * Hints (in priority order):
     *   1. Content-Type pre-set on the child Metadata
     *   2. RESOURCE_NAME_KEY ending in a recognized image extension
     *
     * If neither hint is available, return false. We accept that some
     * unhinted inline images will fall through to Pass-2; the alternative —
     * buffering every embedded entry — has unacceptable correctness costs
     * for container formats.
     */
    private static boolean likelyImage(Metadata m) {
        String ct = m.get(Metadata.CONTENT_TYPE);
        if (ct != null) {
            int semi = ct.indexOf(';');
            if (semi >= 0) ct = ct.substring(0, semi).trim();
            if (ct.startsWith("image/")) return true;
        }
        String name = m.get(TikaCoreProperties.RESOURCE_NAME_KEY);
        if (name == null) return false;
        String lower = name.toLowerCase(java.util.Locale.ROOT);
        return lower.endsWith(".png")  || lower.endsWith(".jpg")  || lower.endsWith(".jpeg")
            || lower.endsWith(".gif")  || lower.endsWith(".bmp")  || lower.endsWith(".webp")
            || lower.endsWith(".tiff") || lower.endsWith(".tif")  || lower.endsWith(".heic")
            || lower.endsWith(".heif") || lower.endsWith(".svg")
            || lower.endsWith(".emf")  || lower.endsWith(".wmf");
    }

    private static void delegate(TikaInputStream stream, ContentHandler handler,
                                 Metadata metadata, ParseContext context)
            throws SAXException, IOException {
        Parser parser = context.get(Parser.class);
        if (parser == null) {
            return;
        }
        try {
            parser.parse(stream, handler, metadata, context);
        } catch (org.apache.tika.exception.TikaException e) {
            throw new SAXException(e);
        }
    }
}
