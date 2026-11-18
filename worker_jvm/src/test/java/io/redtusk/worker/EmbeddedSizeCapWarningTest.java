package io.redtusk.worker;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Pass 2's size caps must not be SILENT. An embedded file cut at the per-file cap, and entries
 * skipped once the per-pass byte budget is spent, used to show up only in the worker log: the
 * result looked complete. Each must now surface as a worker warning (which RmetaWriter puts in
 * rmeta.warnings[], and the engine maps to the sealed result's warnings).
 *
 * Caps are shrunk through the package-private constructor so the fixture stays a few KB.
 */
class EmbeddedSizeCapWarningTest {

    private static File zip(Path dir, String... namesAndSizes) throws Exception {
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        try (ZipOutputStream z = new ZipOutputStream(bos)) {
            for (int i = 0; i < namesAndSizes.length; i += 2) {
                z.putNextEntry(new ZipEntry(namesAndSizes[i]));
                byte[] b = new byte[Integer.parseInt(namesAndSizes[i + 1])];
                for (int j = 0; j < b.length; j++) b[j] = (byte) ('a' + (j % 26));
                z.write(b);
                z.closeEntry();
            }
        }
        File f = dir.resolve("in.zip").toFile();
        Files.write(f.toPath(), bos.toByteArray());
        return f;
    }

    private static List<String> codes(List<ParseResult.WorkerWarning> ws) {
        return ws.stream().map(ParseResult.WorkerWarning::code).toList();
    }

    @Test
    void aFileCutAtThePerFileCapIsWarned(@TempDir Path tmp) throws Exception {
        // MUTATION: drop the post-read probe -> the 4000-byte member is written as 1000 bytes
        // with no warning, which is the silent truncation this test exists for.
        File in = zip(tmp, "big.txt", "4000", "small.txt", "10");
        var ex = new EmbeddedFileExtractor(10, 100, false, 1000, 1_000_000);
        ex.extract(in, tmp.resolve("out"));
        List<ParseResult.WorkerWarning> ws = ex.warnings();
        assertEquals(List.of("embedded_file_truncated"), codes(ws), ws.toString());
        assertTrue(ws.get(0).entryPath().endsWith("big.txt"), ws.toString());
        assertEquals(1000, Files.size(tmp.resolve("out/embedded/big.txt")));
    }

    @Test
    void aFileExactlyAtTheCapIsNotWarned(@TempDir Path tmp) throws Exception {
        // MUTATION: warn whenever bytes.length == cap -> an exact-size file is reported as cut.
        File in = zip(tmp, "exact.txt", "1000");
        var ex = new EmbeddedFileExtractor(10, 100, false, 1000, 1_000_000);
        ex.extract(in, tmp.resolve("out"));
        assertEquals(List.of(), codes(ex.warnings()));
    }

    @Test
    void entriesSkippedByTheByteBudgetAreWarnedOnce(@TempDir Path tmp) throws Exception {
        // MUTATION: drop the skip counter -> three members silently vanish from embedded/.
        File in = zip(tmp, "a.txt", "600", "b.txt", "600", "c.txt", "600", "d.txt", "600");
        var ex = new EmbeddedFileExtractor(10, 100, false, 1_000_000, 1000);
        ex.extract(in, tmp.resolve("out"));
        List<ParseResult.WorkerWarning> ws = ex.warnings();
        assertEquals(List.of("extracted_bytes_budget"), codes(ws), ws.toString());
        assertTrue(ws.get(0).detail().startsWith("3 embedded entries not written"), ws.toString());
    }

    @Test
    void theProductionCapsAreUnchanged() {
        var ex = new EmbeddedFileExtractor(10, 100, false);
        assertEquals(EmbeddedFileExtractor.MAX_FILE_BYTES, ex.maxFileBytes());
        assertEquals(EmbeddedFileExtractor.MAX_EXTRACTED_BUDGET_BYTES, ex.budgetBytes());
    }
}
