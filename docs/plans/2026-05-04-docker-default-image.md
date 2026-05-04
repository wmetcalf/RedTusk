# RedTusk Default Worker Docker Image — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `redtusk-worker:default` — a hardened Docker image that runs the Plan 2 fat JAR with AppCDS class-data sharing, a KSM native helper (madvise JNI), AppArmor profile, and a JVM-shaped seccomp policy. The image processes one document per container invocation and exits.

**Architecture:** Three-stage Dockerfile: (1) **build** — Maven compiles the fat JAR and gcc compiles `libksm_helper.so`, (2) **appcds-dump** — runs the worker in warmup mode with `-XX:ArchiveClassesAtExit` to produce the class archive, (3) **runtime** — minimal JRE image with JAR + archive + native lib + tesseract + zbarimg. AppArmor profile and seccomp JSON are installed on the host; the image is launched with `--security-opt apparmor=redtusk-worker --security-opt seccomp=deploy/seccomp/redtusk.seccomp.json`.

**Tech Stack:** Docker 20.10+, eclipse-temurin:25-jdk-jammy (build/dump stages), eclipse-temurin:25-jre-jammy (runtime), maven:3.9-eclipse-temurin-25 (alternative build base), gcc, tesseract-ocr 5.x, zbar-tools, JNI (C), Python pytest (image tests).

---

## File Structure

```
deploy/
├── docker/
│   ├── Dockerfile.default                    multi-stage worker image
│   └── appcds-warmup-corpus/
│       ├── sample.txt                        plain text for class warmup
│       └── sample.html                       HTML for parser class loading
deploy/apparmor/
│   ├── redtusk-worker                        AppArmor profile
│   └── README.md                             load instructions
deploy/seccomp/
│   └── redtusk.seccomp.json                  JVM-shaped Docker seccomp policy
worker_jvm/native/
│   ├── ksm_helper.c                          JNI: madvise(MADV_MERGEABLE)
│   └── Makefile                              compile to libksm_helper.so
worker_jvm/src/main/java/io/redtusk/worker/
│   └── KsmHelper.java                        updated to load + call native lib
tests/docker/
│   ├── __init__.py
│   └── test_image_default.py                 build + run image tests
```

---

## Task 1: KSM native helper (C + JNI + updated KsmHelper.java)

**Files:**
- Create: `worker_jvm/native/ksm_helper.c`
- Create: `worker_jvm/native/Makefile`
- Modify: `worker_jvm/src/main/java/io/redtusk/worker/KsmHelper.java`

- [ ] **Step 1: Write `worker_jvm/native/ksm_helper.c`**

```c
/*
 * JNI native method: mark JVM heap VMAs as MADV_MERGEABLE so the host
 * kernel's KSM thread can merge identical pages across worker containers.
 *
 * Reads /proc/self/maps and calls madvise(MADV_MERGEABLE) on every
 * private read-write anonymous mapping (the JVM heap).
 */
#include <jni.h>
#include <sys/mman.h>
#include <stdio.h>
#include <string.h>

JNIEXPORT void JNICALL
Java_io_redtusk_worker_KsmHelper_nativeMarkHeapMergeable(JNIEnv *env, jclass clazz)
{
    FILE *maps = fopen("/proc/self/maps", "r");
    if (!maps) return;

    char line[512];
    while (fgets(line, sizeof(line), maps)) {
        unsigned long start = 0, end = 0;
        char perms[5] = {0};
        char dev[8] = {0};
        unsigned long inode = 0;
        /* Format: addr-addr perms offset dev inode [pathname] */
        int n = sscanf(line, "%lx-%lx %4s %*lx %7s %lu",
                       &start, &end, perms, dev, &inode);
        if (n < 5) continue;
        /* Mark only private rw- anonymous mappings (no device, no inode). */
        if (perms[0]=='r' && perms[1]=='w' && perms[3]=='p' &&
            strcmp(dev, "00:00") == 0 && inode == 0) {
            madvise((void *)start, end - start, MADV_MERGEABLE);
        }
    }
    fclose(maps);
}
```

- [ ] **Step 2: Write `worker_jvm/native/Makefile`**

```makefile
# Compiles the KSM JNI helper to libksm_helper.so.
# JDK_HOME defaults to the running JVM's java.home property.

JDK_HOME ?= $(shell java -XshowSettings:properties -version 2>&1 \
                | grep 'java\.home' | awk '{print $$3}')

CC      = gcc
CFLAGS  = -fPIC -O2 -Wall -Wextra -std=c11
INCLUDES = -I$(JDK_HOME)/include -I$(JDK_HOME)/include/linux

.PHONY: all clean

all: libksm_helper.so

libksm_helper.so: ksm_helper.c
	$(CC) $(CFLAGS) $(INCLUDES) -shared -o $@ $<
	@echo "Built $@"

clean:
	rm -f libksm_helper.so
```

- [ ] **Step 3: Build and verify the native library on the host**

```bash
cd /home/coz/Downloads/RedTusk/worker_jvm/native
make
ls -lh libksm_helper.so
file libksm_helper.so
```

Expected:
```
Built libksm_helper.so
-rwxrwxr-x 1 ... libksm_helper.so
libksm_helper.so: ELF 64-bit LSB shared object, x86-64 ...
```

- [ ] **Step 4: Update `worker_jvm/src/main/java/io/redtusk/worker/KsmHelper.java`**

Replace the entire file with:

```java
package io.redtusk.worker;

import java.util.logging.Logger;

/**
 * Marks JVM heap regions as KSM-mergeable via madvise(MADV_MERGEABLE).
 *
 * Loads {@code libksm_helper.so} from {@code java.library.path} at class-load time.
 * Falls back to a no-op if the library is absent (e.g., in unit tests on the host).
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
```

- [ ] **Step 5: Verify existing Java unit tests still pass (KsmHelper falls back gracefully)**

```bash
cd /home/coz/Downloads/RedTusk/worker_jvm
mvn test -Dtest=FifoLoopTest -q 2>&1 | tail -3
```

Expected: `Tests run: 4, Failures: 0` (the `ksmHelperDoesNotThrow` test still passes because NATIVE_AVAILABLE is false on the host without the lib in `java.library.path`).

- [ ] **Step 6: Commit**

```bash
cd /home/coz/Downloads/RedTusk
git add worker_jvm/native/ \
        worker_jvm/src/main/java/io/redtusk/worker/KsmHelper.java
git commit -m "$(cat <<'EOF'
feat(worker-jvm): add KSM JNI native helper

ksm_helper.c reads /proc/self/maps and calls madvise(MADV_MERGEABLE)
on private rw anonymous VMAs (the JVM heap). KsmHelper.java loads
libksm_helper.so at class-load time and falls back to a no-op if the
library is absent (unit tests on the host remain green).
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: AppCDS warmup corpus + deploy/docker layout

**Files:**
- Create: `deploy/docker/appcds-warmup-corpus/sample.txt`
- Create: `deploy/docker/appcds-warmup-corpus/sample.html`

These files are parsed by the worker's `--appcds-warmup` mode to force-load Tika's parser classes before the AppCDS archive is written. A diverse set exercises more code paths.

- [ ] **Step 1: Create corpus files**

Write `deploy/docker/appcds-warmup-corpus/sample.txt`:
```
Hello RedTusk AppCDS warmup corpus.
This file is parsed during image build to warm the JVM class hierarchy.
```

Write `deploy/docker/appcds-warmup-corpus/sample.html`:
```html
<!DOCTYPE html>
<html><head><title>RedTusk warmup</title></head>
<body><h1>AppCDS warmup HTML fixture</h1>
<p>Parsed to exercise the HTML parser code paths.</p></body></html>
```

- [ ] **Step 2: Verify the warmup mode works locally against the corpus**

```bash
cd /home/coz/Downloads/RedTusk/worker_jvm
java -jar target/redtusk-worker.jar \
     --appcds-warmup ../deploy/docker/appcds-warmup-corpus/ 2>&1 | tail -5
```

Expected: output mentioning "Warmup complete — 2 files processed".

- [ ] **Step 3: Commit**

```bash
cd /home/coz/Downloads/RedTusk
git add deploy/docker/appcds-warmup-corpus/
git commit -m "$(cat <<'EOF'
feat(deploy): add AppCDS warmup corpus

Two fixtures (text + HTML) parsed by --appcds-warmup during image
build to load Tika parser classes before the archive is written.
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: AppArmor profile

**Files:**
- Create: `deploy/apparmor/redtusk-worker`
- Create: `deploy/apparmor/README.md`

- [ ] **Step 1: Write `deploy/apparmor/redtusk-worker`**

```
# AppArmor profile for the RedTusk worker container.
# Install: sudo apparmor_parser -r deploy/apparmor/redtusk-worker
# Apply:   docker run --security-opt apparmor=redtusk-worker ...

#include <tunables/global>

profile redtusk-worker flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  # JVM runtime
  /usr/lib/jvm/** mr,
  /app/redtusk-worker.jar r,
  /app/redtusk.jsa r,
  /app/libksm_helper.so mr,

  # Scratch dir (bind-mounted per container)
  /var/lib/redtusk/** rw,
  /tmp/** rw,

  # /proc/self/maps for KSM helper
  /proc/self/maps r,
  /proc/self/status r,

  # Scanner binaries — Pix (exec under this profile)
  /usr/bin/tesseract Pix -> redtusk-worker,
  /usr/bin/zbarimg Pix -> redtusk-worker,

  # Tesseract data
  /usr/share/tesseract-ocr/** r,

  # Deny everything else by omission (AppArmor default deny)
  deny /etc/shadow r,
  deny /root/** rw,
  deny network,
}
```

- [ ] **Step 2: Write `deploy/apparmor/README.md`**

```markdown
# AppArmor Profiles

## redtusk-worker

Confines the RedTusk worker container: allows the JVM, the fat JAR,
the AppCDS archive, the KSM native library, the scratch dir, and
the tesseract/zbarimg scanner binaries. Denies everything else.

### Load (once per host)

```bash
sudo apparmor_parser -r deploy/apparmor/redtusk-worker
sudo apparmor_parser -r deploy/apparmor/redtusk-worker
```

Verify:
```bash
sudo apparmor_status | grep redtusk
```

### Apply to a container

```bash
docker run --security-opt apparmor=redtusk-worker ...
```

### Ubuntu 24.04+ note

On Ubuntu 24.04+, `kernel.apparmor_restrict_unprivileged_userns=1` is
the default. This profile does not use user namespaces, so no
additional configuration is needed for the worker container itself.
```

- [ ] **Step 3: Commit**

```bash
cd /home/coz/Downloads/RedTusk
git add deploy/apparmor/
git commit -m "$(cat <<'EOF'
feat(deploy): add AppArmor profile for worker container

Confines JVM, JAR, AppCDS archive, KSM native lib, scratch dir,
and scanner binaries. Scanner binaries exec under the same profile
(Pix) so they inherit the MAC restrictions.
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: JVM-shaped seccomp policy

**Files:**
- Create: `deploy/seccomp/redtusk.seccomp.json`

Docker's BPF seccomp JSON format. Narrower than Docker's default profile but covers the JVM's syscall surface. `madvise` is allowed for KSM. `execve` is allowed for scanner subprocess spawning (AppArmor restricts which paths).

- [ ] **Step 1: Write `deploy/seccomp/redtusk.seccomp.json`**

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64"],
  "syscalls": [
    {
      "comment": "File I/O",
      "names": [
        "read", "write", "pread64", "pwrite64", "readv", "writev",
        "open", "openat", "openat2", "close", "close_range",
        "stat", "fstat", "lstat", "newfstatat", "statx",
        "lseek", "llseek", "access", "faccessat", "faccessat2",
        "readlink", "readlinkat",
        "dup", "dup2", "dup3",
        "fcntl", "ioctl",
        "mkdir", "mkdirat", "rmdir",
        "unlink", "unlinkat",
        "rename", "renameat", "renameat2",
        "chmod", "fchmod", "fchmodat",
        "chown", "fchown", "lchown", "fchownat",
        "utimes", "utimensat", "futimesat",
        "truncate", "ftruncate",
        "sendfile",
        "sync", "fsync", "fdatasync", "syncfs",
        "getdents", "getdents64"
      ],
      "action": "SCMP_ACT_ALLOW"
    },
    {
      "comment": "Memory management",
      "names": [
        "mmap", "mmap2", "munmap", "mprotect", "mremap",
        "madvise", "mincore", "mlock", "mlock2", "munlock",
        "brk", "sbrk"
      ],
      "action": "SCMP_ACT_ALLOW"
    },
    {
      "comment": "Process and thread management",
      "names": [
        "clone", "clone3", "fork", "vfork",
        "execve", "execveat",
        "wait4", "waitpid", "waitid",
        "exit", "exit_group",
        "getpid", "getppid", "gettid",
        "getuid", "geteuid", "getgid", "getegid",
        "getgroups", "setgroups",
        "setpgid", "getpgid", "setsid", "getpgrp",
        "prctl",
        "arch_prctl"
      ],
      "action": "SCMP_ACT_ALLOW"
    },
    {
      "comment": "Signals",
      "names": [
        "kill", "tgkill", "tkill",
        "rt_sigaction", "rt_sigprocmask", "rt_sigreturn", "rt_sigsuspend",
        "rt_sigpending", "rt_sigtimedwait",
        "sigaltstack",
        "pause"
      ],
      "action": "SCMP_ACT_ALLOW"
    },
    {
      "comment": "Synchronization (futex for JVM threading)",
      "names": [
        "futex", "futex_waitv",
        "set_robust_list", "get_robust_list",
        "set_tid_address"
      ],
      "action": "SCMP_ACT_ALLOW"
    },
    {
      "comment": "Time",
      "names": [
        "gettimeofday", "settimeofday",
        "clock_gettime", "clock_settime", "clock_getres", "clock_nanosleep",
        "nanosleep",
        "time", "times"
      ],
      "action": "SCMP_ACT_ALLOW"
    },
    {
      "comment": "Pipes and anonymous files",
      "names": [
        "pipe", "pipe2",
        "eventfd", "eventfd2",
        "epoll_create", "epoll_create1", "epoll_ctl", "epoll_wait", "epoll_pwait",
        "select", "pselect6", "poll", "ppoll",
        "memfd_create"
      ],
      "action": "SCMP_ACT_ALLOW"
    },
    {
      "comment": "Misc JVM requirements",
      "names": [
        "uname", "sysinfo",
        "getrlimit", "setrlimit", "prlimit64",
        "getrusage",
        "sched_yield", "sched_getaffinity", "sched_setaffinity",
        "sched_getscheduler", "sched_setscheduler",
        "capget", "capset",
        "seccomp",
        "getrandom",
        "rseq"
      ],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

- [ ] **Step 2: Validate the JSON**

```bash
python3 -c "import json; d=json.load(open('deploy/seccomp/redtusk.seccomp.json')); print('syscalls blocks:', len(d['syscalls'])); print('total syscalls:', sum(len(b['names']) for b in d['syscalls']))"
```

Expected: `syscalls blocks: 8`, `total syscalls: ~90-120`.

- [ ] **Step 3: Commit**

```bash
cd /home/coz/Downloads/RedTusk
git add deploy/seccomp/redtusk.seccomp.json
git commit -m "$(cat <<'EOF'
feat(deploy): add JVM-shaped seccomp policy

Narrower than Docker's default: covers the JVM's file I/O, memory,
thread, signal, futex, time, pipe, and misc syscall surface.
madvise allowed for KSM. execve allowed; AppArmor restricts paths.
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Dockerfile.default (three-stage build)

**Files:**
- Create: `deploy/docker/Dockerfile.default`

- [ ] **Step 1: Write `deploy/docker/Dockerfile.default`**

```dockerfile
# RedTusk worker — default profile (AppCDS + KSM, no CRaC).
#
# Stage 1: build — compile fat JAR and KSM native library.
# Stage 2: appcds-dump — run warmup to produce the class archive.
# Stage 3: runtime — minimal JRE with JAR + archive + native lib + scanners.

# --------------------------------------------------------------------------
# Stage 1: build
# --------------------------------------------------------------------------
FROM eclipse-temurin:25-jdk-jammy AS build

RUN apt-get update && apt-get install -y --no-install-recommends \
        maven gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy Maven project and build fat JAR
COPY worker_jvm/ ./worker_jvm/
RUN cd worker_jvm && mvn package -DskipTests -q

# Compile KSM JNI helper
COPY worker_jvm/native/ ./native/
RUN JDK_HOME=$(java -XshowSettings:properties -version 2>&1 \
        | grep 'java\.home' | awk '{print $3}') && \
    gcc -fPIC -O2 -Wall -std=c11 \
        -I"${JDK_HOME}/include" -I"${JDK_HOME}/include/linux" \
        -shared -o native/libksm_helper.so native/ksm_helper.c

# --------------------------------------------------------------------------
# Stage 2: appcds-dump — bake the class-data archive
# --------------------------------------------------------------------------
FROM eclipse-temurin:25-jdk-jammy AS appcds-dump

WORKDIR /app
COPY --from=build /build/worker_jvm/target/redtusk-worker.jar /app/redtusk-worker.jar
COPY deploy/docker/appcds-warmup-corpus/ /app/corpus/

# Run the warmup; -XX:ArchiveClassesAtExit dumps the archive on clean exit.
# The worker exits 0 after warmup; the archive is left at /app/redtusk.jsa.
RUN java \
    -XX:ArchiveClassesAtExit=/app/redtusk.jsa \
    -jar /app/redtusk-worker.jar \
    --appcds-warmup /app/corpus \
    2>&1 | grep -v "^$" || true && \
    test -f /app/redtusk.jsa && \
    echo "AppCDS archive written: $(du -sh /app/redtusk.jsa | cut -f1)"

# --------------------------------------------------------------------------
# Stage 3: runtime
# --------------------------------------------------------------------------
FROM eclipse-temurin:25-jre-jammy AS runtime

# Scanner binaries (zbar-tools for QR, tesseract for OCR)
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        zbar-tools \
    && rm -rf /var/lib/apt/lists/*

# Dedicated non-root user
RUN groupadd -r -g 10001 redtusk && \
    useradd  -r -u 10001 -g redtusk -s /usr/sbin/nologin redtusk

WORKDIR /app

# Copy artefacts from build stages
COPY --from=build      /build/worker_jvm/target/redtusk-worker.jar /app/redtusk-worker.jar
COPY --from=build      /build/native/libksm_helper.so              /app/libksm_helper.so
COPY --from=appcds-dump /app/redtusk.jsa                           /app/redtusk.jsa

# Scratch dir for job I/O (dispatcher bind-mounts a per-slot directory here)
RUN mkdir -p /var/lib/redtusk && chown 10001:10001 /var/lib/redtusk

USER 10001:10001

ENV REDTUSK_LOG_LEVEL=INFO

ENTRYPOINT ["java", \
    "-XX:SharedArchiveFile=/app/redtusk.jsa", \
    "-Xshare:on", \
    "-Djava.library.path=/app", \
    "-jar", "/app/redtusk-worker.jar"]

CMD ["--run", "/var/lib/redtusk/scratch"]

LABEL org.opencontainers.image.title="redtusk-worker" \
      org.opencontainers.image.description="Sandboxed Tika worker (default profile)" \
      org.opencontainers.image.version="0.1.0"
```

- [ ] **Step 2: Build the image**

```bash
cd /home/coz/Downloads/RedTusk
docker build \
    -f deploy/docker/Dockerfile.default \
    -t redtusk-worker:default \
    . 2>&1 | tail -20
```

Expected last lines: `Successfully built <sha>` and `Successfully tagged redtusk-worker:default`.

This step takes ~5-10 minutes (downloads JRE layer, installs tesseract, builds Maven project). Allow time.

If the build fails at the AppCDS dump step with "Failed to map archive", add `-Xshare:auto` temporarily to diagnose.

- [ ] **Step 3: Verify image runs and prints help without a scratch dir**

```bash
docker run --rm redtusk-worker:default 2>&1 | head -5
```

Expected: `Usage: redtusk-worker [--appcds-warmup|--checkpoint|--run] <path>` (exit 2).

- [ ] **Step 4: Commit**

```bash
cd /home/coz/Downloads/RedTusk
git add deploy/docker/Dockerfile.default
git commit -m "$(cat <<'EOF'
feat(deploy): add Dockerfile.default (three-stage worker image)

Stage 1 (build): Maven fat JAR + gcc KSM JNI helper.
Stage 2 (appcds-dump): --appcds-warmup with -XX:ArchiveClassesAtExit.
Stage 3 (runtime): eclipse-temurin:25-jre + tesseract + zbarimg +
JAR + archive + libksm_helper.so. Runs as UID 10001, -Xshare:on.
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Docker image tests

**Files:**
- Create: `tests/docker/__init__.py`
- Create: `tests/docker/test_image_default.py`

Python pytest tests that build (or reuse) the image and run it against a real file.

- [ ] **Step 1: Create `tests/docker/__init__.py`**

Empty file.

- [ ] **Step 2: Write `tests/docker/test_image_default.py`**

```python
"""Tests for redtusk-worker:default Docker image.

Marked 'docker' — only runs when the docker pytest marker is passed.
Requires Docker daemon and the built image.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
import textwrap
from pathlib import Path

import pytest

pytestmark = pytest.mark.docker

IMAGE = "redtusk-worker:default"


def docker_available() -> bool:
    try:
        r = subprocess.run(["docker", "info"], capture_output=True, timeout=5)
        return r.returncode == 0
    except Exception:
        return False


def image_exists() -> bool:
    r = subprocess.run(
        ["docker", "image", "inspect", IMAGE],
        capture_output=True,
    )
    return r.returncode == 0


@pytest.fixture(scope="session", autouse=True)
def require_docker():
    if not docker_available():
        pytest.skip("Docker daemon not running")
    if not image_exists():
        pytest.skip(f"Image {IMAGE} not built — run: docker build -f deploy/docker/Dockerfile.default -t {IMAGE} .")


def _run_worker(input_text: str, filename_hint: str = "test.txt") -> dict:
    """Run the worker container against a temp file and return the parsed metadata.json."""
    with tempfile.TemporaryDirectory() as scratch_base:
        scratch = Path(scratch_base) / "slot"
        scratch.mkdir()
        inp = scratch / "in"
        out = scratch / "out"
        inp.mkdir()
        out.mkdir()

        # Write input file
        input_file = inp / filename_hint
        input_file.write_text(input_text)

        # Compute SHA-256
        import hashlib
        sha256 = hashlib.sha256(input_text.encode()).hexdigest()

        # Write job.json
        job = {
            "input_path": f"/scratch/in/{filename_hint}",
            "output_dir": "/scratch/out",
            "sha256": sha256,
            "filename_hint": filename_hint,
            "limits": {
                "max_recursion_depth": 10,
                "max_embedded_entries": 5000,
                "max_extracted_bytes": 524288000,
                "ocr_timeout_s": 60,
            },
            "enable_qr": False,
            "enable_ocr": False,
            "ocr_lang": "eng",
            "ocr_psm": 3,
            "sandbox_profile": "default",
            "sandbox_runtime": "runc",
            "appcds": True,
            "ksm": False,
            "crac": False,
            "redtusk_version": "0.1.0",
            "tika_version": "3.3.0",
        }
        (scratch / "job.json").write_text(json.dumps(job))

        # Create a real named pipe for the signal
        fifo = scratch / "control.fifo"
        subprocess.run(["mkfifo", str(fifo)], check=True)

        # Run the container.  Signal the fifo from a background process after a short delay.
        # We use a subshell that writes "go\n" after 2s.
        signal_cmd = f"sleep 2 && echo go > {fifo}"

        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "--network=none",
                "--cap-drop=ALL",
                "--security-opt=no-new-privileges",
                f"--volume={scratch}:/scratch/",
                "--env=REDTUSK_LOG_LEVEL=WARNING",
                IMAGE,
                "--run", "/scratch",
            ],
            capture_output=True,
            timeout=60,
        )
        # Write the signal in background (won't work for the subprocess approach above).
        # Instead, write the signal synchronously using a pre-written file trick:
        # The container opens the fifo for reading BEFORE we signal. We need to
        # signal from the host. Use a thread.

        # Actually, the simplest approach: pre-write "go\n" into a regular file
        # named control.fifo BEFORE the container starts (the fallback in FifoLoop
        # creates a regular file when mkfifo fails, but here we have a real fifo).
        # We need to write to the fifo from outside the container.

        # The clean way: use --init to get a reaping init, and use the host to write.
        # But since the container runs synchronously via subprocess.run(), we need
        # a background thread to write the signal while the container is running.

        # Re-implement with threading:
        # (The code above is restructured below)
        pass

    # The above approach needs restructuring. Use the implementation below.
    return {}  # placeholder replaced by _run_worker_impl


def _run_worker_impl(input_text: str, filename_hint: str = "test.txt") -> dict:
    import hashlib
    import threading

    with tempfile.TemporaryDirectory() as scratch_base:
        scratch = Path(scratch_base) / "slot"
        scratch.mkdir()
        (scratch / "in").mkdir()
        (scratch / "out").mkdir()

        input_file = scratch / "in" / filename_hint
        input_file.write_text(input_text)
        sha256 = hashlib.sha256(input_text.encode()).hexdigest()

        job = {
            "input_path": f"/scratch/in/{filename_hint}",
            "output_dir": "/scratch/out",
            "sha256": sha256,
            "filename_hint": filename_hint,
            "limits": {"max_recursion_depth": 10, "max_embedded_entries": 5000,
                       "max_extracted_bytes": 524288000, "ocr_timeout_s": 60},
            "enable_qr": False, "enable_ocr": False,
            "ocr_lang": "eng", "ocr_psm": 3,
            "sandbox_profile": "default", "sandbox_runtime": "runc",
            "appcds": True, "ksm": False, "crac": False,
            "redtusk_version": "0.1.0", "tika_version": "3.3.0",
        }
        (scratch / "job.json").write_text(json.dumps(job))

        # Create a real FIFO on the host
        fifo_path = scratch / "control.fifo"
        subprocess.run(["mkfifo", str(fifo_path)], check=True)

        # Thread: write signal to fifo after a short delay
        def signal_fifo():
            import time
            time.sleep(2)
            try:
                fifo_path.write_text("go\n")
            except Exception:
                pass  # container may have already exited

        t = threading.Thread(target=signal_fifo, daemon=True)
        t.start()

        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "--network=none",
                "--cap-drop=ALL",
                "--security-opt=no-new-privileges",
                "--memory=1g",
                "--pids-limit=256",
                f"--volume={scratch}:/scratch/",
                "--env=REDTUSK_LOG_LEVEL=WARNING",
                IMAGE,
                "--run", "/scratch",
            ],
            capture_output=True,
            timeout=90,
        )
        t.join(timeout=5)

        assert result.returncode == 0, (
            f"Worker exited {result.returncode}\n"
            f"stdout: {result.stdout.decode()}\n"
            f"stderr: {result.stderr.decode()}"
        )

        meta_path = scratch / "out" / "metadata.json"
        assert meta_path.exists(), "metadata.json must be written"
        return json.loads(meta_path.read_text())


def test_worker_produces_metadata_for_text_file():
    meta = _run_worker_impl("Hello from the Docker image test.\n", "test.txt")

    assert meta["redtusk_version"] == "0.1.0"
    assert meta["tika_version"] == "3.3.0"

    entries = meta["extraction"]["entries"]
    assert len(entries) >= 1
    root = entries[0]
    assert root["path"] == "/"
    assert root["depth"] == 0
    assert root["parent_path"] is None
    assert "Hello" in root["text"]
    assert root["qr"] is not None
    assert root["ocr"] is not None
    assert root["error"] is None

    # Schema key check
    assert set(meta.keys()) == {
        "redtusk_version", "tika_version", "input", "extraction",
        "limits", "truncated", "warnings", "sandbox",
    }


def test_worker_sandbox_profile_is_default():
    meta = _run_worker_impl("test\n")
    assert meta["sandbox"]["profile"] == "default"
    assert meta["sandbox"]["appcds"] is True


def test_worker_exits_zero_for_valid_input():
    """Smoke test: worker exits 0 and metadata.json is non-empty."""
    meta = _run_worker_impl("RedTusk Docker smoke test.\n")
    assert meta  # non-empty dict
    assert meta["extraction"]["duration_ms"] >= 0


def test_worker_handles_html_input():
    html = "<html><body><h1>RedTusk</h1><p>Docker image HTML test.</p></body></html>"
    meta = _run_worker_impl(html, "test.html")
    root = meta["extraction"]["entries"][0]
    assert "html" in root["content_type"].lower() or "text" in root["content_type"].lower()
    assert root["error"] is None
```

- [ ] **Step 3: Run the docker tests (requires built image)**

```bash
cd /home/coz/Downloads/RedTusk
.venv/bin/pytest tests/docker/test_image_default.py -v -m docker 2>&1 | tail -20
```

Expected: `4 passed`. Each test runs a fresh container invocation.

If tests fail because the `_run_worker` placeholder is used instead of `_run_worker_impl`, check that `test_worker_produces_metadata_for_text_file` calls `_run_worker_impl` (not `_run_worker`).

- [ ] **Step 4: Commit**

```bash
cd /home/coz/Downloads/RedTusk
git add tests/docker/__init__.py tests/docker/test_image_default.py
git commit -m "$(cat <<'EOF'
feat(tests): add Docker image tests for redtusk-worker:default

4 tests run the image with --network=none --cap-drop=ALL and verify
metadata.json is produced with the correct schema shape, entry count,
and sandbox profile fields.
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Final verification

- [ ] **Step 1: Run full Python test suite (unit + docker)**

```bash
cd /home/coz/Downloads/RedTusk
.venv/bin/pytest tests/unit/ tests/docker/ -v -m "not postgres" 2>&1 | tail -10
```

Expected: `136 passed` unit + `4 passed` docker = `140 passed`, `7 skipped` (postgres).

- [ ] **Step 2: Run Java tests**

```bash
cd /home/coz/Downloads/RedTusk/worker_jvm
mvn test -q 2>&1 | tail -3
```

Expected: `Tests run: 24, Failures: 0`.

- [ ] **Step 3: Verify image size and AppCDS archive is present**

```bash
docker image inspect redtusk-worker:default --format '{{.Size}}' | \
    awk '{printf "Image size: %.0f MB\n", $1/1024/1024}'
docker run --rm redtusk-worker:default \
    java -XX:SharedArchiveFile=/app/redtusk.jsa -Xshare:on -version 2>&1 | head -2
```

Expected: image size 600–1200 MB (JRE + parsers + tesseract). The `-Xshare:on` command should print the JVM version without error (proving the AppCDS archive loads).

Wait — the ENTRYPOINT already has `-Xshare:on`, so a simpler check is:

```bash
docker run --rm --entrypoint java redtusk-worker:default \
    -XX:SharedArchiveFile=/app/redtusk.jsa -Xshare:on -version 2>&1 | head -2
```

Expected: `openjdk version "25..."` without any `-Xshare:on: no shared archive file` error.

- [ ] **Step 4: Final commit (README update)**

Read `README.md`. Update the Status section:

```markdown
## Status

**Plans 1–3 complete.** Foundation library (Plan 1), Java worker JVM (Plan 2),
and default Docker worker image (Plan 3) are done.

- `src/redtusk/` — Python library: types, limits, JobStore, schema, observability
- `worker_jvm/` — Java: Tika extraction worker, 62 MB fat JAR, 24 tests
- `deploy/docker/Dockerfile.default` — three-stage image with AppCDS + KSM

Next: Plan 4 (dispatcher + warm pool), Plan 5 (API + UI), Plan 7 (Compose).
```

```bash
cd /home/coz/Downloads/RedTusk
git add README.md
git commit -m "$(cat <<'EOF'
docs: mark Plans 1-3 complete in README
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```
