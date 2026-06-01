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
    __u32 mask = CAP_TO_MASK(cap);
    data[idx].effective &= ~mask;
    data[idx].permitted &= ~mask;
    data[idx].inheritable &= ~mask;
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

    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0) {
        perror("cap_dropper: prctl(PR_SET_NO_NEW_PRIVS)");
        (*env)->ThrowNew(env, (*env)->FindClass(env, "java/lang/IllegalStateException"),
                         "capability drop failed: no_new_privs");
    }
}
