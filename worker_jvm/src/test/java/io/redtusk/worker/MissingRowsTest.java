package io.redtusk.worker;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * includeMissingRows must default OFF.
 *
 * It emits a row for every GAP in a sheet's used range; content-bearing rows are emitted either
 * way, so on a sparse workbook it is pure padding. Measured on a 1.8 MB xlsm: 3,885,164 lines of
 * extracted text of which 3,882,321 (99.9%) were tab-only empty rows -- 8 MB of output and 209s
 * of parse, against 8.2s with it off and BYTE-IDENTICAL extraction (44 entries, 43 VBA modules
 * either way).
 */
class MissingRowsTest {

    @Test
    void defaultsOffMatchingTikasOwnDefault() {
        // MUTATION: default it back on -> a sparse sheet emits millions of blank rows and a
        // document that parses in 8s takes 209s, which is what pushed one past the guest budget.
        assertFalse(ParserRunner.parseIncludeMissingRows(null));
        assertFalse(ParserRunner.parseIncludeMissingRows(""));
        assertFalse(ParserRunner.parseIncludeMissingRows("0"));
        assertFalse(ParserRunner.parseIncludeMissingRows("no"));
    }

    @Test
    void anOperatorCanTurnItBackOn() {
        // Row-for-row fidelity is a legitimate ask for a specific case; it just must not be the
        // default that every sparse sheet in the corpus pays for.
        assertTrue(ParserRunner.parseIncludeMissingRows("1"));
        assertTrue(ParserRunner.parseIncludeMissingRows("true"));
        assertTrue(ParserRunner.parseIncludeMissingRows("TRUE"));
    }

    @Test
    void bothPassesShareOneOfficeConfig() {
        // Same anti-drift property as the PDF config: pass 2 used to build its own.
        assertNotNull(ParserRunner.newOfficeConfig());
        assertEquals(ParserRunner.includeMissingRows(),
                ParserRunner.newOfficeConfig().isIncludeMissingRows());
    }
}
