#!/usr/bin/env python3
"""check_render_landed — a finished render must be at the ONE documented path.

WHY THIS EXISTS (card t_320bae4c, board music, measured 2026-10-16)
------------------------------------------------------------------
The render rail fetches the engine's audio into `SUNOLOCAL_WRAPPER_OUT`, and
`music/scripts/acestep_plan.py` defaulted that to `/tmp`. Inside the render pod
that is pod-local storage, so the rail's own copy was unreachable minutes later:

    $ kubectl -n mining logs job/music-pipeline-render-manual-1792179220
      ...185s status=completed
    audio saved to /tmp/sentimental-piano-room-with-the-light-going.flac
    $ kubectl -n mining cp <render-pod>:/tmp/...flac .
    Error from server (NotFound): pods "..." not found

The render SUCCEEDED and the bytes DID survive in two other places (the
sunolocal artifact store and the engine's own output dir - both measured
byte-identical: sha256 d909ad910a0cf8476bd210f671d09ef699e60fe993d42c79704b9c9318135eb9),
but the rail had no check that its OWN output existed at all: a plan that did
not claim a loop got its `.rendered` marker on `rc=0` alone. "Where does a
finished render land?" was answered only by the /tmp path that dies.

THE CONTRACT (decided here, card t_320bae4c)
--------------------------------------------
A finished render lands at exactly one path. Every stage that consumes a master
reads it THERE:

    host (nexus) : /var/lib/music-plans/<plan-stem>.<ext>   <- DOCUMENTED_HOST_PATH
    pod          : /plans/<plan-stem>.<ext>                 <- the same directory, mounted

  <plan-stem>  the plan JSON's own file name (`/var/lib/music-plans/<stem>.json`)
  <ext>        the container the engine produced (ace -> .flac, fixture -> .wav)

The rail sets `SUNOLOCAL_WRAPPER_OUT` to that mount (mining-k8s chart commit
8533861, card t_b21aeb51), so the wrapper's own copy IS the deliverable, and it
runs THIS script after every successful render and before any success marker.
A rail that moves off the path fails at the next render - loudly, naming the
path it looked in - instead of leaving the pack stage an empty directory.

NOT the pack stage's input (both are the engine's own copies, not the rail's
output): `/var/lib/sunolocal/artifacts/suno-<job-key>.<ext>` (named by the job
key, not by the plan stem; reachable through the task's `audio_url`) and
zephyr's `~/Music/acestep/suno-<...>.flac` (ComfyUI's own output directory).

ONE DEFINITION
--------------
DOCTOMENTED_HOST_PATH below is the single constant. The render CronJob passes
its own mount (`--host-path {{ .Values.outHostPath }}`), so a chart change that
moves the rail away from the documented path is exit 3 (MOVED) - the failure
this card exists to make impossible to ship silently. `--selftest` also reads
the chart's `values.yaml` and fails when the two disagree.

MODES
  --print-contract
      Print the contract, machine-readable (--json) or as text. This is the
      answer to "where does a render land?" for a brief, a card or a bot.
  --check --plans DIR --stem STEM [--host-path PATH] [--json]
      exit 0  DIR/<stem>.<flac|wav|mp3> exists (and PATH, when given, IS the
              documented host path)
      exit 1  no such file: the render did not land where the contract says
      exit 3  --host-path names a DIFFERENT directory than the contract: the
              rail has been moved and the documented path was not updated
      exit 2  usage error
  --selftest
      Prove all four behaviours on real files in a scratch directory, and check
      the chart's own `outHostPath` against the constant.

Usage:
  python3 music/scripts/check_render_landed.py --print-contract
  python3 music/scripts/check_render_landed.py --check --plans /var/lib/music-plans \
      --stem sentimental-piano-room-with-the-light-going --host-path /var/lib/music-plans
  python3 music/scripts/check_render_landed.py --selftest
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# ── the contract, in ONE place ───────────────────────────────────────────────
DOCUMENTED_HOST_PATH = "/var/lib/music-plans"
DOCUMENTED_POD_PATH = "/plans"
# Same order the rail's own master_for() probes, so the two cannot disagree.
DOCUMENTED_EXTENSIONS = ("flac", "wav", "mp3")
# The other half of this decision: the chart that mounts DOCUMENTED_HOST_PATH
# into the render job as DOCUMENTED_POD_PATH.
CHART_VALUES_DISPLAY = "mining-k8s/helm/charts/music-pipeline/values.yaml (outHostPath)"
CHART_VALUES = os.path.join(os.path.expanduser("~"), "mining-k8s", "helm",
                            "charts", "music-pipeline", "values.yaml")

OK, ABSENT, USAGE, MOVED = 0, 1, 2, 3


def landed_file(plans: Path, stem: str) -> Path | None:
    """The documented path for this render, or None when it is not there."""
    for ext in DOCUMENTED_EXTENSIONS:
        cand = plans / f"{stem}.{ext}"
        if cand.is_file():
            return cand
    return None


def contract() -> dict:
    return {
        "host_path": DOCUMENTED_HOST_PATH,
        "pod_path": DOCUMENTED_POD_PATH,
        "file": "<plan-stem>.<ext>",
        "extensions": list(DOCUMENTED_EXTENSIONS),
        "written_by": "the render CronJob, via SUNOLOCAL_WRAPPER_OUT",
        "mounted_by": CHART_VALUES_DISPLAY,
        "not_the_input": [
            "/var/lib/sunolocal/artifacts/suno-<job-key>.<ext>",
            "zephyr:~/Music/acestep/suno-<...>.flac",
        ],
        "checked_by": "music/scripts/check_render_landed.py (run by the rail)",
        "documented_in": [
            "music/stages.yaml (RENDER OUTPUT CONTRACT)",
            "mining-k8s helm/charts/music-pipeline/values.yaml (outHostPath)",
        ],
    }


def print_contract(as_json: bool) -> None:
    c = contract()
    if as_json:
        print(json.dumps(c, indent=2))
        return
    print("RENDER OUTPUT CONTRACT (card t_320bae4c)")
    print(f"  host (nexus) : {c['host_path']}/{c['file']}")
    print(f"  pod          : {c['pod_path']}/{c['file']}   (the same directory)")
    print(f"  ext          : {' | '.join(c['extensions'])} (what the engine produced)")
    print(f"  written by   : {c['written_by']}")
    print(f"  mounted by   : {c['mounted_by']}")
    print("  NOT the input: " + ", ".join(c["not_the_input"]))
    print(f"  checked by   : {c['checked_by']}")


def check(plans: Path, stem: str, host_path: str | None, as_json: bool) -> int:
    found = landed_file(plans, stem)
    moved = host_path is not None and host_path != DOCUMENTED_HOST_PATH
    result = {
        "stem": stem,
        "plans_dir": str(plans),
        "expected": f"{plans}/{stem}.<{'|'.join(DOCUMENTED_EXTENSIONS)}>",
        "found": str(found) if found else None,
        "landed": found is not None,
        "documented_host_path": DOCUMENTED_HOST_PATH,
        "host_path": host_path,
        "moved": moved,
    }
    if as_json:
        print(json.dumps(result, indent=2))
    else:
        if found:
            print(f"landed  : {found} ({found.stat().st_size} B)")
        else:
            print(f"MISSING : no {result['expected']}")
            print(f"          a finished render lands at "
                  f"{DOCUMENTED_HOST_PATH}/{stem}.{DOCUMENTED_EXTENSIONS[0]} on nexus"
                  f" ({DOCUMENTED_POD_PATH}/{stem}.{DOCUMENTED_EXTENSIONS[0]} in the "
                  f"render pod) - card t_320bae4c")
        if moved:
            print(f"MOVED   : the caller's plans dir is {host_path!r} but the "
                  f"documented host path is {DOCUMENTED_HOST_PATH!r}")
    # Drift outranks absence: it is the more specific, actionable diagnosis, and
    # a stale document is wrong even when this particular file did land.
    if moved:
        return MOVED
    return OK if found else ABSENT


# ── selftest: the red and the green, on real files ───────────────────────────
def _run(args: list[str]) -> tuple[int, str]:
    p = subprocess.run([sys.executable, os.path.abspath(__file__), *args],
                       capture_output=True, text=True)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def selftest() -> int:
    checks: list[tuple[str, bool, str]] = []

    def expect(name: str, want: int, got: int, out: str, must_say: str = "") -> None:
        ok = got == want and (not must_say or must_say in out)
        checks.append((name, ok,
                       f"exit {got} (wanted {want})"
                       + (f", output never said {must_say!r}" if must_say and must_say not in out else "")))

    with tempfile.TemporaryDirectory() as td:
        plans = Path(td) / "plans"
        plans.mkdir()
        stem = "selftest-render"
        good_stem = "selftest-loop-claim"

        # RED - a render that landed nowhere (the /tmp case, card t_320bae4c).
        rc, out = _run(["--check", "--plans", str(plans), "--stem", stem,
                        "--host-path", DOCUMENTED_HOST_PATH])
        expect("a render that landed nowhere FAILS (rc 1)", ABSENT, rc, out,
               "MISSING")

        # an absent plans dir is the same answer, not a traceback
        rc, out = _run(["--check", "--plans", str(plans / "nope"), "--stem", stem])
        expect("an absent plans dir FAILS (rc 1)", ABSENT, rc, out)

        # GREEN - the documented path, real bytes.
        master = plans / f"{stem}.flac"
        master.write_bytes(b"fLaC" + b"\x00" * 64)
        rc, out = _run(["--check", "--plans", str(plans), "--stem", stem,
                        "--host-path", DOCUMENTED_HOST_PATH])
        expect("a render at the documented path PASSES (rc 0)", OK, rc, out, "landed")
        expect("the PASS names the file it found", OK, rc, out, str(master))

        # the ext is whatever the engine produced (fixture engines render .wav)
        (plans / f"{good_stem}.wav").write_bytes(b"RIFF" + b"\x00" * 64)
        rc, out = _run(["--check", "--plans", str(plans), "--stem", good_stem])
        expect("a .wav render at the same path PASSES (rc 0)", OK, rc, out)

        # MOVED - the rail was moved off the documented path. This is the check
        # the card asks for: a future change to the rail cannot silently move it.
        moved = plans / "elsewhere"
        moved.mkdir()
        (moved / f"{stem}.flac").write_bytes(master.read_bytes())
        rc, out = _run(["--check", "--plans", str(moved), "--stem", stem,
                        "--host-path", "/var/lib/some-other-plans"])
        expect("a rail moved off the documented path FAILS (rc 3), even though "
               "the file is there", MOVED, rc, out, "MOVED")

        # usage error, named
        rc, out = _run(["--check", "--stem", stem])
        expect("--check without --plans is a usage error (rc 2)", USAGE, rc, out)

        # contract mode
        rc, out = _run(["--print-contract", "--json"])
        expect("--print-contract --json emits the path", OK, rc, out,
               DOCUMENTED_HOST_PATH)

    # The other half: the chart must mount the documented directory.
    chart = Path(os.path.expanduser(CHART_VALUES))
    if chart.is_file():
        text = chart.read_text()
        m = re.search(r"^outHostPath:[ \t]*(\S+)", text, re.M)
        got = m.group(1).strip().strip('"') if m else "<no outHostPath key>"
        checks.append((
            f"the chart's outHostPath is the documented host path ({chart})",
            got == DOCUMENTED_HOST_PATH,
            f"values.yaml says {got!r}, the contract says {DOCUMENTED_HOST_PATH!r}"))
    else:
        print(f"SKIP  chart values not present at {chart} - "
              f"cannot compare outHostPath (set $HOME or run on nexus)")

    bad = 0
    for name, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"  [{detail}]"))
        bad += 0 if ok else 1
    if bad:
        print(f"\n{len(checks) - bad}/{len(checks)} checks behaved")
        print(f"BROKEN: {bad} check(s) misbehaved")
        return 1
    print(f"\nOK: {len(checks)} checks behaved "
          f"(red on a render that landed nowhere, green at the documented path, "
          f"red when the rail is moved)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="the ONE documented path a finished render lands at "
                    "(card t_320bae4c)")
    ap.add_argument("--print-contract", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--plans", default=None,
                    help="the plans dir to look in (the rail passes its mount)")
    ap.add_argument("--stem", default=None, help="the plan's own file name")
    ap.add_argument("--host-path", default=None,
                    help="the caller's own host path for that dir; when it is not "
                         "the documented one, exit 3 (the rail was moved)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    modes = [args.print_contract, args.check, args.selftest]
    if sum(1 for m in modes if m) != 1:
        print("usage: pick exactly one of --print-contract, --check, --selftest",
              file=sys.stderr)
        return USAGE
    if args.print_contract:
        print_contract(args.json)
        return OK
    if args.selftest:
        return selftest()
    if not args.plans or not args.stem:
        print("usage: --check needs --plans DIR and --stem STEM", file=sys.stderr)
        return USAGE
    return check(Path(args.plans), args.stem, args.host_path, args.json)


if __name__ == "__main__":
    sys.exit(main())
