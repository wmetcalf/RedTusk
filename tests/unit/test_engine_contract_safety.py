"""Regression guards for engine→blastbox contract safety.

Both were surfaced by the corpus parity gate during the blastbox.host cutover —
the bespoke rmeta path never validated against the blastbox contract, so these
were latent until the engine started emitting ``DeclaredArtifact``/``Detection``:

  * artifact ids built from embedded-file paths with spaces / unicode / overlong
    names must be sanitized to ``^[A-Za-z0-9._-]{1,128}$`` AND de-duplicated
    (blastbox rejects an invalid OR a duplicate id → engine_error).
  * the detection ``label`` (the root MIME) must fit the 64-char contract cap.
"""

from __future__ import annotations

import re

import pytest
from blastbox.contract import DeclaredArtifact, Detection
from pydantic import ValidationError

from redtusk.engine import _safe_artifact_id

_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


def test_safe_artifact_id_sanitizes_spaces_and_unicode():
    used: set[str] = set()
    aid = _safe_artifact_id("rmeta/embedded/Quarterly Report (café) №1.pdf", used)
    assert _ID_RE.match(aid)
    # contract accepts it
    DeclaredArtifact(id=aid, path="rmeta/embedded/x.pdf", kind="embedded_file")


def test_safe_artifact_id_dedupes_collisions():
    used: set[str] = set()
    a = _safe_artifact_id("rmeta/embedded/a b.pdf", used)
    b = _safe_artifact_id("rmeta/embedded/a_b.pdf", used)  # sanitizes to the same stem
    c = _safe_artifact_id("rmeta/embedded/a b.pdf", used)  # exact repeat
    assert a != b != c and a != c
    assert all(_ID_RE.match(x) for x in (a, b, c))


def test_safe_artifact_id_truncates_overlong_with_hash():
    used: set[str] = set()
    long1 = "rmeta/embedded/" + "x" * 300 + "_one.bin"
    long2 = "rmeta/embedded/" + "x" * 300 + "_two.bin"
    a = _safe_artifact_id(long1, used)
    b = _safe_artifact_id(long2, used)
    assert len(a) <= 128 and len(b) <= 128
    assert _ID_RE.match(a) and _ID_RE.match(b)
    assert a != b  # distinct tails hashed distinctly


def test_safe_artifact_id_all_disallowed_chars_is_nonempty():
    used: set[str] = set()
    aid = _safe_artifact_id("///", used)
    assert _ID_RE.match(aid)


def test_detection_label_cap_matches_contract():
    # A real 71-char OOXML MIME exceeds the 64-char label cap; the engine slices
    # it. Prove the contract accepts a 64-char label and rejects 65.
    Detection(label="x" * 64, mime="m", confidence=1.0, source="redtusk")
    with pytest.raises(ValidationError):
        Detection(label="x" * 65, mime="m", confidence=1.0, source="redtusk")


def test_reconstruct_rmeta_artifact_paths_from_entries(tmp_path):
    """gVisor C/R fallback: when the restored worker's readdir is stale (rglob misses files
    is_file() confirms), detonate reconstructs the artifact manifest from the rmeta entries
    instead of a directory walk — declaring rmeta/metadata.json + each entry's embedded file that
    actually exists on disk, for BOTH normal and lossy (sanitized+hashed) names. Absent entries
    are skipped."""
    from redtusk.engine import _embedded_disk_relpath, _reconstruct_rmeta_artifact_paths

    rmeta = tmp_path / "rmeta"
    (rmeta / "embedded").mkdir(parents=True)
    (rmeta / "metadata.json").write_text("{}")
    (rmeta / "embedded" / "image1.wmf").write_bytes(b"x")
    lossy_name = "/évil*.png"
    lossy_disk = _embedded_disk_relpath(lossy_name)  # JVM-replicated on-disk name
    (rmeta / "embedded" / lossy_disk).write_bytes(b"y")
    entries = [
        {"path": "/"}, {"path": "/image1.wmf"}, {"path": lossy_name}, {"path": "/gone.png"},
    ]
    got = _reconstruct_rmeta_artifact_paths(tmp_path, rmeta, entries)
    assert "rmeta/metadata.json" in got
    assert "rmeta/embedded/image1.wmf" in got
    assert f"rmeta/embedded/{lossy_disk}" in got  # lossy name reconstructed + declared
    assert not any("gone" in p for p in got)  # absent entry skipped


def test_embedded_disk_relpath_replicates_jvm():
    """Mirrors EmbeddedFileExtractor.resolveOutFile + disambiguate(shortHash = SHA-256[:16])."""
    import hashlib

    from redtusk.engine import _embedded_disk_relpath

    assert _embedded_disk_relpath("/image1.wmf") == "image1.wmf"  # normal: unchanged, no hash
    lossy = "évil*.png"
    tag = hashlib.sha256(lossy.encode()).hexdigest()[:16]
    assert _embedded_disk_relpath("/" + lossy) == f"_vil__{tag}.png"  # lossy → hash before .ext
    tag2 = hashlib.sha256(b"a*b/c.png").hexdigest()[:16]
    assert _embedded_disk_relpath("/a*b/c.png") == f"a_b/c_{tag2}.png"  # lossy parent → final hash


def test_sanitize_embedded_component_matches_jvm():
    from redtusk.engine import _sanitize_embedded_component

    assert _sanitize_embedded_component("image1.wmf") == "image1.wmf"  # normal: unchanged
    assert _sanitize_embedded_component("ré*sumé") == "r__sum_"  # non-[a-zA-Z0-9._+- ] -> _
    assert _sanitize_embedded_component("") == "_"
    assert _sanitize_embedded_component("..") == "_"
