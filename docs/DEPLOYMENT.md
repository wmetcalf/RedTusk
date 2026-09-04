# Deployment action inventory

What must be rebuilt, and where it lands, for each kind of version bump.

## The single path

```sh
scripts/release_engine.sh                      # show the plan (dry run — the default)
scripts/release_engine.sh --apply --tag 0815   # test -> image (jar + AOT) -> audit -> deploy -> verify
```

It chains the existing pieces and gates both ends: `deploy_inventory.sh` before, the image
jar/AOT audit in the middle, and `verify_warm_tier.sh` + `deploy_inventory.sh` after. It refuses
to build an image from failing tests, and refuses to call a deploy successful if the tier did not
come back warm. Step 4 (which recreates production containers) is printed for you to run rather
than fired automatically.

The sections below are the manual reference for what that path does, and for the cases it does
not cover. Run `scripts/deploy_inventory.sh` **before and after** any deployment — it reports
what is actually deployed and exits non-zero on drift.

## Why this document exists

The same packages (`blastbox`, `redtusk`) are installed into **two independent surfaces**, and
rebuilding one does not touch the other:

| surface | what it holds | who runs it |
|---|---|---|
| **container image** (`redtusk:<tag>`) | blastbox + redtusk python | `*-api-*`, `*-dispatcher-*` on the host |
| **FC guest rootfs** (`*.ext4`) | its OWN blastbox + redtusk python, the JDK, `redtusk-worker.jar`, the AOT cache, `/opt/blastbox/{run_guest.py,engines.py,engine}` | inside every Firecracker microVM |

A rootfs older than the running image means **the guest is executing older code than the host**.
That state is invisible from `docker ps` and was live on this fleet from 2026-07-20 to 2026-08-14.
`deploy_inventory.sh` now fails on it explicitly.

## Coupling rules

These artifacts are generated *from* each other and must move together:

- **jar → AOT cache.** `redtusk.aot` is produced from `redtusk-worker.jar` by a record→create
  pass and is flag- and classpath-sensitive. A cache that does not match its jar fails to map
  (`Unable to map shared spaces`) and silently costs startup on **every job**. Never swap a jar
  into a rootfs by hand — rebuild the image so the cache is regenerated with it.
- **rootfs → warm snapshot.** Slots restore from a memory snapshot of a booted guest. A new
  rootfs requires the pool base to be rebuilt, or slots keep restoring the old guest.
- **JVM flags → AOT cache.** `_DEFAULT_JVM_FLAGS` in `src/redtusk/engine.py` must match the flags
  the cache was built with. Changing one without the other silently disables the cache.

## Action inventory

### 1. blastbox version bump (host-side only: dispatcher/API logic)

1. Rebuild the container image.
2. Recreate `*-api-*` and **every** `*-dispatcher-*` in the stack — including the tier-specific
   ones (`aws-burst`, `gvisor`). Missing one leaves a stack on mixed images.
3. **Also rebuild the FC rootfs** if the change touches anything under `blastbox/worker/`
   (`run_guest.py`, `fc_warm.py`, `warm.py`, `harness.py`) — that code runs *in the guest*, and
   the image rebuild does not reach it.
4. Verify: `deploy_inventory.sh` → all containers in the stack on one image, one blastbox version.

#### Every dispatcher needs the blob store

A dispatcher with no `BLASTBOX_BLOB_URL` seals results into a `LocalBlobStore` the API never
reads: its jobs reach **DONE** and their results **404**, with a healthy container, no error and
no log line. That was live for the gvisor and cold tiers until 2026-08-18 — 17,617 completed
jobs whose results are unfetchable and, after the terminal purge, mostly unrecoverable.

The endpoint differs **per service**: the api reaches MinIO by host IP, but the dispatchers sit
on the internal backend network with no egress route and must use the `http://minio:9000` ALIAS.
Give a dispatcher the api's value and every job fails with `result upload failed after 3
attempts` (fail-closed — the result is retained, not lost — but the tier produces nothing).

`scripts/deploy_inventory.sh` now checks both this and whether the node's compose files still
match the repo's. Run `--self-test` to see every check fire against a fixture.

#### Shipping a blastbox that is not on PyPI yet

`Dockerfile.host` pins a released blastbox. To run a host-side fix ahead of a release, do NOT
build from a local source copy with the same version — everything then reports the release
number for code that is not the release, and step 4 above (the whole point of the inventory)
goes blind. Instead:

```bash
# in the blastbox repo — stamps a PEP 440 local version, 0.1.27+g<sha>[.dirty]
WHEEL=$(deploy/build_dev_wheel.sh | tail -1)
scp "$WHEEL" <host>:<redtusk>/deploy/docker/wheels/
# on the host
docker build -f deploy/docker/Dockerfile.host \
    --build-arg BLASTBOX_WHEEL="$(basename "$WHEEL")" -t redtusk:<tag> .
```

The wheel installs over the pin with `--force-reinstall --no-deps`, and `pip show blastbox`
(which is what `deploy_inventory.sh` reads) then reports `0.1.27+g<sha>` — impossible to
confuse with PyPI. Leave `BLASTBOX_WHEEL` unset for a normal release build.

### 1a. Building images that record what they were built from

```
scripts/build_images.sh <tag> [blastbox-version]
```

That is a thin wrapper around `blastbox build-images`, which reads
`blastbox-images.toml` in this repo. **The declaration is the build**: every
image, the base each one is pinned to, which `ARG` receives that base, and both
rootfs artifacts are named there, so a tier that is missing from it is a tier
nothing rebuilds.

It stamps all five images -- worker base, cold worker, host, and the two warm
images -- with the blastbox version, the source revision, and what each was
built **on**; verifies every stamp reads back; and only then exports the rootfs
artifacts. Nothing is built unstamped: if the stamp is refused, the run stops
rather than producing an image whose label it could not write. Nothing is
exported from an image that failed verification, and nothing replaces a live
artifact until the plan's `requires` have been found in it.

Add `--dry-run` to print exactly what would be built and exported, resolved,
without touching anything.

Environment overrides:

| variable | effect |
|---|---|
| `BLASTBOX_SRC` | **required** — a blastbox **source** tree. The two warm-tier images are built from Dockerfiles that live there and are not in the wheel |
| `REDTUSK_FC_DIR` | where the Firecracker `redtusk-rootfs.ext4` is written |
| `REDTUSK_GVISOR_DIR` | where the gVisor tree is written (default `/var/lib/redtusk-gvisor`) |
| `BLASTBOX_WHEEL` | ship a pre-release host-side blastbox instead of the pinned PyPI one (see section 1) |

The upstream bases are no longer environment variables: they are declared in
`blastbox-images.toml`, and a test asserts each one matches the `ARG` default in
the Dockerfile it belongs to — if those drift, a plain `docker build` and a
planned build produce images on different bases while both look correct.

Why this is not optional: on 2026-09-02 the base that built the running
`redtusk-cold-worker` no longer existed. Its jar matched none of the fourteen
`redtusk-worker:*` tags on the box and no dangling image, so the deployed worker
could not be rebuilt at all -- and rebuilding it on any available base would
have swapped the Java engine while looking like a routine version bump. Nothing
had recorded the base, so the gap was invisible until someone went looking.

**How strong the pin is depends on where the base lives.** A base with a
registry digest is pinned by that digest and every builder resolves it. A
*local-only* base -- which all three of these are, since nothing here is pushed
-- is pinned by its reference, with the immutable image ID recorded in the
label. An image ID is not a usable `FROM`: buildkit reads `sha256:...` as the
repository `docker.io/library/sha256:...` and tries to pull it. So for local
bases the guarantee is "the build used whatever this reference meant at build
time, and the label says which image that was" -- checkable afterwards rather
than guaranteed by construction. Push the base to a registry for the strong
form.

Two traps the script handles for you:

* **A deployed tree is not a git checkout.** `.git/` is excluded from the
  rsync, so `git rev-parse` fails there and a stamp with no revision is
  refused. `scripts/deploy_to_host.sh` writes the sha into
  `.blastbox-revision` before it syncs -- it also refuses to deploy a dirty
  tree, because that sha would not describe what is being shipped.
* **The ARG names are not uniform.** These Dockerfiles use `BASE_IMAGE`;
  blastbox's `deploy/gvisor/Dockerfile.redtusk` uses `BASE`. Docker silently
  IGNORES a `--build-arg` the Dockerfile does not declare -- and declaring it is
  not enough either: an ARG inside a stage cannot parameterize a `FROM`, and in
  a multi-stage build only the last stage becomes the image, so a parameterized
  *builder* pins nothing. `blastbox stamp` refuses all three cases, and
  `tests/unit/test_build_script_arg_names.py` catches them in CI without docker.

**The warm tiers do not run the cold worker image.** gVisor and Firecracker each
run a rootfs exported from a separate image, so flipping `REDTUSK_WORKER_IMAGE`
updates the cold tier and leaves those two on whatever they were last built
from -- a fleet running two versions while every tag says one. `BLASTBOX_SRC` is therefore REQUIRED: those two images are built from
Dockerfiles that live in blastbox, and are stamped with **that** tree's
revision, because recording this repo's would name a commit that does not
contain the file which built them.

Exporting them is part of the same run -- there is no separate export step any
more. Keeping one is what let the two disagree: images could be rebuilt without
the artifacts being replaced, so the warm tiers went on booting whatever they
were last exported from. Measured on
2026-09-03: the live gVisor rootfs held blastbox 0.1.27 while the tags said
0.1.30, until it was rebuilt.

The images are built in order and verified at the end, so a failure at step
2 or 3 leaves the earlier tags already built. They are not wired into anything
until you point `deploy/docker/.env` at them.

Verify anything already built with `blastbox stamp --read <image>`, and the
whole fleet with `blastbox doctor`.

### 1b. Reading where the slot cycle goes

`scripts/slot_cycle_profile.sh` reports the per-phase breakdown from the dispatcher's
`warm_phases` log line (one per warm job, host-side, keyed by `job_id`). `guest` is the only
phase that is extraction; everything else is the cost of running it in a disposable sandbox.
If the tier serves jobs but the script reports no `warm_phases` lines, the dispatcher image
predates blastbox `2d88c70` — see §1.

Do not resurrect per-job durations paired from the GUEST logs: those lines carry no correlation
id, so under concurrency the k-th start and the k-th completion are different jobs. That method
reported 0.67s and 5.48s for the same tier minutes apart.

**Result-upload fan-out.** `BLASTBOX_BLOB_UPLOAD_CONCURRENCY` (default 16) is the dispatcher-wide
budget for concurrent `put_object` calls, because `put_output` costs one round-trip PER ARTIFACT
and a result tree is often hundreds of them. It is a **per-dispatcher** budget, not per-job: one
`S3BlobStore` — one connection pool — is shared by every concurrent job, so a per-job fan-out
would put ~`slots x budget` threads on a pool sized for `budget` alone. `=1` restores the
original fully serial path and is the escape hatch for an A/B.

The knob must be listed in each dispatcher's compose `environment:` block to reach the container;
setting it only in `.env` does nothing, and setting it with `docker exec` does not survive a
`compose up` recreate.

### 2. RedTusk engine bump — python only (`src/redtusk/`)

1. Rebuild the container image (cold/container tiers).
2. Rebuild the FC rootfs (the guest has its own copy — this is the step most often skipped).
3. Rebuild the pool base so slots restore the new guest.
4. Verify with the fixed-cost probe in §"Verifying a warm tier".

### 3. RedTusk engine bump — Java worker (`worker_jvm/`)

1. `mvn -f worker_jvm/pom.xml package` → `redtusk-worker.jar`.
2. Rebuild the **image**, which regenerates the AOT cache from the new jar
   (`Dockerfile.localtika`: `AOTMode=record` → `AOTMode=create`). Do not hand-copy the jar.
3. Rebuild the FC rootfs, then the pool base.
4. Verify: `deploy_inventory.sh --deep` must NOT report `STALE AOT`.

### 4. Guest-only config (`deploy/firecracker/guest.*.env`, `init`, engine selection)

1. Rebuild the FC rootfs, then the pool base. No container rebuild needed.
2. Verify: `/opt/blastbox/engine` inside the rootfs holds the intended
   `module:Class` (`deploy_inventory.sh --deep` prints it). If it is `UNSET`,
   `run_guest.py` falls back to `BLASTBOX_FC_ENGINE` and then to the `probe` engine.

### 5. Adding or reprovisioning a node

Per-host GIDs (docker/kvm) differ and silently break the FC tier — run the node env sync before
expecting work to land. Confirm the node appears in `deploy_inventory.sh` output; an unreachable
node is capacity you do not have, and the fleet will not tell you.

## Verifying a warm tier actually is warm

Per-job cost on a warm tier should be **independent of document size**, because the fixed cost
was moved before the snapshot. Two checks:

1. **Fixed-cost probe.** Submit a 3-byte text file and a real document. If they cost the same and
   that cost is seconds, the fixed cost is still being paid per job — the tier is warm in name only.
2. **Warm-path log lines.** `redtusk warm JVM ready (blocked at READY) after N.NNs` — N should be
   ~4s (boot + prewarm parse), not ~0.8s (boot only). A ~0.8s reading means `REDTUSK_PREWARM`
   never reached the JVM. And `redtusk warm JVM unavailable (...); cold fallback` firing at all
   means the tier has silently degraded to a per-job JVM boot.

Historical baseline for regression checks (measured 2026-08-14, before the fix):
per-job in-guest 3.30s for a 3-byte input, of which ~2.2s was rebuilding the Tika parser tree.

## Known drift traps

- **Sibling rootfs images.** Several similarly-named `.ext4` files sit in the same directory and
  only one is live. Resolve the live one from the container's `BLASTBOX_FC_ROOTFS` **through its
  bind mount**, never by name — `/var/lib/redtusk-fc/` and `/home/coz/redtusk-bb-fc/` both hold a
  `redtusk-rootfs.ext4`, and they are different images.
- **Hand-set container env** does not survive `compose up` recreating the container.
- **Two stacks share these hosts** (`redtusk-bb-*`, `titanarum-bb-*`) with independent images,
  rootfs images and blastbox versions. Always scope actions by stack prefix.

## Measured: why prewarm did NOT ship to the FC snapshot tier (2026-08-14)

Built, deployed and rolled back the same day. Recorded so the experiment is not repeated.

| | floor (3-byte job) | marginal (200KB) | typical job |
|---|---|---|---|
| live rootfs | 2546 ms | 1168 ms | ~3.7 s |
| prewarm build | 5367 ms | **140 ms** | ~5.5 s |

Both halves behaved as designed, and instrumentation confirmed it: `using warm JVM` fired on
every job, `warm JVM unavailable` never fired, and `warm JVM ready ... after 6.75s` showed the
prewarm parse ran before the checkpoint. Marginal parse cost fell 8x.

It still lost, because the two changes compose badly **on this tier specifically**:

- A warm JVM here serves exactly ONE job, so sharing the parser tree saves nothing by itself —
  a single parse constructs it once either way. The 140 ms only happens because the *prewarm*
  parse already built it.
- The prewarm parse dirties a large heap (`-Xms800m -XX:+AlwaysPreTouch`) **before** the
  checkpoint. Every restored slot then page-faults that working set back in from the `.mem`
  file, which costs more than the ~2.2 s of parser construction it removed.

So the fixed floor grew by more than the marginal cost shrank. In-guest time went 3.3 s -> 5.0 s.

Where the shared parser DOES pay off: tiers whose JVM serves many jobs (gVisor warm, the
static/push agents, CRaC restore). It is not a warm-FC optimisation.

To revisit, attack the snapshot working set rather than the parse: a smaller warm-tier heap,
dropping `AlwaysPreTouch` for the snapshot build, or a GC/compaction before the checkpoint —
then re-measure with `scripts/verify_warm_tier.sh`, which is what caught this.

## THE regression: the worker jar got 3.2x slower between 2026-06-11 and 2026-08-14

Controlled measurement (same JVM, same flags, same file-IPC harness, same container image —
**only the jar mounted in differs**):

```
old.jar (from redtusk-worker:crac, built 2026-06-11)  boot->ready 342ms   ready->DOC 1832ms
new.jar (built from current source, 2026-08-14)       boot->ready 338ms   ready->DOC 5772ms
```

Boot is identical, so this is not JVM startup, AOT, CRaC, blastbox, or the tier. It is inside
the worker jar — i.e. the Tika fork (`TIKA_FORK_SHA`, currently
`de08f007adf6d51e10166dfb07ad9f9ab281c35b`) or the worker code built around it. A trivial 43-byte
HTML document went from 1.8s to 5.8s.

This dominates every other per-job cost on the fleet, and it is the reason the tier "used to be
fast": the 2026-06-11 CRaC image does a full restore-plus-job in ~2.35s, while anything built
from current source takes ~8.9s on the identical path.

**Bisect range: 2026-06-11 -> now.** The Tika upstream sync landed inside that window and is the
prime suspect. Reproduce with the jar-swap probe above — it isolates the jar in ~30 seconds and
needs no fleet, no rootfs and no deploy.

Two things ruled OUT by controlled A/B, so do not re-investigate them:

- **The shared parser tree is neutral here.** Identical tree and Dockerfiles, only `sharedParser`
  reverted: 8908/9077/8857ms vs 9050/8921/8865ms. A warm JVM on these tiers serves exactly one
  job, so hoisting the parser saves nothing; it only pays off where one JVM serves many.
- **Checkpoint size is not the cause.** Both images' `/app/checkpoint` are 43-44MB.

Beware when comparing images: `redtusk-worker:crac` is two months old and was built from an older
Dockerfile generation. Comparing it against a fresh build varies the jar AND the build recipe at
once. Two conclusions were drawn wrongly in this session before the variables were separated.

### Bisected: the Tika sync broke default-config caching

Timing `new AutoDetectParser()` twice in one JVM, same JDK/flags, only the jar differs:

```
b54f5612 (2026-06-15, pre-sync)  firstCtor  722ms   secondCtor   24ms
de08f007 (2026-08-08, current)   firstCtor 4324ms   secondCtor 3094ms
```

Before the sync, `TikaConfig.getDefaultConfig()` handed back a cached singleton, so a second
construction was nearly free. After it, EVERY construction redoes ~3.1s of work, and even the
first regressed 722ms -> 4324ms. Parser count is identical (140 in both), so this is not a bigger
parser set — it is lost caching.

Bisect, by pin (jar-swap probe, ~2 min per build):

```
1a543d56 (~06-11)  1858 ms   FAST
b54f5612 (06-15)   1828 ms   FAST      <- last good
fe5933d1 (07-19)   -- SHA no longer exists in the fork (rebased away)
0a0372e4 (07-19)   5621 ms   SLOW      <- first bad
f2b166c6 (07-20)   5598 ms   SLOW
de08f007 (08-08)   5772 ms   SLOW
```

**Culprit range: `b54f5612..0a0372e4` in wmetcalf/tika `4.0-upstream-office-links`** — the
upstream sync merge. Remaining work is a git bisect inside that range in the fork itself.

This also explains why hoisting the parser tree (`sharedParser`) measured as a 300x win in a
microbenchmark but neutral on the fleet: these tiers construct exactly once per job, and the
FIRST construction regressed too. Fixing the caching in the fork recovers ~3.6s per job on every
tier at once — worth far more than any tier-level tuning.

## Measured scaling: slot count and spawn concurrency are COMPLEMENTARY (2026-08-17)

Steady-state throughput, measured over the middle of each run (excluding warmup and the drain
tail — a cumulative rate is dragged down badly by one straggler, see below):

| config | steady-state |
|---|---|
| serial spawn, 16 warm slots | 1.67/s |
| serial spawn, 24 warm slots | 1.81/s |
| spawn concurrency 4, 16 slots | 1.85/s |
| **spawn concurrency 4, 24 slots** | **2.60/s** |
| spawn concurrency 8, 32 slots | 2.65/s (+2%, not worth the RAM) |

Neither knob alone gets past ~1.85/s: more slots need a faster refill rate to stay fed, and
serial spawning capped refill at ~1.74 slots/s. Judging the concurrency change at a fixed 16
slots made it look worthless (1.85 vs 1.81 for simply running 24 serial slots) — it is worth
+44% once the slot count moves with it.

**Do not measure with the harness's final cumulative rate.** In a 600-job run, 599 jobs completed
at ~1.78/s and then ONE straggler hung ~90s, decaying the printed number to 1.17/s. Compute the
rate over a mid-run window instead.

### The next bottleneck is dispatcher-side, not the pool

At 24 slots the spawn rate, job-start rate and completion rate are all pinned at ~1.7/s, and a
freshly spawned slot waits **3.16s (p90 5.4s)** before it is handed work while in-guest time is
~1.1s. Slot supply is no longer the constraint; per-job dispatcher work (claim, sample
materialisation, staging, seal, upload) is.

### The autosizer's per-slot footprint is ~8x too conservative

`node_sizer` budgets `Σ ceiling_i · footprint_i ≤ budget` with
`BLASTBOX_NODE_ENGINE_REDTUSK_RAM_MIB=2048`. Measured on a live 24-slot pool: **PSS 243 MB/slot**
(RSS 318 MB), because every restored slot COW-shares ONE 2.0 GB snapshot `.mem` rather than
owning 2 GB. The real model is "one 2 GB shared image + ~250 MB per slot", so the autosizer
would under-provision a warm-snapshot FC tier by roughly 8x, and on a multi-engine node its
water-fill would starve the other engines for RAM that is never actually used.

`spawn_concurrency` itself needs no sizer change: in-flight spawns count against
`concurrent_ceiling` (the gate inside `_gated_spawn`), so the ceiling still bounds total real
workers. Verified under load — peak 25 firecracker processes against a ceiling of 32.

### The 1-in-600 straggler is one pathological document

`ransomeware-guide.pdf` (8.4 MB, 151 embedded entries) takes **111s end-to-end, 84s of it in the
parse**, against the engine's 120s worker timeout. It sits ON the boundary, so it randomly either
completes, trips `engine_error: timed out after 120.0 seconds`, or outlives its warm worker and is
reaped as "warm worker abandoned: owning dispatcher gone". It failed 3 times in one afternoon and
is the single job that ruined the 600-job run's headline number. Not a pool defect.

Also note: `total_s` in the job store is dominated by QUEUE time during a burst (jobs showing
~430s total had 1.6–13.7s of run time). Use `finished_at - started_at` to judge engine speed.
