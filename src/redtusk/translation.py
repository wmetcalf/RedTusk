"""Translate ExtractResult into tika-server wire formats."""

from __future__ import annotations

import io
import posixpath
import tarfile
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from redtusk.types import ExtractResult


def to_tika_text(result: ExtractResult) -> str:
    """Return root entry text."""
    if not result.extraction.entries:
        return ""
    return result.extraction.entries[0].text


def to_meta_json(result: ExtractResult) -> dict[str, Any]:
    """Return root entry metadata dict with Content-Type injected."""
    if not result.extraction.entries:
        return {}
    entry = result.extraction.entries[0]
    meta: dict[str, Any] = dict(entry.metadata)
    meta["Content-Type"] = entry.content_type
    return meta


def to_rmeta_json(result: ExtractResult) -> list[dict[str, Any]]:
    """Return a list of flat dicts in tika-server rmeta format."""
    out: list[dict[str, Any]] = []
    for entry in result.extraction.entries:
        item: dict[str, Any] = {
            str(k): str(v) if not isinstance(v, str) else v
            for k, v in entry.metadata.items()
        }
        item["Content-Type"] = entry.content_type
        if entry.text:
            item["X-TIKA:content"] = entry.text
        if entry.depth > 0:
            item["X-TIKA:embedded_resource_path"] = entry.path
        out.append(item)
    return out


def to_detect_text(result: ExtractResult) -> str:
    """Return the root content type."""
    return result.extraction.root_content_type or "application/octet-stream"


def to_language_text(result: ExtractResult) -> str:
    """Return the root language."""
    return result.extraction.root_language or ""


def to_unpack_tar(result: ExtractResult, *, include_root: bool) -> bytes:
    """Build an in-memory tar archive containing per-entry text."""
    buf = io.BytesIO()
    with tarfile.open(mode="w", fileobj=buf) as tar:
        for entry in result.extraction.entries:
            if not include_root and entry.depth == 0:
                continue
            if not entry.text:
                continue
            data = entry.text.encode("utf-8")

            name = entry.path.replace("\\", "/").lstrip("/") or "root"
            name = posixpath.normpath(name)
            drive_like = len(name) >= 2 and name[1] == ":"
            if (
                name in {"", ".", ".."}
                or name.startswith("../")
                or "/../" in name
                or name.startswith("/")
                or drive_like
            ):
                name = "unsafe_path_" + name.replace("/", "_")

            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()
