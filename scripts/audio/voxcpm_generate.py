#!/usr/bin/env python3
"""VoxCPM generation wrapper for the storyteller.

Loads VoxCPM2 (F16 by default; Q8_0/Q4_K via GGUF where supported), generates
a single utterance with optional Voice Design, writes WAV/MP3.

Usage:
    voxcpm_generate.py --text "..." --out /tmp/x.wav [--quality f16|q8|q4]
                        [--voice-desc "(A young woman, gentle voice)"]
"""
import argparse
import sys
from pathlib import Path


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

    # Model id: F16 python path (HF original) is the default; GGUF quants
    # would use VoxCPM.cpp — for now, quality selects nothing different on
    # the Python path (F16 weights); q8/q4 are served by VoxCPM.cpp later.
    model_id = "openbmb/VoxCPM2"
    print(f"loading {model_id} (quality={args.quality})...", file=sys.stderr)
    model = VoxCPM.from_pretrained(model_id, load_denoiser=False)

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
