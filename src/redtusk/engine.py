"""RedTusk blastbox Engine implementation.

Wraps the RedTusk JVM/Tika worker (``redtusk-worker.jar``) as a blastbox
``Engine``.  Under blastbox.host the cold worker is itself the disposable,
socket-less sandbox container, so the engine launches the JVM **in-process**
(``java -jar /app/redtusk-worker.jar --run <scratch>``) rather than shelling
out to a nested ``docker run`` (which the socket-less worker cannot do).  The
engine:

1. Writes the input file into a scratch directory, sets up the file-IPC
   handshake (``control/job.json`` + ``control/control.go``), and runs the
   JVM worker as a subprocess.
2. Parses the rmeta ``metadata.json`` the JVM worker writes to the output dir.
3. Reconstructs a recursive ``EmbeddedResource`` tree from the flat,
   depth-ordered ``extraction.entries[]`` list using a depth-stack.
4. Returns a ``DetonationResult`` with the tree as payload plus any declared
   artifacts (thumbnails, embedded files) the worker wrote.

Running the worker requires a JRE (``java``) and ``redtusk-worker.jar`` on disk
— both baked into the ``redtusk-cold-worker`` image at ``/app``.  The jar, AOT
cache, java binary and JVM flags are env-overridable (``REDTUSK_WORKER_JAR``,
``REDTUSK_AOT_CACHE``, ``REDTUSK_JAVA_BIN``, ``REDTUSK_JAVA_OPTS``) for dev/test.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shlex
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from blastbox.contract import (
    DeclaredArtifact,
    Detection,
    EmbeddedResource,
    ExtractedText,
    Record,
    Warning,
)
from blastbox.limits import Limits
from blastbox.worker.engine import DetonationResult

logger = logging.getLogger(__name__)

# Default locations of the JVM worker artifacts inside the cold-worker image.
# All are env-overridable so a dev box / CI can point at a locally-built jar.
_DEFAULT_JAVA_BIN = "java"
_DEFAULT_WORKER_JAR = "/app/redtusk-worker.jar"
_DEFAULT_AOT_CACHE = "/app/redtusk.aot"
_DEFAULT_JAVA_LIBRARY_PATH = "/app"

# JVM flags mirror the redtusk-worker image ENTRYPOINT.  They MUST match the
# flags the AOT cache was built with (UseSerialGC / TieredStopAtLevel=1 / 800m
# heap / native-access) or JDK 25 rejects the cache at load time.
_DEFAULT_JVM_FLAGS: tuple[str, ...] = (
    "-XX:+UseSerialGC",
    "-XX:TieredStopAtLevel=1",
    "-Xms800m",
    "-Xmx800m",
    "-XX:+AlwaysPreTouch",
    "--enable-native-access=ALL-UNNAMED",
)

# Job descriptor defaults matching the existing test harness.
_DEFAULT_JOB: dict[str, Any] = {
    "limits": {
        "max_recursion_depth": 10,
        "max_embedded_entries": 5000,
        "max_extracted_bytes": 524_288_000,
        "ocr_timeout_s": 30,
    },
    "enable_qr": False,
    "enable_ocr": False,
    "enable_thumbnails": False,
    "ocr_lang": "eng",
    "ocr_psm": 3,
    "ocr_max_image_dim": 2000,
    "ocr_skip_blank": True,
    "sandbox_profile": "default",
    "sandbox_runtime": "runc",
    "appcds": True,
    "ksm": False,
    "crac": False,
    "redtusk_version": "0.1.0",
    "zxing_path": "/usr/local/bin/ZXingReader",
    "tesseract_path": "tesseract",
}


# ---------------------------------------------------------------------------
# rmeta → blastbox contract conversion helpers
# ---------------------------------------------------------------------------


def _coerce_metadata_value(v: Any) -> Any:
    """Coerce a Tika metadata value into a ``Record``-safe type.

    Record fields accept: ``str | int | float | bool | None``, ``list[scalar]``,
    or a nested ``Record``.  Tika metadata is often a list of strings or a bare
    string; anything else is stringified so we never crash on unexpected shapes.
    """
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    if isinstance(v, list):
        coerced: list[Any] = []
        for item in v:
            if isinstance(item, (bool, int, float, str)) or item is None:
                coerced.append(item)
            else:
                coerced.append(str(item))
        return coerced
    if isinstance(v, dict):
        # Nested dict → nested Record
        return _make_record(v)
    return str(v)


def _make_record(raw: dict[str, Any]) -> Record:
    """Build a ``Record`` from a dict of Tika metadata, coercing all values."""
    fields: dict[str, Any] = {}
    for k, v in raw.items():
        safe_key = str(k)[:256]  # guard against absurdly long keys
        fields[safe_key] = _coerce_metadata_value(v)
    return Record(fields=fields)


def _build_tree(entries: list[dict[str, Any]]) -> EmbeddedResource:
    """Reconstruct the recursive ``EmbeddedResource`` tree from a flat list.

    The ``extraction.entries[]`` list is depth-ordered (parent always appears
    before its children) and each entry carries a ``depth`` integer.  We use a
    *depth-stack* to attach each entry as a child of the most-recent entry
    whose depth is one less than the current entry's depth.

    Algorithm:
    - ``stack`` is a list of ``(depth, EmbeddedResource)`` pairs, representing
      the "open" ancestry at any point.
    - For each entry, pop entries from the stack whose depth >= current depth
      (they are closed siblings or ancestors that are now fully processed).
    - Attach the new node to the top of the stack (its parent).
    - Push the new node.

    Text: each entry with non-empty ``text`` gets an ``ExtractedText`` child
    appended immediately after the ``EmbeddedResource`` is created.
    """
    if not entries:
        # Synthesize a minimal root node when the worker produced nothing.
        return EmbeddedResource(
            embedded_path="/",
            content_type="application/octet-stream",
            depth=0,
            metadata=Record(fields={}),
            children=[],
        )

    def _make_node(e: dict[str, Any]) -> EmbeddedResource:
        path = e.get("path") or "/"
        ct = e.get("content_type") or "application/octet-stream"
        depth = int(e.get("depth", 0))
        meta_raw = e.get("metadata") or {}
        # Include a small set of useful per-entry scalar fields in the Record.
        extra: dict[str, Any] = {}
        for scalar_key in ("sha256", "md5", "sha1", "size_bytes", "language", "error",
                           "phash", "colorhash"):
            val = e.get(scalar_key)
            if val is not None:
                extra[scalar_key] = _coerce_metadata_value(val)
        combined: dict[str, Any] = {**extra}
        if isinstance(meta_raw, dict):
            for k, v in meta_raw.items():
                combined[str(k)] = _coerce_metadata_value(v)
        node = EmbeddedResource(
            embedded_path=path,
            content_type=ct,
            depth=depth,
            metadata=Record(fields=combined),
            children=[],
        )
        text = e.get("text") or ""
        if text:
            node.children.append(
                ExtractedText(text=text, char_count=len(text))
            )
        return node

    # Build all nodes first.
    nodes = [_make_node(e) for e in entries]

    # Depth-stack tree assembly.
    # stack: list of (node_depth, node) open ancestors
    root = nodes[0]
    if len(nodes) == 1:
        return root

    stack: list[tuple[int, EmbeddedResource]] = [(root.depth, root)]

    for node in nodes[1:]:
        # Pop until the top of the stack is the correct parent
        # (depth == node.depth - 1), or we're back to root.
        while len(stack) > 1 and stack[-1][0] >= node.depth:
            stack.pop()
        # Attach as child of the current stack top.
        parent = stack[-1][1]
        parent.children.append(node)
        stack.append((node.depth, node))

    return root


# ---------------------------------------------------------------------------
# Worker invocation
# ---------------------------------------------------------------------------


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _java_worker_argv(scratch: Path) -> list[str]:
    """Build the in-process JVM worker argv (``java ... -jar ... --run <scratch>``).

    Mirrors the redtusk-worker image ENTRYPOINT so the AOT cache — which is
    flag-sensitive — loads cleanly.  Everything is env-overridable:

    - ``REDTUSK_JAVA_BIN``          java executable (default ``java``)
    - ``REDTUSK_WORKER_JAR``        worker jar (default ``/app/redtusk-worker.jar``)
    - ``REDTUSK_AOT_CACHE``         AOT cache; only added when the file exists
    - ``REDTUSK_JAVA_LIBRARY_PATH`` native lib dir (default ``/app``)
    - ``REDTUSK_JAVA_OPTS``         full JVM-flag override (shlex-split), replacing
                                    the default flag bundle entirely
    """
    java_bin = os.environ.get("REDTUSK_JAVA_BIN", _DEFAULT_JAVA_BIN)
    jar = os.environ.get("REDTUSK_WORKER_JAR", _DEFAULT_WORKER_JAR)
    lib_path = os.environ.get("REDTUSK_JAVA_LIBRARY_PATH", _DEFAULT_JAVA_LIBRARY_PATH)
    aot_cache = os.environ.get("REDTUSK_AOT_CACHE", _DEFAULT_AOT_CACHE)

    opts_override = os.environ.get("REDTUSK_JAVA_OPTS")
    if opts_override is not None:
        jvm_flags = shlex.split(opts_override)
    else:
        jvm_flags = [f"-Djava.library.path={lib_path}", *_DEFAULT_JVM_FLAGS]
        # The AOT cache is flag-sensitive and baked into the cold-worker image;
        # only load it when present so a bare dev box still runs (slower).
        if aot_cache and Path(aot_cache).is_file():
            jvm_flags.insert(0, f"-XX:AOTCache={aot_cache}")

    return [java_bin, *jvm_flags, "-jar", jar, "--run", str(scratch)]


# Seconds to wait for a warmup JVM to announce ``control.ready`` before giving up
# and falling back to the cold path.
_WARMUP_READY_TIMEOUT = 60.0

# The file-IPC scratch the CRaC checkpoint is pinned to (must be writable at
# restore — the cold worker's rootfs is read-only, only /tmp tmpfs is writable, so
# this lives under /tmp and the Dockerfile bakes the checkpoint with the same path).
_DEFAULT_CRAC_SCRATCH = "/tmp/redtusk-crac"


@dataclass
class _WarmWorker:
    """A pre-booted JVM worker blocked at READY, ready to be fed one job.

    The JVM is started by ``warmup()`` (paying the ~JVM-boot cost once, BEFORE the
    FC warm snapshot is taken) in ``--run`` mode: it announces ``control.ready``
    then blocks on ``control.go``.  ``detonate()`` writes the input + ``job.json``
    + touches ``control.go``; the already-warm JVM processes the one job and exits.
    """

    proc: subprocess.Popen[bytes]
    scratch: Path
    in_dir: Path
    control_dir: Path
    tmp: tempfile.TemporaryDirectory[str]


def _run_worker(
    input_path: Path,
    rmeta_outdir: Path,
    *,
    timeout: float = 120.0,
) -> None:
    """Run the ``redtusk-worker:default`` container against *input_path*.

    The worker uses file-IPC (``--run /scratch``):
    - ``/scratch/in/<filename>`` : read-only input
    - ``/scratch/out/``          : writable output dir (bind-mounted to *rmeta_outdir*)
    - ``/scratch/control/``      : handshake files

    The JVM worker writes ``metadata.json`` (rmeta format) + any artifact files
    into *rmeta_outdir*.  The blastbox harness writes its own ``metadata.json``
    (envelope format) to the *parent* ``outdir``; we use a subdirectory here so
    the two ``metadata.json`` files never collide.

    Protocol:
    1. Worker starts → creates ``control/control.ready``.
    2. We poll for ``control.ready``, then write ``control/job.json`` and
       touch ``control/control.go``.
    3. Worker processes, writes ``out/metadata.json``, exits 0.
    """
    input_bytes = input_path.read_bytes()
    sha256 = _sha256_bytes(input_bytes)
    filename_hint = input_path.name or "input"

    with tempfile.TemporaryDirectory() as scratch_base:
        scratch = Path(scratch_base) / "slot"
        in_dir = scratch / "in"
        control_dir = scratch / "control"

        scratch.mkdir()
        in_dir.mkdir()
        rmeta_outdir.mkdir(parents=True, exist_ok=True)
        control_dir.mkdir()

        # Write input
        (in_dir / filename_hint).write_bytes(input_bytes)

        # Build job descriptor.  The JVM worker (FileIpcChannel.receiveJob)
        # consumes input_path/output_dir *literally*, so in-process these are the
        # real host paths — not the container-relative /scratch/in, /scratch/out
        # the old docker-run path used.  output_dir is rmeta_outdir so the
        # worker's metadata.json + artifacts land under the harness outdir.
        job: dict[str, Any] = {
            **_DEFAULT_JOB,
            "input_path": str(in_dir / filename_hint),
            "output_dir": str(rmeta_outdir),
            "sha256": sha256,
            "filename_hint": filename_hint,
        }

        def _signal_worker() -> None:
            """Wait for control.ready, then write job.json + control.go."""
            ready_file = control_dir / "control.ready"
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                if ready_file.exists():
                    break
                time.sleep(0.1)
            # Write job.json then go-signal regardless (worker may have
            # already timed out waiting for us if we're very slow).
            (control_dir / "job.json").write_text(
                json.dumps(job, ensure_ascii=False), encoding="utf-8"
            )
            (control_dir / "control.go").touch()

        t = threading.Thread(target=_signal_worker, daemon=True)
        t.start()

        # Launch the JVM worker in-process.  Isolation (network=none, cap-drop,
        # tmpfs, memory/pids caps) is provided by the *outer* blastbox cold-worker
        # container — this used to be a nested ``docker run``, which the
        # socket-less cold worker cannot do.
        cmd = _java_worker_argv(scratch)
        env = {
            **os.environ,
            "REDTUSK_LOG_LEVEL": os.environ.get("REDTUSK_LOG_LEVEL", "WARNING"),
        }

        logger.debug("RedTusk JVM worker cmd: %s", " ".join(cmd))
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout,
            env=env,
        )
        t.join(timeout=5)

        if result.returncode != 0:
            stderr_tail = result.stderr.decode(errors="replace")[-2000:]
            raise RuntimeError(
                f"redtusk-worker (jvm) exited {result.returncode}: {stderr_tail}"
            )


def _crac_restore_worker(
    input_path: Path,
    rmeta_outdir: Path,
    *,
    checkpoint_dir: str,
    scratch_dir: str,
    timeout: float = 120.0,
) -> None:
    """Restore a baked CRaC checkpoint and feed it one job (file-IPC).

    A warm-JVM tier for PLAIN containers: the JVM is checkpointed at image-build
    time with Azul's warp engine, so each job ``java -XX:CRaCRestoreFrom=<dir>``
    skips the JVM cold boot (no Firecracker / gVisor C/R needed; warp needs no
    privileged caps).  *scratch_dir* MUST match the path the checkpoint was pinned
    to.  Pre-stage input + job.json + control.go, then restore: the warm JVM
    re-announces ready, sees the go signal, processes one job, writes
    metadata.json, exits.
    """
    input_bytes = input_path.read_bytes()
    filename_hint = input_path.name or "input"
    scratch = Path(scratch_dir)
    in_dir = scratch / "in"
    control_dir = scratch / "control"
    for d in (in_dir, control_dir):
        d.mkdir(parents=True, exist_ok=True)
    rmeta_outdir.mkdir(parents=True, exist_ok=True)
    # Clear stale control state from any prior restore reusing this scratch.
    for name in ("control.ready", "control.go", "job.json"):
        (control_dir / name).unlink(missing_ok=True)

    (in_dir / filename_hint).write_bytes(input_bytes)
    job: dict[str, Any] = {
        **_DEFAULT_JOB,
        "input_path": str(in_dir / filename_hint),
        "output_dir": str(rmeta_outdir),
        "sha256": _sha256_bytes(input_bytes),
        "filename_hint": filename_hint,
    }
    (control_dir / "job.json").write_text(
        json.dumps(job, ensure_ascii=False), encoding="utf-8"
    )
    (control_dir / "control.go").touch()

    java_bin = os.environ.get("REDTUSK_JAVA_BIN", _DEFAULT_JAVA_BIN)
    cmd = [java_bin, f"-XX:CRaCRestoreFrom={checkpoint_dir}"]
    env = {
        **os.environ,
        "REDTUSK_LOG_LEVEL": os.environ.get("REDTUSK_LOG_LEVEL", "WARNING"),
    }
    logger.debug("RedTusk CRaC restore cmd: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, timeout=timeout, env=env)
    if result.returncode != 0:
        stderr_tail = result.stderr.decode(errors="replace")[-2000:]
        raise RuntimeError(
            f"redtusk-worker (crac restore) exited {result.returncode}: {stderr_tail}"
        )


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class RedTuskEngine:
    """Blastbox Engine wrapping the RedTusk JVM recursive-extraction worker.

    Implements the ``blastbox.worker.engine.Engine`` protocol.
    """

    name: str = "redtusk"
    formats: frozenset[str] = frozenset({"*"})

    # Holds a pre-booted JVM after warmup(); None on the cold path.
    _warm: _WarmWorker | None = None

    def warmup(self) -> None:
        """Pre-boot a JVM worker so a warm tier (FC snapshot) captures it at READY.

        Optional + fail-soft: the blastbox warm lifecycle calls this before the
        snapshot is taken, so the ~JVM-boot cost is paid once and ``detonate()``
        feeds the already-warm JVM (saving boot per job).  Any failure leaves the
        engine on the cold path — warmup MUST NOT raise (a raise fails the slot).
        Inert on the cold path (warmup is simply never called there).
        """
        proc: subprocess.Popen[bytes] | None = None
        tmp: tempfile.TemporaryDirectory[str] | None = None
        try:
            tmp = tempfile.TemporaryDirectory(prefix="redtusk-warm-")
            scratch = Path(tmp.name) / "slot"
            in_dir = scratch / "in"
            control_dir = scratch / "control"
            for d in (scratch, in_dir, control_dir):
                d.mkdir(parents=True)

            cmd = _java_worker_argv(scratch)
            env = {
                **os.environ,
                "REDTUSK_LOG_LEVEL": os.environ.get("REDTUSK_LOG_LEVEL", "WARNING"),
            }
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env
            )

            # The JVM announces control.ready (loading Tika classes from the AOT
            # cache along the way), then blocks on control.go.
            ready = control_dir / "control.ready"
            deadline = time.monotonic() + _WARMUP_READY_TIMEOUT
            while time.monotonic() < deadline:
                if ready.exists():
                    self._warm = _WarmWorker(
                        proc=proc, scratch=scratch, in_dir=in_dir,
                        control_dir=control_dir, tmp=tmp,
                    )
                    logger.info("redtusk warm JVM ready (blocked at READY)")
                    return
                if proc.poll() is not None:
                    break  # JVM exited before signalling ready
                time.sleep(0.05)

            logger.warning("redtusk warmup: JVM did not signal ready; cold path")
            if proc.poll() is None:
                proc.kill()
            proc.wait(timeout=5)
            tmp.cleanup()
        except Exception as exc:  # noqa: BLE001
            logger.warning("redtusk warmup failed (cold path): %s", exc)
            self._warm = None
            # Don't leak the JVM process / temp dir if we raised after Popen (e.g. an
            # OSError from ready.exists() or an interrupted sleep). On the success path
            # the proc+tmp are owned by self._warm (cleaned by close()/_produce_rmeta);
            # this branch only runs on failure, where nothing else will reap them.
            if proc is not None:
                try:
                    if proc.poll() is None:
                        proc.kill()
                    proc.wait(timeout=5)
                except Exception:  # noqa: BLE001
                    pass
            if tmp is not None:
                try:
                    tmp.cleanup()
                except Exception:  # noqa: BLE001
                    pass

    def close(self) -> None:
        """Tear down an unused warm JVM (e.g. a warm slot reaped without a job)."""
        warm = self._warm
        self._warm = None
        if warm is None:
            return
        try:
            if warm.proc.poll() is None:
                warm.proc.kill()
            warm.proc.wait(timeout=5)
        except Exception:  # noqa: BLE001
            pass
        finally:
            warm.tmp.cleanup()

    def _produce_rmeta(self, input: Path, rmeta_dir: Path, timeout: float) -> None:
        """Produce the rmeta document into *rmeta_dir*.

        Three tiers, all fail-closed to cold:
        - **CRaC** (``REDTUSK_CRAC_CHECKPOINT`` set) — restore a baked warp
          checkpoint per job (warm JVM in a plain container).
        - **warm** (``warmup()`` pre-booted a JVM) — feed the already-warm JVM
          (the FC warm-snapshot tier).
        - **cold** — a fresh per-job JVM.
        """
        checkpoint = os.environ.get("REDTUSK_CRAC_CHECKPOINT")
        if checkpoint:
            scratch = os.environ.get("REDTUSK_CRAC_SCRATCH", _DEFAULT_CRAC_SCRATCH)
            try:
                _crac_restore_worker(
                    input, rmeta_dir,
                    checkpoint_dir=checkpoint, scratch_dir=scratch, timeout=timeout,
                )
                return
            except Exception as exc:  # noqa: BLE001
                logger.warning("redtusk CRaC restore failed (%s); cold fallback", exc)
                _run_worker(input, rmeta_dir, timeout=timeout)
                return

        warm = self._warm
        self._warm = None  # one job per warm JVM; consume it
        if warm is None or warm.proc.poll() is not None:
            _run_worker(input, rmeta_dir, timeout=timeout)
            return
        try:
            input_bytes = input.read_bytes()
            filename_hint = input.name or "input"
            rmeta_dir.mkdir(parents=True, exist_ok=True)
            (warm.in_dir / filename_hint).write_bytes(input_bytes)
            job: dict[str, Any] = {
                **_DEFAULT_JOB,
                "input_path": str(warm.in_dir / filename_hint),
                "output_dir": str(rmeta_dir),
                "sha256": _sha256_bytes(input_bytes),
                "filename_hint": filename_hint,
            }
            (warm.control_dir / "job.json").write_text(
                json.dumps(job, ensure_ascii=False), encoding="utf-8"
            )
            (warm.control_dir / "control.go").touch()
            try:
                _, stderr = warm.proc.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                warm.proc.kill()
                warm.proc.communicate()
                raise RuntimeError(
                    f"redtusk warm worker timed out after {timeout}s"
                ) from None
            if warm.proc.returncode != 0:
                tail = (stderr or b"").decode(errors="replace")[-2000:]
                raise RuntimeError(
                    f"redtusk-worker (warm jvm) exited {warm.proc.returncode}: {tail}"
                )
        except Exception as exc:  # noqa: BLE001
            # Fail-closed to cold: a fresh JVM produces the rmeta into the same dir.
            logger.warning("redtusk warm detonation failed (%s); cold fallback", exc)
            _run_worker(input, rmeta_dir, timeout=timeout)
            return
        finally:
            # Always reap the warm JVM + temp dir. On success communicate() already reaped
            # proc (poll() != None → no-op). On an exception BEFORE communicate() (e.g.
            # read_bytes/write_bytes raised), the JVM is still blocked on control.go — kill it
            # so it isn't leaked (it would otherwise hold its heap forever), then drop the dir.
            try:
                if warm.proc.poll() is None:
                    warm.proc.kill()
                    warm.proc.wait(timeout=5)
            except Exception:  # noqa: BLE001
                pass
            try:
                warm.tmp.cleanup()
            except Exception:  # noqa: BLE001
                pass

    def detonate(
        self,
        input: Path,
        outdir: Path,
        limits: Limits,
    ) -> DetonationResult:
        """Run the RedTusk worker; map rmeta → ``DetonationResult``.

        Steps
        -----
        1. Run the ``redtusk-worker:default`` Docker container, writing rmeta
           output into ``outdir/rmeta/`` (a subdirectory) so the JVM worker's
           ``metadata.json`` does not collide with the blastbox harness's own
           ``metadata.json`` which the harness writes to ``outdir`` after we
           return.
        2. Parse ``outdir/rmeta/metadata.json`` (the rmeta document).
        3. Rebuild the recursive ``EmbeddedResource`` tree from the flat
           ``extraction.entries[]`` list.
        4. Copy / reference any non-``metadata.json`` files the JVM wrote into
           ``outdir/rmeta/`` as ``DeclaredArtifact`` entries, with paths
           relative to ``outdir``.
        5. Map rmeta-level warnings to ``Warning`` objects.
        6. Return ``DetonationResult``.

        Exceptions propagate to the harness (which seals them as
        ``engine_error``).
        """
        # Isolate the JVM worker's output into a subdirectory so its
        # ``metadata.json`` (rmeta format) never clobbers the blastbox
        # harness's ``metadata.json`` (envelope format) in outdir.
        rmeta_dir = outdir / "rmeta"
        self._produce_rmeta(input, rmeta_dir, timeout=float(limits.timeout_s))

        meta_path = rmeta_dir / "metadata.json"
        if not meta_path.is_file():
            raise RuntimeError("redtusk worker did not produce metadata.json")

        rmeta: dict[str, Any] = json.loads(meta_path.read_bytes())

        extraction = rmeta.get("extraction", {})
        entries: list[dict[str, Any]] = extraction.get("entries", [])
        root_ct: str = extraction.get("root_content_type") or "application/octet-stream"

        # Build payload tree
        payload = _build_tree(entries)

        # Detection from root content-type.  ``label`` is capped at 64 chars by
        # the contract; long MIME types (e.g. the 71-char OOXML wordprocessingml
        # type) are truncated for the label while the full value is preserved in
        # ``mime``.
        detected = Detection(
            label=(root_ct.split(";")[0].strip() or "unknown")[:64],
            mime=root_ct,
            confidence=1.0,
            source="redtusk",
        )

        # Collect artifacts: every non-metadata.json file the JVM wrote,
        # referenced with paths relative to outdir (not rmeta_dir) so the
        # blastbox envelope path confinement passes with outdir as root.
        artifacts: list[DeclaredArtifact] = []
        used_ids: set[str] = set()
        for f in sorted(rmeta_dir.rglob("*")):
            if not f.is_file():
                continue
            # Declare rmeta/metadata.json (the recursive extraction tree) as an artifact
            # like every other rmeta file — do NOT skip it. It is served verbatim by the
            # /v1/jobs/{id}/rmeta route, so it MUST go through the trust gate: declaring it
            # makes seal_envelope re-hash it, the warm path copy+re-verify it, and the
            # manifest-enforced serve route accept it (audit M-4 — previously this file was
            # served as worker-controlled bytes the host never validated). It is distinct
            # from the blastbox ENVELOPE metadata.json at the output-dir ROOT (this one is
            # under the rmeta/ subdir → declared path "rmeta/metadata.json").
            rel_to_outdir = f.relative_to(outdir)
            rel_str = str(rel_to_outdir)
            artifact_id = _safe_artifact_id(rel_str, used_ids)
            kind = _infer_artifact_kind(rel_str)
            artifacts.append(DeclaredArtifact(id=artifact_id, path=rel_str, kind=kind))

        # Map rmeta warnings
        warnings: list[Warning] = []
        for w in rmeta.get("warnings", []):
            code = str(w.get("code") or "redtusk_warning")[:64]
            detail = str(w.get("detail") or "")[:2000]
            warnings.append(Warning(code=code, message=detail))
        if rmeta.get("truncated"):
            tr = rmeta["truncated"]
            warnings.append(Warning(
                code="truncated",
                message=f"Extraction truncated: reason={tr.get('reason')}, "
                        f"limit={tr.get('limit')}, observed={tr.get('observed')}",
            ))

        return DetonationResult(
            payload=payload,
            artifacts=artifacts,
            detected=detected,
            warnings=warnings,
            status="ok",
        )


_ARTIFACT_ID_DISALLOWED = re.compile(r"[^A-Za-z0-9._-]")


def _safe_artifact_id(rel_str: str, used: set[str]) -> str:
    """Build a contract-valid, unique ``DeclaredArtifact.id`` from a rel path.

    The blastbox contract requires ``^[A-Za-z0-9._-]{1,128}$``.  Embedded-file
    names from the JVM worker can contain spaces, unicode, or arbitrary bytes
    (e.g. an email attachment's real filename), so every disallowed char is
    mapped to ``_``.  On overflow the readable tail is kept plus a hash of the
    full path for uniqueness, and any residual collision is disambiguated — the
    envelope must never carry a duplicate artifact id (blastbox rejects those).
    The full original path is preserved verbatim in ``DeclaredArtifact.path``.
    """
    safe = _ARTIFACT_ID_DISALLOWED.sub("_", rel_str) or "artifact"
    if len(safe) > 128:
        digest = hashlib.sha256(rel_str.encode("utf-8", "replace")).hexdigest()[:16]
        safe = safe[-(128 - 17):] + "_" + digest
    candidate = safe
    n = 1
    while candidate in used:
        suffix = f"_{n}"
        candidate = safe[: 128 - len(suffix)] + suffix
        n += 1
    used.add(candidate)
    return candidate


def _infer_artifact_kind(rel_path: str) -> str:
    """Infer a ``DeclaredArtifact.kind`` from the relative output path."""
    lower = rel_path.lower()
    if "thumbnail" in lower or lower.endswith(".jpg") or lower.endswith(".jpeg"):
        return "thumbnail"
    if lower.startswith("embedded/") or lower.startswith("embedded\\"):
        return "embedded_file"
    if lower.endswith(".txt"):
        return "text"
    return "output"
