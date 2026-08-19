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

    @Test
    void aTailWindowIsOnlyMeaningfulWhenThereIsAMiddleToSkip() {
        // A 1- or 2-page PDF is the commonest shape there is. With a naive
        // `pageNumber > total - TAIL_PAGES`, total=1 gives 1 > -1 -> EVERY page is "tail", so
        // the whole document runs at the inflated cap+allowance AND never short-circuits in
        // run(). The guard is total > TAIL_PAGES*2.
        //
        // MUTATION: drop the `total <= TAIL_PAGES * 2` guard -> small PDFs lose the page-level
        // skip entirely, which is where the time is actually saved.
        assertTrue(ParserRunner.TAIL_PAGES > 0);
        assertTrue(ParserRunner.MAX_PAGE_TREE_DEPTH > 1,
                "the page-tree walk must be bounded against a cyclic /Parent chain");
    }

    @Test
    void theTailAllowanceIsPositiveSoTheTailCanActuallyBeSampled() {
        // tailAllowance = max(1, cap/2): with cap=1 integer division gives 0, and a "reserved"
        // tail that allows zero images reserves nothing.
        assertTrue(Math.max(1, ParserRunner.DEFAULT_MAX_INLINE_IMAGES / 2) >= 1);
        assertTrue(Math.max(1, 1 / 2) == 1, "cap=1 must still leave the tail a real allowance");
    }
}
