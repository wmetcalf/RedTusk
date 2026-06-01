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

    /** Drop CAP_CHECKPOINT_RESTORE (and CAP_SETPCAP). Fails CLOSED when the drop
     *  fails while the capability was actually held.
     *
     *  <p>Two distinct failure shapes:</p>
     *  <ul>
     *    <li><b>Cap genuinely absent</b> — e.g. the worker already runs without
     *        CAP_CHECKPOINT_RESTORE / CAP_SETPCAP in any set. PR_CAPBSET_DROP can
     *        still EPERM (it needs CAP_SETPCAP in *effective*), but there is no
     *        exposure because the cap was never usable. This is a legitimate
     *        no-op: log and continue.</li>
     *    <li><b>Cap held but drop failed</b> — the worker holds the cap and we
     *        could not remove it. This is a real privilege-exposure and MUST
     *        fail closed: re-throw / exit non-zero, never silently continue.</li>
     *  </ul>
     *
     *  <p>We still fail closed if the native library is missing (a configuration
     *  bug, not a runtime permissions situation).</p>
     */
    public static void dropCheckpointRestoreCapability() {
        if (!NATIVE_AVAILABLE) {
            throw new IllegalStateException(
                "capability dropper native library unavailable: " + NATIVE_LOAD_ERROR
            );
        }
        // Probe BEFORE attempting the drop so we can classify a subsequent
        // failure as "cap was held" (fatal) vs "cap never held" (soft no-op).
        boolean capHeldBefore = nativeHasTargetCapability();
        try {
            nativeDropCheckpointRestore();
            LOG.info("CapDropper: dropped CAP_CHECKPOINT_RESTORE/CAP_SETPCAP and set PR_SET_NO_NEW_PRIVS");
        } catch (IllegalStateException e) {
            if (capHeldBefore) {
                // The cap was actually held and we failed to drop or verify it —
                // a genuine privilege exposure. Fail closed.
                LOG.severe("CapDropper: FATAL — capability was held but drop/verify failed: "
                        + e.getMessage());
                throw e;
            }
            // Cap was never held: PR_CAPBSET_DROP needing effective CAP_SETPCAP
            // (Docker `--cap-add` + non-root USER) is the benign case. Continue.
            LOG.warning("CapDropper: drop skipped (capability not held; no exposure): "
                    + e.getMessage());
        }
    }

    private static native void nativeDropCheckpointRestore();

    /** True if CAP_CHECKPOINT_RESTORE or CAP_SETPCAP is currently held in any
     *  capability set. Used to decide whether a failed drop is fatal. */
    private static native boolean nativeHasTargetCapability();
}
