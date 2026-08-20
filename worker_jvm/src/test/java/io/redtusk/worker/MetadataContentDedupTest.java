package io.redtusk.worker;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * `tk:content` must not reach the rmeta: it is the entry's full body, which RedTusk already
 * stores in the `text` field.
 *
 * Measured on a 1.4 MB XLSX before this filter: metadata.json 13.0 MB -> 26.1 MB and job time
 * 10.1s -> 18.5s, with one VBA module's metadata at 67,092 B against a text field of 66,309 B --
 * the same content, byte for byte.
 *
 * Tests the PREDICATE, not a round-trip through Metadata: `Metadata.set("tk:...")` is silently
 * dropped by Tika (that namespace is computed, not settable), so a test that populates a
 * Metadata and asserts the key is absent passes whether or not the filter exists. The first
 * version of this file did exactly that and proved nothing.
 */
class MetadataContentDedupTest {

    @Test
    void theDuplicatedBodyIsSuppressed() {
        // MUTATION: drop the tk:content case -> every entry's body is stored twice and the
        // rmeta doubles.
        assertTrue(ParserRunner.isSuppressedMetadataKey("tk:content"));
    }

    @Test
    void theWholeTikaNativeNamespaceIsSuppressed() {
        // Merged policy (main's 84a6d8c): filter the whole tk: namespace, not just the body.
        // This branch arrived from the other end -- tk:content duplicating every entry's text --
        // and the prefix rule subsumes that case.
        //
        // MUTATION: narrow this back to an exact match on tk:content -> tk:parsed-by and friends
        // leak into every entry's metadata.
        for (String drop : new String[] {
                "tk:content", "tk:chunks", "tk:parsed-by",
                "tk:encoding-detection-trace", "tk:content-handler" }) {
            assertTrue(ParserRunner.isSuppressedMetadataKey(drop), drop + " must be suppressed");
        }
    }

    @Test
    void theNamespacePrefixComesFromTikaNotALiteral() {
        // The rename that made this necessary (X-TIKA: -> tk:) is proof the name moves.
        assertTrue(ParserRunner.TIKA_NATIVE_PREFIX.endsWith(":"));
        assertTrue(ParserRunner.isSuppressedMetadataKey(ParserRunner.TIKA_NATIVE_PREFIX + "anything"));
    }

    @Test
    void thePreExistingFiltersStillApply() {
        assertTrue(ParserRunner.isSuppressedMetadataKey("X-TIKA:Parsed-By"));
        assertTrue(ParserRunner.isSuppressedMetadataKey("Content-Type"));
        assertFalse(ParserRunner.isSuppressedMetadataKey("dc:creator"));
        assertFalse(ParserRunner.isSuppressedMetadataKey("Content-Encoding"));
    }
}
