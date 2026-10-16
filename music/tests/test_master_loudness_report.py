#!/usr/bin/env python3
"""master.py loudness-report regression checks — the mix/stage speaks the gate's ruler.

Standing rule (FAILURE -> TEST). Card t_568c67d2: `music/mix/master.py`
normalized with two-pass loudnorm to `target_lufs`, then measured the result with
`volumedetect` mean_volume — a plain RMS mean, no K-weighting, no gating — and
never measured the integrated LUFS it had actually targeted. The gate had already
retired that ruler (card t_9546841b), so the master stage and the package stage
spoke different dialects and nothing said whether the target was hit.

Measured on this host (zephyr, ffmpeg 9.0.2) while writing these checks:

  * the tool's own two-pass path never ran at all. It read
    `json.loads(stderr.splitlines()[-1])`, and on ffmpeg 9.x the last stderr line
    is the muxer `size=N/A time=...` line, not the loudnorm JSON block. The run
    silently fell back to one-pass.
  * that fallback passed `measured_I=0.0 ... measured_thresh=0.0`, telling
    loudnorm the file was already at 0 LUFS. On a copy of the Virtual
    Reflections master `this-small-forever` the tool wrote a master at
    **-28.0 LUFS integrated** — 14 LU below the -14 LUFS target it was asked for
    — while its volumedetect line read mean_volume -30.4 dB. Nothing in the log
    said the target was missed.
  * after the fix the same file normalizes to **-14.00 LUFS** (volumedetect mean
    -16.3 dB) and a copy of `welcome` to -13.90 LUFS (+0.10 LU), both inside the
    gate window, with the deviation logged.

Checks:
  A. the first-pass JSON block is read although muxer stats follow it
  B. end-to-end: a normalization run reports integrated LUFS, true peak and the
     deviation, and the reported number matches an independent ebur128 run
  C. that same run does not fall back to one-pass, and gate_loudness PASSES the
     master the tool just certified (one ruler, both stages)
  D. volumedetect survives only as labelled RMS context, never as the loudness
     result
  E. a master deliberately outside +/-1 LUFS is flagged by the verifier, with the
     gate's tolerance and not a private one
  F. the drifted master FAILS the run (exit 1) with LOUDNESS DRIFT on stderr;
     --allow-loudness-drift downgrades it to a warning
  G. the ruler is not re-implemented in master.py (no second dialect), and the
     targets come from the gate's table

Run: PYTHONPATH=. .venv/bin/python music/tests/test_master_loudness_report.py
(also runs under a bare python3; only ffmpeg/ffprobe and the stdlib are used)
"""

import contextlib
import importlib.util
import io
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
MASTER = REPO / "music" / "mix" / "master.py"
GATE = REPO / "music" / "gates" / "gate_loudness.py"

INTEGRATED_RE = re.compile(r"\bI:\s*(-?[\d.]+|-inf)\s*LUFS", re.IGNORECASE)
REPORTED_RE = re.compile(r"integrated loudness:\s*(-?[\d.]+)\s*LUFS")
DEVIATION_RE = re.compile(r"deviation\s*([+-]\d+\.\d+)\s*LUFS")

# Real ffmpeg 9.0.2 stderr shape from a `loudnorm=...:print_format=json`
# first pass: the JSON block, then the muxer stats.
FIRST_PASS_STDERR = (
    '[Parsed_loudnorm_0 @ 0x55f50afae600] \n'
    '{\n\t"input_i" : "-14.01",\n\t"input_tp" : "-2.37",\n'
    '\t"input_lra" : "8.70",\n\t"input_thresh" : "-24.46",\n'
    '\t"output_i" : "-14.32",\n\t"output_tp" : "-1.50",\n'
    '\t"output_lra" : "7.30",\n\t"output_thresh" : "-24.62",\n'
    '\t"normalization_type" : "dynamic",\n\t"target_offset" : "0.32"\n'
    '}\n'
    '[out#0/null @ 0x56082acb51c0] video:0KiB audio:231300KiB subtitle:0KiB '
    'other streams:0KiB global headers:0KiB muxing overhead: unknown\n'
    'size=N/A time=00:05:08.40 bitrate=N/A speed=44.8x'
)

fails: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}"
          + (f"  [{detail}]" if detail and not ok else ""))
    if not ok:
        fails.append(name)


def load_master():
    spec = importlib.util.spec_from_file_location(
        "music_mix_master_under_test", MASTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tone(path: pathlib.Path, volume_db: float, seconds: float = 10) -> None:
    """A 440 Hz tone at the given gain — the fixture generator."""
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
         f"sine=frequency=440:duration={seconds}",
         "-af", f"volume={volume_db}dB", "-ar", "44100", "-ac", "2", str(path)],
        check=True, capture_output=True, text=True, timeout=120)


def independent(path: pathlib.Path) -> float:
    """Integrated loudness measured by a separate ffmpeg invocation."""
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
         "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True, timeout=600)
    hits = INTEGRATED_RE.findall(proc.stderr or "")
    if not hits:
        raise RuntimeError(f"independent ebur128 found no I: line for {path}")
    return float(hits[-1])


def run_main(module, argv: list) -> tuple:
    """Call main(argv) in-process; return (rc, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = module.main(argv)
    return rc, out.getvalue(), err.getvalue()


# ---------------------------------------------------------------------------
if not MASTER.is_file():
    print(f"FAIL  master present  [{MASTER} does not exist]")
    sys.exit(1)
if not GATE.is_file():
    print(f"FAIL  gate present  [{GATE} does not exist]")
    sys.exit(1)
if not shutil.which("ffmpeg"):
    print("FAIL  ffmpeg present  [not on PATH]")
    sys.exit(1)

mom = load_master()
tmp = pathlib.Path(tempfile.mkdtemp(prefix="master-loudness-test-"))
try:
    # --- A. the retired positional read of the first pass ---------------------
    print()
    print("A. the loudnorm first-pass block is read although muxer stats follow it")
    try:
        json.loads(FIRST_PASS_STDERR.strip().splitlines()[-1])
        old_read_worked = True
    except json.JSONDecodeError:
        old_read_worked = False
    check("the retired positional read (stderr.splitlines()[-1]) cannot read "
          "this block — the defect this check pins", not old_read_worked)
    parsed = mom.parse_loudnorm_first_pass(FIRST_PASS_STDERR)
    check("the new reader finds the JSON block anyway",
          parsed.get("input_i") == "-14.01"
          and parsed.get("target_offset") == "0.32", str(parsed))
    try:
        mom.parse_loudnorm_first_pass("[out#0/null @ 0x1] video:0KiB\nsize=N/A")
        raised = False
    except ValueError:
        raised = True
    check("a stderr with no loudnorm JSON raises instead of returning junk", raised)

    # --- B. end-to-end normalization report ----------------------------------
    print()
    print("B. a real normalization run reports the integrated LUFS it hit")
    src = tmp / "src.wav"
    out = tmp / "out.wav"
    tone(src, -6.0)                      # ~-27.8 LUFS
    rc, so, se = run_main(mom, [str(src), "--output", str(out)])
    check("the run exits 0", rc == 0, f"rc={rc} {se.strip()[-200:]}")
    m = REPORTED_RE.search(so)
    check("stdout reports an integrated LUFS value", m is not None, so[-400:])
    reported = float(m.group(1)) if m else None
    ind = independent(out)
    check(f"the reported value ({reported} LUFS) matches an independent ebur128 "
          f"run ({ind:.2f} LUFS) to 0.1 LU",
          reported is not None and abs(reported - ind) <= 0.1,
          f"reported={reported} independent={ind}")
    check("stdout reports the deviation from target_lufs",
          DEVIATION_RE.search(so) is not None, so[-400:])
    check("stdout reports the true peak", "true peak" in so)
    check("stdout names the ruler it used (the gate's)",
          "ebur128" in so and "LUFS" in so)
    check("the normalized master is inside the gate's window",
          abs(ind - -14.0) <= 1.0, f"independent={ind}")
    check("the two-pass path really ran (no one-pass fallback)",
          "falling back to one-pass" not in so.lower(), so[-400:])

    # --- C. one ruler: the gate agrees with the tool on the same artifact -----
    print()
    print("C. gate_loudness PASSES the master this tool just certified")
    g = subprocess.run([sys.executable, str(GATE), "--master", str(out),
                        "--target", "streaming"],
                       capture_output=True, text=True, timeout=900)
    check("gate_loudness passes the tool's output", g.returncode == 0,
          (g.stdout + g.stderr)[-300:])

    # --- D. volumedetect is context, never the verdict ------------------------
    print()
    print("D. volumedetect survives only as labelled RMS context")
    check("the RMS block is labelled as not-the-loudness-result",
          "RMS context (NOT the loudness result" in so, so[-400:])
    vlines = [ln for ln in so.splitlines() if "volumedetect" in ln]
    check("every volumedetect line is a labelled context line",
          bool(vlines) and all(("RMS context" in ln or "  volumedetect " in ln)
                               for ln in vlines), str(vlines))
    check("the loudness lines do not carry mean_volume",
          not [ln for ln in so.splitlines()
               if "LUFS" in ln and "mean_volume" in ln])
    src_txt = MASTER.read_text()
    check("the loudness verdict comes from the gate's ruler, in the docstring too",
          "verify_master_loudness" in src_txt)

    # --- E. a master deliberately outside the window --------------------------
    print()
    print("E. a master deliberately outside +/-1 LUFS is flagged")
    hot = tmp / "hot.wav"
    tone(hot, 12.0)                      # ~-9.8 LUFS
    hot_lufs = independent(hot)
    check(f"the deliberate master measures {hot_lufs:.1f} LUFS, outside the "
          "window", abs(hot_lufs - -14.0) > 1.0, f"{hot_lufs}")
    v = mom.verify_master_loudness(hot, -14.0)
    check("the verifier reports it as outside the window",
          v["ok"] and not v["within_tolerance"], str(v))
    check("the deviation matches an independent measurement to 0.1 LU",
          abs(v["deviation_lufs"] - (hot_lufs - -14.0)) <= 0.1,
          f"verifier={v['deviation_lufs']} independent={hot_lufs - -14.0}")
    check("the direction is LOUD (positive deviation), not inverted",
          v["deviation_lufs"] > 0)
    check("the tolerance is the gate's, not a private one",
          v["tolerance_lufs"] == mom.loudness_gate().DEFAULT_TOLERANCE,
          f"{v['tolerance_lufs']}")
    check("the ruler it reports is the gate's ebur128 ruler",
          "ebur128" in v["ruler"].lower(), v["ruler"])

    # --- F. the drifted master fails the run ---------------------------------
    print()
    print("F. a drifted master FAILS the run; --allow-loudness-drift warns only")
    # The normalizer is stubbed to hand back the deliberately hot master: a
    # two-pass loudnorm run that hits its target cannot produce drift, so this is
    # the only way to exercise the drift branch of main() with a real hot file.
    real_two_pass = mom.normalize_loudness_two_pass
    drift_out = tmp / "drift.wav"
    try:
        mom.normalize_loudness_two_pass = lambda *a, **k: hot
        rc_f, so_f, se_f = run_main(
            mom, [str(src), "--output", str(drift_out)])
    finally:
        mom.normalize_loudness_two_pass = real_two_pass
    check("the run FAILS (exit 1) on a master outside the window", rc_f == 1,
          f"rc={rc_f} {se_f[-300:]}")
    check("stderr says LOUDNESS DRIFT and names the direction",
          "LOUDNESS DRIFT" in se_f and "LOUD" in se_f, se_f[-300:])
    check("stderr carries the failure line, not just a warning",
          "FAILED" in se_f, se_f[-300:])
    check("no traceback", "Traceback" not in so_f + se_f)
    check("the drift block names the master and the ruler",
          "master    :" in se_f and "ruler     :" in se_f, se_f[-300:])

    try:
        mom.normalize_loudness_two_pass = lambda *a, **k: hot
        rc_a, so_a, se_a = run_main(
            mom, [str(src), "--output", str(tmp / "drift-allowed.wav"),
                  "--allow-loudness-drift"])
    finally:
        mom.normalize_loudness_two_pass = real_two_pass
    check("--allow-loudness-drift downgrades the drift to a warning (exit 0)",
          rc_a == 0, f"rc={rc_a} {se_a[-200:]}")
    check("the warning still says gate_loudness will fail the master",
          re.search(r"gate_loudness will fail this\s+master at package time",
                    so_a, re.IGNORECASE) is not None, so_a[-300:])

    # --- G. no second dialect -------------------------------------------------
    print()
    print("G. master.py carries no loudness dialect of its own")
    check("master.py defines no LUFS regex of its own",
          "INTEGRATED_RE" not in src_txt
          and not re.search(r"re\.compile\(\s*r?\"[^\"]*LUFS", src_txt))
    check("master.py measures loudness through the gate's measure()",
          "gate.measure(" in src_txt)
    check("master.py loads the gate from music/gates/gate_loudness.py",
          str(mom.GATE_LOUDNESS_PATH).endswith("music/gates/gate_loudness.py"),
          str(mom.GATE_LOUDNESS_PATH))
    targets = mom.loudness_targets()
    check("the targets are the gate's table (-14 streaming / -16 sync)",
          targets.get("streaming") == -14.0 and targets.get("sync") == -16.0,
          str(targets))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print()
if fails:
    print(f"RESULT: FAIL ({len(fails)})")
    for f in fails:
        print(f"  - {f}")
    sys.exit(1)
print("RESULT: PASS")
