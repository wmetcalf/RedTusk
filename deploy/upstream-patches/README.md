# Upstream contribution patches

Two bug fixes discovered while exploring kata + nydus integration for
RedTusk's microvm prototype. The kata path was ultimately superseded by
the Firecracker-based runtime (see `deploy/firecracker/`), so RedTusk
itself does not apply these patches — they are kept here for upstream
submission to the respective projects.

## nydus-snapshotter-imageref.patch

Against [containerd/nydus-snapshotter](https://github.com/containerd/nydus-snapshotter)
`v0.15.15`.

**The bug:** the snapshotter looks up the image reference from
`containerd.io/snapshot/cri.image-ref` (set only by the Kubernetes CRI
plugin) or `containerd.io/snapshot/remote/stargz.reference`. With non-CRI
clients (`ctr`, `nerdctl`), neither label is present (or `TargetRefLabel`
carries a content sha256), so `registry.ParseImage()` falls back to
`docker.io/library/sha256:<hex>` and nydusd's per-mount config points at
Docker Hub for blob fetches.

**The fix:** when `NYDUS_DEFAULT_IMAGE_REF` is set in the snapshotter's
environment, treat it as authoritative and ignore the labels. This is
one-image-per-deployment (the env var is global), which fits the
single-purpose worker image case.

## kata-runtime-nydus-rootfs.patch

Against [kata-containers/kata-containers](https://github.com/kata-containers/kata-containers)
`3.31.0`. Two-line fix in `src/runtime/pkg/katautils/create.go`.

**The bug:** `CreateSandbox()` at line 134 checks `!vc.IsErofsRootFS(rootFs)`
but is missing `!vc.IsNydusRootFSType(rootFs.Type)` — the same check
`CreateContainer()` at line 267 already has. When a non-CRI client drives
kata with a nydus snapshot, `rootFs` comes through as
`Type="fuse.nydus-overlayfs"` and `Source="overlay"` (the virtual fs name,
not a path). The missing guard at line 134 means kata calls
`ResolvePath("overlay")` which becomes `<bundle>/overlay` → no such file
→ fatal "file ... does not exist".

**The fix:** mirror line 267's guard at line 134.
