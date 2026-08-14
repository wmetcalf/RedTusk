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
