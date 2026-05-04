package io.redtusk.worker;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class JobDescriptorTest {

    private static final ObjectMapper OM = new ObjectMapper();

    @Test
    void roundTripMinimal() throws Exception {
        String json = """
            {
              "input_path": "/scratch/in/document.docx",
              "output_dir": "/scratch/out",
              "sha256": "ae1c000000000000000000000000000000000000000000000000000000000000",
              "filename_hint": "document.docx",
              "limits": {
                "max_recursion_depth": 10,
                "max_embedded_entries": 5000,
                "max_extracted_bytes": 524288000,
                "ocr_timeout_s": 60
              },
              "enable_qr": true,
              "enable_ocr": false,
              "ocr_lang": "eng",
              "ocr_psm": 3,
              "sandbox_profile": "default",
              "sandbox_runtime": "runsc",
              "appcds": true,
              "ksm": true,
              "crac": false,
              "redtusk_version": "0.1.0",
            }
            """;
        JobDescriptor jd = OM.readValue(json, JobDescriptor.class);
        assertEquals("/scratch/in/document.docx", jd.inputPath());
        assertEquals("/scratch/out", jd.outputDir());
        assertEquals("ae1c000000000000000000000000000000000000000000000000000000000000", jd.sha256());
        assertEquals("document.docx", jd.filenameHint());
        assertEquals(10, jd.limits().maxRecursionDepth());
        assertEquals(5000, jd.limits().maxEmbeddedEntries());
        assertTrue(jd.enableQr());
        assertFalse(jd.enableOcr());
        assertEquals("eng", jd.ocrLang());
        assertEquals(3, jd.ocrPsm());
        assertEquals("default", jd.sandboxProfile());
        assertTrue(jd.appcds());
        assertFalse(jd.crac());
    }

    @Test
    void nullFilenameHintIsAllowed() throws Exception {
        String json = """
            {
              "input_path": "/scratch/in/upload.bin",
              "output_dir": "/scratch/out",
              "sha256": "ae1c000000000000000000000000000000000000000000000000000000000000",
              "filename_hint": null,
              "limits": {"max_recursion_depth":10,"max_embedded_entries":5000,
                         "max_extracted_bytes":524288000,"ocr_timeout_s":60},
              "enable_qr": true,
              "enable_ocr": false,
              "ocr_lang": "eng",
              "ocr_psm": 3,
              "sandbox_profile": "default",
              "sandbox_runtime": "runc",
              "appcds": false,
              "ksm": false,
              "crac": false,
              "redtusk_version": "0.1.0",
            }
            """;
        JobDescriptor jd = OM.readValue(json, JobDescriptor.class);
        assertNull(jd.filenameHint());
    }
}
