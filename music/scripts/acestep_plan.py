#!/usr/bin/env python3
"""
acestep_plan.py — render a PLAN via sunolocal studio API.
Replaces direct ComfyUI invocation with a Suno-shaped API call.

The planner (`music/planner/planner.py`) produces a plan: caption, lyrics, bpm,
key, duration, time signature. This renders it via sunolocal.

Usage (inside the pod):
    python3 acestep_plan.py /path/to/plan.json
    python3 acestep_plan.py /path/to/plan.json --name stem
    python3 acestep_plan.py /path/to/plan.json --qa          # chain the mastering pass
    python3 acestep_plan.py /path/to/plan.json --seed 7
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import subprocess

# Configuration
SUNOLOCAL_HOST = os.environ.get(
    "SUNOLOCAL_HOST",
    "http://sunolocal.mining.svc.cluster.local:8123"
)
POLL_INTERVAL = 5  # seconds
DEFAULT_TIMEOUT = 900  # seconds

# A REFUSAL IS NOT A FAILURE (card t_69cab80b, 2026-10-16).
#
# The render rail records what this script decided, and until now it had one
# code for both: `return 1` is "the submit or the poll failed" AND the draft
# refusal was `sys.exit("FATAL: ...")`, which is also 1. The rail therefore
# wrote a `.refused` marker — "a human must edit the sheet" — for a network
# blip, and a marker is what stops the plan being attempted again. Measured on
# the live rail (job music-pipeline-render-29869781, 2026-10-16 16:41): a plan
# refused as a draft got `.refused`, and nothing re-attempts it.
#
# So the two are separate codes now:
#
#   1  an operational failure: the engine was unreachable, the poll failed, the
#      answer had no audio_url. The rail writes NO marker, so the next run
#      retries it - which is what "ComfyUI was up and then it failed" means.
#   4  a REFUSAL: the plan needs a human (a scaffold sheet, no sections, empty
#      lyrics). It is decided locally, before any network call, and the rail
#      records it in `<stem>.refused` WITH the plan's fingerprint, so a later
#      edit to the plan opens it again (card t_69cab80b).
REFUSED_EXIT = 4


class Refused(SystemExit):
    """The refusal the rail records: exit code 4, with a readable message.

    `sys.exit("message")` exits 1, which is also what an operational failure
    returns (see REFUSED_EXIT above), and a caller that reads only the code
    cannot tell the two apart. This carries both: the code the render rail
    records a `.refused` marker for, and the message a caller that catches it
    (or the wrapper's own tests) can read.
    """

    def __init__(self, message: str) -> None:
        sys.stderr.write(message + "\n")
        super().__init__(REFUSED_EXIT)
        self.message = message

    def __str__(self) -> str:
        return self.message


def refuse(message: str) -> None:
    """Say why, then exit with the refusal code the rail records."""
    raise Refused(message)


def _http_json(url, data=None, method=None, headers=None, timeout=30):
    """Perform an HTTP JSON request and return parsed JSON."""
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    req_data = None
    if data is not None:
        req_data = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=req_data,
        headers=req_headers,
        method=method or ("POST" if data is not None else "GET"),
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            return json.loads(body) if body else None
    except urllib.error.HTTPError as e:
        sys.stderr.write(
            f"HTTP {e.code} from {url}: {e.read().decode(errors='replace')[:600]}\n"
        )
        raise
    except urllib.error.URLError as e:
        sys.stderr.write(f"URL error: {e}\n")
        raise


def load_plan(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def singable_lines(content: str) -> list:
    """The lines of a section that are meant to be SUNG.

    A DRAFT plan is a scaffold: it carries the section tags and the template's
    per-section craft notes in parentheses, and no lyrics. Those notes are
    guidance, not words. A note can WRAP across lines, so a line that opens a
    parenthesis and does not close it keeps the following lines out too - the
    unwrapped version of this test passed a scaffold whose directions wrapped
    (card t_bc6a0c00 measured it on the epic-orchestral-boss sheet).
    """
    kept = []
    depth = 0
    for raw in content.splitlines():
        line = raw.strip()
        if not line:
            continue
        if depth:
            # still inside a direction opened on an earlier line
            depth = max(depth + line.count("(") - line.count(")"), 0)
            continue
        if line.startswith(("#", "(")):
            depth = max(depth + line.count("(") - line.count(")"), 0)
            continue
        kept.append(line)
    return kept


def check_lyrics(plan: dict, allow_empty: bool) -> None:
    """Refuse a plan whose lyrics are a scaffold or a set of bare tags.

    This is the guard the render CronJob's own comment relies on: it calls this
    script WITHOUT --allow-empty and records a `<stem>.refused` marker on
    `REFUSED_EXIT` (4, card t_69cab80b - 1 is an operational failure and gets no
    marker), so a draft plan must be refused HERE, before any network call, or
    the engine renders a track whose vocal line is the template's craft notes.

    The previous version of this file only refused lyrics that were COMPLETELY
    empty. A scaffold is never completely empty - it has the tags - so a queued
    draft went straight to the engine. Measured 2026-10-16 on the three draft
    plans the brief queue produced (card t_a14e5d52); the section-level check
    below is the version the pre-sunolocal script carried.

    AN INSTRUMENTAL PLAN IS NOT A DRAFT (card t_25a6499c D3, card t_8c5a6b91).
    A plan carrying `"instrumental": true` has bare section tags BY DESIGN -
    they are structure control and there is nothing to sing - so the refusal
    would mark every instrumental genre `refused` forever and the queue could
    never render one. The plan's OWN FIELD is the declaration. It is
    deliberately NOT inferred from "the sections are empty", which is what
    would relax the draft refusal: a draft plan has no `instrumental` field,
    so it is still refused here exactly as before.
    """
    if plan.get("instrumental"):
        return
    body = plan.get("lyrics", "")
    if not body.strip():
        if not allow_empty:
            refuse(
                "FATAL: plan has empty lyrics — a draft section needs human input. "
                "Use --allow-empty to force rendering anyway."
            )
        return
    # `[ \t]*\n` and not `\s*`: `\s` matches newlines, so `\s*\n` lets an empty
    # section swallow the next section's tag and report itself as full.
    sections = re.findall(r"^\[([^\]]+)\][ \t]*\n(.*?)(?=\n\[|\Z)", body, re.M | re.S)
    if not sections:
        if not allow_empty:
            refuse("FATAL: plan has no [Section] headers — nothing to sing. "
                   "Use --allow-empty to force rendering anyway.")
        return
    empty = [tag for tag, content in sections if not singable_lines(content)]
    if empty and not allow_empty:
        refuse(
            f"FATAL: {len(empty)} section(s) have no lyrics: {', '.join(empty)}.\n"
            "       This is a DRAFT plan — a human writes the lines into it first.\n"
            "       (--allow-empty renders anyway, for instrumental or scratch passes.)"
        )


def build_suno_request(plan: dict) -> dict:
    """Map plan fields to SunoGenerateRequest JSON.

    TEMPO AND KEY ARE CARRIED EXPLICITLY (card t_25a6499c D1/D2). The
    Suno-shaped body has no tempo field and no key field of its own, and this
    wrapper is where both used to be lost:

      * `plan["bpm"]` never left the plan, so the engine answered its
        hardcoded 120 for every genre (sentimental-piano came out 1.67x its
        72 BPM anchor);
      * `plan["key"]` had nowhere to go, so the engine filled the key from the
        style caption and the ACE node received 674 characters of paragraph as
        `keyscale`.

    Both are sunolocal extensions on the body now (`bpm`, `keyscale`) and are
    passed through verbatim. `instrumental` is carried the same way: it used to
    be hardcoded False, which was card t_25a6499c D5 — the render rail dropped
    the flag, so an instrumental plan rendered as a vocal track with an empty
    vocal line.
    """
    # Required fields: prompt (caption), lyrics, title, duration.
    # Optional: we set defaults for others.
    return {
        "prompt": plan.get("caption", ""),
        "lyrics": plan.get("lyrics", ""),
        "title": plan.get("title", ""),
        # From the PLAN, not assumed. A plan without the field is vocal, which
        # is the old behaviour for every plan already on disk.
        "instrumental": bool(plan.get("instrumental")),
        "model": "v6",
        "custom_mode": False,
        "negative_tags": None,
        "vocal_gender": None,
        "duration": int(plan.get("duration", 180)),
        "style_weight": None,
        "weirdness_constraint": None,
        "audio_weight": None,
        "variety": None,
        "callback_url": None,
        "seed": None,  # we will pass seed separately if needed
        "engine": os.environ.get("SUNOLOCAL_ENGINE", "ace"),
        # sunolocal extensions; None means "not specified". `bpm` then falls back
        # to the engine's documented default (120). `keyscale` gets NO default:
        # when the plan states no key the ACE node resolves the key from the
        # caption, which is where the modality lives (card t_1578cc47). A value
        # invented here would not sit behind the caption — the node injects a
        # non-empty keyscale into its constrained decode and thereby overrides it.
        "bpm": int(plan["bpm"]) if plan.get("bpm") is not None else None,
        "keyscale": (str(plan["key"]).strip() or None) if plan.get("key") else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="render a plan via sunolocal API")
    ap.add_argument("plan", help="path to a plan JSON from planner.py")
    ap.add_argument(
        "--seed", type=int, default=42, help="seed passed to the engine (if supported)"
    )
    ap.add_argument(
        "--name",
        default=None,
        help="output stem (default: plan filename without extension)",
    )
    ap.add_argument(
        "--allow-empty",
        action="store_true",
        help="render even when sections are empty (draft/instrumental)",
    )
    ap.add_argument(
        "--qa",
        action="store_true",
        help="chain acestep_qa.py over the result (repair + genre fix + LUFS)",
    )
    ap.add_argument(
        "--qa-genre",
        default="General / Balanced",
        help="Music_Fix profile for the QA pass",
    )
    ap.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help="seconds to wait for completion",
    )
    args = ap.parse_args()

    plan = load_plan(args.plan)
    check_lyrics(plan, args.allow_empty)

    stem = args.name or os.path.splitext(os.path.basename(args.plan))[0]

    # Build request
    request_data = build_suno_request(plan)
    # Override seed if provided (the engine may use it)
    if args.seed is not None:
        request_data["seed"] = args.seed

    print(f"plan     : {args.plan}")
    print(f"title    : {plan.get('title')}   authorship: {plan.get('authorship','(unstated)')}")
    # `keyscale` on the wire is None when no artifact states a key, and this
    # line says so instead of printing a bare "None" that a reader takes for a
    # key signature (card t_f65b0f4c).
    print(f"params   : {plan.get('bpm')} BPM · {plan.get('key') or 'key=unknown'} · "
          f"{plan.get('timesignature')}/4 · {plan.get('duration')}s")
    print(f"mode     : {'INSTRUMENTAL (no lyrics box)' if plan.get('instrumental') else 'VOCAL'}"
          f"  (instrumental={bool(plan.get('instrumental'))}, carried to the engine)")
    print(f"sunolocal: {SUNOLOCAL_HOST}")

    # Submit job
    try:
        resp = _http_json(
            f"{SUNOLOCAL_HOST}/api/v1/generate",
            data=request_data,
            method="POST",
        )
    except Exception as e:
        sys.stderr.write(f"Failed to submit to sunolocal: {e}\n")
        return 1

    if not resp or "task_id" not in resp:
        sys.stderr.write(f"Unexpected response: {resp}\n")
        return 1

    task_id = resp["task_id"]
    print(f"queued   : {task_id} (status: {resp.get('status', 'pending')})")

    # Poll for completion
    start = time.time()
    while time.time() - start < args.timeout:
        time.sleep(POLL_INTERVAL)
        try:
            task_resp = _http_json(
                f"{SUNOLOCAL_HOST}/api/v1/task/{task_id}",
                method="GET",
            )
        except Exception as e:
            sys.stderr.write(f"Polling error: {e}\n")
            continue

        if not task_resp:
            sys.stderr.write("Empty task response\n")
            continue

        status = task_resp.get("status")
        print(f"  ...{int(time.time()-start)}s status={status}", flush=True)

        if status == "completed":
            # studio.py merges the job result into the TOP LEVEL of the task
            # payload; older/other producers may nest it under "result".
            # Accept both.
            result = task_resp.get("result") or {}
            merged = {**task_resp, **result} if isinstance(result, dict) else dict(task_resp)
            audio_url = merged.get("audio_url")
            if not audio_url:
                sys.stderr.write(f"Completed but no audio_url in response: {merged}\n")
                return 1

            # Construct full download URL
            if audio_url.startswith("/"):
                download_url = f"{SUNOLOCAL_HOST}{audio_url}"
            else:
                download_url = audio_url  # assume full

            # Determine output path. The extension comes from the artifact the
            # service actually produced (audio_url), not from the engine name:
            # ace renders .flac, yue2 .flac, fixture .wav.
            #
            # The DIRECTORY is the caller's decision, never a default: a finished
            # render has exactly ONE documented path, /var/lib/music-plans/
            # <stem>.<ext> on the node (the render rail sets
            # SUNOLOCAL_WRAPPER_OUT to its mount of it), and the pack stage reads
            # it there (card t_320bae4c, music/stages.yaml RENDER OUTPUT
            # CONTRACT, music/scripts/check_render_landed.py). An unset value
            # used to write this copy to /tmp without a word - pod-local, gone
            # with the pod, and the rail certified the render anyway. The
            # fallback stays /tmp for an ad-hoc caller, but it says so.
            out_dir = os.environ.get("SUNOLOCAL_WRAPPER_OUT") or ""
            if not out_dir:
                out_dir = "/tmp"
                sys.stderr.write(
                    "WARNING: SUNOLOCAL_WRAPPER_OUT is unset - writing the render "
                    f"copy to {out_dir}, which does NOT outlive this process. The "
                    "documented render path is <SUNOLOCAL_WRAPPER_OUT>/<stem>.<ext> "
                    "= /var/lib/music-plans/<stem>.<ext> on the node (card "
                    "t_320bae4c).\n")
            url_ext = os.path.splitext(audio_url)[1].lstrip(".")
            ext = url_ext if url_ext in ("wav", "flac", "mp3") else "wav"
            out_path = os.path.join(out_dir, f"{stem}.{ext}")

            # Download the audio file
            try:
                req = urllib.request.Request(download_url)
                with urllib.request.urlopen(req, timeout=60) as resp:
                    audio_bytes = resp.read()
                with open(out_path, "wb") as f:
                    f.write(audio_bytes)
                print(f"audio saved to {out_path}")
            except Exception as e:
                sys.stderr.write(f"Failed to download audio: {e}\n")
                return 1

            # If QA requested, run the QA script
            if args.qa:
                qa_script = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), "acestep_qa.py"
                )
                if not os.path.isfile(qa_script):
                    sys.stderr.write(f"QA script not found: {qa_script}\n")
                    return 1
                print(f"--- QA pass ---")
                ret = subprocess.run(
                    [
                        sys.executable,
                        qa_script,
                        out_path,
                        "--genre",
                        args.qa_genre,
                    ]
                )
                return ret.returncode
            else:
                return 0

        elif status == "failed":
            error = task_resp.get("result", {}).get("error", "unknown")
            sys.stderr.write(f"Job failed: {error}\n")
            return 1
        # else pending or processing, continue loop

    sys.stderr.write(f"Timeout after {args.timeout}s waiting for task {task_id}\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
