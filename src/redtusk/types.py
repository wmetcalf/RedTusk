"""In-memory data model for RedTusk.

Frozen dataclasses for every value the system handles. Each carries
``to_dict`` / ``from_dict`` so they can be serialized to / from the
canonical JSON shape that workers produce and the API serves.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import UUID

# Horizontal whitespace = ASCII space/tab + the Unicode Zs "space separator"
# category (NBSP, ogham, en/em/thin/hair spaces, narrow + medium-math space,
# ideographic space). Kept in exact sync with the UI's collapseWs().
_WS_HCLASS = " \t\u00a0\u1680\u2000-\u200a\u202f\u205f\u3000"
_WS_ZEROWIDTH = re.compile("[\u200b\u200c\u200d\u2060\ufeff]")
_WS_LINESEP = re.compile("\r\n|\r|\u2028|\u2029")
_WS_HRUN = re.compile(f"[{_WS_HCLASS}]+")
_WS_TRAIL = re.compile(f"[{_WS_HCLASS}]+\n")
_WS_BLANKS = re.compile(r"\n{3,}")


def wsnorm(text: str) -> str:
    """Whitespace-normalised copy of extracted text, for readable display.

    Handles Unicode whitespace (common in obfuscated/malicious docs), kept in
    exact sync with the UI's ``collapseWs()``:

      * zero-width / invisible chars (U+200B-D, U+2060, BOM U+FEFF) are removed;
      * CRLF/CR and the Unicode line/paragraph separators (U+2028/9) become LF;
      * a run of horizontal whitespace (ASCII space/tab + the Unicode Zs
        category) collapses to one char — a tab if the run held any tab
        ("whatever is longest"), else a space;
      * trailing horizontal whitespace per line is stripped;
      * 3+ consecutive newlines collapse to a single blank line.

    The raw ``text`` is left untouched as the forensic source of truth — this
    is only the readable view.
    """
    s = _WS_ZEROWIDTH.sub("", text)
    s = _WS_LINESEP.sub("\n", s)
    s = _WS_HRUN.sub(lambda m: "\t" if "\t" in m.group(0) else " ", s)
    s = _WS_TRAIL.sub("\n", s)
    s = _WS_BLANKS.sub("\n\n", s)
    return s


class SlotState(StrEnum):
    WARMING = "warming"
    IDLE = "idle"
    ASSIGNED = "assigned"
    DRAINING = "draining"
    SPAWN_FAILED = "spawn_failed"


@dataclass(eq=True)
class Slot:
    id: UUID
    state: SlotState
    container_id: str | None
    scratch_dir: Path | None
    assigned_job_id: str | None
    assigned_at: datetime | None  # UTC, set on ASSIGNED transition
    spawn_attempts: int           # incremented each SPAWN_FAILED retry
    is_burst: bool                # True if spawned above pool_size baseline


class JobState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"

    def is_terminal(self) -> bool:
        return self in (JobState.SUCCEEDED, JobState.FAILED)


class SkipReason(StrEnum):
    """Why a scanner (QR or OCR) was not run on an entry."""

    NO_IMAGES = "no_images"
    TIMEOUT_BUDGET = "timeout_budget"
    ERROR = "error"
    DISABLED = "disabled"
    BLANK_IMAGE = "blank_image"
    # Entry was observed mid-parse by DraftSnapshotWriter; placeholder in a
    # draft metadata.json that gets overwritten by the final write OR promoted
    # to a real partial when the dispatcher salvages a timed-out job.
    IN_PROGRESS = "in_progress"


class TruncationReason(StrEnum):
    """Why recursive extraction was cut short."""

    MAX_EMBEDDED_ENTRIES = "max_embedded_entries"
    MAX_RECURSION_DEPTH = "max_recursion_depth"
    MAX_EXTRACTED_BYTES = "max_extracted_bytes"
    # Sentinel: worker is still parsing. DraftSnapshotWriter writes this on
    # every mid-parse snapshot; the dispatcher rewrites to JOB_TIMEOUT when
    # promoting a draft after SIGKILL.
    IN_PROGRESS = "in_progress"
    # The dispatcher SIGKILLed the worker past job_timeout_s and promoted the
    # last mid-parse snapshot to a partial result.
    JOB_TIMEOUT = "job_timeout"


@dataclass(frozen=True)
class QrCode:
    data: str
    format: str
    raw_bytes: str | None = None
    position: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "data": self.data,
            "format": self.format,
            "raw_bytes": self.raw_bytes,
            "position": self.position,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> QrCode:
        return cls(
            data=d["data"],
            format=d["format"],
            raw_bytes=d.get("raw_bytes"),
            position=d.get("position"),
        )


@dataclass(frozen=True)
class QrResult:
    codes: list[QrCode] = field(default_factory=list)
    skipped: SkipReason | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "codes": [c.to_dict() for c in self.codes],
            "skipped": self.skipped.value if self.skipped is not None else None,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> QrResult:
        skipped = SkipReason(d["skipped"]) if d.get("skipped") is not None else None
        return cls(
            codes=[QrCode.from_dict(c) for c in d.get("codes", [])],
            skipped=skipped,
        )


@dataclass(frozen=True)
class OcrResult:
    text: str = ""
    language: str | None = None
    duration_ms: int = 0
    skipped: SkipReason | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "language": self.language,
            "duration_ms": self.duration_ms,
            "skipped": self.skipped.value if self.skipped is not None else None,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> OcrResult:
        skipped = SkipReason(d["skipped"]) if d.get("skipped") is not None else None
        return cls(
            text=d.get("text", ""),
            language=d.get("language"),
            duration_ms=d.get("duration_ms", 0),
            skipped=skipped,
        )


@dataclass(frozen=True)
class WarningEntry:
    code: str
    detail: str
    entry_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "detail": self.detail, "entry_path": self.entry_path}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> WarningEntry:
        return cls(code=d["code"], detail=d["detail"], entry_path=d.get("entry_path"))


@dataclass(frozen=True)
class TruncationInfo:
    reason: TruncationReason
    limit: int
    observed: int

    def to_dict(self) -> dict[str, Any]:
        return {"reason": self.reason.value, "limit": self.limit, "observed": self.observed}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> TruncationInfo:
        return cls(
            reason=TruncationReason(d["reason"]),
            limit=d["limit"],
            observed=d["observed"],
        )


@dataclass(frozen=True)
class EmbeddedEntry:
    path: str
    parent_path: str | None
    depth: int
    content_type: str
    size_bytes: int
    sha256: str | None     # null for embedded until EmbeddedFileExtractor fills it in
    md5: str | None        # MD5 of raw file bytes
    sha1: str | None       # SHA-1 of raw file bytes
    has_thumbnail: bool    # True if a JPEG thumbnail was generated under embedded/thumbnails/
    phash: str | None      # perceptual hash (DCT-based) — populated for image entries
    colorhash: str | None  # color distribution hash — populated for image entries
    metadata: dict[str, Any]
    text: str
    language: str | None
    qr: QrResult
    ocr: OcrResult
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "parent_path": self.parent_path,
            "depth": self.depth,
            "content_type": self.content_type,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "md5": self.md5,
            "sha1": self.sha1,
            "has_thumbnail": self.has_thumbnail,
            "phash": self.phash,
            "colorhash": self.colorhash,
            "metadata": dict(self.metadata),
            "text": self.text,
            # Whitespace-normalised view of `text`, computed once at
            # serialization so the UI + any API consumer reference one canonical
            # collapsed form instead of each reimplementing it. `text` stays the
            # untouched source of truth.
            "text_wsnorm": wsnorm(self.text),
            "language": self.language,
            "qr": self.qr.to_dict(),
            "ocr": self.ocr.to_dict(),
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> EmbeddedEntry:
        return cls(
            path=d["path"],
            parent_path=d.get("parent_path"),
            depth=d["depth"],
            content_type=d["content_type"],
            size_bytes=d["size_bytes"],
            sha256=d.get("sha256"),
            md5=d.get("md5"),
            sha1=d.get("sha1"),
            has_thumbnail=bool(d.get("has_thumbnail", False)),
            phash=d.get("phash"),
            colorhash=d.get("colorhash"),
            metadata=dict(d.get("metadata", {})),
            text=d.get("text", ""),
            language=d.get("language"),
            qr=QrResult.from_dict(d["qr"]),
            ocr=OcrResult.from_dict(d["ocr"]),
            error=d.get("error"),
        )


@dataclass(frozen=True)
class InputInfo:
    sha256: str
    size_bytes: int
    filename_hint: str | None
    submitted_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "filename_hint": self.filename_hint,
            "submitted_at": self.submitted_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> InputInfo:
        return cls(
            sha256=d["sha256"],
            size_bytes=d["size_bytes"],
            filename_hint=d.get("filename_hint"),
            submitted_at=datetime.fromisoformat(d["submitted_at"]),
        )


@dataclass(frozen=True)
class ExtractionInfo:
    root_content_type: str
    root_language: str | None
    duration_ms: int
    entries: list[EmbeddedEntry]

    def to_dict(self) -> dict[str, Any]:
        return {
            "root_content_type": self.root_content_type,
            "root_language": self.root_language,
            "duration_ms": self.duration_ms,
            "entries": [e.to_dict() for e in self.entries],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ExtractionInfo:
        return cls(
            root_content_type=d["root_content_type"],
            root_language=d.get("root_language"),
            duration_ms=d["duration_ms"],
            entries=[EmbeddedEntry.from_dict(e) for e in d["entries"]],
        )


@dataclass(frozen=True)
class LimitsInfo:
    max_recursion_depth: int
    max_embedded_entries: int
    max_extracted_bytes: int
    ocr_timeout_s: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_recursion_depth": self.max_recursion_depth,
            "max_embedded_entries": self.max_embedded_entries,
            "max_extracted_bytes": self.max_extracted_bytes,
            "ocr_timeout_s": self.ocr_timeout_s,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> LimitsInfo:
        return cls(
            max_recursion_depth=d["max_recursion_depth"],
            max_embedded_entries=d["max_embedded_entries"],
            max_extracted_bytes=d["max_extracted_bytes"],
            ocr_timeout_s=d["ocr_timeout_s"],
        )


@dataclass(frozen=True)
class SandboxInfo:
    profile: str
    runtime: str
    appcds: bool
    ksm: bool
    crac: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile,
            "runtime": self.runtime,
            "appcds": self.appcds,
            "ksm": self.ksm,
            "crac": self.crac,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SandboxInfo:
        return cls(
            profile=d["profile"],
            runtime=d["runtime"],
            appcds=d["appcds"],
            ksm=d["ksm"],
            crac=d["crac"],
        )


@dataclass(frozen=True)
class ExtractResult:
    redtusk_version: str
    input: InputInfo
    extraction: ExtractionInfo
    limits: LimitsInfo
    truncated: TruncationInfo | None
    warnings: list[WarningEntry]
    sandbox: SandboxInfo

    def to_dict(self) -> dict[str, Any]:
        return {
            "redtusk_version": self.redtusk_version,
            "input": self.input.to_dict(),
            "extraction": self.extraction.to_dict(),
            "limits": self.limits.to_dict(),
            "truncated": self.truncated.to_dict() if self.truncated is not None else None,
            "warnings": [w.to_dict() for w in self.warnings],
            "sandbox": self.sandbox.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ExtractResult:
        truncated = (
            TruncationInfo.from_dict(d["truncated"]) if d.get("truncated") is not None else None
        )
        return cls(
            redtusk_version=d["redtusk_version"],
            input=InputInfo.from_dict(d["input"]),
            extraction=ExtractionInfo.from_dict(d["extraction"]),
            limits=LimitsInfo.from_dict(d["limits"]),
            truncated=truncated,
            warnings=[WarningEntry.from_dict(w) for w in d.get("warnings", [])],
            sandbox=SandboxInfo.from_dict(d["sandbox"]),
        )


@dataclass
class JobRecord:
    """Persisted record of a single extraction job.

    Mutable across its lifecycle: state transitions queued -> running ->
    succeeded|failed; timestamps are filled as the job moves; result is
    populated on success; error_code/error_detail are populated on failure.
    """

    id: str
    state: JobState
    submitted_at: datetime
    # Filled when the dispatcher claims the job from the queue. From this
    # point the job is "running" but may still be waiting for a worker slot.
    started_at: datetime | None
    # Filled when the worker pool slot has been acquired and the signal has
    # been sent — the worker actually starts processing here. Newer field;
    # absent on records created before this column was added.
    worker_started_at: datetime | None = None
    completed_at: datetime | None = None
    input_sha256: str = ""
    input_size_bytes: int = 0
    filename_hint: str | None = None
    input_path: str | None = None   # host path to staged input file (set by API on job creation)
    result: ExtractResult | None = None
    error_code: str | None = None
    error_detail: str | None = None

    def to_dict(self) -> dict[str, Any]:
        queue_ms: int | None = None
        pool_wait_ms: int | None = None
        processing_ms: int | None = None
        parse_ms: int | None = None
        if self.started_at is not None:
            # API → dispatcher claim (DB queue wait)
            queue_ms = int((self.started_at - self.submitted_at).total_seconds() * 1000)
        if self.started_at is not None and self.worker_started_at is not None:
            # dispatcher claim → worker slot acquired & signaled
            pool_wait_ms = int((self.worker_started_at - self.started_at).total_seconds() * 1000)
        if self.completed_at is not None:
            # processing_ms = time inside the worker pipeline (real Tika + ingest).
            # Falls back to the legacy started_at-to-completed measurement on
            # records that predate worker_started_at.
            anchor = self.worker_started_at or self.started_at
            if anchor is not None:
                processing_ms = int((self.completed_at - anchor).total_seconds() * 1000)
        # parse_ms reflects Tika's self-reported extraction time inside the
        # worker — strictly less than processing_ms (no ingest/copy overhead).
        if self.result is not None:
            try:
                parse_ms = int(self.result.extraction.duration_ms)
            except (AttributeError, TypeError):
                parse_ms = None
        return {
            "id": self.id,
            "state": self.state.value,
            "submitted_at": self.submitted_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "worker_started_at": (
                self.worker_started_at.isoformat() if self.worker_started_at else None
            ),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "queue_ms": queue_ms,
            "pool_wait_ms": pool_wait_ms,
            "processing_ms": processing_ms,
            "parse_ms": parse_ms,
            "input_sha256": self.input_sha256,
            "input_size_bytes": self.input_size_bytes,
            "filename_hint": self.filename_hint,
            "input_path": self.input_path,
            "result": self.result.to_dict() if self.result is not None else None,
            "error_code": self.error_code,
            "error_detail": self.error_detail,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> JobRecord:
        return cls(
            id=d["id"],
            state=JobState(d["state"]),
            submitted_at=datetime.fromisoformat(d["submitted_at"]),
            started_at=datetime.fromisoformat(d["started_at"]) if d.get("started_at") else None,
            worker_started_at=(
                datetime.fromisoformat(d["worker_started_at"])
                if d.get("worker_started_at") else None
            ),
            completed_at=(
                datetime.fromisoformat(d["completed_at"]) if d.get("completed_at") else None
            ),
            input_sha256=d["input_sha256"],
            input_size_bytes=d["input_size_bytes"],
            filename_hint=d.get("filename_hint"),
            input_path=d.get("input_path"),
            result=ExtractResult.from_dict(d["result"]) if d.get("result") is not None else None,
            error_code=d.get("error_code"),
            error_detail=d.get("error_detail"),
        )
