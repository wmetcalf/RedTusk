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
