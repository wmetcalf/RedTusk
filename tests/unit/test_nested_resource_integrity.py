"""Actual Tika postorder and collision-free nested artifact storage."""

import hashlib
from pathlib import Path
from typing import Any

from redtusk.engine import _build_tree, _embedded_storage_relpath, _reconstruct_rmeta_artifact_paths


def entry(path: str, parent: str | None, depth: int) -> dict[str, Any]:
    return {
        "path": path,
        "parent_path": parent,
        "depth": depth,
        "content_type": "application/octet-stream",
        "metadata": {},
        "text": "",
    }


def test_postorder_keeps_child_under_its_container() -> None:
    root = _build_tree(
        [entry("/", None, 0), entry("/a.rar/child.txt", "/a.rar", 2), entry("/a.rar", "/", 1)]
    )
    assert len(root.children) == 1
    archive = root.children[0]
    assert archive.embedded_path == "/a.rar"
    assert archive.children[0].embedded_path == "/a.rar/child.txt"


def test_missing_parent_is_visible_not_silently_reparented() -> None:
    root = _build_tree([entry("/", None, 0), entry("/gone/child", "/gone", 2)])
    assert root.children[0].metadata.fields["parent_resolution"] == "missing_or_invalid_parent"


def test_container_and_child_storage_cannot_collide(tmp_path: Path) -> None:
    paths = ["/a.rar", "/a.rar/child.txt", "/résumé.txt", "/r_sum_.txt", "/" + "x" * 5000]
    saved = []
    for path in paths:
        rel = _embedded_storage_relpath(path)
        assert rel == "objects/" + hashlib.sha256(path[1:].encode()).hexdigest() + "/content"
        target = tmp_path / "rmeta" / "embedded" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.encode())
        saved.append(target)
    assert len(set(saved)) == len(paths)
    artifacts = _reconstruct_rmeta_artifact_paths(
        tmp_path, tmp_path / "rmeta", [entry(p, "/", 1) for p in paths]
    )
    assert len(artifacts) == len(paths)
