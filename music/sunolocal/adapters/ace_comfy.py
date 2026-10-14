"""
ACE-Step adapter for sunolocal.

Renders a plan by invoking the music pipeline's existing renderer
(`acestep_plan.py`), which queues a ComfyUI workflow and polls it. This
adapter adds no new GPU path: it builds the subprocess call, points the
renderer at the ComfyUI endpoint, and collects the produced WAV.

Env overrides (all resolved per call):
  SUNOLOCAL_ACESTEP_SCRIPT   path to acestep_plan.py
  SUNOLOCAL_ACESTEP_OUTPUT   directory the renderer writes into
  SUNOLOCAL_COMFY_URL        ComfyUI base URL (zephyr NodePort by default)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

DEFAULT_SCRIPT = (
    "/opt/sunolocal/scripts/acestep_plan_direct.py"
)


def _script() -> Path:
    return Path(os.environ.get("SUNOLOCAL_ACESTEP_SCRIPT", DEFAULT_SCRIPT))


def _output_base() -> Path:
    default = Path("/var/lib/sunolocal/acestep")
    base = Path(os.environ.get("SUNOLOCAL_ACESTEP_OUTPUT", str(default)))
    base.mkdir(parents=True, exist_ok=True)
    return base


def _comfy_url() -> str:
    return os.environ.get("SUNOLOCAL_COMFY_URL", "http://localhost:32188")


def render_acestep(
    plan_dict: Dict[str, Any],
    seed: Optional[int] = None,
    timeout_s: int = 900,
) -> Tuple[bytes, str, Dict[str, Any]]:
    """Render one plan; returns (wav_bytes, mime, metadata)."""
    out_base = _output_base()
    script = _script()
    if not script.is_file():
        raise RuntimeError(f"renderer script not found: {script} (set SUNOLOCAL_ACESTEP_SCRIPT)")

    with tempfile.TemporaryDirectory() as tmp:
        plan_path = Path(tmp) / "plan.json"
        plan_path.write_text(json.dumps(plan_dict, indent=2), encoding="utf-8")
        stem = f"suno-{int(time.time() * 1000)}-{os.getpid()}"
        env = dict(os.environ)
        env["COMFY_URL"] = _comfy_url()
        cmd = [
            sys.executable,
            str(script),
            str(plan_path),
            "--seed",
            str(seed if seed is not None else 42),
            "--name",
            stem,
            "--allow-empty",
            "--timeout",
            "600",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s, env=env)

    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-6:]
        raise RuntimeError(f"acestep_plan.py failed rc={proc.returncode}: {' / '.join(tail)}")

    # Look for the produced file in the output base with the given stem and either .wav or .flac extension
    wav_candidates = list(out_base.glob(f"{stem}.wav"))
    flac_candidates = list(out_base.glob(f"{stem}.flac"))
    candidates = wav_candidates + flac_candidates
    if not candidates:
        raise RuntimeError(f"renderer reported success but no audio file was found for stem {stem} in {out_base}")
    # If there are multiple, pick the first one (shouldn't happen)
    audio_file = candidates[0]
    data = audio_file.read_bytes()
    # Determine MIME type based on extension
    if audio_file.suffix == ".wav":
        mime = "audio/wav"
    elif audio_file.suffix == ".flac":
        mime = "audio/flac"
    else:
        # Fallback
        mime = "application/octet-stream"
    meta = {
        "engine": "ace",
        "stem": stem,
        "output": str(audio_file),
        "plan": plan_dict,
        "stdout_tail": (proc.stdout or "").strip().splitlines()[-3:],
    }
    return data, mime, meta
