#define _GNU_SOURCE
#include <jni.h>
#include <linux/capability.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>

#ifndef CAP_CHECKPOINT_RESTORE
#define CAP_CHECKPOINT_RESTORE 40
#endif

#ifndef CAP_TO_INDEX
#define CAP_TO_INDEX(x) ((x) >> 5)
#endif

#ifndef CAP_TO_MASK
#define CAP_TO_MASK(x) (1U << ((x) & 31))
#endif

/*
 * Drop CAP_CHECKPOINT_RESTORE and CAP_SETPCAP from the bounding set and from
 * the current effective/permitted/inheritable sets, then set PR_SET_NO_NEW_PRIVS
 * so the process can never re-acquire capabilities.
 * Called by CapDropper.java immediately after CRaC restore completes.
 */
static void clear_capability(struct __user_cap_data_struct *data, int cap) {
    int idx = CAP_TO_INDEX(cap);
    /* Bounds check: idx must index within the version-3 cap data array.
     * A bogus/large cap value would otherwise write out of bounds. */
    if (idx < 0 || idx >= _LINUX_CAPABILITY_U32S_3) {
        return;
    }
    __u32 mask = CAP_TO_MASK(cap);
    data[idx].effective &= ~mask;
    data[idx].permitted &= ~mask;
    data[idx].inheritable &= ~mask;
}

/* Return non-zero if `cap` is still set in any of the effective/permitted/
 * inheritable sets of `data`. Used to verify a drop actually took effect. */
static int capability_still_present(const struct __user_cap_data_struct *data, int cap) {
    int idx = CAP_TO_INDEX(cap);
    if (idx < 0 || idx >= _LINUX_CAPABILITY_U32S_3) {
        return 0;
    }
    __u32 mask = CAP_TO_MASK(cap);
    return (data[idx].effective & mask)
        || (data[idx].permitted & mask)
        || (data[idx].inheritable & mask);
}

/*
 * Returns JNI_TRUE if CAP_CHECKPOINT_RESTORE or CAP_SETPCAP is currently held
 * in ANY of the effective/permitted/inheritable sets, JNI_FALSE otherwise.
 * Lets the Java caller decide whether a failed drop is fatal (cap was held →
 * exposure, must fail closed) or a legitimate no-op (cap genuinely absent).
 * On capget error, returns JNI_TRUE (fail safe: assume the cap may be present).
 */
JNIEXPORT jboolean JNICALL
Java_io_redtusk_worker_CapDropper_nativeHasTargetCapability(JNIEnv *env, jclass clazz) {
    (void) env;
    (void) clazz;

    struct __user_cap_header_struct header;
    struct __user_cap_data_struct data[_LINUX_CAPABILITY_U32S_3];
    memset(&header, 0, sizeof(header));
    memset(&data, 0, sizeof(data));
    header.version = _LINUX_CAPABILITY_VERSION_3;
    header.pid = 0;

    if (syscall(SYS_capget, &header, &data) != 0) {
        perror("cap_dropper: capget (probe)");
        return JNI_TRUE;
    }
    if (capability_still_present(data, CAP_CHECKPOINT_RESTORE)
            || capability_still_present(data, CAP_SETPCAP)) {
        return JNI_TRUE;
    }
    return JNI_FALSE;
}

JNIEXPORT void JNICALL
Java_io_redtusk_worker_CapDropper_nativeDropCheckpointRestore(JNIEnv *env, jclass clazz) {
    (void) clazz;

    if (prctl(PR_CAPBSET_DROP, CAP_CHECKPOINT_RESTORE, 0, 0, 0) != 0) {
        perror("cap_dropper: prctl(PR_CAPBSET_DROP, CAP_CHECKPOINT_RESTORE)");
        (*env)->ThrowNew(env, (*env)->FindClass(env, "java/lang/IllegalStateException"),
                         "capability drop failed: checkpoint_restore bounding set");
        return;
    }

    if (prctl(PR_CAPBSET_DROP, CAP_SETPCAP, 0, 0, 0) != 0) {
        perror("cap_dropper: prctl(PR_CAPBSET_DROP, CAP_SETPCAP)");
        (*env)->ThrowNew(env, (*env)->FindClass(env, "java/lang/IllegalStateException"),
                         "capability drop failed: setpcap bounding set");
        return;
    }

    struct __user_cap_header_struct header;
    struct __user_cap_data_struct data[_LINUX_CAPABILITY_U32S_3];
    memset(&header, 0, sizeof(header));
    memset(&data, 0, sizeof(data));
    header.version = _LINUX_CAPABILITY_VERSION_3;
    header.pid = 0;

    if (syscall(SYS_capget, &header, &data) != 0) {
        perror("cap_dropper: capget");
        (*env)->ThrowNew(env, (*env)->FindClass(env, "java/lang/IllegalStateException"),
                         "capability drop failed: capget");
        return;
    }

    clear_capability(data, CAP_CHECKPOINT_RESTORE);
    clear_capability(data, CAP_SETPCAP);

    if (syscall(SYS_capset, &header, &data) != 0) {
        perror("cap_dropper: capset");
        (*env)->ThrowNew(env, (*env)->FindClass(env, "java/lang/IllegalStateException"),
                         "capability drop failed: capset");
        return;
    }

    /* Verify the drop actually took effect: re-read the live cap sets and
     * confirm the targeted capabilities are gone from effective/permitted/
     * inheritable. capset can report success yet leave a cap present in some
     * edge cases (e.g. kernels that silently preserve bits, or a racing
     * thread). Fail closed if so — the README guarantees a verified drop. */
    struct __user_cap_data_struct verify[_LINUX_CAPABILITY_U32S_3];
    memset(&verify, 0, sizeof(verify));
    if (syscall(SYS_capget, &header, &verify) != 0) {
        perror("cap_dropper: capget (verify)");
        (*env)->ThrowNew(env, (*env)->FindClass(env, "java/lang/IllegalStateException"),
                         "capability drop failed: capget verify");
        return;
    }
    if (capability_still_present(verify, CAP_CHECKPOINT_RESTORE)
            || capability_still_present(verify, CAP_SETPCAP)) {
        fprintf(stderr, "cap_dropper: targeted capability still present after capset\n");
        (*env)->ThrowNew(env, (*env)->FindClass(env, "java/lang/IllegalStateException"),
                         "capability drop failed: verification found cap still set");
        return;
    }

    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0) {
        perror("cap_dropper: prctl(PR_SET_NO_NEW_PRIVS)");
        (*env)->ThrowNew(env, (*env)->FindClass(env, "java/lang/IllegalStateException"),
                         "capability drop failed: no_new_privs");
    }
}
