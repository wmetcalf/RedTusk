package io.redtusk.worker;

import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.logging.Logger;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Best-effort RTF IOC (Indicator of Compromise) scanner.
 *
 * <p>RTF documents obfuscate external references with hex escapes ({@code \'HH}) and
 * unicode escapes (backslash-u followed by a signed decimal). Credential-harvesting and exploit delivery techniques
 * commonly use {@code \template}, {@code \fldinst HYPERLINK}, and protocol-handler URIs
 * (ms-msdt, search-ms, mhtml) — all of which may be hidden behind those escapes.</p>
 *
 * <p>This scanner performs a lightweight, single-pass deobfuscation of the raw RTF bytes
 * and then applies regex patterns to extract IOCs. All operations are best-effort;
 * failures are logged as warnings and never propagate to the caller.</p>
 *
 * <p>Usage: call {@link #scan(File, String)} after Tika parsing has completed for RTF
 * entries and merge the returned map into the entry's metadata map.</p>
 */
public final class RtfIocScanner {

    private static final Logger LOG = Logger.getLogger(RtfIocScanner.class.getName());

    /** Maximum raw RTF file size to attempt deobfuscation on (32 MB). */
    private static final int MAX_SCAN_BYTES = 32 * 1024 * 1024;

    // -------------------------------------------------------------------------
    // Metadata key constants (rtf: namespace)
    // -------------------------------------------------------------------------

    /** Value of a {@code \template} field (typically a UNC or HTTP URL). */
    public static final String KEY_TEMPLATE_URL = "rtf:templateUrl";

    /** URL from a {@code \fldinst HYPERLINK} instruction. */
    public static final String KEY_HYPERLINK_URL = "rtf:hyperlinkUrl";

    /** Protocol-handler URI (ms-msdt:, search-ms:, mhtml:, smb://). */
    public static final String KEY_PROTOCOL_HANDLER = "rtf:protocolHandler";

    /** Raw UNC path (\\server\share...). */
    public static final String KEY_UNC_PATH = "rtf:uncPath";

    /**
     * URL reconstructed from UTF-16LE null-byte-interleaved hex escapes in the raw RTF.
     * Attackers encode URLs as {@code h\'00t\'00t\'00p} to evade single-byte hex scanners.
     */
    public static final String KEY_NULL_BYTE_URL = "rtf:nullByteUrl";

    // -------------------------------------------------------------------------
    // Detection patterns (applied to the deobfuscated RTF text)
    // -------------------------------------------------------------------------

    /**
     * {@code \template} followed by the target path/URL.
     * Handles optional whitespace and common RTF structural noise.
     */
    private static final Pattern PAT_TEMPLATE =
            Pattern.compile("\\\\template\\s+([^\\\\{}\r\n]+)", Pattern.CASE_INSENSITIVE);

    /**
     * {@code \fldinst} containing a {@code HYPERLINK} instruction.
     * Captures the URL up to the closing quote or RTF group boundary.
     */
    private static final Pattern PAT_FLDINST_HYPERLINK =
            Pattern.compile("\\\\fldinst\\s*\\{?\\s*HYPERLINK\\s+\"([^\"]+)\"",
                    Pattern.CASE_INSENSITIVE);

    /** ms-msdt:, search-ms:, mhtml:, smb:// URIs anywhere in the document. */
    private static final Pattern PAT_PROTOCOL_HANDLER =
            Pattern.compile("(?:ms-msdt:|search-ms:|mhtml:|smb://)\\S+",
                    Pattern.CASE_INSENSITIVE);

    /**
     * {@code \includepicture} with an external URL/path.
     * These are used in credential-harvesting lures.
     */
    private static final Pattern PAT_INCLUDE_PICTURE =
            Pattern.compile("\\\\includepicture\\s+\"([^\"]+)\"",
                    Pattern.CASE_INSENSITIVE);

    /** Generic UNC path: {@code \\server\share} with at least one path component. */
    private static final Pattern PAT_UNC =
            Pattern.compile("\\\\\\\\[a-zA-Z0-9._-]+\\\\[^\\s\\\\]+",
                    Pattern.CASE_INSENSITIVE);

    /**
     * Mixed-case {@code \OBJdata} / {@code \Objdata} etc — attackers capitalise the control
     * word to defeat case-sensitive single-pass parsers.  The RTF spec mandates lowercase;
     * any uppercase variant is a strong obfuscation signal.
     * We require at least two adjacent hex chars after the word to exclude false positives
     * from embedded text that happens to contain the letters.
     */
    private static final Pattern PAT_OBJDATA_MIXEDCASE =
            Pattern.compile("\\\\[Oo][Bb][Jj][Dd][Aa][Tt][Aa]\\s+[0-9a-fA-F]{2}");

    /** Key for mixed-case objdata obfuscation flag. */
    public static final String KEY_OBJDATA_MIXEDCASE = "rtf:objdataMixedCase";

    /**
     * Detects UTF-16LE null-byte-interleaved hex escapes in the raw RTF.
     * Attackers encode URLs as {@code h\'00t\'00t\'00p} (each ASCII char followed by
     * {@code \'00}) to produce UTF-16LE that evades single-byte pattern scanners.
     * In the ISO-8859-1 decoded RTF text each escape appears as backslash-quote-HH,
     * so the pattern requires the leading backslash before the single quote.
     * Four or more such pairs are required before reconstruction to reduce false positives.
     */
    private static final Pattern PAT_NULL_BYTE_INTERLEAVED =
            Pattern.compile("(?:\\\\'([0-9a-fA-F]{2})\\\\'00){4,}", Pattern.CASE_INSENSITIVE);

    /** Inner pair pattern — static to avoid recompilation on each match iteration. */
    private static final Pattern PAT_NULL_BYTE_PAIR =
            Pattern.compile("\\\\'([0-9a-fA-F]{2})\\\\'00", Pattern.CASE_INSENSITIVE);

    /**
     * URLs and UNC paths to look for in the reconstructed UTF-16LE text.
     * Only reconstruct strings that start with a recognisable URL prefix.
     */
    private static final Pattern PAT_RECONSTRUCTED_URL =
            Pattern.compile("(?:https?://|ftp://|smb://|ms-msdt:|search-ms:|mhtml:|\\\\\\\\)\\S{3,}",
                    Pattern.CASE_INSENSITIVE);

    // -------------------------------------------------------------------------
    // Public API
    // -------------------------------------------------------------------------

    /**
     * Scan a single RTF file for IOCs and return a map of metadata key → list of values.
     *
     * <p>Returns an empty map (never null) if the file is not RTF, is too large, or any
     * error occurs.</p>
     *
     * @param inputFile   the raw RTF file on disk
     * @param contentType the detected content type (e.g. {@code application/rtf})
     * @return map of IOC metadata keys to their (possibly multi-valued) lists
     */
    public static Map<String, List<String>> scan(File inputFile, String contentType) {
        Map<String, List<String>> result = new HashMap<>();
        if (!isRtf(contentType)) {
            return result;
        }
        if (inputFile == null || !inputFile.isFile()) {
            return result;
        }
        if (inputFile.length() > MAX_SCAN_BYTES) {
            LOG.warning("RTF IOC scan skipped — file too large: " + inputFile.length());
            return result;
        }
        try {
            byte[] raw = Files.readAllBytes(inputFile.toPath());
            String deobfuscated = deobfuscate(raw);
            extractIocs(deobfuscated, result);
            // Null-byte URL scan operates on the raw RTF (before deobfuscation) because the
            // deobfuscator drops null bytes; the interleaved pattern must be seen in raw form.
            extractNullByteUrls(new String(raw, StandardCharsets.ISO_8859_1), result);
        } catch (IOException e) {
            LOG.warning("RTF IOC scan I/O error: " + e.getMessage());
        } catch (Exception e) {
            LOG.warning("RTF IOC scan unexpected error: " + e.getMessage());
        }
        return result;
    }

    // -------------------------------------------------------------------------
    // Private helpers
    // -------------------------------------------------------------------------

    private static boolean isRtf(String contentType) {
        if (contentType == null) {
            return false;
        }
        String ct = contentType.toLowerCase(java.util.Locale.ROOT);
        return ct.startsWith("application/rtf") || ct.startsWith("text/rtf");
    }

    /**
     * Lightweight single-pass RTF deobfuscation.
     *
     * <p>Replaces {@code \'HH} hex escapes with their ASCII characters,
     * replaces RTF unicode escapes (backslash-u followed by a signed decimal) with the corresponding character
     * (clamped to the BMP), and strips RTF control words that are purely
     * structural noise ({@code \rtlch}, {@code \ltrch}, {@code \cs}, {@code \cf},
     * {@code \f}). Group markers ({@code {}} ) are replaced with spaces so that
     * regex patterns can match across group boundaries.</p>
     *
     * <p>The result is a UTF-8 string suitable for regex scanning.</p>
     */
    static String deobfuscate(byte[] rtfBytes) {
        // Interpret the RTF byte stream as Latin-1 (RTF is 7-bit ASCII with \' escapes).
        String raw = new String(rtfBytes, StandardCharsets.ISO_8859_1);
        StringBuilder out = new StringBuilder(raw.length());
        int i = 0;
        int len = raw.length();
        while (i < len) {
            char c = raw.charAt(i);
            if (c == '\\' && i + 1 < len) {
                char next = raw.charAt(i + 1);
                if (next == '\'') {
                    // Hex escape \'HH
                    if (i + 3 < len) {
                        int hi = Character.digit(raw.charAt(i + 2), 16);
                        int lo = Character.digit(raw.charAt(i + 3), 16);
                        if (hi >= 0 && lo >= 0) {
                            int decoded = (hi << 4) | lo;
                            // Only materialise printable ASCII; leave high bytes as-is
                            if (decoded >= 0x20 && decoded < 0x80) {
                                out.append((char) decoded);
                            }
                            i += 4;
                            continue;
                        }
                    }
                } else if (next == 'u' && i + 2 < len && Character.isDigit(raw.charAt(i + 2))) {
                    // RTF unicode escape: backslash-u + signed decimal (optional trailing space)
                    int j = i + 2;
                    boolean neg = false;
                    if (j < len && raw.charAt(j) == '-') {
                        neg = true;
                        j++;
                    }
                    int num = 0;
                    while (j < len && Character.isDigit(raw.charAt(j))) {
                        num = num * 10 + (raw.charAt(j) - '0');
                        j++;
                    }
                    if (neg) {
                        num = -num;
                    }
                    // RTF signed-16 → code-point
                    int cp = (num < 0) ? (65536 + num) : num;
                    if (cp >= 0x20 && Character.isValidCodePoint(cp)) {
                        out.appendCodePoint(cp);
                    }
                    // consume optional trailing space
                    if (j < len && raw.charAt(j) == ' ') {
                        j++;
                    }
                    i = j;
                    continue;
                } else if (Character.isLetter(next)) {
                    // RTF control word — consume letters and optional digits
                    int j = i + 1;
                    while (j < len && Character.isLetter(raw.charAt(j))) {
                        j++;
                    }
                    // consume optional signed integer parameter
                    if (j < len && (raw.charAt(j) == '-' || Character.isDigit(raw.charAt(j)))) {
                        if (raw.charAt(j) == '-') {
                            j++;
                        }
                        while (j < len && Character.isDigit(raw.charAt(j))) {
                            j++;
                        }
                    }
                    // consume optional delimiter space
                    if (j < len && raw.charAt(j) == ' ') {
                        j++;
                    }
                    String word = raw.substring(i + 1, j).trim();
                    // Strip purely structural noise control words.
                    // Keep everything else (including \template, \fldinst, \hyperlink,
                    // \includepicture) so that the patterns below can match.
                    // Noise list: purely structural/formatting RTF control words that never
                    // carry IOC-relevant text.  Keep \template, \fldinst, \hyperlink, etc.
                    boolean noiseWord = word.equals("rtlch") || word.equals("ltrch")
                            || word.equals("hich") || word.equals("loch") || word.equals("dbch")
                            || word.startsWith("cs") || word.startsWith("cf") || word.startsWith("af")
                            || word.startsWith("lang") || word.startsWith("afs")
                            || (word.startsWith("f") && !word.startsWith("fl"));
                    if (noiseWord) {
                        out.append(' ');
                    } else {
                        // Keep control word text verbatim (including the backslash)
                        // so that patterns like \\template can match.
                        out.append(raw, i, j);
                    }
                    i = j;
                    continue;
                }
            } else if (c == '{' || c == '}') {
                out.append(' ');
                i++;
                continue;
            }
            out.append(c);
            i++;
        }
        return out.toString();
    }

    /**
     * Scan the raw RTF for UTF-16LE null-byte-interleaved hex escapes and reconstruct any
     * URL-like strings found within them.  The raw RTF (decoded as Latin-1) is searched for
     * runs of {@code \'XX\'00} pairs; each run is decoded as UTF-16LE and checked for URL
     * prefixes.  Only matches that look like URLs or UNC paths are recorded.
     */
    private static void extractNullByteUrls(String raw, Map<String, List<String>> out) {
        Matcher m = PAT_NULL_BYTE_INTERLEAVED.matcher(raw);
        while (m.find()) {
            // Reconstruct UTF-16LE: collect the non-null hex byte from each pair
            StringBuilder sb = new StringBuilder();
            String region = m.group(0);
            // Each pair is: \'XX\'00 — extract the XX bytes as UTF-16LE low bytes (BMP range)
            Matcher pair = PAT_NULL_BYTE_PAIR.matcher(region);
            while (pair.find()) {
                int lo = Integer.parseInt(pair.group(1), 16);
                if (lo >= 0x20) {
                    sb.append((char) lo);
                }
            }
            String candidate = sb.toString().trim();
            if (candidate.length() >= 8) {
                Matcher urlMatch = PAT_RECONSTRUCTED_URL.matcher(candidate);
                while (urlMatch.find()) {
                    String url = urlMatch.group().trim();
                    List<String> list = out.computeIfAbsent(KEY_NULL_BYTE_URL, k -> new ArrayList<>());
                    if (!list.contains(url)) {
                        list.add(url);
                    }
                }
            }
        }
    }

    private static void extractIocs(String text, Map<String, List<String>> out) {
        // \template targets
        matchAll(PAT_TEMPLATE, text, 1, out, KEY_TEMPLATE_URL);

        // \fldinst HYPERLINK targets
        matchAll(PAT_FLDINST_HYPERLINK, text, 1, out, KEY_HYPERLINK_URL);

        // Protocol-handler URIs
        matchAll(PAT_PROTOCOL_HANDLER, text, 0, out, KEY_PROTOCOL_HANDLER);

        // \includepicture external references (also a hyperlink vector)
        matchAll(PAT_INCLUDE_PICTURE, text, 1, out, KEY_HYPERLINK_URL);

        // Generic UNC paths
        matchAll(PAT_UNC, text, 0, out, KEY_UNC_PATH);

        // Mixed-case \objdata obfuscation (applied to raw/deobfuscated — control words are preserved)
        matchAll(PAT_OBJDATA_MIXEDCASE, text, 0, out, KEY_OBJDATA_MIXEDCASE);
    }

    /**
     * Collect all non-empty, deduplicated matches of {@code group} from {@code pattern}
     * and append them to {@code out.get(key)}, creating the list if absent.
     */
    private static void matchAll(Pattern pattern, String text, int group,
            Map<String, List<String>> out, String key) {
        Matcher m = pattern.matcher(text);
        while (m.find()) {
            String value = m.group(group).trim();
            if (!value.isEmpty()) {
                List<String> list = out.computeIfAbsent(key, k -> new ArrayList<>());
                if (!list.contains(value)) {
                    list.add(value);
                }
            }
        }
    }

    private RtfIocScanner() {
        // utility class
    }
}
