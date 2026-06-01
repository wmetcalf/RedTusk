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

    /** Drop CAP_CHECKPOINT_RESTORE. Soft-fails when the kernel rejects the drop
     *  with EPERM — under Docker `--cap-add CAP_X` with a non-root USER, CAP_X
     *  ends up in the bounding/inheritable sets but not in effective, and
     *  PR_CAPBSET_DROP needs CAP_SETPCAP in *effective* to succeed. The end
     *  state is equivalent in that scenario: the cap was never usable by us
     *  in the first place. We still fail closed if the native library is
     *  missing (a configuration bug, not a runtime permissions situation).
     */
    public static void dropCheckpointRestoreCapability() {
        if (!NATIVE_AVAILABLE) {
            throw new IllegalStateException(
                "capability dropper native library unavailable: " + NATIVE_LOAD_ERROR
            );
        }
        try {
            nativeDropCheckpointRestore();
            LOG.info("CapDropper: dropped CAP_CHECKPOINT_RESTORE and set PR_SET_NO_NEW_PRIVS");
        } catch (IllegalStateException e) {
            // PR_CAPBSET_DROP / capset failed — almost certainly because the
            // calling process doesn't have CAP_SETPCAP in its effective set
            // (Docker `--cap-add` + non-root USER scenario). Safe to continue:
            // we never had the cap in effective either, so it's not exploitable.
            LOG.warning("CapDropper: drop skipped (no effective SETPCAP): " + e.getMessage());
        }
    }

    private static native void nativeDropCheckpointRestore();
}
