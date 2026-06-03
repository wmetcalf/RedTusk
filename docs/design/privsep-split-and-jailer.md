# Privilege separation: process split + FC jailer

Status: **proposed / implementing** · 2026-06-03 · addresses the multi-agent
review's single HIGH finding.

## Problem

In Firecracker compose mode the **internet-facing api container** runs the
monolithic `serve` process — FastAPI HTTP **+** the warm pool **+** the dispatcher
claim-loop — and FC mode bolts `/dev/kvm` onto it. So one public container holds:
the HTTP attack surface, the Postgres `DATABASE_URL`, **and** `/dev/kvm` +
microVM-spawn, under Docker's default seccomp. That's a real blast-radius
regression vs the gVisor split (where the public api holds only the
docker-socket-proxy handle, not raw KVM). It is *post-RCE* (documents are parsed
in the isolated worker microVM, not this process), but a front-end RCE reaches a
KVM ioctl primitive directly.

Two independent hardenings:

1. **Process/container split** — remove `/dev/kvm` + spawn from the public api.
2. **FC jailer** — confine the VMM itself (defense-in-depth on the component that
   actually touches `/dev/kvm`).

---

## 1. Process split: `serve --role {both,api,dispatcher}`

`serve` gains a `--role` (env `REDTUSK_ROLE`), default **`both`** — so existing
single-container (gVisor) deployments are **byte-for-byte unchanged**.

| role | HTTP server | warm pool + claim-loop + spawn | `/dev/kvm` | published ports |
|---|---|---|---|---|
| `both` (default) | ✅ | ✅ | (FC: yes) | ✅ |
| `api` | ✅ | ❌ | **no** | ✅ |
| `dispatcher` | ❌ | ✅ | yes | no |

- **`api`** builds the FastAPI app + the store, but **no `Pool`/`Dispatcher`
  claim-loop**. It only enqueues jobs and serves status/artifacts. No `/dev/kvm`.
- **`dispatcher`** builds the `Pool` + `Dispatcher` claim-loop (which already
  drains the Postgres queue) and spawns FC microVMs. No uvicorn/HTTP. Holds
  `/dev/kvm`, **no published ports**, internal network only.
- Both connect to the same Postgres — the existing job queue **is** the api↔
  dispatcher channel. No new RPC.

### The sync path (the one real decision)

`POST /v1/convert` (sync) currently claims the **in-process** pool. In `api` role
there is no local pool, so sync becomes **enqueue + poll-the-store-for-result**
within the sync timeout — the `dispatcher`'s claim-loop processes it exactly like
an async job, the api just waits for the terminal state. Implementation: the sync
handler checks for a local dispatcher/pool; `both`/`dispatcher` keep the current
**direct-claim** path (no behavior change), `api` role uses **enqueue+poll**. The
warm pool still makes the actual work fast; sync adds at most one claim-loop tick.

### Compose (FC overlay)

```
api:         role=api,        Dockerfile.api,          ports, NO /dev/kvm
dispatcher:  role=dispatcher, Dockerfile.fc-dispatcher, /dev/kvm, NO ports, backend net
```

The public api loses KVM + spawn entirely; the KVM-holding dispatcher is not
internet-reachable. Both keep `DATABASE_URL` (the api inherently needs the DB).

---

## 2. FC jailer

Run the per-slot VMM under Firecracker's official **`jailer`** (ships in the same
release tarball we already download) instead of `firecracker --no-api` bare:

```
jailer --id <slot> --exec-file <fc-bin> --uid 10001 --gid 10001 \
       --cgroup-version 2 --chroot-base-dir <scratch> [--netns <ns>] \
       -- --no-api --config-file <path-relative-to-chroot>
```

Gives the VMM a chroot, cgroup, fresh net/mount/pid/ipc namespaces, uid-drop, and
the jailer's own seccomp. A VMM escape then lands in that jail as uid 10001, not
loose in the (dispatcher) container. The finicky part is the **chroot path
remap**: the kernel, rootfs, per-slot output disk, fc-config, and the vsock UDS
must live inside `<chroot>/firecracker/<slot>/root/` (hardlink/bind), and the
config paths become chroot-relative.

**Rollout safety:** gated behind `REDTUSK_FC_USE_JAILER` (default **off**) so the
proven bare-spawn path stays the default until validated — flip it on after the
toolz2 pass.

---

## Validation (toolz2, required before flipping defaults)

1. Rebuild the FC dispatcher image (jailer binary + role + jailer spawn).
2. Deploy the split overlay; confirm `docker inspect` shows **no `/dev/kvm` on the
   api**, and the dispatcher holds it.
3. Pool warms in the dispatcher; the auto-bake probe still returns COMPATIBLE.
4. `REDTUSK_FC_USE_JAILER=1`: a jailed microVM boots + restores (probe COMPATIBLE).
5. **342-doc corpus: no regression** (baseline 342/342) on the split + jailed path.
6. Back up the live rootfs + compose first; roll back on any failure.

Non-goals: the `127.0.0.1` default bind (operator chose `0.0.0.0`; documented in
`.env.example`) and a bespoke dispatcher seccomp profile (marginal over Docker's
default, high break-risk).
