# Deployment action inventory

What must be rebuilt, and where it lands, for each kind of version bump.

Run `scripts/deploy_inventory.sh` **before and after** any deployment. It reports what is
actually deployed and exits non-zero on drift.

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
