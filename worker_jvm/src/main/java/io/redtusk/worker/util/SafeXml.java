package io.redtusk.worker.util;

import org.w3c.dom.Document;
import org.xml.sax.InputSource;
import org.xml.sax.SAXException;
import org.xml.sax.XMLReader;

import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import javax.xml.parsers.SAXParser;
import javax.xml.parsers.SAXParserFactory;
import javax.xml.stream.XMLInputFactory;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerConfigurationException;
import javax.xml.transform.TransformerFactory;
import java.io.IOException;
import java.util.logging.Logger;

/**
 * Single hardened entry point for all JAXP XML construction in the worker.
 *
 * <p>The worker is the trust boundary for hostile documents. Every XML reader it
 * constructs must reject external entities, DTDs, stylesheets, and XInclude so a
 * malicious document cannot trigger XXE disclosure or SSRF (the README's
 * "No remote resources" guarantee). This class centralises the JAXP secure
 * configuration so callers cannot accidentally build an unhardened factory.</p>
 *
 * <p>Settings applied (best-effort — features unsupported by a given
 * implementation are swallowed so a parser that lacks one still gets the rest):</p>
 * <ul>
 *   <li>{@code FEATURE_SECURE_PROCESSING = true}</li>
 *   <li>{@code http://apache.org/xml/features/disallow-doctype-decl = true}</li>
 *   <li>{@code http://xml.org/sax/features/external-general-entities = false}</li>
 *   <li>{@code http://xml.org/sax/features/external-parameter-entities = false}</li>
 *   <li>{@code http://apache.org/xml/features/nonvalidating/load-external-dtd = false}</li>
 *   <li>XInclude awareness off, no expansion of entity references</li>
 *   <li>{@code ACCESS_EXTERNAL_DTD = ""}, {@code ACCESS_EXTERNAL_SCHEMA = ""},
 *       {@code ACCESS_EXTERNAL_STYLESHEET = ""}</li>
 * </ul>
 */
public final class SafeXml {

    private static final Logger LOG = Logger.getLogger(SafeXml.class.getName());

    private static final String FEATURE_DISALLOW_DOCTYPE =
            "http://apache.org/xml/features/disallow-doctype-decl";
    private static final String FEATURE_EXTERNAL_GENERAL_ENTITIES =
            "http://xml.org/sax/features/external-general-entities";
    private static final String FEATURE_EXTERNAL_PARAMETER_ENTITIES =
            "http://xml.org/sax/features/external-parameter-entities";
    private static final String FEATURE_LOAD_EXTERNAL_DTD =
            "http://apache.org/xml/features/nonvalidating/load-external-dtd";

    private SafeXml() {}

    /** A hardened {@link DocumentBuilderFactory}: no DOCTYPE, no external entities,
     *  no external DTD, no XInclude. */
    public static DocumentBuilderFactory newDocumentBuilderFactory() {
        DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
        setFeature(dbf, XMLConstants.FEATURE_SECURE_PROCESSING, true);
        setFeature(dbf, FEATURE_DISALLOW_DOCTYPE, true);
        setFeature(dbf, FEATURE_EXTERNAL_GENERAL_ENTITIES, false);
        setFeature(dbf, FEATURE_EXTERNAL_PARAMETER_ENTITIES, false);
        setFeature(dbf, FEATURE_LOAD_EXTERNAL_DTD, false);
        dbf.setXIncludeAware(false);
        dbf.setExpandEntityReferences(false);
        try {
            dbf.setAttribute(XMLConstants.ACCESS_EXTERNAL_DTD, "");
        } catch (IllegalArgumentException ignore) { /* attribute unsupported */ }
        try {
            dbf.setAttribute(XMLConstants.ACCESS_EXTERNAL_SCHEMA, "");
        } catch (IllegalArgumentException ignore) { /* attribute unsupported */ }
        return dbf;
    }

    /** A hardened {@link DocumentBuilder}. */
    public static DocumentBuilder newDocumentBuilder() throws ParserConfigurationException {
        return newDocumentBuilderFactory().newDocumentBuilder();
    }

    /** Parse {@code source} into a DOM {@link Document} using a hardened builder. */
    public static Document parse(InputSource source)
            throws ParserConfigurationException, SAXException, IOException {
        return newDocumentBuilder().parse(source);
    }

    /** A hardened {@link SAXParserFactory}. */
    public static SAXParserFactory newSAXParserFactory() {
        SAXParserFactory spf = SAXParserFactory.newInstance();
        setFeature(spf, XMLConstants.FEATURE_SECURE_PROCESSING, true);
        setFeature(spf, FEATURE_DISALLOW_DOCTYPE, true);
        setFeature(spf, FEATURE_EXTERNAL_GENERAL_ENTITIES, false);
        setFeature(spf, FEATURE_EXTERNAL_PARAMETER_ENTITIES, false);
        setFeature(spf, FEATURE_LOAD_EXTERNAL_DTD, false);
        spf.setXIncludeAware(false);
        return spf;
    }

    /** A hardened {@link SAXParser}. */
    public static SAXParser newSAXParser()
            throws ParserConfigurationException, SAXException {
        SAXParser parser = newSAXParserFactory().newSAXParser();
        setProperty(parser, XMLConstants.ACCESS_EXTERNAL_DTD, "");
        setProperty(parser, XMLConstants.ACCESS_EXTERNAL_SCHEMA, "");
        return parser;
    }

    /** A hardened {@link XMLReader}. */
    public static XMLReader newXMLReader()
            throws ParserConfigurationException, SAXException {
        XMLReader reader = newSAXParser().getXMLReader();
        setReaderFeature(reader, FEATURE_DISALLOW_DOCTYPE, true);
        setReaderFeature(reader, FEATURE_EXTERNAL_GENERAL_ENTITIES, false);
        setReaderFeature(reader, FEATURE_EXTERNAL_PARAMETER_ENTITIES, false);
        setReaderFeature(reader, FEATURE_LOAD_EXTERNAL_DTD, false);
        return reader;
    }

    /** A hardened StAX {@link XMLInputFactory}: external entities and DTD support off. */
    public static XMLInputFactory newXMLInputFactory() {
        XMLInputFactory xif = XMLInputFactory.newFactory();
        setStaxProperty(xif, XMLInputFactory.IS_SUPPORTING_EXTERNAL_ENTITIES, Boolean.FALSE);
        setStaxProperty(xif, XMLInputFactory.SUPPORT_DTD, Boolean.FALSE);
        return xif;
    }

    /** A hardened {@link TransformerFactory}: no external DTD/stylesheet access. */
    public static TransformerFactory newTransformerFactory() {
        TransformerFactory tf = TransformerFactory.newInstance();
        try {
            tf.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
        } catch (TransformerConfigurationException e) {
            LOG.fine("SafeXml: secure processing unsupported on TransformerFactory: " + e.getMessage());
        }
        try {
            tf.setAttribute(XMLConstants.ACCESS_EXTERNAL_DTD, "");
        } catch (IllegalArgumentException ignore) { /* attribute unsupported */ }
        try {
            tf.setAttribute(XMLConstants.ACCESS_EXTERNAL_STYLESHEET, "");
        } catch (IllegalArgumentException ignore) { /* attribute unsupported */ }
        return tf;
    }

    /** A hardened identity {@link Transformer}. */
    public static Transformer newTransformer() throws TransformerConfigurationException {
        return newTransformerFactory().newTransformer();
    }

    // ── internal helpers ────────────────────────────────────────────────────

    private static void setFeature(DocumentBuilderFactory f, String name, boolean value) {
        try {
            f.setFeature(name, value);
        } catch (ParserConfigurationException e) {
            LOG.fine("SafeXml: DBF feature unsupported [" + name + "]: " + e.getMessage());
        }
    }

    private static void setFeature(SAXParserFactory f, String name, boolean value) {
        try {
            f.setFeature(name, value);
        } catch (ParserConfigurationException | SAXException e) {
            LOG.fine("SafeXml: SAXPF feature unsupported [" + name + "]: " + e.getMessage());
        }
    }

    private static void setProperty(SAXParser parser, String name, Object value) {
        try {
            parser.setProperty(name, value);
        } catch (org.xml.sax.SAXNotRecognizedException | org.xml.sax.SAXNotSupportedException e) {
            LOG.fine("SafeXml: SAXParser property unsupported [" + name + "]: " + e.getMessage());
        }
    }

    private static void setReaderFeature(XMLReader reader, String name, boolean value) {
        try {
            reader.setFeature(name, value);
        } catch (org.xml.sax.SAXNotRecognizedException | org.xml.sax.SAXNotSupportedException e) {
            LOG.fine("SafeXml: XMLReader feature unsupported [" + name + "]: " + e.getMessage());
        }
    }

    private static void setStaxProperty(XMLInputFactory xif, String name, Object value) {
        try {
            xif.setProperty(name, value);
        } catch (IllegalArgumentException e) {
            LOG.fine("SafeXml: StAX property unsupported [" + name + "]: " + e.getMessage());
        }
    }
}
