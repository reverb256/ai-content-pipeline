#!/usr/bin/env python3
"""loop_seam_check — measure a loop seam with BOTH rulers, not just the curvature one.

WHY THIS EXISTS
---------------
`music/rubrics/gamer.json` defines `loop_safety` (weight 3 of 10) with this evidence:
"Tail/head RMS compatibility for a loop (last-1s RMS within ~6 dB of first-1s RMS, no
fade-to-silence on a loop claim)". `music/gates/gate_loop_points.py` — the `game-assets`
lane's loop gate — measures junction CURVATURE only (the discrete second difference across
the wrap), so it detects a derivative KINK (a click) and measures nothing about LEVEL.

Measured 2026-10-16 on real synthesized 25.6 s loops (card t_6f0d261e, brief
`music/briefs/elemental-fire.md` §9): a loop with a 1.6 s fade-out tail PASSES
gate_loop_points at 2.21x curvature while its tail-1s sits 8.8 dB below its head-1s — a
hard reject on the rubric's own `reject_signals` ("fade-out or truncated ending on a
game-loop claim"). No single `--click-ratio-max` separates that fade (2.21x) from a real
click (5.99x), so the gate needs a SECOND MEASUREMENT, not a different number. Carded
t_bab8aa19 (nexus-core) for the gate fix; this script is the second ruler in the meantime.
A loop that passes only one ruler is not verified.

PROVENANCE RULE (the reason this script prints paths)
-----------------------------------------------------
An absolute dB figure belongs to the artifact it was measured on. The same sine rendered at
two amplitudes yields the same curvature ratio but dB figures ~18 dB apart; a table that
mixes two renders reports levels no named artifact produces. So this script always prints
the measured artifact's absolute path next to its numbers, and compares the DELTA.

RULERS
------
1. curvature — delegates to music/gates/gate_loop_points.py (unchanged, no forking).
2. level     — |mean_volume(last 1 s) - mean_volume(first 1 s)| must be <= --tolerance-db
               (default 6.0 dB, the rubric's "~6 dB"), measured with ffmpeg volumedetect.

DERIVING the curvature verdict (card t_88879c37)
------------------------------------------------
The delegated gate runs THREE rulers (curvature, the tail/head level ruler, and the
end-ramp/silence guard) and returns 1 when ANY of them fails, so ITS EXIT STATUS IS NOT A
CURVATURE VERDICT. Until this fix this tool read it as one and printed
`curvature: FAIL 2.21x` for a loop whose ratio is UNDER the 3.0x ceiling (measured on
…/workspaces/t_6f0d261e/loop/faded.wav) — the gate had refused for its LEVEL, and the
gate's level fix line was printed as curvature evidence.

The curvature verdict is now read off the gate's OWN curvature line,
`seam : curvature ratio <x>x (max <y>x)`, which the gate prints on PASS and on FAIL. Both
numbers come from that line — the ratio under test AND the ceiling the gate applied — so
this tool keeps no copy of the ceiling. A gate that refused before it measured the seam
(out-of-range loop points, a span under the floor, a silent region), or a gate whose report
this tool can no longer read, leaves the seam UNVERIFIED — which is a FAIL, never a pass.

VERDICT
-------
PASS only when BOTH rulers pass AND the delegated gate itself exits 0. Exit 0 = verified
seamless by both; 1 = at least one ruler reports a break; 2 = usage error. Reasons go to
stderr, each under the ruler that measured it: a gate refusal the two rulers above do not
name is printed as its own `gate :` block with the gate's own problem lines, so one ruler's
failure never speaks for another and no gate refusal is ever dropped from the verdict.

Usage:
  python3 music/scripts/loop_seam_check.py --master loop.wav --loop-points lp.json
                                           [--scratch DIR] [--tolerance-db 6.0] [--json]
  python3 music/scripts/loop_seam_check.py --selftest [--bpm 150] [--bars 16] [--dir DIR]

--selftest builds the four documented artifacts (seamless / fade-out tail / half-period
phase slip / truncated) at the given BPM and bar count, runs both rulers on each, prints the
table with absolute paths, and exit 0 iff the documented behaviour reproduces:

  A seamless    both PASS
  B fade tail   curvature PASS, level FAIL  <- the false pass, closed by ruler 2
  C phase slip  curvature FAIL
  D truncated   curvature FAIL

If B ever reports level PASS, ruler 2 has regressed and this script says so.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
GATE = REPO / "music" / "gates" / "gate_loop_points.py"
MEAN_RE = re.compile(r"mean_volume:\s*(-?[\d.]+)\s*dB")
# The delegated gate's OWN curvature line, printed on PASS and on FAIL. Both numbers are
# read from it: the ratio under test and the ceiling the gate applied (card t_88879c37).
SEAM_RE = re.compile(r"seam\s*:\s*curvature ratio\s*([\d.]+)x\s*\(max\s*([\d.]+)x\)")
# The gate's refusal lines (`  - <problem>`), printed by its fail().
GATE_PROBLEM_RE = re.compile(r"^ {2}- (.*)$")
DEFAULT_TOLERANCE_DB = 6.0


def find_ffmpeg() -> Path:
    """Locate ffmpeg. Prefer the lane's pinned build, then $PATH."""
    env = os.environ.get("FFMPEG_BIN_DIR")
    cands = []
    if env:
        cands.append(Path(env))
    cands.append(Path.home() / ".hermes" / "tools" /
                 "ffmpeg-9.0.1-linux-x64" / "bin")
    for c in cands:
        if (c / "ffmpeg").is_file():
            return c
    found = shutil.which("ffmpeg")
    if found:
        return Path(found).parent
    return Path("/usr/bin")


FF_BIN = find_ffmpeg()


def run(cmd: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                          env=env if env is not None else os.environ.copy())


def mean_volume_db(master: Path, start: float, dur: float = 1.0) -> float | None:
    """mean_volume (dB, plain RMS) of [start, start+dur) via ffmpeg volumedetect."""
    proc = run([str(FF_BIN / "ffmpeg"), "-v", "info", "-ss", f"{max(start, 0.0):.4f}",
                "-t", f"{dur:.4f}", "-i", str(master), "-af", "volumedetect",
                "-f", "null", "-"])
    m = MEAN_RE.search(proc.stderr or "")
    return float(m.group(1)) if m else None


def curvature_ruler(master: Path, loop_points: Path, scratch: Path) -> dict:
    """Delegate to the real gate. Do not re-implement it.

    The delegated gate runs THREE rulers and returns 1 when ANY of them fails, so its
    exit status is NOT a curvature verdict (card t_88879c37). Read the curvature verdict
    off the gate's own `seam : curvature ratio <x>x (max <y>x)` line, which it prints on
    PASS and on FAIL — that line carries both the measured ratio and the ceiling.

    No readable seam line means the seam was NOT verified: either the gate refused before
    it measured one (loop points out of range, a span under the floor, a silent region)
    or its report changed shape. That is a FAIL, never a pass — a tool that cannot read
    its own evidence must not report success.
    """
    proc = run([sys.executable, str(GATE), "--master", str(master),
                "--loop-points", str(loop_points), "--scratch", str(scratch)])
    out = proc.stdout + proc.stderr
    problems = [m.group(1) for m in
                (GATE_PROBLEM_RE.match(ln) for ln in out.splitlines()) if m]
    res = {"verdict": "FAIL", "ratio": None, "ratio_max": None,
           "rc": proc.returncode, "problems": problems, "why": None,
           "output": out.strip()}
    if proc.returncode != 0 and "FAIL gate_loop_points" not in out:
        res["why"] = (f"the delegated gate exited {proc.returncode} without its own "
                      "report — the gate could not run")
        return res
    m = SEAM_RE.search(out)
    if m is None:
        res["why"] = ("the gate printed no 'seam : curvature ratio <x>x (max <y>x)' "
                      "line, so no curvature was measured"
                      if proc.returncode != 0
                      else "the gate exited 0 but printed no seam line")
        return res
    # The gate's own two numbers. Its exit status is deliberately NOT consulted here.
    res["ratio"] = float(m.group(1))
    res["ratio_max"] = float(m.group(2))
    res["verdict"] = "PASS" if res["ratio"] <= res["ratio_max"] else "FAIL"
    return res


def level_ruler(master: Path, loop_start: float, loop_end: float,
                tolerance_db: float) -> dict:
    span = loop_end - loop_start
    if span < 2.0:
        return {"verdict": "FAIL", "head_db": None, "tail_db": None, "delta_db": None,
                "reason": f"loop span {span:.2f}s is shorter than the 2 s minimum"}
    head = mean_volume_db(master, loop_start, 1.0)
    tail = mean_volume_db(master, loop_end - 1.0, 1.0)
    if head is None or tail is None:
        return {"verdict": "FAIL", "head_db": head, "tail_db": tail, "delta_db": None,
                "reason": "volumedetect produced no mean_volume line"}
    delta = abs(tail - head)
    ok = delta <= tolerance_db
    return {"verdict": "PASS" if ok else "FAIL", "head_db": head, "tail_db": tail,
            "delta_db": delta,
            "reason": (f"tail-1s {tail:.1f} dB vs head-1s {head:.1f} dB "
                       f"(delta {delta:.1f} dB, max {tolerance_db:.1f})")}


def check(master: Path, loop_points: Path, scratch: Path | None,
          tolerance_db: float) -> dict:
    lp = json.loads(loop_points.read_text(encoding="utf-8"))
    loop_start = float(lp["loop_start_s"])
    loop_end = float(lp["loop_end_s"])
    sc = scratch or Path(tempfile.mkdtemp(prefix="loopseam-"))
    sc.mkdir(parents=True, exist_ok=True)
    curv = curvature_ruler(master, loop_points, sc)
    lvl = level_ruler(master, loop_start, loop_end, tolerance_db)
    # The delegated gate's refusal, when the curvature ruler did not itself measure the
    # break: the gate also runs an end-ramp and a silence guard this tool does not
    # re-implement, so a PASS here must not silently outvote the gate that measured
    # something this tool cannot see (card t_88879c37 — "a loop that passes only one
    # ruler is not verified" cuts both ways).
    gate = {"rc": curv["rc"], "problems": curv["problems"],
            "unattributed_refusal": curv["rc"] != 0
            and (curv["verdict"] == "PASS" or curv["ratio"] is None)}
    verdict = ("PASS" if curv["verdict"] == "PASS" and lvl["verdict"] == "PASS"
               and curv["rc"] == 0 else "FAIL")
    return {"master": str(master.resolve()), "loop": [loop_start, loop_end],
            "curvature": curv, "level": lvl, "gate": gate, "verdict": verdict}


# ── selftest: build the four documented artifacts and assert the behaviour ──

def write_wav(path: Path, samples: list[float], sr: int) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767))
                               for s in samples))


def build_fixtures(out: Path, bpm: float, bars: int, sr: int = 44100,
                   freq: float = 220.0, fade_s: float = 1.6) -> dict:
    """Four artifacts at the genre's loop length. ONE amplitude for all of them."""
    dur = bars * 4 * 60.0 / bpm
    n = int(sr * dur)
    base = [math.sin(2 * math.pi * freq * i / sr) for i in range(n)]
    out.mkdir(parents=True, exist_ok=True)

    paths = {}
    paths["A_seamless"] = out / "A_seamless.wav"
    write_wav(paths["A_seamless"], base, sr)

    paths["B_faded"] = out / "B_faded.wav"
    b = list(base)
    fade = int(sr * fade_s)
    for i in range(fade):
        b[n - fade + i] *= (fade - i) / fade
    write_wav(paths["B_faded"], b, sr)

    paths["C_phaseslip"] = out / "C_phaseslip.wav"
    c = list(base)
    slip = int(sr * (1.0 / (2 * freq)))
    for i in range(slip):
        c[n - slip + i] = -c[n - slip + i]
    write_wav(paths["C_phaseslip"], c, sr)

    paths["D_truncated"] = out / "D_truncated.wav"
    d = base[: n - int(sr * (1.0 / (4 * freq)))]
    write_wav(paths["D_truncated"], d, sr)
    return {"dur": dur, "paths": paths}


def selftest(args: argparse.Namespace) -> int:
    print(f"loop_seam_check --selftest\n"
          f"  ffmpeg : {FF_BIN}/ffmpeg\n"
          f"  gate   : {GATE}\n"
          f"  loop   : {args.bars} bars at {args.bpm} BPM "
          f"= {args.bars * 4 * 60.0 / args.bpm:.3f} s, one amplitude for all four\n")
    out = Path(args.dir) if args.dir else Path(
        tempfile.mkdtemp(prefix="loopseam-selftest-"))
    out.mkdir(parents=True, exist_ok=True)
    built = build_fixtures(out, args.bpm, args.bars)
    sr = 44100
    durs = {"A_seamless": args.bars * 4 * 60.0 / args.bpm,
            "B_faded": args.bars * 4 * 60.0 / args.bpm,
            "C_phaseslip": args.bars * 4 * 60.0 / args.bpm,
            "D_truncated": (args.bars * 4 * 60.0 / args.bpm)
                           - 1.0 / (4 * 220.0)}

    rows = []
    problems = []
    for name in ("A_seamless", "B_faded", "C_phaseslip", "D_truncated"):
        master = built["paths"][name]
        lp = out / f"{name}.loop_points.json"
        lp.write_text(json.dumps({"loop_start_s": 0.0, "loop_end_s": durs[name],
                                  "seamless": True}))
        res = check(master, lp, out / f"scratch_{name}", args.tolerance_db)
        rows.append((name, res))

    hdr = (f"{'artifact':14} {'curvature':>18} {'level (tail vs head)':>28} {'verdict':>8}")
    print(hdr)
    print("-" * len(hdr))
    for name, res in rows:
        c, l = res["curvature"], res["level"]
        curv = f"{c['verdict']} {c['ratio']:.2f}x" if c["ratio"] else c["verdict"]
        lvl = (f"{l['verdict']} {l['delta_db']:.1f} dB "
               f"({l['tail_db']:.1f} vs {l['head_db']:.1f})"
               if l["delta_db"] is not None else l["verdict"])
        print(f"{name:14} {curv:>18} {lvl:>28} {res['verdict']:>8}")
    print()

    expect = {"A_seamless": ("PASS", "PASS"), "B_faded": ("PASS", "FAIL"),
              "C_phaseslip": ("FAIL", None), "D_truncated": ("FAIL", None)}
    for name, res in rows:
        want_c, want_l = expect[name]
        got_c, got_l = res["curvature"]["verdict"], res["level"]["verdict"]
        if got_c != want_c:
            problems.append(f"{name}: curvature ruler measured {got_c}, documented {want_c} "
                            f"({res['curvature']['ratio']})")
        if want_l and got_l != want_l:
            problems.append(f"{name}: level ruler measured {got_l}, documented {want_l} "
                            f"({res['level'].get('reason')})")
    if rows[1][1]["curvature"]["verdict"] == "PASS" and rows[1][1]["level"]["verdict"] == "PASS":
        problems.append("B_faded: BOTH rulers passed a fade-out tail — the false pass is gone "
                        "(good) but §9 of the brief must be updated and t_bab8aa19 closed")

    for name, res in rows:
        print(f"  {name:14} {res['master']}")
    print()
    if problems:
        print("FAIL loop_seam_check --selftest: documented behaviour did NOT reproduce:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("SELFTEST PASS loop_seam_check: A both rulers PASS; B curvature PASS / level FAIL "
          "(the fade is caught); C and D curvature FAIL")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="loop_seam_check — curvature AND level rulers")
    p.add_argument("--master")
    p.add_argument("--loop-points")
    p.add_argument("--scratch")
    p.add_argument("--tolerance-db", type=float, default=DEFAULT_TOLERANCE_DB)
    p.add_argument("--json", action="store_true")
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--bpm", type=float, default=150.0)
    p.add_argument("--bars", type=int, default=16)
    p.add_argument("--dir")
    args = p.parse_args(argv)

    if args.selftest:
        return selftest(args)
    if not (args.master and args.loop_points):
        p.error("--master and --loop-points are required (or use --selftest)")
    master = Path(args.master)
    lp = Path(args.loop_points)
    if not master.is_file():
        print(f"FAIL loop_seam_check\n  - no master file: {master}", file=sys.stderr)
        return 1
    if not lp.is_file():
        print(f"FAIL loop_seam_check\n  - no loop points file: {lp}", file=sys.stderr)
        return 1
    res = check(master, lp, Path(args.scratch) if args.scratch else None,
                args.tolerance_db)
    if args.json:
        print(json.dumps(res, indent=2))
        return 0 if res["verdict"] == "PASS" else 1
    c, l = res["curvature"], res["level"]
    g = res["gate"]
    if res["verdict"] == "PASS":
        print("PASS loop_seam_check")
        print(f"  master   : {res['master']}")
        print(f"  loop     : [{res['loop'][0]:.3f}s -> {res['loop'][1]:.3f}s]")
        print(f"  curvature: PASS {c['ratio']:.2f}x (the gate's own seam line, max "
              f"{c['ratio_max']:.1f}x) — no click at the wrap")
        print(f"  level    : {l['reason']} — no fade at the wrap")
        print(f"  gate     : PASS — the delegated gate_loop_points ran all its rulers "
              f"and exited 0")
        return 0
    print("FAIL loop_seam_check", file=sys.stderr)
    print(f"  master   : {res['master']}", file=sys.stderr)
    print(f"  loop     : [{res['loop'][0]:.3f}s -> {res['loop'][1]:.3f}s]",
          file=sys.stderr)
    # The curvature line carries the curvature RULER's verdict, derived from the gate's
    # own seam line — never from the gate's exit status (card t_88879c37).
    ok_c = c["verdict"] == "PASS"
    ratio = f"{c['ratio']:.2f}x" if c["ratio"] is not None else "no ratio"
    if ok_c:
        print(f"  curvature: PASS {ratio} (the gate's own seam line, max "
              f"{c['ratio_max']:.1f}x) — no click at the wrap", file=sys.stderr)
    elif c["ratio"] is None:
        print(f"  curvature: FAIL — {c['why']}", file=sys.stderr)
    else:
        print(f"  curvature: FAIL {ratio} (max {c['ratio_max']:.1f}x)",
              file=sys.stderr)
        # The curvature ruler's own evidence: the gate's seam line, its click problem,
        # and the fix IT printed for a click. Nothing else belongs under this ruler.
        for line in c["output"].splitlines():
            s = line.strip()
            if SEAM_RE.search(line) or s.startswith("- seam curvature") \
                    or s.startswith("fix:"):
                print(f"    {s}", file=sys.stderr)
    # The delegated gate's refusal, when the curvature ruler did not measure the break.
    # The gate's own problem lines are printed verbatim so a refusal is never dropped and
    # never re-attributed to a ruler that did not make it.
    if g["unattributed_refusal"]:
        print(f"  gate     : FAIL — the delegated gate_loop_points refused (exit "
              f"{g['rc']}); its own reasons:", file=sys.stderr)
        for p in g["problems"]:
            print(f"    - {p}", file=sys.stderr)
    ok_l = l["verdict"] == "PASS"
    print(f"  level    : {l['verdict']} {l['reason']}", file=sys.stderr)
    if not ok_l:
        print("    the rubric's `loop_safety` reject (a fade-out or level ramp on a "
              "game-loop claim)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
