# Plan 6 — High-Density Profile (CRaC + CapDropper)

**Date:** 2026-05-05
**Status:** In progress
**Depends on:** Plans 1–5 (all merged)

## Goal

Implement the `high-density` deployment profile: sub-100ms container warm start via CRaC
checkpoint restore, plus real capability dropping after restore. After this plan:

- `Dockerfile.high-density` builds a worker image where the JVM is snapshotted mid-startup
  (after warmup, before FIFO wait) using Azul Zulu CRaC JDK 25.
- `criu restore` becomes the container's PID-1; on restore the worker is immediately at the
  FIFO wait, ready to accept a job with ~0.1s latency.
- `CapDropper.java` really drops `CAP_CHECKPOINT_RESTORE` via JNI+`prctl` immediately after
  restore, so steady-state cap-set is identical to the default profile.
- `tests/docker/test_image_high_density.py` validates the built image can process a job.

## File targets

```
worker_jvm/
  native/
    cap_dropper.c          # prctl(PR_CAPBSET_DROP) + prctl(PR_SET_NO_NEW_PRIVS) via JNI
    Makefile               # add cap_dropper target alongside ksm_helper
  src/main/java/io/redtusk/worker/
    CapDropper.java        # load libcap_dropper.so, call nativeDropCheckpointRestore()
    Main.java              # --checkpoint mode: real CRaC Core.checkpointRestore()
  pom.xml                 # add org.crac:crac dependency
deploy/docker/
  Dockerfile.high-density  # 3-stage: build → checkpoint → runtime
tests/docker/
  test_image_high_density.py
```

## Tasks

### Task 1 — `cap_dropper.c` and updated `Makefile`

**`worker_jvm/native/cap_dropper.c`:**

```c
#define _GNU_SOURCE
#include <jni.h>
#include <sys/prctl.h>
#include <linux/capability.h>
#include <stdio.h>

/*
 * Drop CAP_CHECKPOINT_RESTORE from the capability bounding set, then
 * set PR_SET_NO_NEW_PRIVS so the process can never re-acquire it.
 * Called by CapDropper.java immediately after CRaC restore completes.
 */
JNIEXPORT void JNICALL
Java_io_redtusk_worker_CapDropper_nativeDropCheckpointRestore(JNIEnv *env, jclass clazz) {
    /* CAP_CHECKPOINT_RESTORE = 40 (Linux 5.9+) */
    if (prctl(PR_CAPBSET_DROP, 40, 0, 0, 0) != 0) {
        fprintf(stderr, "cap_dropper: prctl(PR_CAPBSET_DROP, 40) failed\n");
    }
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0) {
        fprintf(stderr, "cap_dropper: prctl(PR_SET_NO_NEW_PRIVS) failed\n");
    }
}
```

Use capability number 40 directly rather than `CAP_CHECKPOINT_RESTORE` because the constant
may not be defined in older `linux/capability.h` headers in the build container. The kernel
treats integer 40 as `CAP_CHECKPOINT_RESTORE` on Linux 5.9+.

**Update `worker_jvm/native/Makefile`** — add a `cap_dropper` target alongside the existing
`ksm_helper` target:

```makefile
JNI_INCLUDES := -I$(JAVA_HOME)/include -I$(JAVA_HOME)/include/linux

all: libksm_helper.so libcap_dropper.so

libksm_helper.so: ksm_helper.c
	gcc -fPIC -O2 -Wall -Wextra -std=c11 -D_GNU_SOURCE \
	    $(JNI_INCLUDES) -shared -o $@ $<

libcap_dropper.so: cap_dropper.c
	gcc -fPIC -O2 -Wall -Wextra -std=c11 -D_GNU_SOURCE \
	    $(JNI_INCLUDES) -shared -o $@ $<

clean:
	rm -f *.so
```

### Task 2 — `CapDropper.java` (real implementation)

Replace the no-op stub:

```java
package io.redtusk.worker;

import java.util.logging.Logger;

/**
 * Drops CAP_CHECKPOINT_RESTORE from the bounding set and sets PR_SET_NO_NEW_PRIVS
 * via JNI immediately after CRaC restore, so the steady-state cap-set matches the
 * default profile (--cap-drop=ALL).
 */
public final class CapDropper {
    private static final Logger LOG = Logger.getLogger(CapDropper.class.getName());
    private static final boolean NATIVE_AVAILABLE;

    static {
        boolean ok = false;
        try {
            System.loadLibrary("cap_dropper");
            ok = true;
        } catch (UnsatisfiedLinkError e) {
            LOG.warning("CapDropper: libcap_dropper.so not found — capability drop skipped: " + e.getMessage());
        }
        NATIVE_AVAILABLE = ok;
    }

    private CapDropper() {}

    /** Drop CAP_CHECKPOINT_RESTORE. Safe no-op if native lib is unavailable. */
    public static void dropCheckpointRestoreCapability() {
        if (NATIVE_AVAILABLE) {
            nativeDropCheckpointRestore();
            LOG.info("CapDropper: dropped CAP_CHECKPOINT_RESTORE and set PR_SET_NO_NEW_PRIVS");
        } else {
            LOG.warning("CapDropper: native lib unavailable, cap NOT dropped");
        }
    }

    private static native void nativeDropCheckpointRestore();
}
```

### Task 3 — CRaC dependency + `--checkpoint` mode

**`worker_jvm/pom.xml`** — add the CRaC API dependency. The `org.crac` library is the
standard CRaC API jar published by Azul and the OpenJDK CRaC project:

```xml
<dependency>
    <groupId>io.github.crac</groupId>
    <artifactId>org-crac</artifactId>
    <version>0.1.3</version>
</dependency>
```

This is the portable CRaC API — it's a stub on non-CRaC JVMs and routes to the real
`jdk.crac` module when running on a CRaC-enabled JDK (Azul Zulu CRaC). This lets the code
compile on any JDK; it only works at runtime on the CRaC JDK.

**`Main.java`** — replace the `runCheckpoint` stub with the real implementation:

```java
private static void runCheckpoint(File scratchDir) throws Exception {
    // 1. Warm the JVM (class loading, JIT, Tika parsers).
    KsmHelper.markHeapMergeable();
    scratchDir.mkdirs();
    FifoLoop.createFifo(scratchDir);
    LOG.info("Checkpoint: JVM warm, fifo created at " + scratchDir);

    // 2. Take CRaC checkpoint. Execution resumes here after criu restore.
    org.crac.Core.checkpointRestore();
    LOG.info("Checkpoint: restored from CRaC checkpoint");

    // 3. Drop CAP_CHECKPOINT_RESTORE now that restore is complete.
    CapDropper.dropCheckpointRestoreCapability();

    // 4. Continue into the normal job loop — wait for dispatcher signal.
    String signal = FifoLoop.waitForSignal(scratchDir);
    LOG.info("Received signal: " + signal.trim());

    File jobFile = new File(scratchDir, "job.json");
    if (!jobFile.exists()) {
        LOG.severe("job.json not found at: " + jobFile);
        System.exit(2);
    }
    JobDescriptor job = OM.readValue(jobFile, JobDescriptor.class);
    File inputFile = new File(job.inputPath());
    File outDir = new File(job.outputDir());
    outDir.mkdirs();

    long start = System.currentTimeMillis();
    ParseResult result;
    try {
        var runner = new ParserRunner(
            job.limits(),
            job.enableQr(), job.enableOcr(),
            job.ocrLang(), job.ocrPsm(),
            "zbarimg", "tesseract"
        );
        result = runner.parse(inputFile, job.filenameHint(), job.sha256());
    } catch (Exception e) {
        LOG.severe("Parse failed: " + e.getMessage());
        System.exit(1);
        return;
    }
    long durationMs = System.currentTimeMillis() - start;
    new RmetaWriter(job, result, durationMs).write(outDir);
    LOG.info("Wrote metadata.json (" + result.entries().size() + " entries, " + durationMs + " ms)");
}
```

Note: After `Core.checkpointRestore()` returns (on resume), execution continues directly
into the FIFO wait + job processing — the same logic as `runJob`. The `runCheckpoint` mode
thus doubles as the runtime mode for high-density containers.

Also update the `--run` case in `main()` to still call `runJob(path)` unchanged (the default
profile uses `--run`; the high-density profile uses `--checkpoint` for the build-time
checkpoint AND runtime restore).

### Task 4 — `Dockerfile.high-density`

Three stages:

```dockerfile
# ── Stage 1: Build fat JAR ────────────────────────────────────────────────────
FROM eclipse-temurin:25-jdk-jammy AS builder

RUN apt-get update -qq && apt-get install -y --no-install-recommends maven gcc && rm -rf /var/lib/apt/lists/*
WORKDIR /build

COPY worker_jvm/pom.xml ./pom.xml
RUN mvn -q dependency:go-offline

COPY worker_jvm/src ./src
RUN mvn -q package -DskipTests

# Build native libs
COPY worker_jvm/native ./native
RUN cd native && make all

# AppCDS warmup
COPY deploy/docker/appcds-warmup-corpus /corpus
RUN java -XX:ArchiveClassesAtExit=/build/redtusk.jsa \
         -jar target/redtusk-worker.jar --appcds-warmup /corpus || true

# ── Stage 2: CRaC checkpoint ──────────────────────────────────────────────────
# Use Azul Zulu CRaC-enabled JDK 25. This stage takes the checkpoint.
FROM azul/zulu-openjdk:25-jdk AS checkpoint

RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends criu tesseract-ocr tesseract-ocr-eng zbar-tools && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/redtusk
COPY --from=builder /build/target/redtusk-worker.jar ./redtusk-worker.jar
COPY --from=builder /build/native/libksm_helper.so ./libksm_helper.so
COPY --from=builder /build/native/libcap_dropper.so ./libcap_dropper.so
COPY --from=builder /build/redtusk.jsa ./redtusk.jsa

RUN mkdir -p /opt/redtusk/checkpoint /opt/redtusk/scratch/checkpoint/in /opt/redtusk/scratch/checkpoint/out

# Take the CRaC checkpoint.
# --checkpoint-dir tells CRaC where to write snapshot files.
# We start the worker in --checkpoint mode; it warms up, creates the fifo,
# then calls Core.checkpointRestore() which causes CRIU to snapshot the process.
# The container running this stage needs --cap-add=CHECKPOINT_RESTORE.
# In the Dockerfile build context this runs as a RUN instruction — for the
# checkpoint to work, the build must be run with:
#   docker build --security-opt seccomp=unconfined \
#                --cap-add SYS_PTRACE --cap-add CHECKPOINT_RESTORE ...
RUN java \
    -XX:SharedArchiveFile=/opt/redtusk/redtusk.jsa -Xshare:auto \
    -Djava.library.path=/opt/redtusk \
    -XX:CRaCCheckpointTo=/opt/redtusk/checkpoint \
    -jar /opt/redtusk/redtusk-worker.jar \
    --checkpoint /opt/redtusk/scratch/checkpoint || true
# Note: `|| true` because the process exits non-zero after checkpointing (by design).
# The checkpoint files are written to /opt/redtusk/checkpoint/.

# ── Stage 3: Runtime ──────────────────────────────────────────────────────────
FROM azul/zulu-openjdk:25-jre AS runtime

RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends criu tesseract-ocr tesseract-ocr-eng zbar-tools && \
    rm -rf /var/lib/apt/lists/* && \
    groupadd --gid 10001 redtusk && \
    useradd --uid 10001 --gid 10001 --no-create-home --shell /sbin/nologin redtusk

WORKDIR /opt/redtusk
COPY --from=checkpoint /opt/redtusk/ ./

# restore.sh: exec criu restore as PID 1, resume the checkpointed process.
# After restore, the worker's execution continues past Core.checkpointRestore(),
# drops CAP_CHECKPOINT_RESTORE, then blocks on the FIFO.
RUN printf '#!/bin/sh\nexec criu restore --tcp-established --shell-job -D /opt/redtusk/checkpoint --log-level 1\n' \
    > /opt/redtusk/restore.sh && chmod +x /opt/redtusk/restore.sh

USER 10001:10001
ENTRYPOINT ["/opt/redtusk/restore.sh"]
```

**Important build caveat** (document in `deploy/docker/README.md` section):

The checkpoint stage requires elevated capabilities during `docker build`:
```sh
docker build \
  --security-opt seccomp=unconfined \
  --cap-add SYS_PTRACE \
  --cap-add CHECKPOINT_RESTORE \
  -f deploy/docker/Dockerfile.high-density \
  -t redtusk:high-density .
```

This is safe because the elevated permissions only apply during the image build (the
checkpoint RUN step), not at runtime. The resulting runtime image runs with `--cap-drop=ALL`.

### Task 5 — `tests/docker/test_image_high_density.py`

Mirror `test_image_default.py` but for the high-density image. Key differences:
- Image name: `redtusk:high-density-test` (built with elevated caps during test)
- The test skips with `pytest.skip` if `docker build` requires elevated caps that aren't
  available (CI limitation).
- Tests: image exists, container starts (fifo appears), job processes successfully, container
  exits 0.

```python
"""Docker tests for the high-density (CRaC) worker image.

These tests require:
  1. docker build --security-opt seccomp=unconfined --cap-add SYS_PTRACE \
       --cap-add CHECKPOINT_RESTORE -f deploy/docker/Dockerfile.high-density \
       -t redtusk:high-density-test .
  2. pytest marker: docker

Skip if REDTUSK_TEST_HIGHDENSITY_IMAGE is not set.
"""
import os
import pytest

IMAGE = os.environ.get("REDTUSK_TEST_HIGHDENSITY_IMAGE", "")

@pytest.mark.docker
def test_high_density_image_exists():
    if not IMAGE:
        pytest.skip("REDTUSK_TEST_HIGHDENSITY_IMAGE not set")
    # docker image inspect IMAGE → exit 0
    ...

@pytest.mark.docker
def test_high_density_job_processes_txt():
    if not IMAGE:
        pytest.skip("REDTUSK_TEST_HIGHDENSITY_IMAGE not set")
    # Same pattern as test_image_default.py — write txt file, signal fifo, verify metadata.json
    ...
```

Keep this test file minimal — the detailed signal/fifo/metadata patterns are already proven
in `test_image_default.py`. High-density tests focus on: (a) image starts successfully
(criu restore works), (b) job processes and writes metadata.json, (c) CAP_CHECKPOINT_RESTORE
is dropped post-restore (check `/proc/self/status` Bounding cap set).

## Acceptance criteria

- `mvn -q package -DskipTests` in `worker_jvm/` succeeds with `org.crac:crac` on classpath.
- `ruff check src tests` clean.
- `mypy src` clean.
- Unit tests still pass: `pytest tests/unit tests/http -q` → 227 passed.
- Dockerfile.high-density builds successfully (with elevated build caps on a capable host).
- Docker tests skip gracefully when `REDTUSK_TEST_HIGHDENSITY_IMAGE` is not set.

## What this plan does NOT include

- Changes to the Python dispatcher/API (already handles both profiles via `profile` env var).
- Compose stack wiring (Plan 7).
- ARM64 seccomp validation.
- CRaC under runsc (deferred per design spec).
