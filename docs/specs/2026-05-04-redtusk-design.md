# RedTusk Design Spec

**Date:** 2026-05-04
**Status:** Draft (pending implementation plan)
**Author:** Will Metcalf

## Summary

RedTusk is a sandboxed Apache Tika service for extracting text, metadata, and embedded resources from arbitrary documents — both legitimate customer content and adversarial samples. It exposes a wire-compatible subset of `tika-server`'s HTTP API so existing clients can repoint without code changes, plus a ClippyShot-style asynchronous job API and UI for batch and adversarial workflows.

The core architectural piece is a **warm pool of one-shot, hardened worker containers**: each job runs in a freshly-spawned container that is destroyed afterward, but the JVM startup cost is paid in the background by pre-spawning warm slots. Memory dedup (AppCDS + KSM, optionally CRaC) keeps the pool's idle RAM footprint manageable.

RedTusk is a separate project from ClippyShot. It borrows ClippyShot's sandbox-hardening playbook, dispatcher topology, JobStore protocol, and UI patterns as design references, but does not depend on ClippyShot at runtime or build time.

## Goals

1. Sandbox Apache Tika such that a malicious document cannot escape the worker container, contaminate sibling jobs, or affect the host.
2. Be a drop-in replacement for `tika-server` for the common HTTP endpoints (`/tika`, `/rmeta`, `/meta`, `/detect`, `/unpack`, `/version`, `/mime-types`, `/parsers`).
3. Provide an asynchronous job lifecycle (submit → poll → fetch artifacts) with TTL-based retention and a single-page UI showing recent submissions, mirroring ClippyShot's UX.
4. Keep per-slot warm-pool RAM low enough that a default deployment can sustain a pool of 10+ slots on a modest host.
5. Run cleanly on managed AWS services (Fargate, EKS) using the default profile, and on self-managed EC2 with the high-density profile.
6. Identify QR codes and OCR'd text as discrete, named signals on extracted image entries (not blended into Tika's text output).

## Non-goals

1. **PDF page rasterization.** Rendering a PDF page to PNG is ClippyShot's job. RedTusk only scans images that Tika natively extracts (which already covers most adversarial cases — embedded raster images, image-only scan PDFs).
2. **Per-tenant authentication or RBAC.** v1 is single-tenant; access control is a network-layer concern (reverse proxy, VPN, security group). Multi-tenant auth is a possible v2.
3. **Format allow-listing.** Tika is the dispatch table; we sandbox the process, not the parsers. Anything Tika has a parser for is accepted.
4. **Replacing ClippyShot.** RedTusk and ClippyShot are composable: rasterize-then-extract pipelines call ClippyShot first, then post the page PNGs to RedTusk.

## Architecture

Three-tier deployment, mirroring ClippyShot's split:

```
+--------+        +-----------+        +----------------+
| Client | <----> | API tier  | <----> | Dispatcher +   |
+--------+        | (FastAPI) |        | warm pool      |
                  +-----------+        +-------+--------+
                       |                       |
                       v                       v
                  +-----------+        +----------------+
                  | JobStore  |        | Worker         |
                  | (SQL)     |        | container      |
                  +-----------+        | (per-job, RM'd)|
                                       +----------------+
```

- **API tier:** FastAPI. Serves the tika-compat synchronous endpoints, the RedTusk-native asynchronous `/v1/jobs` endpoints, and the UI. No Docker socket. Talks to JobStore for async records and to the dispatcher (in-process, asyncio) for warm-pool slot allocation.
- **Dispatcher:** Owns the warm pool. Spawns, signals, reaps, and replaces worker containers. Has Docker socket access. Validates `metadata.json` produced by every worker before trusting it.
- **Worker container:** Hardened single-job container with a warm JVM running RedTusk's custom Tika entrypoint. Receives one job, exits, is removed.

The API tier and the dispatcher live in the same Python process for the default deployment but are separable (each module is process-agnostic and could be split into its own container later).

### Two deployment profiles

RedTusk ships two worker image variants. Both share the same dispatcher, JobStore, API tier, and worker entrypoint Java code. The difference is how the JVM is brought up.

| Profile | JVM boot | Caps granted | Memory dedup | Host targets |
|---|---|---|---|---|
| `default` | `java` cold start, AppCDS-mapped | none (`--cap-drop=ALL`) | AppCDS + KSM | Fargate, EKS, runc, runsc, EC2, anywhere |
| `high-density` | `criu restore` from baked checkpoint | `CHECKPOINT_RESTORE` (dropped post-restore) | AppCDS + KSM + CRaC | Self-managed EC2 + runc only |

The dispatcher is profile-agnostic — both variants present the same "warm container blocked on a fifo" interface. Operators choose the profile at deploy time via `REDTUSK_PROFILE={default,high-density}`.

## Repo layout

```
RedTusk/
├── src/redtusk/
│   ├── api.py                  # FastAPI: tika-compat + /v1/jobs + UI
│   ├── dispatcher.py           # Job claim loop, drives the pool
│   ├── pool.py                 # Warm pool data structure + state machine
│   ├── worker_runtime.py       # Per-profile container spawn/signal/reap
│   ├── translation.py          # rmeta -> /tika, /meta, /detect, /unpack
│   ├── jobs/
│   │   ├── base.py             # JobStore protocol
│   │   ├── memory.py
│   │   ├── sql_store.py        # sqlite + postgres
│   │   └── retention.py        # TTL sweeper
│   ├── sandbox/
│   │   ├── container.py        # Hardening flags by profile
│   │   └── detect.py           # runsc/runc auto-detection
│   ├── runtime/
│   │   ├── docker_runtime.py
│   │   └── host_limits.py
│   ├── observability/
│   │   ├── logging.py          # structlog setup
│   │   └── metrics.py          # prometheus_client
│   ├── limits.py               # Limits.from_env() for all REDTUSK_* vars
│   ├── errors.py
│   ├── types.py                # ExtractResult, EmbeddedEntry, JobRecord
│   ├── cli.py                  # serve, dispatcher, worker, selftest, version
│   └── static/                 # UI HTML/CSS/JS
├── worker_jvm/
│   ├── pom.xml                 # Maven build
│   ├── src/main/java/io/redtusk/worker/
│   │   ├── Main.java           # Entrypoint: warmup | checkpoint | run modes
│   │   ├── ParserRunner.java   # Drives RecursiveParserWrapper
│   │   ├── ScannerRunner.java  # ProcessBuilder for tesseract + zbarimg
│   │   ├── FifoLoop.java       # Block on fifo, read job descriptor
│   │   ├── RmetaWriter.java    # Serialize to RedTusk schema
│   │   ├── KsmHelper.java      # JNI to madvise(MADV_MERGEABLE)
│   │   └── CapDropper.java     # prctl(PR_CAPBSET_DROP) post-restore
│   └── src/test/java/...       # Maven Surefire unit tests
├── deploy/
│   ├── docker/
│   │   ├── Dockerfile.default          # AppCDS + KSM
│   │   ├── Dockerfile.high-density     # + CRaC checkpoint baked in
│   │   ├── docker-compose.yml
│   │   └── redtusk-compose             # GID-detect wrapper
│   ├── apparmor/
│   │   ├── redtusk-worker
│   │   └── README.md
│   ├── seccomp/
│   │   └── redtusk.seccomp.policy
│   └── ksm/
│       ├── enable-ksm.sh
│       ├── redtusk-ksm.service
│       └── README.md
├── tests/
│   ├── unit/
│   ├── http/
│   ├── jvm/                            # Java unit tests for worker
│   ├── integration/
│   ├── docker/
│   └── fixtures/
│       ├── safe/
│       ├── adversarial/
│       └── appcds-warmup-corpus/
├── docs/
│   └── specs/
└── pyproject.toml
```

## API surface

### Tika-compat (synchronous)

Mirrors `tika-server`'s wire format so existing clients can repoint:

| Method | Path | Returns | Behavior |
|---|---|---|---|
| `PUT` | `/tika` | `text/plain` | Extract text only (root entry) |
| `PUT` | `/tika/form` | `text/plain` | Multipart form variant |
| `PUT` | `/rmeta` | `application/json` | Recursive metadata + text (default) |
| `PUT` | `/rmeta/text` | `application/json` | Text-form recursive |
| `PUT` | `/rmeta/html` | `application/json` | HTML-form recursive |
| `PUT` | `/rmeta/xml` | `application/json` | XML-form recursive |
| `PUT` | `/meta` | `application/json` | Root entry metadata only |
| `PUT` | `/detect/stream` | `text/plain` | Content-type detection |
| `PUT` | `/unpack` | `application/x-tar` | Embedded resources as tarball |
| `PUT` | `/unpack/all` | `application/x-tar` | Embedded + root as tarball |
| `PUT` | `/language/stream` | `text/plain` | Language detection |
| `GET` | `/version` | `text/plain` | Tika version baked in |
| `GET` | `/mime-types` | `application/json` | Supported MIME list |
| `GET` | `/parsers` | `application/json` | Parser inventory |
| `GET` | `/parsers/details` | `application/json` | Parser inventory with detail |

Headers honored (passed through to worker descriptor):

- `Content-Disposition` — filename hint
- `Password` — PDF/OOXML decryption password
- `X-Tika-PDFExtractInlineImages` — toggle PDF inline image extraction
- `X-Tika-OCRLanguage` — tesseract language override
- `X-Tika-Skip-Embedded` — opt out of recursive parsing for this request
- `Accept` — controls rmeta variant

Each sync request creates an ephemeral job, claims a warm slot with timeout `REDTUSK_SYNC_QUEUE_TIMEOUT_S` (default 30s), awaits completion, returns the translated result, and discards the job record (no persistence). On pool exhaustion past the queue timeout: `503 Service Unavailable` with `Retry-After`. This is the one documented behavioral divergence from `tika-server` (which queues unboundedly inside the JVM).

### RedTusk-native (asynchronous)

Ported pattern from ClippyShot:

| Method | Path | Returns | Behavior |
|---|---|---|---|
| `POST` | `/v1/jobs` | `202 + JSON` | Submit job, returns job ID |
| `GET` | `/v1/jobs/{id}` | `JSON` | Job status + canonical rmeta when complete |
| `GET` | `/v1/jobs/{id}/artifacts/{name}` | varies | Per-entry text files, embedded blobs |
| `GET` | `/v1/jobs` | `JSON` | Paginated submission list (UI source) |
| `DELETE` | `/v1/jobs/{id}` | `204` | Safe-delete: removes job record + artifacts only if state is terminal (`succeeded` or `failed`); returns 409 if `queued` or `running` |
| `GET` | `/v1/readyz` | `200 / 503` | Readiness probe |
| `GET` | `/metrics` | Prometheus | Scrape endpoint |
| `GET` | `/` | `text/html` | Single-page UI |

These persist to JobStore, get TTL'd by `REDTUSK_JOB_RETENTION_SECONDS`, and back the UI. The job record's canonical body is the rmeta JSON; the UI renders it as a tree (one node per extracted entry) with hash + content-type + text preview per node.

### Translation layer

The worker only ever produces one output format: rmeta JSON. The API tier translates to whatever shape the requested endpoint expects:

- `/tika` → `entries[0].text`
- `/meta` → `entries[0].metadata`
- `/rmeta*` → as-is (variant determines `text|html|xml` form which the worker honors via its own flag)
- `/unpack` → repackage `entries[1:]` as tarball
- `/unpack/all` → repackage `entries[*]` as tarball
- `/detect/stream` → `entries[0].content_type`
- `/language/stream` → `entries[0].language`

## Output schema (canonical rmeta)

```json
{
  "redtusk_version": "0.1.0",
  "tika_version": "3.3.0",
  "input": {
    "sha256": "ae1c...",
    "size_bytes": 184320,
    "filename_hint": "invoice.docx",
    "submitted_at": "2026-05-04T18:23:11Z"
  },
  "extraction": {
    "root_content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "root_language": "en",
    "duration_ms": 412,
    "entries": [
      {
        "path": "/",
        "parent_path": null,
        "depth": 0,
        "content_type": "...",
        "size_bytes": 184320,
        "sha256": "ae1c...",
        "metadata": { "Author": "...", "Creation-Date": "..." },
        "text": "...full extracted text...",
        "language": "en",
        "qr": { "codes": [], "skipped": null },
        "ocr": { "text": "", "language": null, "duration_ms": 0, "skipped": "no_images" },
        "error": null
      }
    ]
  },
  "limits": {
    "max_recursion_depth": 10,
    "max_embedded_entries": 5000,
    "max_extracted_bytes": 524288000,
    "ocr_timeout_s": 60
  },
  "truncated": null,
  "warnings": [],
  "sandbox": {
    "profile": "default",
    "runtime": "runsc",
    "appcds": true,
    "ksm": true,
    "crac": false
  }
}
```

Schema invariants (validated by dispatcher before trusting worker output):

- `entries[0].path == "/"` and `entries[0].depth == 0`.
- `entries[*].path` is unique within the job.
- For `depth > 0`, `parent_path` references an earlier entry's `path`.
- `qr` and `ocr` fields are always present (possibly empty / skipped) on every entry, so downstream consumers can rely on a stable shape.
- `truncated` is null OR an object `{"reason": "max_embedded_entries|max_recursion_depth|max_extracted_bytes", "limit": N, "observed": N}`.
- `warnings[]` items are objects `{"code": "<short>", "detail": "<message>", "entry_path": "<optional>"}`.

## Per-job data flow

### Synchronous (e.g. `/rmeta`)

1. Client `PUT /rmeta` with file body + headers.
2. API validates upload size (`REDTUSK_MAX_INPUT`, default 100 MiB; streaming check), sanitizes filename hint, builds job descriptor `{input_path, sha256, headers, limits, output_format}`.
3. API writes input to a transient file in the **shared submission volume**, calls `pool.claim(timeout=REDTUSK_SYNC_QUEUE_TIMEOUT_S)`.
4. Pool returns idle `Slot`. Dispatcher hardlinks input into `slot.scratch_dir/in/`, writes `slot.scratch_dir/job.json`, writes `"go\n"` to the worker's control fifo (`slot.scratch_dir/control.fifo`, created by the worker on startup as a named pipe under `mkfifo(3)`).
5. Worker JVM unblocks, reads `job.json`, parses input via `RecursiveParserWrapper` with configured limits, runs scanners on image entries, writes `slot.scratch_dir/out/metadata.json` + per-entry text files, exits 0.
6. Dispatcher detects exit, validates `metadata.json` against schema, marks slot draining, immediately spawns replacement.
7. API tier reads rmeta JSON, runs translation for the requested endpoint, returns result. Transient input + scratch dir wiped.

### Asynchronous (`/v1/jobs`)

Identical from step 4 onward, except:

- In step 2 the JobStore record is created with `state=queued`.
- The dispatcher's claim loop (separate asyncio task) picks up queued jobs rather than the API tier blocking.
- After step 6, artifacts are copied from the scratch dir into the **persistent artifact tree** keyed by job ID.
- State transitions: `queued → running → succeeded | failed`.

### Hardlink, not copy

API and worker scratch dirs are on the same filesystem (named docker volume mounted into both). Inputs are hardlinked into worker scratch to avoid double-copy of large uploads. Worker mount of its scratch is read-only for `in/`, read-write for `out/`.

### Dispatcher must validate worker output

The worker is the untrusted part of the system from the dispatcher's perspective — even though we wrote it. Before trusting `metadata.json`, the dispatcher:

- Validates against the JSON Schema in `src/redtusk/types.py`.
- Caps total size at `REDTUSK_MAX_METADATA_BYTES` (default 64 MiB).
- Recomputes SHA-256 on the root entry to verify worker integrity.
- Rejects if any field is structurally weird (extra top-level keys, NaN/Infinity floats, non-UTF-8 strings).

## Error handling

| Failure | Detection | Behavior |
|---|---|---|
| Worker crashes mid-extraction (segfault, OOM kill) | Container exits non-zero, `out/metadata.json` missing or malformed | Mark job failed `code=worker_crash`. Sync: 502. Async: state=failed. Pool spawns replacement. |
| Worker hangs | Per-job wall-clock timeout (`REDTUSK_JOB_TIMEOUT_S`, default 60s) elapses with slot still `assigned` | SIGKILL container, fail job `code=timeout`. Sync: 504. Async: state=failed. |
| Tika parse error on root | Worker exits 1, partial `metadata.json` present with `parse_error` field | Job succeeds with `warnings[]`. Mirrors tika-server's "parse errors are not HTTP errors." Sync: 200 with partial result. Async: state=succeeded. |
| Tika error on one embedded entry | Worker continues siblings, that entry has `error` field set | Reflected in `entries[]`, no top-level warning. |
| Recursive limit hit | Worker truncates, sets `truncated` field | Job succeeds; entries[] contains everything extracted up to limit. |
| Scanner failure (tesseract / zbar) | Subprocess non-zero exit | Sets `entries[i].ocr.skipped="error"` or `qr.skipped="error"`, adds `warnings[]` entry, extraction otherwise succeeds. |
| Pool exhausted on sync request | `pool.claim()` times out | Sync: 503 with `Retry-After`. Async: job stays `queued` until claimed. |
| Input rejected pre-pool | API-tier checks (size, malformed multipart, missing body) | 4xx before any worker is touched. |
| Worker fails to spawn (CRaC checkpoint corrupt, image missing) | `docker run` non-zero or no fifo within `REDTUSK_WORKER_WARMUP_TIMEOUT_S` | Pool replacement retries with exponential backoff (250ms, 500ms, 1s, 2s, 5s). After 5 failures, dispatcher logs critical, decrements `target_size` by 1, reports degraded via `/v1/readyz`. |
| Disk full on shared volume | Write fails | Sync: 507. Async: marks job failed `code=disk_full`. |

## Pool management

### Slot state machine

```
[spawn] -> WARMING -> IDLE -> ASSIGNED -> DRAINING -> (gone)
                  |                                       ^
                  +------> SPAWN_FAILED ------------------+
```

- **WARMING:** `docker run` issued, container booting, fifo not yet visible. Dispatcher polls for fifo with timeout `REDTUSK_WORKER_WARMUP_TIMEOUT_S` (default 15s for `default` profile, 5s for `high-density`).
- **IDLE:** fifo present, worker blocked on read. In claim queue.
- **ASSIGNED:** dispatcher wrote `job.json` + signaled fifo. Per-job timer running; SIGKILL on expiry.
- **DRAINING:** container exited (cleanly or not). Dispatcher copies artifacts (success path) or records failure, runs `docker rm`, removes scratch dir. **Replacement spawn is initiated as soon as DRAINING is entered, in parallel with cleanup**, so the pool refills sooner.
- **SPAWN_FAILED:** exponential backoff retry. After max retries, decrement target_size and mark dispatcher degraded.

### Sizing knobs

All `REDTUSK_*` env vars via `Limits.from_env()`:

| Var | Default | Purpose |
|---|---|---|
| `POOL_SIZE` | 10 | Steady-state idle slots |
| `POOL_BURST_SIZE` | 5 | Extra slots on sustained queue depth |
| `POOL_BURST_TRIGGER_S` | 3 | Sustained queue depth duration to trigger burst |
| `POOL_BURST_DRAIN_S` | 60 | Idle time before reaping a burst slot |
| `POOL_MAX_SIZE` | 32 | Hard ceiling regardless of burst |
| `POOL_SPAWN_RATE_LIMIT` | 4/s | Cap on container starts/sec |
| `POOL_SPAWN_RETRY_MAX` | 5 | Spawn retries before shrinking target_size |
| `WORKER_WARMUP_TIMEOUT_S` | 15 (default) / 5 (high-density) | Time to first fifo |
| `JOB_TIMEOUT_S` | 60 | Per-job wall-clock, SIGKILL on expiry |
| `SYNC_QUEUE_TIMEOUT_S` | 30 | Sync request blocks this long for a slot |

### Health probe semantics (`/v1/readyz`)

- 200 OK if pool has at least 1 IDLE slot OR target_size has been reachable in the last 30s.
- 503 if zero IDLE for >30s and no successful spawn in that window.
- Backed by Prometheus gauge `redtusk_pool_idle_slots`.

## Toolchain pins

| Component | Version | Source / image | Notes |
|---|---|---|---|
| JDK (default profile) | OpenJDK 25 LTS | `eclipse-temurin:25-jdk-jammy` | Latest LTS as of Sep 2025; AppCDS via `-XX:ArchiveClassesAtExit` + `-XX:SharedArchiveFile` |
| JDK (high-density profile) | Azul Zulu CRaC build for JDK 25 LTS | `azul/zulu-openjdk-crac:25-jdk` | OpenJDK CRaC for 25 is acceptable as a fallback; Zulu chosen for production stability |
| Apache Tika | 3.3.0 | Maven dependency in `worker_jvm/pom.xml` | Tika 3.3.0 is the current stable release; JDK 25 supported |
| Python | 3.12+ | `pyproject.toml` `requires-python` | Same floor as ClippyShot |
| Tesseract OCR | 5.x | `tesseract-ocr`, `tesseract-ocr-eng` (apt) | System binary at `/usr/bin/tesseract` |
| zbar | latest stable | `zbar-tools` (apt) | System binary at `/usr/bin/zbarimg` |
| Docker / Compose | 20.10+ / Compose v2 | host requirement | Same as ClippyShot |
| CRIU | 3.18+ | bundled with Zulu CRaC image | Required for `criu restore` at PID 1 in high-density |
| FastAPI / uvicorn | latest stable | `pyproject.toml` | |
| Postgres (compose) | 16.x | `postgres:16` | sqlite is the default for non-compose deploys |

JDK upgrades follow LTS cadence: pin to the current LTS, evaluate the next LTS within 6 months of its release. Non-LTS JDK releases are not supported targets.

Tika upgrades are version-coordinated across the worker image and the test-only `tika-server` parity dependency in `pyproject.toml`. Bumping one without the other breaks the parity suite intentionally — that's the failure signal.

## Memory dedup

### AppCDS (both profiles)

Built into the worker image as a separate Docker stage. The build runs the worker entrypoint in `--appcds-warmup` mode against `tests/fixtures/appcds-warmup-corpus/`, dumping `redtusk.jsa` via `-XX:ArchiveClassesAtExit`. The runtime stage starts the JVM with `-XX:SharedArchiveFile=/opt/redtusk/redtusk.jsa -Xshare:on`, failing loudly if the archive can't be mapped.

Page sharing across containers: every container running the same image reads the archive from the same image layer, mmap'd read-only, shared via host page cache automatically. Saved per slot: ~30–80 MB of class metadata.

### KSM (both profiles, opt-in via host config)

Host-side script (`deploy/ksm/enable-ksm.sh`):

```sh
echo 1 > /sys/kernel/mm/ksm/run
echo 1000 > /sys/kernel/mm/ksm/pages_to_scan
echo 200 > /sys/kernel/mm/ksm/sleep_millisecs
```

Worker-side, `KsmHelper.java` calls `madvise(MADV_MERGEABLE)` on JVM heap regions via JNI in a small native helper (~30 LOC C). KSM runs in **opt-in mode** — only RedTusk worker JVM heaps participate.

**Side-channel disclosure:** KSM enables FLUSH+RELOAD timing observation across merged pages. Threat model (`--network=none`, no exfil, container destroyed after one job) makes this mostly theoretical, but documented in `deploy/ksm/README.md`. Operators can set `REDTUSK_DISABLE_KSM=1` to skip the `madvise` call.

### CRaC (high-density profile only)

Built as an additional Docker stage on `Dockerfile.high-density`. The build-time helper boots **Azul Zulu CRaC build for JDK 25 LTS** (see Toolchain pins), runs the worker entrypoint in `--checkpoint` mode, calls `Core.checkpointRestore()`, and dumps CRIU state to `/opt/redtusk/checkpoint/`. The default-profile JDK is OpenJDK 25 LTS (Eclipse Temurin) without CRaC support; the high-density profile pins Zulu CRaC for 25.

At runtime: `restore.sh` execs `criu restore --tcp-established --shell-job -D /opt/redtusk/checkpoint`. The restored process becomes PID 1 of the container. After resuming from checkpoint, the entrypoint drops `CAP_CHECKPOINT_RESTORE` via `prctl(PR_CAPBSET_DROP)` + `prctl(PR_SET_NO_NEW_PRIVS)` before opening the fifo. Steady-state cap-set is identical to the default profile.

**Image size caveat:** The checkpoint contains full memory state — typically 200–400 MB compressed. Documented in `deploy/docker/README.md`. Image pulls are slower; pool spawn is much faster.

### Effective per-slot memory by profile

Estimates for a pool of 10:

| | Cold JVM (no dedup) | Default profile | High-density profile |
|---|---|---|---|
| Per-slot RSS | ~280 MB | ~150 MB | ~50 MB |
| Pool RAM (10 slots) | ~2.8 GB | ~1.5 GB | ~0.5 GB |
| Cold-spawn time | ~3.5 s | ~2.0 s | ~0.1 s |

These are estimates; v1 includes a measurement task to validate them on real workloads before locking the defaults.

## Deploy matrix

| Target | AppCDS | KSM | CRaC | Notes |
|---|---|---|---|---|
| EC2 self-managed (default profile) | ✅ | ✅ | — | systemd unit or user-data enables KSM at boot |
| EC2 self-managed (high-density profile) | ✅ | ✅ | ✅ | runc only (CRIU does not work under runsc) |
| ECS / EKS on EC2 nodes (default) | ✅ | ✅ | — | DaemonSet enables KSM per node |
| ECS / EKS on EC2 nodes (high-density) | ✅ | ✅ | ✅ | Custom AMI w/ CRIU; runc runtime |
| ECS / EKS Fargate (default only) | ✅ | ❌ | — | KSM unavailable in Firecracker; AppCDS still works via host page cache |
| Off-AWS Linux host | ✅ | ✅ | optional | Same as EC2 |

The entrypoint logs a warning at boot if it set `MADV_MERGEABLE` but `/sys/kernel/mm/ksm/run` reads `0` — catches both "operator forgot to enable KSM" and "running on Fargate" as the same observable signal.

## QR + OCR scanners

Tika has built-in `TesseractOCRParser` that blends OCR'd text into entry `text` fields, but for the threat-intel use case we want OCR + QR as **separate, identifiable signals**. Shelling out also gives process-level fault isolation — a tesseract or zbar segfault doesn't take down the JVM.

### Integration

After Tika extraction, the Java worker walks `entries[]` and selects scan candidates:

- **Image entries** (`content_type.startsWith("image/")`) → `tesseract` + `zbarimg` directly on the entry bytes.
- **Everything else** → skipped.

PDF page rasterization is explicitly out of scope (see Non-goals). Tika natively extracts embedded raster images from PDFs as their own entries; we scan those. The exotic case of a payload drawn using PDF vector primitives is RedTusk's blind spot — users who need it pipe through ClippyShot first.

### Subprocess invocation

Java `ProcessBuilder` from `ScannerRunner.java`. Each subprocess gets:

- Per-process wall-clock timeout (`REDTUSK_OCR_PER_CALL_TIMEOUT_S`, default 30s).
- stdin/stdout pipes only (no temp files where avoidable).
- Captured stderr logged at debug level.

Binaries baked into the image: `tesseract-ocr`, `tesseract-ocr-eng` (+ optional language packs), `zbar-tools` (or `python3-pyzbar` if a Python helper is preferred — both work; default to `zbar-tools` for simpler deps).

### Limits / budgets (mirrors ClippyShot)

| Var | Default | Purpose |
|---|---|---|
| `ENABLE_QR` | 1 | QR scanning on by default |
| `ENABLE_OCR` | 0 | OCR opt-in per request |
| `OCR_LANG` | `eng` | tesseract `-l` |
| `OCR_PSM` | 3 | tesseract `--psm` |
| `OCR_TIMEOUT_S` | 60 | Per-job total wall-clock budget for OCR (not per-call) |
| `OCR_PER_CALL_TIMEOUT_S` | 30 | Floor per tesseract invocation |
| `OCR_ALL` | 0 | When 0, image-gating skips entries with no images / vector drawings / populated text layer |

Per-request override via `X-RedTusk-OCR: 1` header or `?ocr=1` query param.

### Failure policy

Scanner failures are **never fatal**. A tesseract or zbar crash sets `entries[i].ocr.skipped="error"` or `qr.skipped="error"`, plus a top-level `warnings[]` entry with code `ocr_scan_error` / `qr_scan_error`. Extraction continues normally.

## Hardening

### Common to both profiles

- `--read-only` rootfs.
- `--security-opt=no-new-privileges`.
- `--memory=1g` (default profile; revisit after measurement) / `--memory=2g` (high-density, allowing extra headroom for restored state).
- `--pids-limit=256`.
- `--cpus=1.0`.
- UID 10001.
- tmpfs at `/tmp` (512 MiB) and `/var/lib/redtusk` (64 MiB).
- `--network=none`.
- `--rm`.
- gVisor (`runsc`) when available, runc otherwise (high-density: runc only).

### Capabilities

- **Default profile:** `--cap-drop=ALL`.
- **High-density profile:** `--cap-drop=ALL --cap-add=CHECKPOINT_RESTORE`. The cap is dropped by the entrypoint (`CapDropper.java`) immediately after CRIU restore completes, before the fifo is opened. Steady-state cap-set is identical to default. Verified in `tests/integration/test_high_density_caps.py` by greps of `/proc/self/status`.

### Seccomp

`deploy/seccomp/redtusk.seccomp.policy` (KAFEL DSL for nsjail-style; Docker BPF JSON variant generated from it).

JVM-shaped policy — narrow because OpenJDK has a tighter syscall footprint than full desktop applications (no fork/exec helpers beyond the scanner allow-list, no font rasterization, no networking syscalls because the worker is `--network=none`):

- All POSIX syscalls used by OpenJDK (file I/O, thread management, memory, signals).
- `madvise` allowed but BPF-checked: only `MADV_MERGEABLE`, `MADV_DONTNEED`, `MADV_FREE` permitted as the second argument.
- `prctl` allowed for `PR_SET_NAME`, `PR_GET_NAME`, `PR_SET_NO_NEW_PRIVS`, `PR_CAPBSET_DROP`.
- `execve` allow-listed against `/usr/bin/tesseract` and `/usr/bin/zbarimg` only (path-checked).
- All other path-bearing syscalls denied for `/etc`, `/proc/sys/*`, `/sys/*` except `/sys/kernel/mm/transparent_hugepage` (JVM startup reads it).

x86_64 + ARM64 both supported (Tika's syscall surface is stable across architectures, unlike LibreOffice's).

### AppArmor

`deploy/apparmor/redtusk-worker`:

- `r` on `/opt/redtusk/`, `/usr/lib/jvm/`, the AppCDS archive path.
- `r` on per-container scratch `in/`.
- `rw` on per-container scratch `out/`.
- `Pix` on `/usr/bin/tesseract`, `/usr/bin/zbarimg` (execute under the parent profile so they inherit MAC restrictions).
- Deny everything else.

## Testing strategy

### Test layout

```
tests/
├── unit/                             # in-process, no docker, no JVM
│   ├── test_pool.py                  # state machine, all transitions, mocked spawn/reap
│   ├── test_dispatcher.py
│   ├── test_jobs.py
│   ├── test_limits.py
│   ├── test_translation.py           # rmeta -> /tika, /meta, /detect, /unpack
│   ├── test_metadata_schema_stable.py
│   └── test_sandbox_*.py
├── http/                             # FastAPI TestClient, mocked dispatcher
│   ├── test_tika_compat.py           # all tika-server endpoint shapes
│   └── test_jobs_api.py
├── jvm/                              # Java unit tests for worker
│   └── src/test/java/...             # Maven Surefire
├── integration/                      # full pipeline; needs JVM + sandbox
│   ├── test_warm_pool_lifecycle.py
│   ├── test_recursive_limits.py      # zip bombs, mail loops, deep nesting
│   ├── test_appcds_active.py         # asserts -Xshare:on actually mapped
│   ├── test_ksm_madvise.py           # asserts MADV_MERGEABLE called
│   ├── test_high_density_caps.py     # CAP_CHECKPOINT_RESTORE drop dance
│   └── test_tika_compat_pipeline.py  # binary-on-binary parity vs upstream tika-server
├── docker/
│   ├── test_image_default.py
│   └── test_image_high_density.py
└── fixtures/
    ├── safe/
    ├── adversarial/                  # zip bomb, mail loop, recursive zip, malformed OOXML, .msg with embedded .docm
    └── appcds-warmup-corpus/
```

### Tika-compat parity suite

`tests/integration/test_tika_compat_pipeline.py` runs the actual upstream `tika-server` and RedTusk side by side on the same fixtures and diffs the responses. This catches API drift early. Tika version pinned in both: as a test-only dependency in `pyproject.toml` and as a production dependency in the worker image; upgrade is a coordinated bump.

### Unit/CLI/HTTP suite runs without JVM

The core `tests/unit + tests/http` suite runs in pure Python without a JVM, sandbox, or Docker — same property as ClippyShot. Workers are mocked via the `Slot` interface. Integration suite is gated by pytest markers (`integration`, `docker`, `jvm`) and runs inside the built image or in CI with the JDK + Docker available.

## Observability

### Metrics

Direct port of ClippyShot's pattern + new pool-specific gauges:

```
redtusk_extractions_total{outcome,format}        counter
redtusk_extraction_duration_seconds{stage}       histogram   stage in {parse, scanners, total}
redtusk_pool_target_size                         gauge
redtusk_pool_idle_slots                          gauge
redtusk_pool_assigned_slots                      gauge
redtusk_pool_warming_slots                       gauge
redtusk_pool_spawn_total{outcome}                counter     outcome in {success, failed, timeout}
redtusk_pool_spawn_duration_seconds              histogram
redtusk_jobs_in_flight                           gauge
redtusk_input_bytes                              histogram
redtusk_extracted_entries                        histogram
redtusk_rejections_total{reason}                 counter
redtusk_sync_queue_wait_seconds                  histogram
redtusk_ksm_pages_shared                         gauge       scraped from /sys/kernel/mm/ksm/pages_shared
redtusk_appcds_mapped_bytes                      gauge       scraped from /proc/self/maps in worker
```

### Logging

structlog, JSON output. Request-ID and job-ID propagated through dispatcher into worker stdout. Worker prefixes log lines with the job ID; dispatcher captures and re-logs structured via the same logging pipeline.

## Configuration

All limits funnel through `redtusk.limits.Limits.from_env()`. Both CLI and HTTP API honor the same `REDTUSK_*` env vars. Adding a new tunable means adding it to `Limits.from_env()` and both entry points pick it up automatically — same discipline as ClippyShot.

Complete env var reference is generated at build time from `Limits` field annotations and committed to `docs/configuration.md`. Changes to `Limits` that don't update the doc fail CI.

## Open questions / future work

These are deliberately deferred from v1:

1. **Multi-tenant auth (option C/D from brainstorming).** v1 is single-tenant; multi-tenant API keys + per-tenant JobStore isolation is a v2 candidate when paying customers exist.
2. **CRaC under runsc.** When gVisor's native checkpoint/restore matures past experimental, revisit using it instead of CRIU for high-density on runsc.
3. **PDF page rasterization fallback.** Currently out of scope; revisit if real-world traffic shows meaningful adversarial cases of vector-drawn QR/OCR content.
4. **ARM64 seccomp validation.** Policy is shared across architectures, but the validation suite should be run on both before claiming production-ready ARM64 support.
5. **Per-slot CPU pinning.** `--cpuset-cpus` per worker for cache locality could improve KSM merge rates and reduce JIT recompilation; measure before adding.
6. **Streaming response for very large rmeta outputs.** Currently buffer the full rmeta JSON; for jobs with thousands of entries, NDJSON streaming on the async API might be worth adding.
