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
import java.util.concurrent.ConcurrentHashMap;
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

    private final boolean enableThumbnails;

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
            buffered.put(embPath, bytes);
            contentTypes.put(embPath, ct);
        }
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
