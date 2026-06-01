/*
 * JNI native method: enable KSM merging for all anonymous memory in this
 * process via prctl(PR_SET_MEMORY_MERGE, 1).
 *
 * PR_SET_MEMORY_MERGE (Linux 5.18+) marks all current and future anonymous
 * VMAs as KSM-eligible without requiring CAP_SYS_ADMIN or iterating /proc/maps.
 * Unlike madvise(MADV_MERGEABLE), it works from within unprivileged containers.
 */
#define _GNU_SOURCE
#include <jni.h>
#include <sys/prctl.h>
#include <stdio.h>
#include <errno.h>
#include <string.h>

#ifndef PR_SET_MEMORY_MERGE
#define PR_SET_MEMORY_MERGE 67
#endif

JNIEXPORT void JNICALL
Java_io_redtusk_worker_KsmHelper_nativeMarkHeapMergeable(JNIEnv *env, jclass clazz)
{
    (void) env;
    (void) clazz;
    /*
     * KSM marking is a best-effort memory-footprint optimization, not a
     * security control, so a failure here must stay non-fatal (don't throw).
     * But silently ignoring the return value hides real misconfiguration
     * (kernel < 5.18, PR_SET_MEMORY_MERGE unsupported, seccomp filter). Check
     * it and log to stderr so the failure is observable without changing KSM
     * semantics.
     */
    if (prctl(PR_SET_MEMORY_MERGE, 1, 0, 0, 0) != 0) {
        fprintf(stderr,
                "ksm_helper: prctl(PR_SET_MEMORY_MERGE, 1) failed: %s\n",
                strerror(errno));
    }
}
