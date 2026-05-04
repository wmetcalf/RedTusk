package io.redtusk.worker;

import java.util.logging.Logger;

/**
 * Drops CAP_CHECKPOINT_RESTORE from current capability sets and the bounding
 * set, then sets PR_SET_NO_NEW_PRIVS via JNI immediately after CRaC restore.
 * Steady-state cap-set after drop is identical to the default profile (--cap-drop=ALL).
 */
public final class CapDropper {
    private static final Logger LOG = Logger.getLogger(CapDropper.class.getName());
    private static final boolean NATIVE_AVAILABLE;
    private static final String NATIVE_LOAD_ERROR;

    static {
        boolean ok = false;
        String error = null;
        try {
            System.loadLibrary("cap_dropper");
            ok = true;
        } catch (UnsatisfiedLinkError e) {
            error = e.getMessage();
            LOG.warning("CapDropper: libcap_dropper.so not found: " + error);
        }
        NATIVE_AVAILABLE = ok;
        NATIVE_LOAD_ERROR = error;
    }

    private CapDropper() {}

    /** Drop CAP_CHECKPOINT_RESTORE, failing closed if the native helper is unavailable. */
    public static void dropCheckpointRestoreCapability() {
        if (!NATIVE_AVAILABLE) {
            throw new IllegalStateException(
                "capability dropper native library unavailable: " + NATIVE_LOAD_ERROR
            );
        }
        nativeDropCheckpointRestore();
        LOG.info("CapDropper: dropped CAP_CHECKPOINT_RESTORE and set PR_SET_NO_NEW_PRIVS");
    }

    private static native void nativeDropCheckpointRestore();
}
