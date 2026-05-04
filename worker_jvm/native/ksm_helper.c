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

#ifndef PR_SET_MEMORY_MERGE
#define PR_SET_MEMORY_MERGE 67
#endif

JNIEXPORT void JNICALL
Java_io_redtusk_worker_KsmHelper_nativeMarkHeapMergeable(JNIEnv *env, jclass clazz)
{
    prctl(PR_SET_MEMORY_MERGE, 1, 0, 0, 0);
}
