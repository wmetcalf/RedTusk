package io.redtusk.worker;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Pass 2 (SavingExtractor) must key entries by the same identity pass 1 (ResourcePaths) gives
 * them, and must count depth in containers, not in directory components of a member's name.
 */
class Pass2IdentityAndDepthTest {

    private static byte[] zipBytes(Object... namesAndBytes) throws Exception {
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        try (ZipOutputStream z = new ZipOutputStream(bos)) {
            for (int i = 0; i < namesAndBytes.length; i += 2) {
                z.putNextEntry(new ZipEntry((String) namesAndBytes[i]));
                z.write((byte[]) namesAndBytes[i + 1]);
                z.closeEntry();
            }
        }
        return bos.toByteArray();
    }

    private static File write(Path dir, byte[] b) throws Exception {
        File f = dir.resolve("in.zip").toFile();
        Files.write(f.toPath(), b);
        return f;
    }

    @Test
    void aBackslashNameIsKeyedLikePassOne(@TempDir Path tmp) throws Exception {
        // ResourcePaths.resolve turns "folder\child.txt" into /folder/child.txt; pass 2 must
        // use the same key or Main cannot merge the saved hashes onto the pass-1 entry.
        File in = write(tmp, zipBytes("folder\\child.txt", "hello".getBytes()));
        Map<String, EmbeddedFileExtractor.FileHashes> hashes = new EmbeddedFileExtractor(10, 100, false)
                .extract(in, tmp.resolve("out"));
        assertTrue(hashes.containsKey("/folder/child.txt"), hashes.keySet().toString());
        assertEquals("folder/child.txt", ResourcePaths.normalizeName("folder\\child.txt"));
    }

    @Test
    void directoryComponentsAreNotContainerDepth(@TempDir Path tmp) throws Exception {
        // maxDepth=1: a top-level member is depth 1 however many '/' its name holds.
        File in = write(tmp, zipBytes("documents/deep/report.txt", "x".getBytes()));
        Map<String, EmbeddedFileExtractor.FileHashes> hashes = new EmbeddedFileExtractor(1, 100, false)
                .extract(in, tmp.resolve("out"));
        assertTrue(hashes.containsKey("/documents/deep/report.txt"), hashes.keySet().toString());
        Path saved = EmbeddedFileExtractor.resolveOutFile(tmp.resolve("out/embedded"),
                "/documents/deep/report.txt", new org.apache.tika.metadata.Metadata());
        assertTrue(Files.isRegularFile(saved));
    }

    @Test
    void nestedContainersStillStopAtMaxDepth(@TempDir Path tmp) throws Exception {
        byte[] inner = zipBytes("leaf.txt", "leaf".getBytes());
        File in = write(tmp, zipBytes("inner.zip", inner));
        Map<String, EmbeddedFileExtractor.FileHashes> one = new EmbeddedFileExtractor(1, 100, false)
                .extract(in, tmp.resolve("out1"));
        assertTrue(one.containsKey("/inner.zip"), one.keySet().toString());
        assertFalse(one.keySet().stream().anyMatch(k -> k.endsWith("leaf.txt")), one.keySet().toString());
        Map<String, EmbeddedFileExtractor.FileHashes> two = new EmbeddedFileExtractor(2, 100, false)
                .extract(in, tmp.resolve("out2"));
        assertTrue(two.containsKey("/inner.zip/leaf.txt"), two.keySet().toString());
    }

    @Test
    void entriesSharingAnIdentityAreBothKeptAndWarned(@TempDir Path tmp) throws Exception {
        // "a\b.txt" and "a/b.txt" normalise to one identity; without the guard the second
        // write destroys the first's bytes.
        File in = write(tmp, zipBytes("a\\b.txt", "first".getBytes(), "a/b.txt", "second".getBytes()));
        var ex = new EmbeddedFileExtractor(10, 100, false);
        Map<String, EmbeddedFileExtractor.FileHashes> hashes = ex.extract(in, tmp.resolve("out"));
        assertTrue(hashes.containsKey("/a/b.txt"), hashes.keySet().toString());
        assertTrue(hashes.containsKey("/a/b.txt#2"), hashes.keySet().toString());
        assertNotEquals(hashes.get("/a/b.txt").sha256(), hashes.get("/a/b.txt#2").sha256());
        assertTrue(ex.warnings().stream().anyMatch(w -> w.code().equals("resource_path_collision")),
                ex.warnings().toString());
    }
}
