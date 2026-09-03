#!/usr/bin/env python3
"""VoxCPM generation wrapper for the storyteller.

Loads VoxCPM2 (F16 by default; Q8_0/Q4_K via GGUF where supported), generates
a single utterance with optional Voice Design, writes WAV/MP3.

Usage:
    voxcpm_generate.py --text "..." --out /tmp/x.wav [--quality f16|q8|q4]
                        [--voice-desc "(A young woman, gentle voice)"]
"""
import argparse
import os
import sys
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════
# HARD RULE (j_kro 2026-09-03): VoxCPM MUST run on the 3090. NEVER CPU.
# FIX THE ORDERING (j_kro ALL CAPS): index-based pins are UNRELIABLE — CUDA's
# default enumeration (fastest-first) differs from nvidia-smi (PCI order), so
# CUDA_VISIBLE_DEVICES=0 meant the MINER (3060 Ti) in a restricted env → renders
# hit the busy miner → CPU fallback → 24GB RAM blowups.
# FIX: force PCI_BUS_ID order (matches nvidia-smi) + select the 3090 BY NAME.
# ═══════════════════════════════════════════════════════════════════════════
import subprocess
import re
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
_3090_IDX = None
try:
    _smi = subprocess.run(
        ["nvidia-smi", "--query-gpu=index,name", "--format=csv,noheader"],
        capture_output=True, text=True, timeout=10).stdout
    for _line in _smi.strip().splitlines():
        _i, _name = [p.strip() for p in _line.split(",")]
        if "3090" in _name:
            _3090_IDX = _i
            break
except Exception:
    pass
os.environ["CUDA_VISIBLE_DEVICES"] = _3090_IDX or "0"  # nvidia-smi idx of the 3090 (PCI order = nvidia-smi order)
os.environ["VLLM_USE_DEVICE"] = "cuda"
os.environ["TORCH_DEVICE"] = "cuda"
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--text", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--quality", default="q8", choices=["f16", "q8", "q4"])
    p.add_argument("--voice-desc", default="")
    p.add_argument("--cfg-value", type=float, default=2.0)
    args = p.parse_args()

    try:
        import soundfile as sf
        from voxcpm import VoxCPM
    except ImportError as e:
        print(f"voxcpm not installed: {e}", file=sys.stderr)
        sys.exit(1)

    # HARD GPU CHECK — abort if CUDA unavailable (never silently run CPU)
    import torch
    if not torch.cuda.is_available():
        print("FATAL: VoxCPM requires CUDA GPU. CPU inference is DISABLED by policy "
              "(j_kro 2026-09-03: CPU TTS blew up 11GB RAM). Check nvidia drivers.",
              file=sys.stderr)
        sys.exit(2)
    print(f"VoxCPM on GPU: {torch.cuda.get_device_name(0)}", file=sys.stderr)

    # Model id: F16 python path (HF original) is the default; GGUF quants
    # would use VoxCPM.cpp — for now, quality selects nothing different on
    # the Python path (F16 weights); q8/q4 are served by VoxCPM.cpp later.
    model_id = "openbmb/VoxCPM2"
    print(f"loading {model_id} (quality={args.quality})...", file=sys.stderr)
    # optimize=False is MANDATORY (OpenBMB upstream, issues #107/#125/#269):
    # torch.compile + CUDA graphs break under multi-process/multi-thread load on
    # the same GPU → CPU fallback → 24GB RAM blowups (seen repeatedly 2026-09-03).
    # Upstream: "same performance on 3090 with or without torch.compile".
    model = VoxCPM.from_pretrained(model_id, load_denoiser=False, optimize=False)

    text = args.text
    if args.voice_desc:
        # Voice Design: description goes in parens at the start
        text = f"({args.voice_desc}){text}"

    print("generating...", file=sys.stderr)
    wav = model.generate(
        text=text,
        cfg_value=args.cfg_value,
        inference_timesteps=10,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(out, wav, model.tts_model.sample_rate)
    print(f"saved {out} ({out.stat().st_size} bytes)", file=sys.stderr)


if __name__ == "__main__":
    main()
