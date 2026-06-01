# Firecracker microVM worker

End-to-end **FC + vsock control + virtio-blk output + Java CRaC** path for
redtusk-worker, wired into RedTusk's pool/dispatcher
(`FirecrackerWorkerRuntime`). Each job runs in a fresh Firecracker microVM
with a pre-warmed JVM restored from a CRaC checkpoint.

- **Control plane** (handshake, job descriptor, input bytes): **AF_VSOCK**
  inside the VM ↔ AF_UNIX on the host. Small payloads, reliable.
- **Output plane** (metadata.json + artifacts): a per-slot **virtio-blk
  ext4 disk** the guest mounts at `/tmp/redtusk-out`. The host reads it back
  after the VM powers off. Output does **not** go over vsock.

Enable with `REDTUSK_WORKER_RUNTIME=firecracker`.

## Why output is on a disk, not vsock

The guest's virtio-vsock driver **corrupts large stream transfers under
concurrent host load** — the wire gains extra bytes beyond the declared frame
length (the worker provably sends exactly `payload.length`; the host reads it
correctly; the transport mangles it in between). A concurrency sweep made it
unambiguous: 0% failure at concurrency 1, ~44% at concurrency 8 with 2 vCPUs,
and it scaled with payload size (large artifacts corrupted on every attempt).

The fix has three layers, all required:

1. **`fc_vcpu_count=1`** — with >1 vCPU the JVM's socket writes race the
   guest vsock driver across CPUs. One vCPU serializes it (44% → ~7%). Tika
   parse is effectively single-threaded, so the throughput cost is negligible.
2. **Output on a virtio-blk disk** — keeps large transfers off vsock entirely.
   This is what takes corruption to **0**. vsock carries only the small,
   reliable control/job/input frames.
3. **Retry-on-`VsockProtocolError`** (`fc_vsock_retries`, dispatcher) — a
   safety net for any residual control-plane desync; re-runs the job on a
   fresh microVM.

Plus an operational rule: **don't oversubscribe** — keep
`(pool_warm_size + pool_burst_size) × fc_vcpu_count ≤ host cores`.

### Result (932-file stratified corpus, FC alone, in-flight 28)

| metric | gVisor (prod) | **FC (fixed)** |
|---|---|---|
| success | 931/932 | **932/932 (100%)** |
| wall | 1661 s | **707 s** (~2.3×) |
| pool_wait p50 | 61,361 ms | **291 ms** |
| processing p95 | 27,901 ms | **11,983 ms** (~2.3×) |
| peak worker RSS | 49 GB | **~20 GB** |

The warm pool genuinely keeps up under FC (microVM restore ≈ 1.2 s), so jobs
almost never wait — vs gVisor's pool saturating and queueing for cold-spawned
containers.

## What's here

| File | Purpose |
|---|---|
| `init-vsock` | FC rootfs init (installed as `/init`): mount tmpfses, mount the virtio-blk **output disk** (`/dev/vdb`) at `/tmp/redtusk-out`, bind the `virtio_vsock` driver, `exec java -XX:CRaCRestoreFrom=/app/checkpoint`, cleanly unmount the output disk before poweroff |
| `init` / `fc-run.sh` | Older pure-virtio-blk one-shot variant (no vsock, cold boot per job). Kept as a reference/fallback; not used by the pool. |
| `fc-config.json` | Example FC microVM config |
| `README.md` | This document |

## Architecture (vsock control + disk output + CRaC + FC)

The diagram below applies to *both* run modes — "host" here means the process
running `FirecrackerWorkerRuntime` (the bare-metal `redtusk serve` in Mode B,
or the `redtusk-api-fc` container in Mode A). KVM is hardware, so the
microVMs themselves are real hardware-isolated VMs regardless.

```
  ┌─────────────────────────────────────┐    ┌────────────────────────────────┐
  │ host (FirecrackerWorkerRuntime)     │    │ Firecracker microVM (per job)  │
  │                                     │    │                                │
  │ create per-slot outdisk.ext4        │    │ /init (init-vsock)             │
  │ bind AF_UNIX <vsock_uds>_<port>     │    │   ├ mount /dev/vdb → /tmp/      │
  │ launch FC: drive[0]=rootfs (ro),    │    │   │     redtusk-out  (output)  │
  │   drive[1]=outdisk (rw, vdb),       │◄══►│   ├ bind virtio_vsock driver   │
  │   vsock{uds_path=<vsock_uds>}       │    │   └ exec java warp restore     │
  │                                     │    │        ↓                       │
  │ ◄─── READY (skip dup READYs)        │    │   VsockIpcChannel.afterRestore │
  │ ───► GO                             │    │   reads /proc/self/environ     │
  │ ───► JOB <n>\n<json>                │    │   opens AF_VSOCK(CID=2,port=N) │
  │ ───► INPUT <m>\n<bytes>             │    │   sends READY, awaits GO       │
  │      (worker writes results to the  │    │   parses → writes /tmp/redtusk │
  │       output DISK, not vsock)       │    │     -out  (= the disk)         │
  │ wait for FC exit (= done signal)    │    │   exits → init umounts disk    │
  │ debugfs rdump outdisk → /out        │    │   → sync → poweroff            │
  │ FC exits → slot reaped              │    │                                │
  └─────────────────────────────────────┘    └────────────────────────────────┘
```

The host reads the ext4 image **without root** via
`debugfs -R "rdump / <dest>" outdisk.ext4`. The "done" signal is the FC
process exiting (the guest powers off when the worker finishes) — the host
does **not** wait for a vsock DONE frame, because the worker closes vsock on
exit and a premature close would look like corruption and trigger a spurious
retry.

## How "disk-output mode" is detected at runtime

There is **no config flag** to turn disk-output on or off. The worker
auto-detects at restore time by checking whether `/dev/vdb` exists:

* **Firecracker** attaches a per-slot virtio-blk → `/dev/vdb` is present →
  `diskOutputMode=true` → `VsockIpcChannel.sendResult` /  `sendArtifact` are
  no-ops, and `Main.java` skips the `Files.readAllBytes` that would have
  fed them (`IpcChannel.outputsOverIpc() == false`).
* **Docker-`microvm`/kata** does not attach an extra drive → no `/dev/vdb`
  → `diskOutputMode=false` → `VsockIpcChannel` streams `RESULT`/`ARTIFACT`
  frames the way it always did, so that path keeps working unchanged.

The same `VsockIpcChannel` class (and the same checkpointed JVM image)
serves both flavors. `afterRestore` logs `diskOutputMode=<bool>` so you can
confirm which mode a slot picked up from its `fc.log`.

Critical gotchas discovered + fixed:

1. **virtio-vsock corrupts large transfers under concurrency** — see "Why
   output is on a disk" above. Output moved to virtio-blk; `fc_vcpu_count=1`.
2. **`/proc/self/environ` on a CRaC-restored process reflects the BUILD
   environ, not the restore environ.** `System.getenv()` caches at JVM start,
   which is well-known; less obvious is that `/proc/self/environ` is set by
   the kernel at `execve` and isn't rewritten by `CRaCRestoreFrom`, so it
   still shows the values the Dockerfile's `RUN java …` was launched with.
   The PORT/CID `getEnvFromProc` reads in `VsockIpcChannel.afterRestore`
   "work" only because `build-vsock-checkpoint.sh` sets them to the same
   values FC's `init-vsock` sets at runtime — a coincidence, not a
   propagation. **Don't trust `/proc/self/environ` for a value that differs
   between build and restore** — use a real environmental signal instead
   (the disk-output mode detection above checks `/dev/vdb` existence for
   exactly this reason).
3. **CRaC re-announces READY**: `afterRestore` (fired via both org.crac and
   jdk.crac registrations) re-sends READY; the dispatcher skips stray READY
   frames.
4. **Stray `-jar` on restore**: `java -XX:CRaCRestoreFrom=… -jar app.jar`
   makes CRaC try to launch a "new main entry" (ClassNotFoundException, noisy
   `RestoreException`). Restore continues the checkpointed process — no `-jar`.
5. **junixsocket caches `AFSocket.supports(CAPABILITY_VSOCK)`**: skip the
   supports check; let `connect()` surface the real error.
6. **virtio_vsock driver doesn't auto-bind without udev**: init walks
   `/sys/bus/virtio/devices/` for class `0x0013` and binds it.
7. **Kernel needs `CONFIG_KSM=y` + `CONFIG_TRANSPARENT_HUGEPAGE=y`**: the warp
   engine `madvise`s on restore; without these it aborts EINVAL.
8. **`uds_path` ownership**: Firecracker binds the gateway at `uds_path`; the
   dispatcher binds only `<uds_path>_<port>` for the inbound listener.

## Quick setup (recommended)

```sh
# from the repo root:
scripts/setup_firecracker_host.sh                 # rootfs + perms, kernel skipped
scripts/setup_firecracker_host.sh --with-kernel   # also build a 6.18.x microVM kernel
```

Idempotent. Handles e2fsprogs install, `kvm` group membership, firecracker
binary discovery, the `docker build` of `redtusk-worker:crac-vsock`, ext4
assembly with the disk-output `init-vsock`, and stages assets at
`/var/lib/redtusk/firecracker/{vmlinux,rootfs-vsock.ext4}` (override with
`--state-dir`). Prints the env vars to run `redtusk serve` when done.

The manual steps below are what the script does — useful if you want to
build piecewise or understand the layers.

## Run mode A: docker-compose stack (just like gVisor)

The api/dispatcher can run **inside the compose stack** and still launch FC
microVMs — the container gets `/dev/kvm` + the `firecracker` binary + e2fsprogs
baked in via `Dockerfile.fc-dispatcher`. Each microVM is a sibling subprocess
of the dispatcher inside the api container; KVM is hardware so the microVMs
themselves are still real hardware-isolated VMs.

```sh
# 1. Pre-build FC kernel + rootfs on the host (one time)
scripts/setup_firecracker_host.sh --with-kernel

# 2. Bring up the stack with the FC overlay
./deploy/docker/redtusk-compose --firecracker up --build -d
./deploy/docker/redtusk-compose --firecracker logs -f api
./deploy/docker/redtusk-compose --firecracker down
```

The wrapper auto-detects the host's `kvm` group GID (the same way it auto-
detects `DOCKER_GID`) and writes it to `.env`. The overlay adds:

* `--device /dev/kvm` and `group_add: [KVM_GID]` so UID 10001 inside the
  container can open `/dev/kvm`.
* Read-only bind-mount of `${REDTUSK_FC_HOST_DIR:-/var/lib/redtusk/firecracker}`
  (the kernel + rootfs you built in step 1) at the same path inside the
  container.
* `REDTUSK_WORKER_RUNTIME=firecracker` + the FC path env vars.
* `/tmp` tmpfs bumped to 1 GiB (Starlette spools large multipart uploads
  there; the gVisor default 128 MiB ENOSPC's under concurrent big uploads).

The wrapper pre-flight-checks that the FC assets exist; if not, it tells you
how to build them. The `docker-compose.firecracker.yml` overlay is the single
source of truth for what FC needs at compose time.

## Building the host environment (manual, used by both modes)

The `setup_firecracker_host.sh` script automates these steps. They're here in
case you want to understand or build piecewise.

```sh
WORKDIR=/var/lib/redtusk/firecracker      # or any persistent dir
sudo mkdir -p $WORKDIR && cd $WORKDIR

# 1. Kernel with KSM + transparent hugepages (warp restore needs both)
curl -fsSL -O https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.18.28.tar.xz
tar -xf linux-6.18.28.tar.xz && cd linux-6.18.28
cp /path/to/minimal-microvm.config .config
sed -i 's/^# CONFIG_KSM is not set/CONFIG_KSM=y/' .config
sed -i 's/^# CONFIG_TRANSPARENT_HUGEPAGE is not set/CONFIG_TRANSPARENT_HUGEPAGE=y\nCONFIG_TRANSPARENT_HUGEPAGE_ALWAYS=y/' .config
make olddefconfig && make -j$(nproc) vmlinux
cp vmlinux $WORKDIR/vmlinux
cd ..

# 2. Build the worker rootfs from the CRaC image.
#    --no-cache-filter build,runtime forces the worker recompile + re-checkpoint
#    while keeping the (slow) tika/zxing stages cached.
sudo docker build -f deploy/docker/Dockerfile.crac \
    --no-cache-filter build,runtime -t redtusk-worker:crac-vsock .
CID=$(sudo docker create redtusk-worker:crac-vsock)
sudo docker export $CID > rootfs-vsock.tar && sudo docker rm $CID
truncate -s 2G rootfs-vsock.ext4
mkfs.ext4 -q -F rootfs-vsock.ext4
sudo mkdir -p mnt && sudo mount -o loop rootfs-vsock.ext4 mnt
sudo tar -xf rootfs-vsock.tar -C mnt
sudo install -m 755 deploy/firecracker/init-vsock mnt/init   # NOTE: the disk-output init
sudo umount mnt && rm -f rootfs-vsock.tar
```

## Run mode B: host-level `redtusk serve` (no compose)

If you prefer a bare-metal `redtusk serve` (no api container — e.g. for
benchmarking, profiling, or environments where compose isn't available),
point the runtime at the assets directly:

```sh
export REDTUSK_WORKER_RUNTIME=firecracker
export REDTUSK_FC_KERNEL=$WORKDIR/vmlinux
export REDTUSK_FC_ROOTFS=$WORKDIR/rootfs-vsock.ext4
export REDTUSK_FC_BIN=/opt/kata/bin/firecracker
# size the pool to NOT oversubscribe: (warm+burst) × fc_vcpu_count ≤ cores
export REDTUSK_POOL_WARM_SIZE=$(( $(nproc) - 4 ))
export REDTUSK_POOL_BURST_SIZE=0
redtusk serve --port 8000     # under `sg kvm` if the user isn't in the kvm group
```

Requirements on the host: `/dev/kvm` accessible (member of `kvm` group),
the `firecracker` binary executable, and `mkfs.ext4` + `debugfs` (e2fsprogs)
for the per-slot output disks. The container/compose dispatcher cannot host FC
(it has no `/dev/kvm`); run the FC dispatcher on the bare-metal host.

## Tunables (`Limits` / `REDTUSK_*`)

| field | default | note |
|---|---|---|
| `fc_vcpu_count` | **1** | keep at 1 — see corruption discussion above |
| `fc_mem_mib` | 1024 | guest RAM |
| `fc_outdisk_mib` | 1024 | per-slot output disk (sparse ext4) |
| `fc_vsock_port` | 10001 | must match `redtusk.vsock_port=` in init |
| `fc_vsock_retries` | 2 | retry job on control-plane desync |

## Operational hardening

The disk-output path adds a few constraints/checks worth knowing:

* **`REDTUSK_SCRATCH_ROOT` must not contain whitespace.** The host passes
  the rdump destination to `debugfs -R "rdump / <dest>"`, and debugfs's
  request parser is space-tokenized — a path with a space silently dumps
  to the wrong target. The runtime refuses such paths up front.
* **Host-side extracted-size cap.** `_rdump_ext4_sync` enforces
  `max_extracted_bytes` on the total it extracts from the output disk. A
  worker that ignored its guest-side cap could otherwise dump up to
  `fc_outdisk_mib` (1 GB) into the slot dir. The cap shutil-rmtrees the
  partial extraction and fails the job cleanly.
* **ext4 superblock magic check.** Before invoking debugfs, the dispatcher
  validates `0xEF53` at offset 0x438 of the image. Defense-in-depth — a
  compromised JVM crafting a malformed image (to chew on a possible
  e2fsprogs CVE) gets rejected before debugfs ever sees it. debugfs still
  runs as the unprivileged dispatcher user, so blast radius is bounded.
* **`metadata.json` must be a regular file.** The dispatcher's
  `_read_capped` rejects symlinks/FIFOs/sockets (a compromised worker
  could otherwise plant `metadata.json -> /etc/passwd` for a stat oracle,
  or a FIFO that would hang `read_bytes` indefinitely). Artifacts already
  reject symlinks via `_copy_artifacts.is_symlink()`.
* **Hard-fail on missing `/dev/vdb`.** The guest init does not "fall back
  to tmpfs" if the output disk fails to mount — the host wouldn't see any
  output anyway, so the init prints `FATAL` and powers off immediately
  rather than silently losing every job's results.
* **Don't oversubscribe.** The corruption returns above
  `(pool_warm_size + pool_burst_size) × fc_vcpu_count > host cores`. Size
  conservatively; with `fc_vcpu_count=1` the limit is just `cores`.
