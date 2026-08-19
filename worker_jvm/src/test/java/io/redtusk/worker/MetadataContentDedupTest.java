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
    void theFilterIsExactMatchNotAPrefix() {
        // A blanket `tk:` filter would also discard tk:parsed-by / tk:encoding-detection-trace /
        // tk:encoding-detector / tk:content-handler, which are small and forensically useful and
        // DO appear in real output alongside tk:content.
        for (String keep : new String[] {
                "tk:parsed-by", "tk:encoding-detection-trace",
                "tk:encoding-detector", "tk:content-handler", "tk:content-length" }) {
            assertFalse(ParserRunner.isSuppressedMetadataKey(keep),
                    keep + " is provenance, not the body — it must survive");
        }
    }

    @Test
    void thePreExistingFiltersStillApply() {
        assertTrue(ParserRunner.isSuppressedMetadataKey("X-TIKA:Parsed-By"));
        assertTrue(ParserRunner.isSuppressedMetadataKey("Content-Type"));
        assertFalse(ParserRunner.isSuppressedMetadataKey("dc:creator"));
        assertFalse(ParserRunner.isSuppressedMetadataKey("Content-Encoding"));
    }
}
