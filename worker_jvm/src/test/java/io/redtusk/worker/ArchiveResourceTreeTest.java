package io.redtusk.worker;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

import static org.junit.jupiter.api.Assertions.*;

class ArchiveResourceTreeTest {
    @Test
    void archiveEntriesRetainNamesTextAndTreeWithThumbnailCapture(@TempDir Path tmp) throws Exception {
        Path zip = tmp.resolve("documents.zip");
        try (var out = new ZipOutputStream(Files.newOutputStream(zip))) {
            out.putNextEntry(new ZipEntry("documents/Résumé.txt"));
            out.write("Archive child evidence 742819".getBytes(StandardCharsets.UTF_8));
            out.closeEntry();
        }
        var runner = new ParserRunner(new JobDescriptor.LimitsDescriptor(10, 100, 1048576, 30),
                false, false, "eng", 3, 2000, true, "", "tesseract")
                .setOutputDir(tmp.resolve("out"), true);
        var result = runner.parse(zip.toFile(), "documents.zip", "0".repeat(64));
        var child = result.entries().stream().filter(e -> e.path().endsWith("Résumé.txt"))
                .findFirst().orElseThrow(() -> new AssertionError("No child in " + result.entries()));
        assertTrue(child.text().contains("Archive child evidence 742819"));
        assertEquals("/documents/Résumé.txt", child.path());
        assertEquals("/", child.parentPath());
        assertEquals(1, child.depth());
        assertEquals("text/plain", child.contentType());
    }

    @Test
    void equalBasenamesKeepDistinctPathsAndNestedContainerParents(@TempDir Path tmp) throws Exception {
        var nested = new java.io.ByteArrayOutputStream();
        try (var out = new ZipOutputStream(nested)) {
            out.putNextEntry(new ZipEntry("folder/child.txt"));
            out.write("Nested child 742819".getBytes(StandardCharsets.UTF_8));
            out.closeEntry();
        }
        Path zip = tmp.resolve("outer.zip");
        try (var out = new ZipOutputStream(Files.newOutputStream(zip))) {
            for (String folder : new String[]{"one", "two"}) {
                out.putNextEntry(new ZipEntry(folder + "/same.txt"));
                out.write(("Distinct child " + folder).getBytes(StandardCharsets.UTF_8));
                out.closeEntry();
            }
            out.putNextEntry(new ZipEntry("archives/inner.zip"));
            out.write(nested.toByteArray());
            out.closeEntry();
        }
        var runner = new ParserRunner(new JobDescriptor.LimitsDescriptor(10, 100, 1048576, 30),
                false, false, "eng", 3, 2000, true, "", "tesseract")
                .setOutputDir(tmp.resolve("out"), true);
        var result = runner.parse(zip.toFile(), "outer.zip", "0".repeat(64));
        var paths = result.entries().stream().map(EntryResult::path).collect(java.util.stream.Collectors.toSet());
        assertEquals(java.util.Set.of("/", "/one/same.txt", "/two/same.txt", "/archives/inner.zip",
                "/archives/inner.zip/folder/child.txt"), paths);
        var child = result.entries().stream().filter(e -> e.path().endsWith("child.txt")).findFirst().orElseThrow();
        assertEquals("/archives/inner.zip", child.parentPath());
        assertEquals(2, child.depth());
        var saved = new EmbeddedFileExtractor(10, 100, false).extract(zip.toFile(), tmp.resolve("saved"));
        assertEquals(4, saved.size());
        assertTrue(saved.keySet().containsAll(paths.stream().filter(p -> !p.equals("/")).toList()));
    }

    @Test
    void equalImageBasenamesKeepTheirOwnBytesAndThumbnails(@TempDir Path tmp) throws Exception {
        Path zip = tmp.resolve("images.zip");
        try (var out = new ZipOutputStream(Files.newOutputStream(zip))) {
            for (int index = 0; index < 2; index++) {
                var image = new java.awt.image.BufferedImage(16, 16, java.awt.image.BufferedImage.TYPE_INT_RGB);
                var graphics = image.createGraphics();
                graphics.setColor(index == 0 ? java.awt.Color.RED : java.awt.Color.BLUE);
                graphics.fillRect(0, 0, 16, 16);
                graphics.dispose();
                var bytes = new java.io.ByteArrayOutputStream();
                javax.imageio.ImageIO.write(image, "png", bytes);
                out.putNextEntry(new ZipEntry("folder-" + index + "/logo.png"));
                out.write(bytes.toByteArray());
                out.closeEntry();
            }
        }
        Path output = tmp.resolve("out");
        Files.createDirectories(output);
        var limits = new JobDescriptor.LimitsDescriptor(10, 100, 1048576, 30);
        var job = new JobDescriptor(zip.toString(), output.toString(), "0".repeat(64), "images.zip", limits,
                false, false, "eng", 3, "default", "runc", false, false, false, "0.1.0", "", "tesseract",
                2000, true, true);
        var runner = new ParserRunner(limits, false, false, "eng", 3, 2000, true, "", "tesseract")
                .setOutputDir(output, true).setDraftSnapshot(job);
        var result = runner.parse(zip.toFile(), "images.zip", "0".repeat(64));
        var images = result.entries().stream().filter(e -> e.contentType().equals("image/png")).toList();
        assertEquals(2, images.size());
        assertTrue(images.stream().allMatch(EntryResult::hasThumbnail));
        assertNotEquals(images.get(0).sha256(), images.get(1).sha256());
        var draft = new com.fasterxml.jackson.databind.ObjectMapper().readTree(output.resolve("metadata.json").toFile());
        var draftPaths = new java.util.HashSet<String>();
        for (var entry : draft.path("extraction").path("entries")) draftPaths.add(entry.path("path").asText());
        assertEquals(java.util.Set.of("/", "/folder-0/logo.png", "/folder-1/logo.png"), draftPaths);
    }
}
