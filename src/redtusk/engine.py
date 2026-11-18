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
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
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

from redtusk.schema import validate_rmeta

logger = logging.getLogger(__name__)


class EngineTimeoutError(RuntimeError):
    """The worker exceeded its time budget on THIS document.

    Distinct from a warm-tier fault on purpose. A crashed warm JVM should fail closed to a fresh
    cold JVM (that is what makes the warm tier safe to enable); a document that simply takes too
    long must not be re-run there, because the cold path has the same parser and the same budget
    and would only spend it twice.
    """


# Default locations of the JVM worker artifacts inside the cold-worker image.
# All are env-overridable so a dev box / CI can point at a locally-built jar.
_DEFAULT_JAVA_BIN = "java"
_DEFAULT_WORKER_JAR = "/app/redtusk-worker.jar"
_DEFAULT_AOT_CACHE = "/app/redtusk.aot"
_DEFAULT_JAVA_LIBRARY_PATH = "/app"

# JVM flags mirror the redtusk-worker image ENTRYPOINT.  They MUST match the
# flags the AOT cache was built with (UseSerialGC / TieredStopAtLevel=1 / 800m
# heap / native-access) or JDK 25 rejects the cache at load time.
# The warm JVM's stdio lands here, inside its own scratch dir, so it is reaped with the slot.
_WARM_STDOUT_LOG = "warm-stdout.log"
_WARM_STDERR_LOG = "warm-stderr.log"
# Only the tail is ever wanted (the fatal line), and a runaway log must not be read whole on a
# failure path.
_WARM_STDERR_TAIL_BYTES = 64 * 1024

# CVE-2026-114938 ("Java4Shell"): heap overflow in HotSpot's AVX-512 VBMI Base64 decode
# intrinsic (JDK 17.0.6+ .. 27). Hostile documents reach java.util.Base64 inside the worker,
# so the intrinsic is OFF for every worker JVM. java.util.Base64 still works (pure-Java path);
# only the assembly stub is disabled. It is part of the default bundle (so the AOT cache and
# the warm FC/gVisor JVMs are booted with it) AND forced onto a REDTUSK_JAVA_OPTS override --
# an operator flag bundle must not be able to silently re-enable the vulnerable stub.
_BASE64_INTRINSICS_OFF = "-XX:-UseBASE64Intrinsics"

_DEFAULT_JVM_FLAGS: tuple[str, ...] = (
    "-XX:+UseSerialGC",
    _BASE64_INTRINSICS_OFF,
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
    # QR default ON: this is a forensic fork — QR codes in docs/emails are a primary IOC
    # (decoded payloads are commonly phishing URLs), and the zxing scan is cheap. Matches
    # ClippyShot's QR-on default. Per-job REDTUSK_ENABLE_QR=0 still turns it off.
    "enable_qr": True,
    # OCR stays OFF by default (heavier: tesseract per image, image-bomb/DoS-sensitive) —
    # opt in per job with REDTUSK_ENABLE_OCR=1.
    "enable_ocr": False,
    # Default ON so warm tiers (FC microVM / gVisor C/R) generate thumbnails too:
    # their guest env is frozen at snapshot time, so a per-job REDTUSK_ENABLE_THUMBNAILS
    # can't reach them — they fall back to this default. Cold still honors the per-job
    # param (the UI toggle, which also defaults on). See _env_param_overrides.
    "enable_thumbnails": True,
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


def _env_param_overrides() -> dict[str, Any]:
    """Map UI-forwarded job params onto the JVM job descriptor.

    The dispatcher forwards a job's allowlisted ``params``
    (``BLASTBOX_ENGINE_REDTUSK_PARAM_KEYS``) into the worker as env vars, but ONLY
    for UPPERCASE env-shaped keys (``^[A-Z][A-Z0-9_]*$`` — the dispatcher's
    unconditional shape floor; lowercase keys are dropped before any allowlist).
    So the web UI sends — and the allowlist lists — ``REDTUSK_ENABLE_QR`` /
    ``REDTUSK_ENABLE_OCR`` / ``REDTUSK_ENABLE_THUMBNAILS`` /
    ``REDTUSK_MAX_RECURSION_DEPTH`` / ``REDTUSK_MAX_EMBEDDED_ENTRIES``. Absent or
    empty → the JVM default in ``_DEFAULT_JOB`` is kept. Anything not in the
    allowlist never reaches here, so this can't flip sandbox/runtime.
    """

    def _flag(name: str) -> bool | None:
        v = os.environ.get(name)
        if not v:
            return None
        return v.strip().lower() in ("1", "true", "yes", "on")

    def _int(name: str, lo: int, hi: int) -> int | None:
        # Clamp the dispatcher-forwarded (potentially client-influenced) limit into [lo, hi]: a
        # negative value must not silently disable the recursion/embedded-entry DoS guard, and an
        # absurd value must not drive the worker toward unbounded recursion/allocation. (Mirrors
        # ClippyShot's clamped _int; job.json is never schema-validated, so this is the only bound.)
        v = os.environ.get(name)
        if not v:
            return None
        try:
            return min(hi, max(lo, int(v)))
        except ValueError:
            return None

    out: dict[str, Any] = {}
    for env_key, job_key in (
        ("REDTUSK_ENABLE_QR", "enable_qr"),
        ("REDTUSK_ENABLE_OCR", "enable_ocr"),
        ("REDTUSK_ENABLE_THUMBNAILS", "enable_thumbnails"),
    ):
        f = _flag(env_key)
        if f is not None:
            out[job_key] = f
    limits: dict[str, Any] = {}
    depth = _int("REDTUSK_MAX_RECURSION_DEPTH", 0, 64)
    if depth is not None:
        limits["max_recursion_depth"] = depth
    # Ceiling: every saved entry can declare TWO artifacts (its bytes and its thumbnail), and
    # blastbox seals at most 16384 artifacts (Envelope.artifacts), so 2 * 8000 + the root
    # thumbnail stays sealable. (It is also below the contract's EmbeddedResource.children cap of
    # 10000, which a flat archive would otherwise hit.) Above it, an image-heavy archive ended
    # as engine_error with every artifact lost.
    entries = _int("REDTUSK_MAX_EMBEDDED_ENTRIES", 0, _MAX_EMBEDDED_ENTRIES)
    if entries is not None:
        limits["max_embedded_entries"] = entries
    if limits:
        out["limits"] = {**_DEFAULT_JOB["limits"], **limits}
    return out


# ---------------------------------------------------------------------------
# rmeta → blastbox contract conversion helpers
# ---------------------------------------------------------------------------

# contract Record.fields is Field(max_length=4096) and RAISES past it. rmeta `metadata` is
# schema-typed {"type":"object"} with no maxProperties, so a document surfacing thousands of
# metadata properties (XMP/OOXML custom props) would overflow it -> crash. Cap the forwarded
# key count below 4096 (leaving headroom for the ~8 per-entry `extra` scalar keys).
_MAX_RECORD_KEYS = 4000


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
    # cap key COUNT (Record.fields max_length=4096)
    for k, v in list(raw.items())[:_MAX_RECORD_KEYS]:
        safe_key = str(k)[:256]  # guard against absurdly long keys
        fields[safe_key] = _coerce_metadata_value(v)
    return Record(fields=fields)


# Metadata keys only the engine may set. A Tika key with one of these names is dropped.
_ENGINE_KEY_PREFIXES: tuple[str, ...] = ("redtusk:", "redtusk_")
_ENGINE_ROOT_KEYS: frozenset[str] = frozenset({"embedded_paths"})

# redtusk:ocr carries at most this much text per node. The full text is already in the node's
# ExtractedText child and in redtusk_rmeta; a third uncapped copy could push an OCR-heavy result
# past blastbox's metadata size limit.
_OCR_TEXT_CAP = 16384

# Upper bound for REDTUSK_MAX_EMBEDDED_ENTRIES; see _env_param_overrides.
_MAX_EMBEDDED_ENTRIES = 8_000

# Skip reasons the worker puts on (nearly) every entry: OCR is off by default and most entries
# are not images. Reporting them would hang an empty Record on every node, so they count as
# "nothing to say"; any other reason (a timeout, a size cap) is evidence and is kept.
_ROUTINE_SKIPS: frozenset[str | None] = frozenset({None, "disabled", "no_images"})


def _engine_entry_fields(e: dict[str, Any]) -> dict[str, Any]:
    """The rmeta entry's own (non-Tika) evidence as ``redtusk:*`` Record fields.

    QR decodes and OCR text are the IOC-bearing ones (a decoded QR is commonly a phishing URL);
    parent_path and the thumbnail state let a consumer walk and explain the tree without parsing
    the rmeta string. Empty results are omitted so 10k-entry trees do not carry 10k empty bags.
    """
    out: dict[str, Any] = {"redtusk:parent_path": _coerce_metadata_value(e.get("parent_path"))}
    if "has_thumbnail" in e:
        out["redtusk:has_thumbnail"] = bool(e.get("has_thumbnail"))
    if e.get("thumbnail_skipped") is not None:
        out["redtusk:thumbnail_skipped"] = str(e["thumbnail_skipped"])
    qr = e.get("qr")
    if isinstance(qr, dict):
        codes = [c for c in (qr.get("codes") or []) if isinstance(c, dict)]
        if codes or qr.get("skipped") not in _ROUTINE_SKIPS:
            out["redtusk:qr"] = Record(fields={
                "data": [_coerce_metadata_value(c.get("data")) for c in codes],
                "format": [_coerce_metadata_value(c.get("format")) for c in codes],
                "position": [_coerce_metadata_value(c.get("position")) for c in codes],
                "raw_bytes": [_coerce_metadata_value(c.get("raw_bytes")) for c in codes],
                "skipped": _coerce_metadata_value(qr.get("skipped")),
            })
    ocr = e.get("ocr")
    if isinstance(ocr, dict) and (ocr.get("text") or ocr.get("skipped") not in _ROUTINE_SKIPS):
        text = str(ocr.get("text") or "")
        out["redtusk:ocr"] = Record(fields={
            "text": text[:_OCR_TEXT_CAP],
            "text_truncated": len(text) > _OCR_TEXT_CAP,
            "language": _coerce_metadata_value(ocr.get("language")),
            "duration_ms": _coerce_metadata_value(ocr.get("duration_ms")),
            "skipped": _coerce_metadata_value(ocr.get("skipped")),
        })
    return out


def _build_tree(entries: list[dict[str, Any]]) -> EmbeddedResource:
    """Reconstruct resource ancestry by path, independent of completion order.

    Tika's recursive wrapper can emit children before their container. Paths and
    parent_path, rather than adjacency, preserve that relationship. Invalid or
    missing parents remain explicit evidence gaps attached to the root.
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
        # Clamp to EmbeddedResource.depth's contract bound (Field(ge=0, le=64), which RAISES);
        # the rmeta schema only enforces depth>=0, so a tampered/drifted entry could exceed 64.
        depth = max(0, min(int(e.get("depth", 0)), 64))
        meta_raw = e.get("metadata") or {}
        # Include a small set of useful per-entry scalar fields in the Record.
        extra: dict[str, Any] = {}
        for scalar_key in ("sha256", "md5", "sha1", "size_bytes", "language", "error",
                           "phash", "colorhash"):
            val = e.get(scalar_key)
            if val is not None:
                extra[scalar_key] = _coerce_metadata_value(val)
        combined: dict[str, Any] = {}
        if isinstance(meta_raw, dict):
            # cap key COUNT (see _MAX_RECORD_KEYS); the drop is reported by detonate()
            for k, v in list(meta_raw.items())[:_MAX_RECORD_KEYS]:
                key = str(k)
                # A document chooses its own metadata keys. Keys in the engine's namespace are
                # dropped outright: applying the engine's fields afterwards is not enough when
                # the engine OMITS one (no OCR text, no truncation), which would leave the
                # document's forged value standing.
                if key.startswith(_ENGINE_KEY_PREFIXES) or key in _ENGINE_ROOT_KEYS:
                    continue
                combined[key] = _coerce_metadata_value(v)
        # The worker's own per-entry scalars (hashes, size, ...) and engine-derived evidence win
        # over any same-named Tika key.
        combined.update(extra)
        combined.update(_engine_entry_fields(e))
        # Clip to the contract field bounds (which RAISE, not truncate): rmeta entry path /
        # content_type / text are schema-valid at ANY length (no maxLength), so an attacker's
        # container entry name (ZIP allows 64KiB names) would overflow embedded_path (4096) /
        # content_type (255) and crash the mapping. char_count keeps the true (pre-clip) length.
        node = EmbeddedResource(
            embedded_path=path[:4096],
            content_type=ct[:255],
            depth=depth,
            metadata=Record(fields=combined),
            children=[],
        )
        text = e.get("text") or ""
        if text:
            node.children.append(
                ExtractedText(text=text[:10_000_000], char_count=len(text))
            )
        return node

    # Build all nodes first.
    nodes = [_make_node(e) for e in entries]

    # Tika emits embedded-document completion in postorder: children can precede
    # their parents. Resolve explicit resource paths after building all nodes.
    root = nodes[0]
    # Keyed by the FULL entry path: embedded_path is clipped to 4096, and two long paths that
    # share a 4096-char prefix (a long-named container and its own child) would collide.
    by_path = {str(e.get("path") or "/"): node for e, node in zip(entries, nodes, strict=True)}
    for entry, node in zip(entries[1:], nodes[1:], strict=True):
        parent_path = entry.get("parent_path")
        if not isinstance(parent_path, str) or not parent_path:
            parent_path = str(entry.get("path") or "/").rsplit("/", 1)[0] or "/"
        parent = by_path.get(parent_path)
        if parent is None or parent is node or parent.depth >= node.depth:
            parent = root
            if parent_path != root.embedded_path and node.metadata is not None:
                node.metadata.fields["parent_resolution"] = "missing_or_invalid_parent"
        parent.children.append(node)
    return root


# ---------------------------------------------------------------------------
# Worker invocation
# ---------------------------------------------------------------------------


def _reset_rmeta_dir(rmeta_dir: Path) -> None:
    """Empty *rmeta_dir* before a cold fallback, so the failed attempt's partial files (embedded
    bytes, a draft temp) are not declared next to the cold result as if the cold JVM wrote them."""
    try:
        if rmeta_dir.is_symlink() or rmeta_dir.is_file():
            rmeta_dir.unlink()
        elif rmeta_dir.exists():
            shutil.rmtree(rmeta_dir)
        return
    except OSError as exc:
        # The fallback must still run. A gVisor C/R-restored process can have a stale
        # directory view (see detonate()), so rmtree may not see the files a crashed warm JVM
        # wrote and fail with ENOTEMPTY. Move the whole directory aside instead: rename
        # needs no listing, and only rmeta/ is ever declared.
        aside = rmeta_dir.with_name(f".{rmeta_dir.name}.failed-{uuid.uuid4().hex[:12]}")
        logger.warning("redtusk: could not empty %s before cold fallback (%s); moving it to %s",
                       rmeta_dir, exc, aside.name)
        rmeta_dir.rename(aside)
        # Best effort: drop whatever this view CAN see, so the aside tree does not count
        # twice against the host's output-size cap. On a stale view some files remain;
        # they are never declared.
        shutil.rmtree(aside, ignore_errors=True)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _force_base64_intrinsics_off(flags: list[str]) -> list[str]:
    """Drop any UseBASE64Intrinsics setting from *flags* and append the OFF flag last.

    HotSpot honours the LAST occurrence of a flag, so appending alone would already win;
    stripping the others keeps the argv unambiguous to a reader of ``ps``/logs.
    """
    kept = [f for f in flags if not f.startswith(("-XX:+UseBASE64Intrinsics",
                                                  "-XX:-UseBASE64Intrinsics"))]
    return [*kept, _BASE64_INTRINSICS_OFF]


# Marker a CRaC checkpoint image carries when the JVM that baked it ran with the intrinsic
# OFF (written by the image build after the checkpoint succeeds; the worker refuses to
# checkpoint with the intrinsic on). A restore keeps the checkpointed JVM's flags, so a
# checkpoint without it -- one baked before the mitigation -- is never restored.
_CRAC_BASE64_OFF_MARKER = "redtusk-base64-intrinsics-off"

# The rmeta/output layout the worker jar writes (io.redtusk.worker.WorkerFormat.VERSION). A
# CRaC restore resumes the jar that was checkpointed at image-build time, so the checkpoint
# image records the format of THAT jar (``redtusk-worker --worker-format``) in this file, and a
# checkpoint whose record is missing (baked before the engine output contract, #64) or names
# another format is never restored. Bump both constants together whenever the worker's output
# layout changes in a way this engine depends on.
_WORKER_FORMAT = 2
_CRAC_WORKER_FORMAT_MARKER = "redtusk-worker-format"


class _StaleWorkerFormatError(RuntimeError):
    """A CRaC checkpoint whose worker writes another output format than this engine reads."""


def _cold_jar_worker_format() -> str | None:
    """Ask the jar a cold fallback would boot which output format it writes (None if unknown).

    Only run when a checkpoint was refused for its format: redtusk-cold-worker:crac boots the
    very jar that was checkpointed, so a cold fallback there would write the same stale
    layout. A jar from before ``--worker-format`` existed exits non-zero (usage) -> None.
    """
    java_bin = os.environ.get("REDTUSK_JAVA_BIN", _DEFAULT_JAVA_BIN)
    jar = os.environ.get("REDTUSK_WORKER_JAR", _DEFAULT_WORKER_JAR)
    try:
        result = subprocess.run(
            [java_bin, _BASE64_INTRINSICS_OFF, "-jar", jar, "--worker-format"],
            capture_output=True, text=True, timeout=60, check=False,
            env=_jvm_env(dict(os.environ)),
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()[:32] or None


def _check_checkpoint_worker_format(checkpoint_dir: str) -> None:
    """Raise unless the checkpoint records this engine's worker output format."""
    marker = Path(checkpoint_dir) / _CRAC_WORKER_FORMAT_MARKER
    try:
        recorded = marker.read_text(encoding="ascii", errors="replace").strip()[:32]
    except OSError:
        recorded = None
    if recorded != str(_WORKER_FORMAT):
        found = "is missing" if recorded is None else f"records format {recorded!r}"
        raise _StaleWorkerFormatError(
            f"CRaC checkpoint {checkpoint_dir}: {_CRAC_WORKER_FORMAT_MARKER} {found}, but this "
            f"engine reads worker format {_WORKER_FORMAT}; the checkpointed worker would write "
            "output this engine misreads. Rebuild redtusk-worker:crac and "
            "redtusk-cold-worker:crac"
        )


def _jvm_env(env: dict[str, str]) -> dict[str, str]:
    """Return *env* with any ``_JAVA_OPTIONS`` forced to end in the OFF flag.

    HotSpot reads ``_JAVA_OPTIONS`` AFTER the command line, so an inherited
    ``_JAVA_OPTIONS=-XX:+UseBASE64Intrinsics`` beats the argv's trailing OFF flag. Appending
    the OFF flag to it restores "the last occurrence is OFF". ``JAVA_TOOL_OPTIONS`` and
    ``JDK_JAVA_OPTIONS`` are read before the command line, so the argv already wins over them.
    Used for JVMs that boot; NOT for a CRaC restore (see _crac_restore_worker).
    """
    java_options = env.get("_JAVA_OPTIONS")
    if java_options is not None:
        env["_JAVA_OPTIONS"] = f"{java_options} {_BASE64_INTRINSICS_OFF}".strip()
    return env


def _java_worker_argv(scratch: Path) -> list[str]:
    """Build the in-process JVM worker argv (``java ... -jar ... --run <scratch>``).

    Mirrors the redtusk-worker image ENTRYPOINT so the AOT cache — which is
    flag-sensitive — loads cleanly.  Everything is env-overridable:

    - ``REDTUSK_JAVA_BIN``          java executable (default ``java``)
    - ``REDTUSK_WORKER_JAR``        worker jar (default ``/app/redtusk-worker.jar``)
    - ``REDTUSK_AOT_CACHE``         AOT cache; only added when the file exists
    - ``REDTUSK_JAVA_LIBRARY_PATH`` native lib dir (default ``/app``)
    - ``REDTUSK_JAVA_OPTS``         full JVM-flag override (shlex-split), replacing
                                    the default flag bundle -- except
                                    ``-XX:-UseBASE64Intrinsics`` (CVE-2026-114938),
                                    which is always forced on
    """
    java_bin = os.environ.get("REDTUSK_JAVA_BIN", _DEFAULT_JAVA_BIN)
    jar = os.environ.get("REDTUSK_WORKER_JAR", _DEFAULT_WORKER_JAR)
    lib_path = os.environ.get("REDTUSK_JAVA_LIBRARY_PATH", _DEFAULT_JAVA_LIBRARY_PATH)
    aot_cache = os.environ.get("REDTUSK_AOT_CACHE", _DEFAULT_AOT_CACHE)

    opts_override = os.environ.get("REDTUSK_JAVA_OPTS")
    if opts_override is not None:
        jvm_flags = _force_base64_intrinsics_off(shlex.split(opts_override))
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
            **_env_param_overrides(),
            "input_path": str(in_dir / filename_hint),
            "output_dir": str(rmeta_outdir),
            "sha256": sha256,
            "filename_hint": filename_hint,
        }

        # EVERYTHING FALLIBLE FIRST, then start the thread. `_java_worker_argv` shlex-splits
        # REDTUSK_JAVA_OPTS and raises ValueError on unbalanced quotes; raising there after
        # t.start() but before the try/finally below left the thread polling to its own
        # deadline with no one to set worker_done -- reinstating the very leak this fixes.
        # Building the argv up here removes the window rather than widening the guard.
        # Launch the JVM worker in-process.  Isolation (network=none, cap-drop,
        # tmpfs, memory/pids caps) is provided by the *outer* blastbox cold-worker
        # container — this used to be a nested ``docker run``, which the
        # socket-less cold worker cannot do.
        cmd = _java_worker_argv(scratch)
        env = {
            **os.environ,
            "REDTUSK_LOG_LEVEL": os.environ.get("REDTUSK_LOG_LEVEL", "WARNING"),
            # PINNED off. REDTUSK_PREWARM is the WARM JVM's knob -- warmup() sets it on the
            # long-lived process, where building the parser tree once before the snapshot pays
            # for itself. This process is one-shot: it would prewarm and then parse exactly
            # once, so the ~1.2s is pure added latency on every cold job AND on every
            # warm->cold fallback. Inheriting it also breaks the promise Main.prewarmParsers'
            # javadoc makes ("set only by the Python engine's warmup()"), which is not
            # something the operator setting it on a container would ever expect.
            "REDTUSK_PREWARM": "0",
        }
        _jvm_env(env)

        logger.debug("RedTusk JVM worker cmd: %s", " ".join(cmd))
        # Set once the JVM has exited: nothing will read the go-signal after that, and the
        # scratch dir is about to be removed with the enclosing TemporaryDirectory.
        worker_done = threading.Event()
        t = threading.Thread(
            target=_signal_worker_loop,
            args=(control_dir, job, timeout, worker_done),
            daemon=True,
        )
        t.start()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=timeout,
                env=env,
            )
        finally:
            # In a finally: a TimeoutExpired (or any raise) leaves this thread polling until its
            # own deadline, and the scratch dir goes away regardless.
            worker_done.set()
            t.join(timeout=5)

        if result.returncode != 0:
            stderr_tail = result.stderr.decode(errors="replace")[-2000:]
            raise RuntimeError(
                f"redtusk-worker (jvm) exited {result.returncode}: {stderr_tail}"
            )


def _signal_worker_loop(
    control_dir: Path,
    job: dict[str, Any],
    timeout: float,
    worker_done: threading.Event,
) -> None:
    """Wait for control.ready, then hand the JVM its job.json + control.go.

    Module level, not a closure, so the test suite can drive THIS loop rather than a
    reimplementation of it.

    ``worker_done`` is what keeps this thread from outliving the job. The JVM runs inside a
    ``tempfile.TemporaryDirectory`` and the caller only does ``join(timeout=5)``, which returns
    whether or not this thread finished -- so before, a worker that exited early (fast failure,
    timeout) left this polling until its OWN deadline, the scratch dir was removed underneath
    it, and it then wrote into a deleted path. That is an unhandled ``FileNotFoundError`` in a
    daemon thread: it goes nowhere, and only pytest's threadexception hook ever surfaced it
    (RedTusk #53).
    """
    ready_file = control_dir / "control.ready"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if ready_file.exists():
            break
        # Event.wait, not sleep: end NOW when the worker is gone, not at our own deadline.
        if worker_done.wait(0.1):
            return
    if worker_done.is_set():
        return
    # Write job.json then go-signal regardless (worker may have
    # already timed out waiting for us if we're very slow).
    try:
        (control_dir / "job.json").write_text(
            json.dumps(job, ensure_ascii=False), encoding="utf-8"
        )
        (control_dir / "control.go").touch()
    except OSError as exc:
        # Losing the race with teardown is not worth a traceback, but it must not be silent
        # either: this thread has no other way to report anything at all.
        logger.debug("signal thread: control dir gone before the go-signal (%s)", exc)


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
    if not (Path(checkpoint_dir) / _CRAC_BASE64_OFF_MARKER).is_file():
        # Raise before staging anything: the caller falls back to a cold JVM, which gets the
        # OFF flag from _java_worker_argv.
        raise RuntimeError(
            f"CRaC checkpoint {checkpoint_dir} has no {_CRAC_BASE64_OFF_MARKER} marker: it was "
            "baked before the CVE-2026-114938 mitigation and would restore with the Base64 "
            "intrinsic on; rebuild redtusk-worker:crac and redtusk-cold-worker:crac"
        )
    _check_checkpoint_worker_format(checkpoint_dir)
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
        **_env_param_overrides(),
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
    # Not _jvm_env: a restore keeps the checkpoint's VM flags, and CRaC refuses any
    # non-restore-settable option at restore ("VM option 'UseBASE64Intrinsics' is not
    # restore-settable"), so appending the OFF flag would only make every restore fail. An
    # inherited -XX:+UseBASE64Intrinsics is refused the same way, so it cannot re-enable the
    # intrinsic either; the checkpoint's flags are vouched for by the marker checked above.
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
                # OPT-IN, default OFF. Parsing before control.ready moves Tika's
                # init ahead of the snapshot — but on the FC warm tier it MEASURED
                # WORSE (fixed floor 2546ms -> 5367ms, 2026-08-14): the prewarm
                # dirties an 800m pre-touched heap before the checkpoint, so every
                # restored slot page-faults that working set back in, costing more
                # than the init it saves. Keep the knob for tiers whose restore is
                # cheap (CRaC checkpoints ~44MB, not a 2GB VM image) and measure
                # with scripts/verify_warm_tier.sh before enabling it anywhere.
                "REDTUSK_PREWARM": os.environ.get("REDTUSK_PREWARM", "0"),
            }
            _jvm_env(env)
            started = time.monotonic()
            # FILES, not pipes. Nothing reads this process's output until communicate() at the
            # FIRST JOB, so everything it emits before then -- boot, Tika class loading, and
            # with REDTUSK_PREWARM a whole parser-tree build -- piles up in a 64 KiB kernel
            # pipe buffer. Fill that and the JVM BLOCKS ON WRITE, never signals ready, and the
            # tier silently degrades to cold with only "did not signal ready" to go on. The
            # images bake REDTUSK_LOG_LEVEL=INFO, so the volume is not hypothetical. A file
            # never blocks the writer, and it also makes the death diagnostic below a plain
            # read instead of a race against a pipe some surviving child still holds open.
            out_log = scratch / _WARM_STDOUT_LOG
            err_log = scratch / _WARM_STDERR_LOG
            proc = subprocess.Popen(
                cmd,
                stdout=out_log.open("wb"),
                stderr=err_log.open("wb"),
                env=env,
            )

            # The JVM announces control.ready (loading Tika classes from the AOT
            # cache, then parsing the prewarm document), and blocks on control.go.
            ready = control_dir / "control.ready"
            deadline = time.monotonic() + _WARMUP_READY_TIMEOUT
            while time.monotonic() < deadline:
                if ready.exists():
                    self._warm = _WarmWorker(
                        proc=proc, scratch=scratch, in_dir=in_dir,
                        control_dir=control_dir, tmp=tmp,
                    )
                    # Elapsed is the cheap field check that the prewarm actually ran:
                    # boot-only is ~0.8s, boot+first-parse ~2s. A warm tier reporting
                    # ~0.8s here means REDTUSK_PREWARM never reached the JVM.
                    logger.info(
                        "redtusk warm JVM ready (blocked at READY) after %.2fs",
                        time.monotonic() - started,
                    )
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

    @staticmethod
    def _warm_exit_detail(warm: _WarmWorker) -> str:
        """Last line of the dead warm JVM's stderr log, for the cold-fallback log.

        The JVM's stderr goes to a FILE in its scratch dir (see warmup), so this is a plain
        bounded read that always terminates. It used to read a PIPE to EOF on the reasoning
        that "the process has already exited, so this cannot block" -- which was wrong twice
        over: EOF needs every WRITER to close, and Tika forks external scanners (ZXingReader,
        tesseract) that inherit stderr, so one surviving child parked a dispatcher thread
        inside a LOGGING HELPER, ahead of the very cold fallback this message annotates.

        Diagnosing one such exit (a go-signal timeout, rc=2) took three deploy cycles precisely
        because this string was missing, so it stays -- just without the hazard.
        """
        try:
            log = Path(warm.scratch) / _WARM_STDERR_LOG
            if not log.exists():
                return "no stderr log"
            raw = log.read_bytes()[-_WARM_STDERR_TAIL_BYTES:]
        except OSError as exc:
            return f"stderr unreadable: {exc}"
        text = raw.decode("utf-8", "replace").strip()
        if not text:
            return "stderr empty"
        # Last non-blank line: the JVM's fatal message, not the banner above it.
        return text.splitlines()[-1][:300]

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
                if isinstance(exc, _StaleWorkerFormatError):
                    cold = _cold_jar_worker_format()
                    if cold != str(_WORKER_FORMAT):
                        # The cold JVM would boot a jar writing a stale layout too (in
                        # redtusk-cold-worker:crac it IS the checkpointed jar): fail closed.
                        raise RuntimeError(
                            f"{exc}; the cold-fallback jar reports worker format {cold!r}, "
                            f"not {_WORKER_FORMAT}, so it cannot stand in"
                        ) from exc
                logger.warning("redtusk CRaC restore failed (%s); cold fallback", exc)
                _reset_rmeta_dir(rmeta_dir)
                _run_worker(input, rmeta_dir, timeout=timeout)
                return

        warm = self._warm
        self._warm = None  # one job per warm JVM; consume it
        if warm is None or warm.proc.poll() is not None:
            # The one tier transition here that used to be SILENT. Every other path
            # logs (warmup success/failure, CRaC cold fallback), so a warm tier that
            # quietly degrades to a cold JVM looks identical to a healthy one in the
            # logs while paying a full JVM boot per job. Measured on the FC warm tier:
            # ~3.3s in-guest for a 3-byte input, i.e. the boot dominates every job.
            logger.warning(
                "redtusk warm JVM unavailable (%s); cold fallback — paying a JVM boot per job",
                "no warm handle: warmup() never ran, or its handle did not survive "
                "snapshot/restore"
                if warm is None
                else f"warm JVM already exited rc={warm.proc.returncode}: "
                f"{self._warm_exit_detail(warm)}",
            )
            _run_worker(input, rmeta_dir, timeout=timeout)
            return
        logger.info("redtusk using warm JVM (no per-job boot)")
        try:
            input_bytes = input.read_bytes()
            filename_hint = input.name or "input"
            rmeta_dir.mkdir(parents=True, exist_ok=True)
            (warm.in_dir / filename_hint).write_bytes(input_bytes)
            job: dict[str, Any] = {
                **_DEFAULT_JOB,
                **_env_param_overrides(),
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
                # Returns (None, None): stdout/stderr are FILES, not pipes (see warmup). It is
                # still the right call -- it waits for exit and reaps the process.
                warm.proc.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                warm.proc.kill()
                warm.proc.communicate()
                # A TIMEOUT IS NOT A WARM-TIER FAULT -- it is a slow document, and the cold path
                # would be just as slow. Raising RuntimeError here fell into the enclosing
                # `except Exception` below, which re-ran the SAME input on a fresh JVM with a FULL
                # fresh `timeout`: total budget 2 x timeout, silently. On a document that sits near
                # the limit (measured: an 8.4 MB PDF with 151 embedded entries, 84s of parse against
                # a 120s budget) that doubling is what pushed it past the host's warm-stale cutoff
                # (worker_timeout_s + requeue_grace_s), so instead of a clean engine_error the job
                # was reaped as "warm worker abandoned: owning dispatcher gone" -- terminal, and
                # holding a slot for the whole time.
                #
                # EngineTimeoutError is handled by its OWN except clause below, placed BEFORE the
                # generic one, so it re-raises instead of being swallowed into a cold retry. A warm
                # JVM that CRASHED (non-zero exit, or a staging error) still falls back to cold with
                # a full budget -- the fail-closed behaviour tests/integration/test_warm_path.py
                # pins.
                #
                # ...but ONLY when this JVM demonstrably TOOK the job. The two failures are
                # indistinguishable at this call: a timeout is equally what you see when the
                # JVM never received the go-signal at all (control dir not visible after a
                # restore, a wedged process, a full stdio pipe). Nothing about the DOCUMENT is
                # implicated there, so suppressing the cold fallback would fail a job
                # terminally for a host-side fault -- trading the double-budget bug for a
                # no-fallback one. The worker writes control.started the instant it takes the
                # go-signal (FifoLoop.markStarted), so this is answerable rather than a guess.
                if not (warm.control_dir / "control.started").exists():
                    raise RuntimeError(
                        f"warm JVM never started the job within {timeout}s (no control.started); "
                        f"treating as an infrastructure fault, not a slow document"
                    ) from None
                raise EngineTimeoutError(
                    f"redtusk worker timed out after {timeout}s"
                ) from None
            if warm.proc.returncode != 0:
                # From the LOG FILE, since communicate() no longer carries the bytes. Same
                # reader as the cold-fallback diagnostic, so a crash message cannot rot in one
                # place while staying correct in the other.
                tail = self._warm_exit_detail(warm)
                raise RuntimeError(
                    f"redtusk-worker (warm jvm) exited {warm.proc.returncode}: {tail}"
                )
        except EngineTimeoutError:
            # Slow document, not a broken warm tier. Do NOT re-run it on a cold JVM: same input,
            # same parser, same budget -> same timeout, at twice the wall-clock and twice the slot
            # occupancy. Surface it so the harness records a clean timeout.
            raise
        except Exception as exc:  # noqa: BLE001
            # Fail-closed to cold for a genuine warm FAULT (JVM crashed / staging failed): a fresh
            # JVM produces the rmeta into the same dir. Pinned by
            # tests/integration/test_warm_path.py.
            logger.warning("redtusk warm detonation failed (%s); cold fallback", exc)
            _reset_rmeta_dir(rmeta_dir)
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

        # Trust gate (restored from the bespoke host): validate the worker-produced
        # rmeta against the strict Draft-2020-12 schema BEFORE we embed it in the
        # envelope / serve it. A malformed rmeta — worker bug, version drift, or a
        # hostile-input-induced shape — fails the job (engine_error) instead of
        # flowing unvalidated to the UI. Real corpus rmeta conforms (no false fails).
        validate_rmeta(rmeta)

        extraction = rmeta.get("extraction", {})
        entries: list[dict[str, Any]] = extraction.get("entries", [])
        root_ct: str = extraction.get("root_content_type") or "application/octet-stream"

        # Build payload tree
        payload = _build_tree(entries)

        # Embed the FULL rmeta document as a single JSON-string envelope field
        # (mirrors ClippyShot's ``clippyshot_metadata``): the host UI reads the
        # extraction tree straight from the sealed envelope, so we no longer ship a
        # separate ``rmeta/metadata.json`` artifact (which collided by name with the
        # blastbox ENVELOPE metadata.json at the zip root).
        #
        # Contract (blastbox-engine.toml required_root_fields): every ok result's root metadata
        # carries redtusk_rmeta. A serialization failure must not fail the job (the typed tree and
        # artifacts are still good evidence) NOR silently drop the field: the field stays present
        # as "" (the UI already treats that as "fall back to /rmeta") and a warning says why.
        # Unreachable today (rmeta is json.loads output, default=str, allow_nan on), but enforced
        # here rather than by that argument. RecursionError is not caught: it propagates as
        # engine_error, never an ok result.
        rmeta_embed_warning: Warning | None = None
        try:
            rmeta_json = json.dumps(rmeta, ensure_ascii=False, default=str)
        except (TypeError, ValueError) as exc:
            rmeta_json = ""
            rmeta_embed_warning = Warning(
                code="rmeta_embed_failed",
                message=f"rmeta document could not be serialized into redtusk_rmeta: "
                        f"{type(exc).__name__}: {exc}"[:2000],
            )
        # _build_tree always gives the root a Record; frozen models still allow mutating the
        # contained fields dict. No guard/except: a failure here is a bug and must surface.
        assert payload.metadata is not None
        payload.metadata.fields["redtusk_rmeta"] = rmeta_json

        # Detection from root content-type. Both contract fields RAISE past their bound and
        # root_content_type is schema-valid at any length (no maxLength), so clip label to 64
        # AND mime to 255 -- a worker-influenced content-type over 255 chars would otherwise
        # crash the mapping (Detection.mime is Field(max_length=255), not truncating).
        detected = Detection(
            label=(root_ct.split(";")[0].strip() or "unknown")[:64],
            mime=root_ct[:255],
            confidence=1.0,
            source="redtusk",
        )

        # Collect artifacts: every file the JVM wrote under rmeta/ (embedded files +
        # thumbnails), referenced with paths relative to outdir (not rmeta_dir) so the
        # blastbox envelope path confinement passes with outdir as root.
        #
        # ``rmeta/metadata.json`` is deliberately NOT declared (see the filter below):
        # its content is embedded in the envelope as the ``redtusk_rmeta`` field, so
        # declaring it too would put a second metadata.json in /result (the wart this
        # change removes). The legacy /v1/jobs/{id}/rmeta route still serves it for
        # jobs sealed before this change (they declared it); new jobs use the field.
        #
        # Normally a fresh rglob of rmeta_dir is authoritative (cold + Firecracker tiers). But a
        # gVisor C/R-restored warm worker has a STALE directory view: readdir/rglob misses the
        # files the JVM wrote post-restore, even though is_file() on the exact path WORKS (which is
        # why meta_path.is_file() passed above). rglob would then silently return nothing and we'd
        # declare an EMPTY manifest. Detect that (rglob missed the rmeta doc we KNOW exists) and
        # reconstruct the artifact list from the rmeta document's OWN entries (in memory, not the
        # FS) — stat-checked so only existing files are declared. Cold/FC are unchanged; the C/R
        # tier gets a correct manifest. (blastbox's C/R runtime separately recovers the BYTES that
        # the same stale view drops from the host bind mount; this fixes the DECLARATION half.)
        rel_paths = sorted(
            f.relative_to(outdir).as_posix() for f in rmeta_dir.rglob("*") if f.is_file()
        )
        if "rmeta/metadata.json" not in rel_paths:
            rel_paths = _reconstruct_rmeta_artifact_paths(outdir, rmeta_dir, entries)
        # The rmeta doc is embedded in the envelope (redtusk_rmeta) — keep it as the
        # stale-view sentinel above, but drop it from the DECLARED set so it isn't a
        # second metadata.json in the sealed /result zip. Sentinel check stays intact
        # (it ran on the unfiltered rglob result).
        # The draft-snapshot temp is a superseded partial copy of metadata.json (orphaned only
        # when a JVM is killed between write and rename); never evidence, never declared.
        rel_paths = [p for p in rel_paths
                     if p not in ("rmeta/metadata.json", "rmeta/" + _DRAFT_TMP_NAME)]
        taken = _current_objects(entries)
        known_embedded = frozenset(
            "rmeta/embedded/" + rel
            for e in entries if str(e.get("path") or "").lstrip("/")
            for rel in _legacy_layouts(str(e.get("path") or ""), taken)
        )
        artifacts: list[DeclaredArtifact] = []
        used_ids: set[str] = set()
        for rel_str in rel_paths:
            artifact_id = _safe_artifact_id(rel_str, used_ids)
            kind = _infer_artifact_kind(rel_str, known_embedded)
            artifacts.append(DeclaredArtifact(id=artifact_id, path=rel_str, kind=kind))

        if payload.metadata is not None:
            declared_paths = set(rel_paths)
            entry_paths: dict[str, str] = {}
            for entry in entries:
                ep = entry.get("path") or ""
                if not ep.lstrip("/"):
                    continue
                for relative in _legacy_layouts(ep, taken):
                    candidate = "rmeta/embedded/" + relative
                    if candidate in declared_paths:
                        entry_paths[ep] = candidate
                        break
            payload.metadata.fields["embedded_paths"] = json.dumps(entry_paths, ensure_ascii=False)

        # Map rmeta warnings
        warnings: list[Warning] = []
        if rmeta_embed_warning is not None:
            warnings.append(rmeta_embed_warning)
        for w in rmeta.get("warnings", []):
            code = str(w.get("code") or "redtusk_warning")[:64]
            detail = str(w.get("detail") or "")[:2000]
            entry_path = w.get("entry_path")
            warnings.append(Warning(
                code=code, message=detail,
                context=str(entry_path)[:255] if entry_path is not None else None,
            ))
        # Record key cap (_MAX_RECORD_KEYS): say which entries lost metadata keys, not just drop.
        for e in entries:
            meta_raw = e.get("metadata")
            if isinstance(meta_raw, dict) and len(meta_raw) > _MAX_RECORD_KEYS:
                warnings.append(Warning(
                    code="metadata_keys_capped",
                    message=(f"entry metadata has {len(meta_raw)} keys; only the first "
                             f"{_MAX_RECORD_KEYS} are in the typed tree (all are in "
                             f"redtusk_rmeta)")[:2000],
                    context=str(e.get("path") or "/")[:255],
                ))
        if rmeta.get("truncated"):
            tr = rmeta["truncated"]
            # Structured on the root as well as in the message, so a consumer can key on the
            # reason / limit without parsing text.
            payload.metadata.fields["redtusk:truncated"] = Record(fields={
                "reason": _coerce_metadata_value(tr.get("reason")),
                "limit": _coerce_metadata_value(tr.get("limit")),
                "observed": _coerce_metadata_value(tr.get("observed")),
            })
            # Clip like the rmeta-warnings loop above: truncated.limit/observed are schema-valid
            # but UNBOUNDED integers, and Warning.message is Field(max_length=2000) (pydantic
            # RAISES, not truncates), so an unclipped f-string crashes the mapping.
            warnings.append(Warning(
                code="truncated",
                message=(f"Extraction truncated: reason={tr.get('reason')}, "
                         f"limit={tr.get('limit')}, observed={tr.get('observed')}")[:2000],
                context=str(tr.get("reason"))[:255],
            ))

        return DetonationResult(
            payload=payload,
            artifacts=artifacts,
            detected=detected,
            warnings=warnings,
            status="ok",
        )


_ARTIFACT_ID_DISALLOWED = re.compile(r"[^A-Za-z0-9._-]")

_EMBEDDED_NAME_DISALLOWED = re.compile(r"[^a-zA-Z0-9._+\- ]")


def _sanitize_embedded_component(part: str) -> str:
    """Sanitize a component using the historical JVM storage layout."""
    cleaned = _EMBEDDED_NAME_DISALLOWED.sub("_", part).strip()
    return cleaned if cleaned not in ("", ".", "..") else "_"


def _legacy_layouts(entry_path: str, taken: frozenset[str] = frozenset()) -> tuple[str, ...]:
    """Storage paths to try for an entry: the current object layout, then the sanitized-name
    layout of earlier workers -- unless that legacy path is some entry's CURRENT object
    (*taken*), which an entry named objects/<sha>/content would otherwise alias."""
    legacy = _embedded_disk_relpath(entry_path)
    current = _embedded_storage_relpath(entry_path)
    return (current,) if legacy in taken else (current, legacy)


def _current_objects(entries: list[dict[str, Any]]) -> frozenset[str]:
    """Every entry's current-layout storage path (see _legacy_layouts)."""
    return frozenset(_embedded_storage_relpath(str(e.get("path") or ""))
                     for e in entries if str(e.get("path") or "").lstrip("/"))


def _embedded_storage_relpath(entry_path: str) -> str:
    """Current JVM layout: stable bounded paths independent of resource names."""
    digest = hashlib.sha256(entry_path.lstrip("/").encode("utf-8")).hexdigest()
    return f"objects/{digest}/content"


def _embedded_disk_relpath(entry_path: str) -> str:
    """Read the historical sanitized-name layout. Map an rmeta entry path to its relative
    path under ``rmeta/embedded/`` — a FULL replication of the JVM EmbeddedFileExtractor's
    ``resolveOutFile`` + ``disambiguate``: each component is sanitized; if ANY component was altered
    (``lossy``) the FINAL component is suffixed with a 16-hex (64-bit) prefix of SHA-256(original
    rel path) before the extension, matching the on-disk name the worker actually wrote. This lets
    the engine reconstruct the declaration WITHOUT a directory listing (needed when a gVisor
    C/R-restored worker's readdir is stale), including for lossy special-character names."""
    rel = entry_path.lstrip("/")
    parts = rel.split("/")
    out_parts: list[str] = []
    lossy = False
    for i, original in enumerate(parts):
        part = _sanitize_embedded_component(original)
        if i == 0 and part == "thumbnails":
            # EmbeddedFileExtractor.resolveOutFile reserves embedded/thumbnails/ for thumbnails.
            part = "thumbnails_"
        if part != original:
            lossy = True
        if lossy and i == len(parts) - 1:
            tag = hashlib.sha256(rel.encode("utf-8")).hexdigest()[:16]
            dot = part.rfind(".")
            part = f"{part[:dot]}_{tag}{part[dot:]}" if dot > 0 else f"{part}_{tag}"
        out_parts.append(part)
    return "/".join(out_parts)


def _reconstruct_rmeta_artifact_paths(
    outdir: Path, rmeta_dir: Path, entries: list[dict[str, Any]]
) -> list[str]:
    """Declare rmeta artifacts from the in-memory rmeta entries (stat-checked) instead of a
    directory walk — for when a gVisor C/R-restored worker's readdir is stale. The rmeta doc is
    always present (meta_path.is_file() passed); embedded files live at
    ``rmeta/embedded/<_embedded_disk_relpath(entry path)>``. Only files that actually exist
    (is_file, which works on the stale view) are returned."""
    paths: set[str] = set()
    if (rmeta_dir / "metadata.json").is_file():
        paths.add("rmeta/metadata.json")
    emb_root = rmeta_dir / "embedded"
    taken = _current_objects(entries)
    cands: list[Path] = []
    for e in entries:
        ep = e.get("path") or ""
        if not ep.lstrip("/"):
            # The root entry's thumbnail (Main.tryGenerateRootThumbnail) is rmeta/thumbnail.jpg.
            if e.get("has_thumbnail"):
                cands.append(rmeta_dir / "thumbnail.jpg")
            continue
        # Current workers separate resource provenance from filesystem layout
        # (objects/<sha256(path)>/content); earlier workers used sanitized names. Both are
        # read, so a result from either worker is declared.
        for rel in _legacy_layouts(ep, taken):
            cands.append(emb_root / rel)
            if e.get("has_thumbnail"):
                # EmbeddedFileExtractor.writeThumbnail: embedded/thumbnails/<embedded rel>.jpg
                cands.append(emb_root / "thumbnails" / (rel + ".jpg"))
    for cand in cands:
        try:
            if cand.is_file():
                paths.add(cand.relative_to(outdir).as_posix())
        except OSError:
            continue
    return sorted(paths)


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


_DRAFT_TMP_NAME = ".metadata.json.draft.tmp"  # DraftSnapshotWriter.DRAFT_TMP_NAME


def _infer_artifact_kind(rel_path: str, known_embedded: frozenset[str] = frozenset()) -> str:
    """``DeclaredArtifact.kind`` from the file's ROLE in the rmeta layout, never its name.

    ``rmeta/thumbnail.jpg`` is the root thumbnail; ``rmeta/embedded/thumbnails/*.jpg`` are entry
    thumbnails; everything else under ``rmeta/embedded/`` is an embedded file -- including one
    whose own name ends .jpg or .txt. The worker never writes an embedded file under
    ``embedded/thumbnails/``: current workers store every entry at
    ``embedded/objects/<sha256(path)>/content`` (EmbeddedFileExtractor.resolveOutFile, mirrored
    by _embedded_storage_relpath), and the previous sanitized-name layout saved a top-level
    ``thumbnails`` entry as ``thumbnails_/...`` (_embedded_disk_relpath). *known_embedded* (the
    rmeta entries' paths in both layouts) is a second guard for the same thing.
    """
    if rel_path in known_embedded:
        return "embedded_file"
    if rel_path == "rmeta/thumbnail.jpg":
        return "thumbnail"
    if rel_path.startswith("rmeta/embedded/thumbnails/") and rel_path.endswith(".jpg"):
        return "thumbnail"
    if rel_path.startswith("rmeta/embedded/"):
        return "embedded_file"
    return "output"
