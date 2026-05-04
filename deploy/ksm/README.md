# KSM (Kernel Same-page Merging) for RedTusk

KSM lets the Linux kernel deduplicate identical memory pages across processes.
RedTusk worker containers share the JVM's AppCDS archive pages via the host
page cache, and KSM can further merge JVM heap pages that contain identical
object graphs (common for Tika's internal parser registries).

## Expected memory savings

| Deployment | RSS (10 slots, no KSM) | RSS (10 slots, with KSM) |
|---|---|---|
| Default profile | ~1.5 GB | ~900 MB (~40% reduction) |
| High-density profile | ~0.5 GB | ~350 MB |

Actual savings vary by workload and document mix.

## Enable on EC2 / self-managed Linux

```sh
sudo install -m 755 deploy/ksm/enable-ksm.sh /usr/local/bin/redtusk-enable-ksm.sh
sudo install -m 644 deploy/ksm/redtusk-ksm.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now redtusk-ksm
```

## Enable on EKS on EC2 nodes

Deploy a DaemonSet that runs `enable-ksm.sh` with `hostPID: true` and a privileged
init container. The KSM kernel thread runs host-wide, so one DaemonSet pod per node
is sufficient.

## Fargate / cloud-managed

KSM is not available on Fargate (Firecracker microVM does not expose
`/sys/kernel/mm/ksm/`). The worker logs a warning at startup if it called
`madvise(MADV_MERGEABLE)` but KSM is not running. Set `REDTUSK_DISABLE_KSM=1`
to suppress the madvise call entirely on Fargate.

## Side-channel disclosure

KSM enables FLUSH+RELOAD timing observation across merged pages. The RedTusk
threat model (`--network=none`, one job per container, container destroyed after
each job) makes practical exploitation of this theoretical. Operators who
process highly sensitive documents and have adversarial access to timing channels
should set `REDTUSK_DISABLE_KSM=1`.
