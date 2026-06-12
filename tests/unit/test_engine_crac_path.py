"""Unit test for the engine's CRaC tier selection + fail-closed-to-cold.

REDTUSK_CRAC_CHECKPOINT routes detonation through the CRaC restore path (warm JVM
from a baked warp checkpoint); ANY failure (e.g. a CPU-feature mismatch when the
checkpoint is restored on a host/runtime whose CPU differs, as under gVisor) MUST
fall back to a fresh cold JVM so the worker still produces correct output. Tests
the branch logic without a real CRaC JVM.
"""

from __future__ import annotations

from pathlib import Path

from redtusk import engine as eng_mod
from redtusk.engine import RedTuskEngine


def test_crac_env_routes_to_crac_then_falls_back_to_cold(monkeypatch, tmp_path):
    calls: list[tuple] = []

    def fake_crac(inp, rmeta, *, checkpoint_dir, scratch_dir, timeout):
        calls.append(("crac", checkpoint_dir, scratch_dir))
        raise RuntimeError("warp: cpu.features mismatch")  # e.g. restore under gVisor

    def fake_cold(inp, rmeta, *, timeout):
        calls.append(("cold",))
        rmeta.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(eng_mod, "_crac_restore_worker", fake_crac)
    monkeypatch.setattr(eng_mod, "_run_worker", fake_cold)
    monkeypatch.setenv("REDTUSK_CRAC_CHECKPOINT", "/app/checkpoint")

    RedTuskEngine()._produce_rmeta(Path("in"), tmp_path / "rmeta", 10.0)

    assert calls == [("crac", "/app/checkpoint", "/tmp/redtusk-crac"), ("cold",)]


def test_crac_env_honors_scratch_override(monkeypatch, tmp_path):
    seen: list[str] = []
    monkeypatch.setattr(
        eng_mod, "_crac_restore_worker",
        lambda i, r, *, checkpoint_dir, scratch_dir, timeout: seen.append(scratch_dir),
    )
    monkeypatch.setenv("REDTUSK_CRAC_CHECKPOINT", "/ckpt")
    monkeypatch.setenv("REDTUSK_CRAC_SCRATCH", "/tmp/custom")
    RedTuskEngine()._produce_rmeta(Path("in"), tmp_path / "rmeta", 10.0)
    assert seen == ["/tmp/custom"]


def test_no_crac_env_uses_cold(monkeypatch, tmp_path):
    calls: list[str] = []
    monkeypatch.setattr(eng_mod, "_run_worker", lambda i, r, *, timeout: calls.append("cold"))
    monkeypatch.delenv("REDTUSK_CRAC_CHECKPOINT", raising=False)
    RedTuskEngine()._produce_rmeta(Path("in"), tmp_path / "rmeta", 10.0)
    assert calls == ["cold"]
