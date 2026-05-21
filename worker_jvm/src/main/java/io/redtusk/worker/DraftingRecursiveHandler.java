package io.redtusk.worker;

import org.apache.tika.metadata.Metadata;
import org.apache.tika.sax.BasicContentHandlerFactory;
import org.apache.tika.sax.ContentHandlerFactory;
import org.apache.tika.sax.RecursiveParserWrapperHandler;
import org.xml.sax.ContentHandler;
import org.xml.sax.SAXException;

/**
 * Recursive parser handler that fires a {@link DraftSnapshotWriter} after each
 * entry the wrapper completes. Subclasses RecursiveParserWrapperHandler so the
 * standard metadata-list bookkeeping is unchanged; we just piggy-back on
 * {@code endEmbeddedDocument} and {@code endDocument} to write a partial
 * metadata.json to disk while the parse is still in flight.
 *
 * <p>Purpose: if the dispatcher SIGKILLs the worker past job_timeout_s, the
 * partial that's already on disk is what the dispatcher will salvage instead
 * of failing the job with no result at all. See {@link DraftSnapshotWriter}.</p>
 */
final class DraftingRecursiveHandler extends RecursiveParserWrapperHandler {

    private final DraftSnapshotWriter writer;

    DraftingRecursiveHandler(ContentHandlerFactory factory, DraftSnapshotWriter writer) {
        super(factory);
        this.writer = writer;
    }

    @Override
    public void endEmbeddedDocument(ContentHandler ch, Metadata metadata) throws SAXException {
        super.endEmbeddedDocument(ch, metadata);
        // metadataList now contains the new entry; throttled write.
        writer.maybeFlush(getMetadataList());
    }

    @Override
    public void endDocument(ContentHandler ch, Metadata metadata) throws SAXException {
        super.endDocument(ch, metadata);
        // Document end is the last chance before wrapper.parse() returns.
        writer.flushNow(getMetadataList());
    }
}
