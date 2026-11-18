"""RedTusk's engine contract (``blastbox-engine.toml``) is valid and real results conform to it.

The contract describes what the engine emits today; the per-test hooks (``tests.engine_contract
.conform``) check every result the suite already produces. This file adds the checks that need a
dedicated test: the file parses, names this engine, and a sealed envelope from the real harness
conforms -- and that the contract is tight enough to fail on a file nobody declared a family for.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

ec = pytest.importorskip("blastbox.contract.engine_contract")

from blastbox.limits import Limits  # noqa: E402
from blastbox.worker.harness import run_detonation  # noqa: E402

from redtusk.engine import RedTuskEngine, _infer_artifact_kind  # noqa: E402
from tests.engine_contract import CONTRACT_PATH  # noqa: E402
from tests.unit.test_engine_envelope import _write_fixture_rmeta  # noqa: E402


def _contract() -> Any:
    return ec.load_contract(CONTRACT_PATH)


def test_contract_file_validates() -> None:
    assert ec.find_contract(__file__) == CONTRACT_PATH
    assert ec.main(["validate", str(CONTRACT_PATH)]) == 0


def test_contract_names_this_engine() -> None:
    c = _contract()
    assert c.engine.name == RedTuskEngine.name
    assert set(c.engine.formats) == set(RedTuskEngine.formats)


def test_contract_kinds_are_ones_the_engine_can_declare() -> None:
    # _infer_artifact_kind sees "rmeta/..." paths, so these are the only kinds it returns.
    reachable = {_infer_artifact_kind(p) for p in (
        "rmeta/embedded/a.bin", "rmeta/embedded/a.jpg", "rmeta/embedded/a.txt",
        "rmeta/thumbnail.jpg", "rmeta/embedded/thumbnails/a.png.jpg")}
    assert {a.kind for a in _contract().artifacts} <= reachable


def _fixture_engine(monkeypatch: pytest.MonkeyPatch, extra: dict[str, bytes] | None = None) -> None:
    def produce(self: Any, input: Path, rmeta_dir: Path, timeout: float) -> None:
        _write_fixture_rmeta(rmeta_dir)
        for rel, data in (extra or {}).items():
            (rmeta_dir / rel).parent.mkdir(parents=True, exist_ok=True)
            (rmeta_dir / rel).write_bytes(data)

    monkeypatch.setattr(RedTuskEngine, "_produce_rmeta", produce)


def test_sealed_envelope_conforms(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Through the real harness: DetonationResult -> seal_envelope -> metadata.json."""
    _fixture_engine(monkeypatch, {"thumbnail.jpg": b"\xff\xd8root",
                                  "embedded/notes.txt": b"hello"})
    inp = tmp_path / "x.xlsx"
    inp.write_bytes(b"x")
    out = tmp_path / "out"
    rc = run_detonation(cast(Any, RedTuskEngine()), input_path=inp, output_dir=out,
                        limits=Limits(timeout_s=10))
    assert rc == 0
    env = json.loads((out / "metadata.json").read_text())
    assert env["status"] == "ok", env
    assert ec.check_envelope(_contract(), env) == []
    kinds = {a["path"]: a["kind"] for a in env["artifacts"]}
    # The families the contract documents, as the engine really declares them.
    assert kinds["rmeta/thumbnail.jpg"] == "thumbnail"
    assert kinds["rmeta/embedded/thumbnails/image3.jpeg.jpg"] == "thumbnail"
    assert kinds["rmeta/embedded/image3.jpeg"] == "thumbnail"  # gap kind-from-filename
    assert kinds["rmeta/embedded/notes.txt"] == "text"


def test_contract_rejects_an_undeclared_family(tmp_path: Path,
                                               monkeypatch: pytest.MonkeyPatch) -> None:
    """The contract is a real bound, not a catch-all: a file the JVM has no reason to write
    outside embedded/ is declared by the engine and must fail the check."""
    _fixture_engine(monkeypatch, {"surprise.bin": b"?"})
    inp = tmp_path / "x.xlsx"
    inp.write_bytes(b"x")
    out = tmp_path / "out"
    out.mkdir()
    res = RedTuskEngine().detonate(inp, out, Limits(timeout_s=10))
    problems = ec.check_result(_contract(), res, out)
    assert [p.code for p in problems] == ["undeclared_artifact"], problems
