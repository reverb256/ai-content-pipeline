#!/usr/bin/env python3
"""acestep_brief.py — one line in, one song out.

This is the "layer in between" (option A): instead of hand-authoring caption,
lyrics, bpm, key and duration, hand ACE-Step's OWN language model a plain-English
brief and let it plan the song.

Why this exists: the first track was authored entirely by hand — every creative
field typed out — which means changing the song meant editing a script. The
Artist node in ComfyUI_RH_ACE-Step wraps the model's built-in planner (the "LM"
half of ACE-Step's hybrid LM+DiT architecture), and it emits a complete
ACE-StepGenerationParams blueprint from a single prompt.

Contrast:
    GenerationParams node  -> YOU supply caption, lyrics, bpm, duration, key
    Artist node            -> the LLM supplies all of it, from `prompt`

The plan is still inspectable: the Artist node's output is ordinary
generation params, so option B (our own planner, driven by the researched genre
templates) can slot in at exactly the same place without touching the rest.

Usage (from a host that can reach the pod's ComfyUI, or inside the pod):
    python3 acestep_brief.py "a tender song about intimacy in vrchat"
    python3 acestep_brief.py "rainy night chill lounge" --instrumental
    python3 acestep_brief.py "anime opening about becoming someone new" --lang "Japanese (ja)"

Output lands in ~/Music/acestep/ on the host (the pod mounts it at
/home/j_kro/3d-out/music, inside ComfyUI's --output-directory, because ComfyUI
realpaths the save target and rejects anything outside it).
"""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request

COMFY = "http://localhost:8188"
OUTPUT_PREFIX = "music/acestep"          # -> ~/Music/acestep/ on the host
DEFAULT_LANG = "English (en)"


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
        detail = e.read().decode(errors="replace")
        raise SystemExit(f"HTTP {e.code} from {path}:\n{detail}")


def slug(text, maxlen=48):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:maxlen] or "song"


def build(brief, language, instrumental, seed, filename):
    """Loader -> Artist (the planner) -> Creator -> SaveAudio."""
    return {
        "1": {"class_type": "RunningHub ACE-Step Loader",
              "inputs": {"llm type": "acestep-5Hz-lm-1.7B"}},
        # THE LAYER: one prompt in, a full song blueprint out.
        "2": {"class_type": "RunningHub ACE-Step Artist",
              "inputs": {"llm_handler": ["1", 1],
                         "prompt": brief,
                         "vocal_language": language,
                         "instrumental": instrumental,
                         "seed": seed}},
        "3": {"class_type": "RunningHub ACE-Step Creator",
              "inputs": {"dit_handler": ["1", 0],
                         "llm_handler": ["1", 1],
                         "params": ["2", 0],
                         "seed": seed}},
        "4": {"class_type": "SaveAudio",
              "inputs": {"audio": ["3", 0],
                         "filename_prefix": f"{OUTPUT_PREFIX}/{filename}"}},
    }


def main():
    ap = argparse.ArgumentParser(description="brief -> song via ACE-Step's planner")
    ap.add_argument("brief", help="one line of English describing the song")
    ap.add_argument("--lang", default=DEFAULT_LANG,
                    help=f'vocal language, e.g. "Japanese (ja)" (default: {DEFAULT_LANG})')
    ap.add_argument("--instrumental", action="store_true")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--name", help="output filename stem (default: slug of the brief)")
    ap.add_argument("--timeout", type=int, default=900, help="seconds to wait")
    args = ap.parse_args()

    filename = args.name or slug(args.brief)
    wf = build(args.brief, args.lang, args.instrumental, args.seed, filename)

    print(f"brief      : {args.brief}")
    print(f"language   : {args.lang}   instrumental: {args.instrumental}   seed: {args.seed}")
    print(f"planner    : RunningHub ACE-Step Artist (the model's own LM)")
    queued = api("/prompt", {"prompt": wf})
    pid = queued["prompt_id"]
    print(f"queued     : {pid}")
    print("waiting    : the planner writes lyrics + picks bpm/key/duration, then the DiT renders")

    start = time.time()
    while time.time() - start < args.timeout:
        time.sleep(15)
        hist = api(f"/history/{pid}")
        if hist and pid in hist:
            entry = hist[pid]
            status = entry.get("status", {})
            if status.get("completed") or status.get("status_str") in ("success", "error"):
                elapsed = time.time() - start
                print(f"\nfinished in {elapsed:.0f}s — status: {status.get('status_str')}")
                for node_id, out in (entry.get("outputs") or {}).items():
                    for a in out.get("audio", []):
                        print(f"  output: {a.get('filename')}  (subfolder={a.get('subfolder') or '.'})")
                if status.get("status_str") == "error":
                    for m in status.get("messages", []):
                        print("  ", str(m)[:400])
                    return 1
                return 0
        print(f"  ...{int(time.time()-start)}s", flush=True)

    print(f"\nTIMEOUT after {args.timeout}s — the prompt may still be running; "
          f"check /history/{pid}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
