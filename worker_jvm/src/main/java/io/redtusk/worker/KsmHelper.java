package io.redtusk.worker;

import java.util.logging.Logger;

/**
 * Marks JVM heap regions as KSM-mergeable via madvise(MADV_MERGEABLE).
 *
 * Loads {@code libksm_helper.so} from {@code java.library.path} at class-load time.
 * Falls back to a no-op if the library is absent (unit tests on the host).
 */
public final class KsmHelper {

    private static final Logger LOG = Logger.getLogger(KsmHelper.class.getName());
    private static final boolean NATIVE_AVAILABLE;

    static {
        boolean available = false;
        try {
            System.loadLibrary("ksm_helper");
            available = true;
            LOG.fine("KsmHelper: native library loaded");
        } catch (UnsatisfiedLinkError e) {
            LOG.fine("KsmHelper: native library not available — " + e.getMessage());
        }
        NATIVE_AVAILABLE = available;
    }

    private KsmHelper() {}

    private static native void nativeMarkHeapMergeable();

    /**
     * Marks JVM heap VMAs as MADV_MERGEABLE via the native helper.
     * No-op if {@code libksm_helper.so} could not be loaded.
     */
    public static void markHeapMergeable() {
        if (NATIVE_AVAILABLE) {
            nativeMarkHeapMergeable();
            LOG.fine("KsmHelper: marked heap as KSM-mergeable");
        }
    }
}
