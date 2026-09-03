#!/usr/bin/env python3
"""gen_general_atmos.py — generate GENERAL-PURPOSE ambience/room-tone beds via MMAudio.

The pipeline ships assets/atmos/*.wav that storyteller.py loops and duck-mixes
under dialogue. Today the atmos library is Cartographer-only (9 space-station
hums). This script generates a general library so ANY story (rain, forest,
cafe, office, street, etc.) resolves an atmos bed instead of falling back to
brown noise.

Usage (run inside the VoxCPM venv — the only env with mmaudio installed):

    ~/Projects/VoxCPM/.venv/bin/python scripts/audio/tools/gen_general_atmos.py \
        [--duration 12] [--device cuda:1] [--only rain,cafe] [--out assets/atmos]

Design notes
- MMAudio large_44k_v2 outputs mono 44.1 kHz. Beds are inherently mono-ish
  (ambience), so the master mix handles width. Output files are written at
  44.1 kHz / 16-bit PCM and the canonicalize step (canonicalize_assets.py)
  upgrades them to 48 kHz / 24-bit / stereo.
- Every bed is named by a stable slug the cue resolver can find:
  [ATMOS: rain] -> assets/atmos/rain.wav
  [ATMOS: forest] -> assets/atmos/forest.wav
  ...
"""
from __future__ import annotations

import argparse
import logging
import re
import sys
import time
from pathlib import Path

import torch

MMAUDIO_ROOT = Path("/home/j_kro/Projects/MMAudio")
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(MMAUDIO_ROOT))
sys.path.insert(0, str(MMAUDIO_ROOT / "mmaudio"))

from mmaudio.eval_utils import all_model_cfg, generate, setup_eval_logging  # noqa: E402
from mmaudio.model.flow_matching import FlowMatching  # noqa: E402
from mmaudio.model.networks import get_my_mmaudio  # noqa: E402
from mmaudio.model.utils.features_utils import FeaturesUtils  # noqa: E402

# name -> MMAudio prompt. These map to the *_library keys storyteller
# resolves: slug(name) → assets/atmos/<slug>.wav
ATMOS_CATALOG: dict[str, str] = {
    # --- indoor rooms (room tone / ambience beds) ---
    "roomtone-indoor-quiet": (
        "quiet indoor room tone, still air, faint room presence, "
        "no people, no movement, neutral calm"
    ),
    "roomtone-office-open": (
        "open office ambience, soft HVAC airflow, distant keyboard typing, "
        "low murmur of people working, moderate room tone"
    ),
    "roomtone-cafe": (
        "small cafe ambience, clinking cups, quiet chatter, coffee machine "
        "hiss, warm cozy atmosphere"
    ),
    "roomtone-library": (
        "quiet library room tone, soft pages turning, distant footsteps on "
        "carpet, hush, calm studious atmosphere"
    ),
    "roomtone-basement": (
        "damp basement ambience, low furnace hum, faint echo, musty quiet, "
        "slightly eerie stillness"
    ),
    # --- weather / natural ---
    "rain": (
        "steady rain falling, rhythmic patter on leaves and ground, "
        "outdoor ambience, peaceful, no thunder"
    ),
    "rain-on-window": (
        "rain tapping against a window pane, indoor perspective, "
        "cozy muffled outdoor rain, steady drizzle"
    ),
    "wind": (
        "steady wind blowing through trees, soft rustling leaves, "
        "outdoor ambience, breezy, calm"
    ),
    "wind-storm": (
        "strong wind storm, howling gusts around a building, "
        "rattling, intense but distant, ominous"
    ),
    "ocean-waves": (
        "gentle ocean waves rolling onto a sandy beach, steady surf, "
        "seagulls distant, peaceful seaside ambience"
    ),
    "forest": (
        "quiet forest ambience, birdsong, rustling leaves in a light breeze, "
        "distant stream, peaceful natural outdoor"
    ),
    "thunder-rain": (
        "distant thunder rolling with steady rain, heavy storm ambience, "
        "outdoor, dramatic but calm"
    ),
    "night-crickets": (
        "quiet countryside night ambience, crickets chirping, "
        "soft breeze, calm dark outdoor atmosphere"
    ),
    "city-street": (
        "city street ambience, distant traffic, muffled car engines, "
        "occasional pedestrian footsteps, urban daytime"
    ),
    "harbor": (
        "harbor ambience, lapping water against docks, distant boat engines, "
        "seagulls, working waterfront atmosphere"
    ),
    "snowfall": (
        "quiet snowfall ambience, muffled winter stillness, "
        "soft wind over snow, peaceful serene"
    ),
    # --- sci-fi / fantastical (beyond Cartographer names; generic) ---
    "spacecraft-cabin": (
        "spacecraft cabin ambience, low constant air circulation hum, "
        "faint electronics, enclosed calm"
    ),
    "alien-jungle": (
        "alien jungle ambience, exotic birds and insect calls, "
        "humid dense vegetation, mysterious and lush"
    ),
    "underground-cavern": (
        "large underground cavern ambience, water dripping in the distance, "
        "echoing empty space, low rumble, mysterious"
    ),
    "desert-wind": (
        "desert ambience, wind over sand dunes, dry air, distant heat shimmer, "
        "lonely open landscape, quiet"
    ),
    # --- atmosphere for specific drama scenes ---
    "tension-room": (
        "tense room ambience, very low ominous drone, silent waiting, "
        "almost inaudible hum, suspenseful stillness"
    ),
    "hospice-ward": (
        "quiet hospital ward ambience, soft beeping monitors, distant "
        "hallway movement, hushed calm, gentle"
    ),
}


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--duration", type=float, default=12.0)
    ap.add_argument("--device", default="cuda:1", help="cuda device (default cuda:1 = 3060 Ti)")
    ap.add_argument("--only", default="", help="comma names to generate (default: all)")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", type=Path, default=REPO / "assets" / "atmos")
    ap.add_argument("--full-precision", action="store_true")
    ap.add_argument("--skip-existing", action="store_true")
    args = ap.parse_args(argv)

    setup_eval_logging(logging.INFO)
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True

    # choose tasks
    if args.only:
        names = [n.strip() for n in args.only.split(",") if n.strip()]
        unknown = [n for n in names if n not in ATMOS_CATALOG]
        if unknown:
            print(f"unknown names: {unknown}; known: {sorted(ATMOS_CATALOG)}", file=sys.stderr)
            return 2
        tasks = [(n, ATMOS_CATALOG[n]) for n in names]
    else:
        tasks = list(ATMOS_CATALOG.items())

    args.out.mkdir(parents=True, exist_ok=True)
    todo = []
    for stem, prompt in tasks:
        out = args.out / f"{stem}.wav"
        if args.skip_existing and out.exists() and out.stat().st_size > 5000:
            print(f"SKIP existing {out.name}")
            continue
        todo.append((stem, prompt, out))
    if not todo:
        print("all assets already present")
        return 0
    print(f"generating {len(todo)} atmos beds (duration={args.duration}s)")

    # model
    device = args.device
    dtype = torch.float32 if args.full_precision else torch.bfloat16
    model = all_model_cfg["large_44k_v2"]
    print(f"device={device} dtype={dtype} model={model.model_name}")
    net = get_my_mmaudio(model.model_name).to(device, dtype).eval()
    net.load_weights(torch.load(model.model_path, map_location=device, weights_only=True))
    seq_cfg = model.seq_cfg
    feature_utils = FeaturesUtils(
        tod_vae_ckpt=model.vae_path,
        synchformer_ckpt=model.synchformer_ckpt,
        enable_conditions=True,
        mode=model.mode,
        need_vae_encoder=False,
    ).to(device, dtype).eval()
    rng = torch.Generator(device=device)
    fm = FlowMatching(min_sigma=0, inference_mode="euler", num_steps=25)
    print("model ready")

    t_all = time.time()
    ok = 0
    fail = 0
    for i, (stem, prompt, out) in enumerate(todo, start=1):
        rng.manual_seed(args.seed + i * 31)
        seq_cfg.duration = args.duration
        net.update_seq_lengths(seq_cfg.latent_seq_len, seq_cfg.clip_seq_len, seq_cfg.sync_seq_len)
        t0 = time.time()
        try:
            with torch.inference_mode():
                audio = generate(
                    None, None, [prompt],
                    negative_text=["music, melody, singing, voice, speech"],
                    feature_utils=feature_utils, net=net, fm=fm,
                    rng=rng, cfg_strength=4.5,
                )
            a = audio.float().cpu()[0].squeeze().numpy()
            import soundfile as sf
            sf.write(out, a, seq_cfg.sampling_rate, subtype="PCM_16")
            dur = a.shape[-1] / seq_cfg.sampling_rate
            print(f"[{i}/{len(todo)}] {stem}: {dur:.1f}s in {time.time()-t0:.1f}s -> {out}", flush=True)
            ok += 1
        except Exception as e:  # noqa: BLE001
            print(f"[{i}/{len(todo)}] {stem}: FAILED {e}", flush=True)
            fail += 1

    print(f"done: {ok} ok, {fail} failed in {time.time()-t_all:.1f}s")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())