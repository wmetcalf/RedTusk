package io.redtusk.worker;

import org.apache.tika.io.TikaInputStream;
import org.apache.tika.metadata.Metadata;
import org.apache.tika.metadata.TikaCoreProperties;
import org.apache.tika.parser.ParseContext;
import org.junit.jupiter.api.Test;
import org.xml.sax.helpers.DefaultHandler;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.util.Arrays;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/**
 * sharedParser() registers Rar5Parser through setParsers(), which wraps every entry in a
 * type-filtering ParserDecorator. The config walks must see through those decorators, or image
 * hashing (phash) is silently off on every job.
 */
class SharedParserConfigTest {

    @Test
    void imageHashingSurvivesTheDecoratedParserTree() throws Exception {
        BufferedImage img = new BufferedImage(64, 64, BufferedImage.TYPE_INT_RGB);
        for (int x = 0; x < 64; x++) for (int y = 0; y < 64; y++) img.setRGB(x, y, (x * 4) << 16 | (y * 4) << 8);
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        ImageIO.write(img, "png", bos);
        Metadata md = new Metadata();
        try (TikaInputStream tis = TikaInputStream.get(bos.toByteArray())) {
            ParserRunner.sharedParser().parse(tis, new DefaultHandler(), md, new ParseContext());
        }
        assertTrue(Arrays.stream(md.names()).anyMatch(n -> n.toLowerCase().contains("phash")),
                Arrays.toString(md.names()));
    }

    @Test
    void aSeparatorOnlyNameIsAMemberNotTheRoot() {
        Metadata root = new Metadata();
        Metadata member = new Metadata();
        member.set(TikaCoreProperties.EMBEDDED_ID_PATH, "/1");
        member.set(TikaCoreProperties.EMBEDDED_RESOURCE_PATH, "/");
        member.set(TikaCoreProperties.RESOURCE_NAME_KEY, "\\");
        var resolved = ResourcePaths.resolve(List.of(root, member));
        assertEquals("/", resolved.get(root).path());
        assertEquals("/_", resolved.get(member).path());
        assertEquals(1, resolved.get(member).depth());
    }
}
