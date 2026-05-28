# Worker container runtimes

RedTusk's per-job worker is a sandboxed process. The dispatcher selects
the sandbox at slot-creation time via `REDTUSK_WORKER_RUNTIME` (in
`deploy/docker/.env` for compose, or directly for one-shot mode).

| Setting | Boundary | When | Cost |
|---|---|---|---|
| `""` (auto) | best available, prefer `runsc` | default | — |
| `runc` | Linux namespaces + cgroups + seccomp + cap-drop | trusted-document deployments; CI smoke tests; hosts where gVisor's 9p breaks something | shared host kernel |
| `runsc` | gVisor — userspace re-implementation of the Linux kernel intercepts syscalls | default for untrusted documents on most Linux hosts | ~10-30% throughput overhead vs runc; some workloads incompatible (large mmap, FIFOs, certain ioctls) |
| `firecracker` | Each job runs in a fresh Firecracker microVM with vsock IPC; Java CRaC restores in ~700 ms | strongest isolation; fresh hardware boundary per job; fastest p50 on a mixed-format corpus | needs `/dev/kvm` on the host; ~1 s slot creation; see `deploy/firecracker/` |
| `kata` | Kata Containers microVM (passthrough to Docker's kata runtime if installed) | available if kata is already wired into Docker; not actively maintained by RedTusk | needs `/dev/kvm` + kata install on host |

## `runc` setup

Built into Docker. No setup.

## `runsc` (gVisor) setup

```sh
ARCH=$(uname -m)
URL=https://storage.googleapis.com/gvisor/releases/release/latest/${ARCH}
wget -q ${URL}/runsc ${URL}/runsc.sha512 ${URL}/containerd-shim-runsc-v1 ${URL}/containerd-shim-runsc-v1.sha512
sha512sum -c runsc.sha512 -c containerd-shim-runsc-v1.sha512
sudo install -m 755 runsc containerd-shim-runsc-v1 /usr/local/bin/
```

Add to `/etc/docker/daemon.json`:
```json
{
  "runtimes": {
    "runsc": {"path": "/usr/local/bin/runsc"}
  }
}
```

Restart Docker, verify with `docker info | grep -i runtimes`, then set
`REDTUSK_WORKER_RUNTIME=runsc` in the .env.

## `firecracker` setup

See `deploy/firecracker/README.md`. Requires:

1. `/dev/kvm` on the host (bare metal or AWS `c8i`/`m8i`/`r8i` with nested
   virt enabled), `firecracker` binary, and e2fsprogs (`mkfs.ext4`/`debugfs`)
2. A kernel built with `CONFIG_KSM=y` and `CONFIG_TRANSPARENT_HUGEPAGE=y`
   (the Azul Zulu warp engine uses both internally on restore)
3. A custom rootfs built from `redtusk-worker:crac-vsock` (init mounts the
   per-slot virtio-blk output disk — see the build steps in the FC README)
4. `REDTUSK_WORKER_RUNTIME=firecracker`. `FirecrackerWorkerRuntime` is wired
   into the pool/dispatcher. NB: the **compose dispatcher cannot host FC**
   (no `/dev/kvm` in the container) — run the FC dispatcher on the bare-metal
   host (`redtusk serve`, under `sg kvm` if not in the kvm group).

IPC split: vsock carries the control handshake + job descriptor + input;
**output (metadata + artifacts) goes to a per-slot virtio-blk disk**, not
vsock (the guest vsock layer corrupts large transfers under concurrency).
Keep `fc_vcpu_count=1` and don't oversubscribe — see the FC README. The
worker auto-detects disk-output mode by checking `/dev/vdb` existence at
restore (no config flag), so the same rootfs serves both FC (with the
output drive) and any legacy Docker-`microvm`/kata streaming setup
(without it).

Operator notes:
* `REDTUSK_SCRATCH_ROOT` **must not contain whitespace** — the host's
  `debugfs rdump` request would misparse otherwise. The runtime refuses
  such paths up front.
* The dispatcher needs `mkfs.ext4` + `debugfs` (e2fsprogs) for per-slot
  output disks, plus the `firecracker` binary and `/dev/kvm` access
  (kvm group or root). The container/compose dispatcher has none of
  these — run the FC dispatcher on the bare-metal host.
* `max_extracted_bytes` is enforced **host-side** on the rdumped output
  (a runaway worker can otherwise fill the slot dir up to
  `fc_outdisk_mib`).

Full 932-file stratified corpus (FC alone, in-flight 28):

| Runtime | success | wall | pool_wait p50 | processing p95 |
|---|---|---|---|---|
| gVisor | 931/932 | 1661 s | 61.4 s | 27.9 s |
| **FC (fixed)** | **932/932** | **707 s** | **0.29 s** | **12.0 s** |

FC is 100% reliable and ~2.3× faster wall with the tightest p95 tail; gVisor's
outliers are I/O-heavy formats (xlsx) where its 9p filesystem stalls, and its
warm pool can't keep up under a burst (61 s median pool_wait).

## `kata` setup

Not documented here — RedTusk's dispatcher passes `--runtime=kata` to
Docker if `REDTUSK_WORKER_RUNTIME=kata` is set, but we don't ship a
recipe for installing kata anymore. If you have it working from a
different source, just point at it. The `firecracker` runtime is the
recommended microVM path going forward.

## AWS notes

- `runc` and `runsc`: any instance type.
- `firecracker` and `kata`: only on instances with nested virtualization
  (`c8i`/`m8i`/`r8i` with `--nested-virtualization-enabled true`, or
  `.metal` instances).
