package io.redtusk.worker;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.stream.Stream;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

import static org.junit.jupiter.api.Assertions.*;

/**
 * embedded/thumbnails/ belongs to writeThumbnail. An archive member whose top-level name is
 * "thumbnails" must land somewhere else, or it is declared as a thumbnail, overwrites another
 * entry's thumbnail, or has its own bytes overwritten by one.
 */
class ThumbnailNamespaceTest {

    private static byte[] png() throws Exception {
        BufferedImage img = new BufferedImage(8, 8, BufferedImage.TYPE_INT_RGB);
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        ImageIO.write(img, "png", bos);
        return bos.toByteArray();
    }

    private static File zip(Path dir, Object... namesAndBytes) throws Exception {
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        try (ZipOutputStream z = new ZipOutputStream(bos)) {
            for (int i = 0; i < namesAndBytes.length; i += 2) {
                z.putNextEntry(new ZipEntry((String) namesAndBytes[i]));
                z.write((byte[]) namesAndBytes[i + 1]);
                z.closeEntry();
            }
        }
        File f = dir.resolve("in.zip").toFile();
        Files.write(f.toPath(), bos.toByteArray());
        return f;
    }

    @Test
    void aMemberNamedThumbnailsIsNotWrittenIntoTheThumbnailDir(@TempDir Path tmp) throws Exception {
        byte[] mz = {'M', 'Z', (byte) 0x90, 0};
        // The payload is listed FIRST so that, before the fix, pic.png's thumbnail would
        // overwrite it at embedded/thumbnails/pic.png.jpg.
        File in = zip(tmp, "thumbnails/pic.png.jpg", mz, "pic.png", png());
        Path out = tmp.resolve("out");
        new EmbeddedFileExtractor(10, 100, true).extract(in, out);

        Path thumbs = out.resolve("embedded/thumbnails");
        List<String> inThumbs;
        try (Stream<Path> s = Files.walk(thumbs)) {
            inThumbs = s.filter(Files::isRegularFile).map(p -> thumbs.relativize(p).toString()).toList();
        }
        assertEquals(List.of("pic.png.jpg"), inThumbs);
        assertFalse(java.util.Arrays.equals(mz, Files.readAllBytes(thumbs.resolve("pic.png.jpg"))));

        Path payload = EmbeddedFileExtractor.resolveOutFile(
                out.resolve("embedded"), "/thumbnails/pic.png.jpg", new org.apache.tika.metadata.Metadata());
        assertNotNull(payload);
        assertTrue(out.resolve("embedded").relativize(payload).toString().startsWith("thumbnails_/"),
                payload.toString());
        assertArrayEquals(mz, Files.readAllBytes(payload));
    }

    @Test
    void onlyTheTopLevelComponentIsReserved(@TempDir Path tmp) {
        Path root = tmp.resolve("embedded");
        var md = new org.apache.tika.metadata.Metadata();
        assertEquals(root.resolve("a/thumbnails/x.jpg"),
                EmbeddedFileExtractor.resolveOutFile(root, "/a/thumbnails/x.jpg", md));
        Path file = EmbeddedFileExtractor.resolveOutFile(root, "/thumbnails", md);
        assertNotNull(file);
        assertNotEquals(root.resolve("thumbnails"), file);
    }
}
