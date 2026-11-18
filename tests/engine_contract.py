"""Check engine results against ``blastbox-engine.toml`` wherever a test already holds one.

The checker (``blastbox.contract.engine_contract``) ships in a blastbox release newer than the
one this repo pins. Imported dynamically so the suite still runs (and mypy still passes) on the
pinned blastbox: there, :func:`conform` is a no-op and ``tests/unit/test_engine_contract.py``
skips. Where the checker exists, every helper that calls :func:`conform` asserts conformance.
"""
from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

CONTRACT_PATH = Path(__file__).resolve().parents[1] / "blastbox-engine.toml"


def checker() -> Any | None:
    """The contract checker module, or None on a blastbox that predates it."""
    try:
        return importlib.import_module("blastbox.contract.engine_contract")
    except ImportError:
        return None


def conform(result: Any, outdir: str | Path | None = None) -> None:
    """Assert *result* (a DetonationResult, Envelope, or parsed envelope metadata.json)
    conforms to RedTusk's contract. No-op when the checker is unavailable."""
    mod = checker()
    if mod is None:
        return
    mod.assert_conforms(mod.load_contract(CONTRACT_PATH), result, outdir)
