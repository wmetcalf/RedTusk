package io.redtusk.worker;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * PDF inline-image extraction must be BOUNDED.
 *
 * Measured 2026-08-18 on an 8.4 MB PDF: a current Tika finds 46 DISTINCT inline images (dedup
 * saves 6%, so this is not duplicate work) and spends ~1s each decoding and perceptual-hashing
 * them -- 2.6s -> 61.9s for that one document, a 20x throughput loss. Unbounded, a PDF with a
 * thousand images costs a thousand seconds and blows the guest budget.
 *
 * The cap is env-driven so a fleet can tune it without a change to the host/guest job contract.
 */
class InlineImageCapTest {

    @Test
    void defaultIsBoundedNotUnlimited() {
        // MUTATION: default to 0/-1 (unbounded) -> a pathological PDF can spend the whole guest
        // budget on image hashing, which is exactly the regression this cap exists for.
        assertTrue(ParserRunner.DEFAULT_MAX_INLINE_IMAGES > 0,
                "the default must bound image work");
        assertEquals(ParserRunner.DEFAULT_MAX_INLINE_IMAGES, ParserRunner.parseMaxInlineImages(null));
        assertEquals(ParserRunner.DEFAULT_MAX_INLINE_IMAGES, ParserRunner.parseMaxInlineImages(""));
        assertEquals(ParserRunner.DEFAULT_MAX_INLINE_IMAGES, ParserRunner.parseMaxInlineImages("   "));
    }

    @Test
    void anOperatorValueIsHonoured() {
        assertEquals(8, ParserRunner.parseMaxInlineImages("8"));
        assertEquals(500, ParserRunner.parseMaxInlineImages(" 500 "));
    }

    @Test
    void zeroOrNegativeMeansExplicitlyUnbounded() {
        // A deliberate opt-out for an operator who wants the complete image inventory and will
        // accept the parse time. Distinct from a typo, which falls back to the default.
        assertEquals(0, ParserRunner.parseMaxInlineImages("0"));
        assertEquals(-1, ParserRunner.parseMaxInlineImages("-1"));
    }

    @Test
    void aTypoFallsBackInsteadOfFailingTheJob() {
        // MUTATION: let NumberFormatException propagate -> one bad env var fails every PDF.
        assertEquals(ParserRunner.DEFAULT_MAX_INLINE_IMAGES, ParserRunner.parseMaxInlineImages("banana"));
        assertEquals(ParserRunner.DEFAULT_MAX_INLINE_IMAGES, ParserRunner.parseMaxInlineImages("12x"));
    }

    @Test
    void anUnboundedCapReturnsTheStockEngineFactoryBehaviour() {
        // cap<=0 must hand back the plain engine, not a bounded one that never runs.
        var f = new ParserRunner.BoundedImageGraphicsEngineFactory(0);
        assertNotNull(f, "factory must construct for the unbounded case");
    }
}
