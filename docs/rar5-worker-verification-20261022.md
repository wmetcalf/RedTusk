# RAR5 and nested resource verification

> **Superseded decoder (2026-11-18):** the live runs below used the earlier libarchive `bsdtar` PAX-stream decoder. The branch now decodes RAR5 with a pinned static `7zz`: one bounded `7zz x -so` of the whole archive, split by the listed member sizes (archives with link entries whose stream does not match fall back to one run per member). The 7zz path has local and unit-test evidence only; re-run the live table before relying on it for 7zz.


The worker recognizes RAR5 and converts its entries to a bounded PAX stream with
libarchive `bsdtar`, inside the existing disposable worker. It does not extract
untrusted paths to a host directory. Entry count, expanded bytes and subprocess
runtime are bounded; encrypted/unsupported input reports an extraction error.

Embedded objects use a SHA-256 of their original relative resource path for storage.
The original Unicode names and resource hierarchy remain in metadata. This avoids
filesystem collisions between an archive and its children and allows Loadout to
restore the submitted names without trusting storage paths from the document.

Local checks: 58 Java tests, zero failures/errors, one existing opt-in skip; Python
unit and HTTP suites passed; targeted Ruff and strict mypy passed. Benign upstream
RAR5 fixtures and their provenance are under worker_jvm/src/test/resources/rar5.

Actual `Quotation.rar`, SHA-256
`6159da6562c28f19de6ede854e04686b7cc589e606825dc66e3daa1742475270`,
produced `Quotation.vbs`, 928795 bytes, SHA-256
`4ac7311577c78611fccfcad00611e9fe778aba3e2ebfc81a67de9bdffc88f675`:

| Host/runtime | Job | Result |
| --- | --- | --- |
| toolz2 cold | 4e82f178-5aa9-4a42-926e-4e6a2b02d5e6 | sealed ok, 12.45 s |
| toolz2 Firecracker | f10ce303-bc29-49a1-a993-7817e49f14b9 | sealed ok, 6.35 s |
| toolz3 cold | 4051cd10-cc36-4927-92bd-e8130c9cb7c0 | sealed ok, 7.42 s |
| toolz3 Firecracker | 1868ee62-848e-4684-88ad-969ae271ba7c | sealed ok, 5.37 s |
| toolz3 gVisor | acd41f9d-8147-4f0c-babe-ffae6ca1d8a8 | sealed ok, 4.57 s |

Both hosts use `redtusk:rar5-20261021` and
`redtusk-cold-worker:rar5-20261021`. The FC rootfs is stamped from
`redtusk-fc-worker:rar5-20261021`; toolz3's gVisor rootfs uses
`redtusk-warm-gvisor:rar5-20261021` and includes the Java executable on its
filesystem PATH (image ENV is absent after export).

Deployment configs were backed up as
`/home/coz/redtusk-bb/deploy/docker/docker-compose.fleet-active.json.before-rar5-20261021`.
Restore only after draining jobs, then restart the original project services:
`redtusk-bb` on toolz2 and `rt-pr83` on toolz3. Old images/rootfs remain available.
Release/proof files are in `/home/coz/loadout-audit/releases/20261021-rar5` remotely
and `/home/coz/Downloads/loadout-audit-20261021/rar5-release` locally.
