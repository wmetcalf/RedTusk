package io.redtusk.worker;

import com.sun.management.HotSpotDiagnosticMXBean;

import java.lang.management.ManagementFactory;

/**
 * CVE-2026-114938 ("Java4Shell"): the HotSpot AVX-512 VBMI Base64 decode intrinsic overflows
 * the heap on hostile input, and documents reach {@code java.util.Base64} inside Tika. Every
 * launcher passes {@code -XX:-UseBASE64Intrinsics}; this guard is the backstop for a launcher
 * that does not (a new script, an env var such as {@code _JAVA_OPTIONS} that wins over the
 * command line). The worker refuses to run, and refuses to bake a CRaC checkpoint, with the
 * intrinsic on.
 */
final class Base64IntrinsicGuard {
    static final String OPTION = "UseBASE64Intrinsics";

    private Base64IntrinsicGuard() { }

    /** True when this JVM would use the Base64 intrinsic. */
    static boolean intrinsicEnabled() {
        HotSpotDiagnosticMXBean bean =
                ManagementFactory.getPlatformMXBean(HotSpotDiagnosticMXBean.class);
        if (bean == null) {
            return false; // not HotSpot: no such intrinsic
        }
        try {
            return Boolean.parseBoolean(bean.getVMOption(OPTION).getValue());
        } catch (IllegalArgumentException e) {
            return false; // this VM has no such option, so no such intrinsic
        }
    }

    /** Exit with status 2 before touching any input if the intrinsic is on. */
    static void requireOff() {
        if (intrinsicEnabled()) {
            System.err.println("redtusk-worker: refusing to run with -XX:+" + OPTION
                    + " (CVE-2026-114938); launch the JVM with -XX:-" + OPTION);
            System.exit(2);
        }
    }
}
