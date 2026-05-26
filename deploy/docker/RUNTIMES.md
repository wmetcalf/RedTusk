# Worker container runtimes

RedTusk's per-job worker is an OCI container; the dispatcher selects the
OCI runtime at `docker run` time. The runtime is the security boundary
between an untrusted document and the host kernel.

Three runtimes are supported, set via the `REDTUSK_WORKER_RUNTIME` env
var (in `deploy/docker/.env` for compose, or directly for one-shot mode).
Empty (the default) means auto-detect — prefer runsc when registered,
fall back to runc.

| Setting | Boundary | When | Cost |
|---|---|---|---|
| `""` (auto) | best available, prefer runsc | default | — |
| `runc` | Linux namespaces + cgroups + seccomp + cap-drop | trusted-document deployments; CI smoke tests; hosts where gVisor 9p breaks something | shared host kernel |
| `runsc` | gVisor — a userspace re-implementation of the Linux kernel intercepts syscalls | default for untrusted documents on most Linux hosts | ~10-30% throughput overhead vs runc; some workloads incompatible (large mmap, FIFOs, certain ioctls) |
| `kata` | Kata Containers microVM — each container gets its own Linux kernel via Firecracker/QEMU, hardware-enforced boundary | strongest isolation; required for hostile/0-day-bearing inputs | needs `/dev/kvm` on the host; bare metal or AWS C8i/M8i/R8i with `NestedVirtualization=true`; small per-container memory overhead for the guest kernel |

## Setting up `kata` on a Linux host

1. The host must expose KVM: `ls /dev/kvm` must succeed.
   - Bare metal: usually works.
   - AWS: only `c8i.*`, `m8i.*`, `r8i.*` instances with
     `NestedVirtualization=true` set at launch (or any `.metal` instance).
   - Other clouds vary; check their nested-virtualization documentation.

2. Install Kata Containers and register it as a Docker runtime:
   ```sh
   # Debian/Ubuntu — quickest path via kata-deploy or distro packages
   curl -fsSL https://download.opensuse.org/repositories/home:/katacontainers:/releases:/$(uname -m):/master/Debian_11/Release.key | sudo gpg --dearmor -o /usr/share/keyrings/kata-containers.gpg
   echo "deb [signed-by=/usr/share/keyrings/kata-containers.gpg] https://download.opensuse.org/repositories/home:/katacontainers:/releases:/$(uname -m):/master/Debian_11/ /" | sudo tee /etc/apt/sources.list.d/kata-containers.list
   sudo apt-get update && sudo apt-get install -y kata-runtime kata-shim
   ```

3. Add the runtime to `/etc/docker/daemon.json`:
   ```json
   {
     "runtimes": {
       "kata": {
         "path": "/usr/bin/kata-runtime"
       }
     }
   }
   ```
   then `sudo systemctl restart docker`.

4. Verify with `docker info | grep -i runtimes` — `kata` should be listed.

5. Set in `deploy/docker/.env`:
   ```
   REDTUSK_WORKER_RUNTIME=kata
   ```
   and restart the api: `./deploy/docker/redtusk-compose up -d --force-recreate api`.

## Setting up on AWS

For `kata`:
- Launch a `c8i.2xlarge` or larger via the CLI/API with
  `--nested-virtualization-enabled true` (or set in the launch template).
- Install Kata as above on the instance.
- Same `REDTUSK_WORKER_RUNTIME=kata` in `.env`.

For `runsc` (gVisor):
- Any EC2 instance type; install gVisor and register as Docker runtime.

For local dev → AWS parity: same Dockerfile, same `--runtime` setting,
just different host. The worker image (`redtusk-worker:default`) is
runtime-agnostic — it works under all three.

## Empirical notes from production testing

Tested on toolz2 (Ubuntu 24.04, Intel Xeon, KVM available) with Kata
Containers 3.31.0 + the redtusk-worker:default image and a 200-file
.lnk benchmark vs the gVisor baseline:

| metric                 | gVisor (default)   | Kata + QEMU + virtio-fs |
|------------------------|--------------------|-------------------------|
| parse_ms p50           | 2.11s              | 1.67s  (-21%)           |
| processing_ms p50      | 4.76s              | 3.79s  (-20%)           |
| spawn_duration mean    | ~15s               | **64.75s**              |
| pool_wait_ms p50       | 0.05s              | **48.02s**              |
| throughput (batch)     | ~30 jobs/min       | ~24 jobs/min            |

**Per-job parse work is genuinely faster under Kata** (likely because
the JVM runs against a real Linux kernel instead of gVisor's userspace
emulation). **But spawn cost dominates under load** — 16 concurrent
QEMU boots serialize on the Docker daemon and KVM resource setup, and
each fresh VM kernel-init costs several seconds.

VM templating (Kata's [factory] section) would normally fix this, but
it is **incompatible with virtio-fs / file-backed memory** by design
(memory cloning vs host fd-sharing conflict). To use templating you'd
have to redesign worker IPC to use vsock + a block-device rootfs
instead of bind mounts — a significant change to the dispatcher and
worker contract.

Firecracker (`configuration-fc.toml`) doesn't ship with virtio-fs in
this Kata build either, so it needs a containerd snapshotter swap
(devmapper or nydus) before it can run a container with bind mounts.
Also significant infra work.

**Net recommendation**: stay on `runsc` for production today. Use
`kata` only if you want the stronger sandbox AND can tolerate the
~20% throughput hit. The microVM-isolation upgrade is most worthwhile
when paired with a future IPC redesign (vsock + block-device rootfs);
at that point templating or Firecracker become viable and Kata can
beat gVisor on throughput AND security simultaneously.

## Kernel-CVE exposure per runtime

A worker that runs under `runc` shares the host kernel. Local-privilege-
escalation CVEs in the Linux kernel (e.g. **CVE-2026-31431 "CopyFail"**
in `algif_aead`) are reachable from inside the container unless seccomp
explicitly blocks the entry point. Specifically: `socket(AF_ALG, ...)`
is **NOT blocked by Docker's default seccomp profile** — verified
empirically.

| Runtime | Default exposure | How to harden |
|---|---|---|
| `runsc` (gVisor) | safe — gVisor's userspace kernel does not implement AF_ALG; `socket(AF_ALG, ...)` returns EAFNOSUPPORT | no action required |
| `kata` | safe — guest microVM has its own kernel; host kernel CVEs don't traverse the hypervisor boundary | no action required |
| `runc` | **VULNERABLE** with Docker default seccomp | set `REDTUSK_WORKER_SECCOMP_PROFILE=/host/path/to/redtusk.seccomp.json` (shipped under `deploy/seccomp/`); or set `REDTUSK_DEFAULT_RUNC_SECCOMP` to auto-apply it for every runc spawn |

Our shipped `deploy/seccomp/redtusk.seccomp.json` is default-deny and
does not allow `socket()` at all — it closes AF_ALG along with every
other network family the worker doesn't need. The dispatcher logs a
`container.runc_default_seccomp` warning at first spawn when runc is
selected with no profile, so the exposure is visible in operational
logs.

## Verifying which runtime processed a job

Each job result includes a sandbox subsection:
```json
{
  "sandbox": {
    "profile": "default",
    "runtime": "kata",         // ← effective runtime
    "appcds": true,
    "ksm": true,
    "crac": false
  }
}
```

`runtime` reflects what was actually used, not what was requested. If
the configured runtime isn't registered with Docker, the dispatcher
falls back to the auto-detected one and warns at startup.
