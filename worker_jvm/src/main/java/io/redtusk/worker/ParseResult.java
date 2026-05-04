package io.redtusk.worker;

import java.util.List;

/**
 * Returned by {@link ParserRunner#parse}. Carries the extracted entries,
 * any accumulated warnings (scanner failures), and truncation info when limits were hit.
 */
public record ParseResult(
    List<EntryResult> entries,
    List<WorkerWarning> warnings,
    WorkerTruncation truncated   // null if no limit was hit
) {

    /** A warning entry matching the schema's warnings[] shape. */
    public record WorkerWarning(String code, String detail, String entryPath) {}

    /** Truncation info matching the schema's truncated object shape. */
    public record WorkerTruncation(String reason, int limit, int observed) {}
}
