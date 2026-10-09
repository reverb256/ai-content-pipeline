#!/usr/bin/env python3
"""acestep_plan.py — render a PLAN. The bridge from option B to audio.

The planner (`music/planner/planner.py`) produces a plan: caption, lyrics, bpm,
key, duration, time signature. This renders it.

WHY THIS USES THE MANUAL NODE, NOT THE ARTIST NODE
--------------------------------------------------
`RunningHub ACE-Step Artist` is the model's own planner — give it a sentence and
it invents the whole song, including details the brief never asked for. That is
option A, and it is the wrong half of the pipeline here: the plan already exists
and its whole value is that it was constrained by our researched craft and
validated before render. Feeding the plan to `GenerationParams` renders exactly
what was planned. Handing the same brief back to `Artist` would throw the plan
away and re-invent it.

Order: plan -> validate -> render -> (optionally) master via acestep_qa.py.

Usage (inside the pod, or anywhere that can reach ComfyUI):
    python3 acestep_plan.py /path/to/plan.json
    python3 acestep_plan.py /path/to/plan.json --qa          # chain the mastering pass
    python3 acestep_plan.py /path/to/plan.json --seed 7
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

COMFY = os.environ.get("COMFY_URL", "http://localhost:8188")
# Inside the pod the host's ~/Music is mounted INSIDE ComfyUI's output dir; see
# helm/apps/comfyui-zephyr.yaml. On the host it is ~/Music.
MUSIC_SUBDIR = "music/acestep"
OUTPUT_PREFIX = MUSIC_SUBDIR


def api(path, payload=None, timeout=30):
    url = f"{COMFY}{path}"
    if payload is None:
        req = urllib.request.Request(url)
    else:
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
            return json.loads(body) if body else None
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code} from {path}:\n{e.read().decode(errors='replace')[:600]}")


def load_plan(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        plan = json.load(fh)
    for field in ("caption", "lyrics", "bpm", "key", "duration", "timesignature"):
        if plan.get(field) in (None, ""):
            sys.exit(f"FATAL: plan is missing '{field}': {path}")
    return plan


def check_lyrics(plan: dict, allow_empty: bool) -> None:
    """A draft plan scaffolds sections for a human and they are EMPTY.

    Rendering a draft silently produces an instrumental with a vocal-shaped
    hole, which looks like a model failure and is not one. Refuse by default.
    """
    body = plan["lyrics"]
    # `[ \t]*\n` and not `\s*\n`: `\s` matches newlines, so `\s*\n` lets an
    # empty section swallow the next section's tag and report as full.
    sections = re.findall(r"^\[([^\]]+)\][ \t]*\n(.*?)(?=\n\[|\Z)", body, re.M | re.S)
    empty = [tag for tag, content in sections
             if not [ln for ln in content.splitlines()
                     if ln.strip() and not ln.strip().startswith(("#", "("))]]
    if not sections:
        sys.exit("FATAL: plan has no [Section] headers — nothing to sing.")
    if empty and not allow_empty:
        sys.exit(
            f"FATAL: {len(empty)} section(s) have no lyrics: {', '.join(empty)}.\n"
            "       This is a DRAFT plan — a human writes the lines into it first.\n"
            "       (--allow-empty renders anyway, for instrumental or scratch passes.)")


def build(plan: dict, seed: int, filename: str) -> dict:
    """Loader -> GenerationParams (the PLAN, not a re-invention) -> Creator -> Save."""
    return {
        "1": {"class_type": "RunningHub ACE-Step Loader",
              "inputs": {"llm type": "acestep-5Hz-lm-1.7B"}},
        # The plan goes in verbatim. This is the difference from option A.
        "2": {"class_type": "RunningHub ACE-Step GenerationParams",
              "inputs": {"caption": plan["caption"],
                         "lyrics": plan["lyrics"],
                         "bpm": int(plan["bpm"]),
                         "duration": float(plan["duration"]),
                         "keyscale": plan["key"],
                         "timesignature": str(plan["timesignature"])}},
        "3": {"class_type": "RunningHub ACE-Step Creator",
              "inputs": {"dit_handler": ["1", 0],
                         "llm_handler": ["1", 1],
                         "params": ["2", 0],
                         "seed": seed}},
        "4": {"class_type": "SaveAudio",
              "inputs": {"audio": ["3", 0],
                         "filename_prefix": f"{OUTPUT_PREFIX}/{filename}"}},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="render a plan to audio")
    ap.add_argument("plan", help="path to a plan JSON from planner.py")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--name", default=None, help="output stem (default: plan filename)")
    ap.add_argument("--allow-empty", action="store_true",
                    help="render even when sections are empty (draft/instrumental)")
    ap.add_argument("--qa", action="store_true",
                    help="chain acestep_qa.py over the result (repair + genre fix + LUFS)")
    ap.add_argument("--qa-genre", default="General / Balanced",
                    help="Music_Fix profile for the QA pass")
    ap.add_argument("--timeout", type=int, default=900)
    args = ap.parse_args()

    plan = load_plan(args.plan)
    check_lyrics(plan, args.allow_empty)

    stem = args.name or os.path.splitext(os.path.basename(args.plan))[0]
    wf = build(plan, args.seed, stem)

    print(f"plan     : {args.plan}")
    print(f"title    : {plan.get('title')}   authorship: {plan.get('authorship','(unstated)')}")
    print(f"params   : {plan['bpm']} BPM · {plan['key']} · {plan['timesignature']}/4 · {plan['duration']}s")
    print(f"mode     : MANUAL (the plan is rendered as planned, not re-invented)")
    queued = api("/prompt", {"prompt": wf})
    pid = queued["prompt_id"]
    print(f"queued   : {pid}")

    start = time.time()
    while time.time() - start < args.timeout:
        time.sleep(15)
        hist = api(f"/history/{pid}")
        if hist and pid in hist:
            entry = hist[pid]
            status = entry.get("status", {})
            if status.get("completed") or status.get("status_str") in ("success", "error"):
                print(f"\nfinished in {time.time()-start:.0f}s — {status.get('status_str')}")
                if status.get("status_str") == "error":
                    for m in status.get("messages", []):
                        print("  ", str(m)[:500])
                    return 1
                produced = None
                for node_id, out in (entry.get("outputs") or {}).items():
                    for a in out.get("audio", []):
                        produced = a.get("filename")
                        print(f"  output: {produced}  (subfolder={a.get('subfolder') or '.'})")
                if produced and args.qa:
                    print("\n--- QA pass ---")
                    r = subprocess.run([sys.executable, os.path.join(
                        os.path.dirname(os.path.abspath(__file__)), "acestep_qa.py"),
                        produced, "--genre", args.qa_genre])
                    return r.returncode
                return 0
        print(f"  ...{int(time.time()-start)}s", flush=True)

    print(f"\nTIMEOUT after {args.timeout}s — check /history/{pid}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
