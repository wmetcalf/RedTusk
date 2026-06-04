"""RedTusk blastbox Engine implementation.

Wraps the RedTusk JVM worker (``redtusk-worker:default`` Docker image) as a
blastbox ``Engine``.  The engine:

1. Writes the input file into a scratch directory, sets up the file-IPC
   handshake (``control/job.json`` + ``control/control.go``), and runs the
   worker container via ``docker run``.
2. Parses the rmeta ``metadata.json`` the JVM worker writes to ``out/``.
3. Reconstructs a recursive ``EmbeddedResource`` tree from the flat,
   depth-ordered ``extraction.entries[]`` list using a depth-stack.
4. Returns a ``DetonationResult`` with the tree as payload plus any declared
   artifacts (thumbnails, embedded files) the worker wrote.

Running the worker requires Docker and the ``redtusk-worker:default`` image.
"""
from __future__ import annotations

import hashlib
import json
import logging
import subprocess
import tempfile
import threading
import time
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

IMAGE = "redtusk-worker:default"

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

        # World-writable so container UID 10001 can write control files and
        # output files.  The harness writes the blastbox envelope to the
        # *parent* outdir — not into rmeta_outdir — so permissions here only
        # need to satisfy the container + our own reads.
        for d in (scratch, in_dir, rmeta_outdir, control_dir):
            d.chmod(0o777)

        # Write input
        (in_dir / filename_hint).write_bytes(input_bytes)

        # Build job descriptor
        job: dict[str, Any] = {
            **_DEFAULT_JOB,
            "input_path": f"/scratch/in/{filename_hint}",
            "output_dir": "/scratch/out",
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

        cmd = [
            "docker", "run", "--rm",
            "--network=none",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--memory=2g",
            "--pids-limit=512",
            "--tmpfs", "/tmp:rw,exec,nosuid,size=512m",
            "--tmpfs", "/var/lib/redtusk:rw,nosuid,size=64m,uid=10001,gid=10001",
            f"--volume={scratch}:/scratch",
            f"--volume={rmeta_outdir}:/scratch/out",
            "--env=REDTUSK_LOG_LEVEL=WARNING",
            IMAGE,
            "--run", "/scratch",
        ]

        logger.debug("RedTusk worker cmd: %s", " ".join(cmd))
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout,
        )
        t.join(timeout=5)

        if result.returncode != 0:
            stderr_tail = result.stderr.decode(errors="replace")[-2000:]
            raise RuntimeError(
                f"redtusk-worker exited {result.returncode}: {stderr_tail}"
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
        _run_worker(input, rmeta_dir, timeout=float(limits.timeout_s))

        meta_path = rmeta_dir / "metadata.json"
        if not meta_path.is_file():
            raise RuntimeError("redtusk worker did not produce metadata.json")

        rmeta: dict[str, Any] = json.loads(meta_path.read_bytes())

        extraction = rmeta.get("extraction", {})
        entries: list[dict[str, Any]] = extraction.get("entries", [])
        root_ct: str = extraction.get("root_content_type") or "application/octet-stream"

        # Build payload tree
        payload = _build_tree(entries)

        # Detection from root content-type
        detected = Detection(
            label=root_ct.split(";")[0].strip() or "unknown",
            mime=root_ct,
            confidence=1.0,
            source="redtusk",
        )

        # Collect artifacts: every non-metadata.json file the JVM wrote,
        # referenced with paths relative to outdir (not rmeta_dir) so the
        # blastbox envelope path confinement passes with outdir as root.
        artifacts: list[DeclaredArtifact] = []
        for f in sorted(rmeta_dir.rglob("*")):
            if not f.is_file():
                continue
            if f == meta_path:
                continue
            rel_to_outdir = f.relative_to(outdir)
            rel_str = str(rel_to_outdir)
            # id: replace path separators to keep the id safe [A-Za-z0-9._-]
            artifact_id = rel_str.replace("/", "_").replace("\\", "_")
            # Truncate to 128 chars if needed
            if len(artifact_id) > 128:
                artifact_id = artifact_id[-128:]
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
