"""DEPRECATED STUB — do not use. The real gate is
music/gates/gate_release_ready.py.

This module existed as an existence-only checker that
passed DUMMY text files — the exact defect the
architecture forbids ("a gate that greps a file for a
feature name is a defect — it passes while the artifact
is broken"). It now delegates to the executable gate.

Usage:
  python3 music/gates/gate_release_ready.py \
      --package-dir <dir>
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
from pathlib import Path

MUSIC_DIR = Path(__file__).resolve().parent
_GATE_PATH = MUSIC_DIR / "gates" / "gate_release_ready.py"


def _load():
    spec = importlib.util.spec_from_file_location(
        "music_gates_release_ready", _GATE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def gate_release_ready(track_id: str, package_path: str):
    """Backwards-compatible wrapper. Returns
    (passed: bool, findings: list[str])."""
    module = _load()
    argv = ["--package-dir", package_path]
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        code = module.main(argv)
    findings = [ln.strip("  - ")
                for ln in err.getvalue().splitlines()
                if ln.strip().startswith("- ")]
    return code == 0, findings


if __name__ == "__main__":
    module = _load()
    sys.exit(module.main())
