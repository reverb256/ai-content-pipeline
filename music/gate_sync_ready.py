"""DEPRECATED STUB — do not use. The real gate is
music/gates/gate_sync_ready.py.

This module existed as an existence-only checker that
passed DUMMY text files — the exact defect the
architecture forbids ("a gate that greps a file for a
feature name is a defect — it passes while the artifact
is broken"). It now delegates to the executable gate.

Usage:
  python3 music/gates/gate_sync_ready.py \
      --package-dir <dir> [--lane sync|direct-license|game-assets]
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

MUSIC_DIR = Path(__file__).resolve().parent
_GATE_PATH = MUSIC_DIR / "gates" / "gate_sync_ready.py"


def _load():
    spec = importlib.util.spec_from_file_location(
        "music_gates_sync_ready", _GATE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_sync_ready(package_path: str,
                      lane: str = "sync") -> bool:
    """Backwards-compatible wrapper. Returns True on PASS."""
    module = _load()
    argv = ["--package-dir", package_path, "--lane", lane]
    return module.main(argv) == 0


if __name__ == "__main__":
    module = _load()
    sys.exit(module.main())
