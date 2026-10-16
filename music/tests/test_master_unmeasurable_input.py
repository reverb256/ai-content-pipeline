#!/usr/bin/env python3
"""master.py refuses inputs the EBU R128 ruler cannot measure (card t_df793408).

Standing rule (FAILURE -> TEST). Card t_568c67d2 fixed the two-pass normalizer
but left this: for an input shorter than an EBU R128 gating block (~400 ms), a
silent input, or an input whose every gating block sits below the ruler's
-70 LUFS absolute gate, loudnorm's first pass returns `input_i = -inf` and
`target_offset = inf`. master.py copied those values straight into the second
pass:

    loudnorm=...:measured_I=-inf:...:offset=inf:linear=true

ffmpeg rejects that ("Value -inf for parameter 'measured_I' out of range
[-99 - 0]") and the run died with a raw ffmpeg stderr dump inside the tool's
RuntimeError — no cause, no remedy, no master.

Measured on zephyr 2026-10-16 (ffmpeg 9.0.2) while writing these checks;
ebur128 prints -70.0 LUFS (its floor) where loudnorm prints -inf, which is why
the cause is read from the pass-1 values plus the real duration:

  input                      dur     pass1 input_i  pass1 input_tp  ebur128 I
  440 Hz tone                0.30 s  -inf           -24.06         -70.0 LUFS
  440 Hz tone                0.39 s  -inf           -24.06         -70.0 LUFS
  440 Hz tone                0.40 s  -27.75         -24.06         -27.8 LUFS
  440 Hz tone at -75 dBFS    2.00 s  -inf           -77.95         -70.0 LUFS
  digital silence            3.00 s  -inf           -inf           -70.0 LUFS
  0.2 s burst + 3 s silence  3.20 s  -32.10         -24.06         -32.0 LUFS

Decision, documented in master.py: REFUSE. One-pass loudnorm is not the fix —
measured, one-pass on the 0.30 s tone writes a file (rc 0) whose ebur128
integrated loudness is -70.0 LUFS (the floor, because no 400 ms gating block
exists) and which gate_loudness FAILS at a -56.00 LUFS deviation, with its peak
pushed to -1.50 dBFS on the way. A master no stage can measure and the package
gate must reject is not a deliverable, so no master is written.

Checks:
  A. 0.30 s tone: exit 1, cause names "shorter than the 400 ms EBU R128 gating
     block (300 ms)", the pass-1 evidence is carried, no ffmpeg dump, no
     traceback, no master written
  B. 0.39 s tone: the duration in the cause is the measured one (390 ms)
  C. 3 s digital silence: exit 1, cause is "input is silent", no dump, no
     traceback, no master written
  D. 2 s tone at a -75 dBFS peak: exit 1, cause is "no gating block above the
     EBU R128 absolute gate" — a third cause, neither "silent" nor "too short"
  E. 0.40 s tone (the boundary): NOT refused — exit 0, inside the window, and
     gate_loudness PASSES the artifact
  F. an input the ruler CAN measure is still mastered even with short content:
     a 0.2 s burst + 3 s silence is not refused
  G. the retired call is pinned with real pass-1 values: `measured_I=-inf` in a
     loudnorm second pass fails, while the tool raises the named error instead

Run: /usr/bin/python3 music/tests/test_master_unmeasurable_input.py
(also runs under PYTHONPATH=. .venv/bin/python; only ffmpeg/ffprobe and the
stdlib are used)
"""

import contextlib
import importlib.util
import io
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
DUMP_RE = re.compile(
    r"out of range|Parsed_loudnorm|Numerical result|ffmpeg command failed")

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


def ffmpeg(*args: str, check_rc: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(["ffmpeg", "-y", "-v", "error", *args],
                          capture_output=True, text=True, timeout=300)
    if check_rc and proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {proc.stderr[-400:]}")
    return proc


def tone(path: pathlib.Path, seconds: float, volume_db: float = -6.0) -> None:
    """A 440 Hz tone — the fixture generator (0.30 s of it is under a gating block)."""
    ffmpeg("-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}",
           "-af", f"volume={volume_db}dB", "-ar", "44100", "-ac", "2",
           "-c:a", "pcm_s16le", str(path))


def silence(path: pathlib.Path, seconds: float) -> None:
    ffmpeg("-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
           "-t", str(seconds), "-c:a", "pcm_s16le", str(path))


def burst_then_silence(path: pathlib.Path, burst: float, quiet: float) -> None:
    """A short burst followed by silence, in one measurable file."""
    a = path.with_name(path.stem + "-burst.wav")
    b = path.with_name(path.stem + "-quiet.wav")
    tone(a, burst)
    silence(b, quiet)
    ffmpeg("-i", str(a), "-i", str(b), "-filter_complex",
           "[0:a][1:a]concat=n=2:v=0:a=1[out]", "-map", "[out]",
           "-c:a", "pcm_s16le", str(path))


def duration_seconds(path: pathlib.Path) -> float:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, timeout=120)
    return float(proc.stdout.strip())


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


def refusal(module, src: pathlib.Path, out: pathlib.Path) -> tuple:
    """Run master.py on a refusal fixture; return (rc, stdout, stderr)."""
    if out.exists():
        out.unlink()
    return run_main(module, [str(src), "--output", str(out)])


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
tmp = pathlib.Path(tempfile.mkdtemp(prefix="master-unmeasurable-test-"))
try:
    short = tmp / "tone-0.30s.wav"
    near = tmp / "tone-0.39s.wav"
    edge = tmp / "tone-0.40s.wav"
    quiet2 = tmp / "tone-2s--75dBFS.wav"
    silent = tmp / "silence-3s.wav"
    mixed = tmp / "burst-0.2s-then-silence-3s.wav"
    tone(short, 0.30)
    tone(near, 0.39)
    tone(edge, 0.40)
    tone(quiet2, 2.0, volume_db=-57.0)
    silence(silent, 3.0)
    burst_then_silence(mixed, 0.2, 3.0)

    # --- A. a tone shorter than a gating block -------------------------------
    print()
    print("A. 0.30 s tone: refused, with the cause named")
    out_a = tmp / "out-0.30s.wav"
    rc_a, so_a, se_a = refusal(mom, short, out_a)
    check("the run exits 1 (rc=1)", rc_a == 1, f"rc={rc_a} {se_a[-200:]}")
    check("the cause names the 400 ms gating block and the real 300 ms",
          "shorter than the 400 ms EBU R128 gating block" in se_a
          and "(300 ms" in se_a, se_a[-500:])
    check("the failure line says no master was written",
          "no master was written" in se_a, se_a[-300:])
    check("the remedy is named (at least 400 ms of audible content)",
          "at least 400 ms of audible content" in se_a, se_a[-300:])
    check("the pass-1 evidence is carried (input_i=-inf, target_offset=inf)",
          "input_i=-inf" in se_a and "target_offset=inf" in se_a, se_a[-300:])
    check("no ffmpeg stderr dump leaked into the output",
          DUMP_RE.search(so_a + se_a) is None, (so_a + se_a)[-300:])
    check("no traceback", "Traceback" not in so_a + se_a)
    check("no master was written", not out_a.exists())
    check("'measured_I=-inf' was never handed to a filter",
          "measured_I=-inf" not in so_a + se_a)

    # --- B. the duration in the cause is measured, not assumed ---------------
    print()
    print("B. 0.39 s tone: the cause carries the measured duration (390 ms)")
    out_b = tmp / "out-0.39s.wav"
    rc_b, so_b, se_b = refusal(mom, near, out_b)
    check("the run exits 1", rc_b == 1, f"rc={rc_b} {se_b[-200:]}")
    check("the cause names 390 ms, the fixture's real length",
          "(390 ms" in se_b, se_b[-400:])
    check("an independent ffprobe agrees on 0.39 s",
          abs(duration_seconds(near) - 0.39) < 0.005,
          f"{duration_seconds(near)}")
    check("no master was written", not out_b.exists())

    # --- C. digital silence --------------------------------------------------
    print()
    print("C. 3 s digital silence: refused as silent, not as too short")
    out_c = tmp / "out-silence.wav"
    rc_c, so_c, se_c = refusal(mom, silent, out_c)
    check("the run exits 1", rc_c == 1, f"rc={rc_c} {se_c[-200:]}")
    check("the cause says the input is silent",
          "input is silent" in se_c, se_c[-500:])
    check("the cause is not the gating-block one (it is 3 s long)",
          "shorter than the 400 ms EBU R128 gating block" not in se_c,
          se_c[-500:])
    check("no ffmpeg stderr dump leaked into the output",
          DUMP_RE.search(so_c + se_c) is None, (so_c + se_c)[-300:])
    check("no traceback", "Traceback" not in so_c + se_c)
    check("no master was written", not out_c.exists())

    # --- D. content below the absolute gate ----------------------------------
    print()
    print("D. 2 s tone at a -75 dBFS peak: the third cause, not 'silent'")
    out_d = tmp / "out-quiet2.wav"
    rc_d, so_d, se_d = refusal(mom, quiet2, out_d)
    check("the run exits 1", rc_d == 1, f"rc={rc_d} {se_d[-200:]}")
    check("the cause names the EBU R128 absolute gate",
          "no gating block above the EBU R128 absolute gate" in se_d,
          se_d[-500:])
    check("the cause is neither 'silent' nor 'too short'",
          "input is silent" not in se_d
          and "shorter than the 400 ms" not in se_d, se_d[-500:])
    check("the cause carries the real true peak (-77.9x dBFS) read from pass 1",
          re.search(r"true peak \(-77\.\d+ dBFS\)", se_d) is not None,
          se_d[-400:])
    check("no master was written", not out_d.exists())

    # --- E. the 0.40 s boundary is still mastered ----------------------------
    print()
    print("E. 0.40 s tone: the refusal does not over-reach")
    out_e = tmp / "out-0.40s.wav"
    rc_e, so_e, se_e = run_main(mom, [str(edge), "--output", str(out_e)])
    check("the run exits 0", rc_e == 0, f"rc={rc_e} {se_e[-300:]}")
    check("a master was written", out_e.exists())
    check("the tool reports the loudness it hit",
          re.search(r"integrated loudness:\s*(-?\d+\.\d+)\s*LUFS", so_e)
          is not None, so_e[-300:])
    gate_e = subprocess.run([sys.executable, str(GATE), "--master", str(out_e),
                             "--target", "streaming"],
                            capture_output=True, text=True, timeout=900)
    check("gate_loudness PASSES the 0.40 s artifact", gate_e.returncode == 0,
          (gate_e.stdout + gate_e.stderr)[-300:])
    check("an independent ebur128 run agrees it is inside the window",
          abs(independent(out_e) - -14.0) <= 1.0, f"{independent(out_e)}")

    # --- F. a measurable input is never refused ------------------------------
    print()
    print("F. 0.2 s burst + 3 s silence is measurable: mastered, not refused")
    out_f = tmp / "out-burst.wav"
    rc_f, so_f, se_f = run_main(mom, [str(mixed), "--output", str(out_f)])
    check("the refusal path was NOT taken",
          "cannot loudness-normalize" not in so_f + se_f
          and "no master was written" not in se_f, (so_f + se_f)[-400:])
    check("the ruler measured it (independent ebur128 is not the -70 LUFS floor)",
          abs(independent(mixed) - -70.0) > 0.5, f"{independent(mixed)}")
    check("a master was written for it", out_f.exists())
    check("its verdict comes from the Step-2 loudness verifier, not a refusal",
          re.search(r"integrated loudness:\s*-?\d+\.\d+\s*LUFS", so_f)
          is not None
          and ("LOUDNESS OK" in so_f or "LOUDNESS DRIFT" in se_f),
          (so_f + se_f)[-400:])

    # --- G. the retired call, pinned on real pass-1 values -------------------
    print()
    print("G. the retired second pass is pinned: measured_I=-inf fails in ffmpeg")
    first = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(short), "-af",
         "loudnorm=I=-14.0:LRA=11:TP=-1.5:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True, timeout=300)
    data = mom.parse_loudnorm_first_pass(first.stderr or "")
    check("pass 1 of the 0.30 s tone really reports input_i=-inf",
          data.get("input_i") == "-inf", str(data))
    check("and a non-finite target_offset", data.get("target_offset") == "inf",
          str(data))
    check("the tool's finite check rejects that measurement",
          mom.finite_or_none(data.get("input_i")) is None
          and mom.finite_or_none("-27.75") == -27.75)
    old_style = (
        f"loudnorm=I=-14.0:LRA=11:TP=-1.5:measured_I={data.get('input_i')}"
        f":measured_LRA={data.get('input_lra')}"
        f":measured_TP={data.get('input_tp')}"
        f":measured_thresh={data.get('input_thresh')}"
        f":offset={data.get('target_offset')}:linear=true:print_format=summary")
    retired_out = tmp / "out-retired.wav"
    proc = subprocess.run(
        ["ffmpeg", "-y", "-i", str(short), "-af", old_style, "-ar", "44100",
         "-ac", "2", "-c:a", "pcm_s16le", str(retired_out)],
        capture_output=True, text=True, timeout=300)
    check("the retired call fails in ffmpeg (rc != 0)", proc.returncode != 0,
          f"rc={proc.returncode}")
    check("ffmpeg's own words are the out-of-range error this card replaces",
          "out of range" in (proc.stderr or ""), (proc.stderr or "")[-300:])
    check("and it wrote no file", not retired_out.exists())
    try:
        mom.normalize_loudness_two_pass(short, tmp / "out-raised.wav", -14.0)
        raised = None
    except Exception as e:                      # noqa: BLE001 - named below
        raised = e
    check("the tool now raises its named error instead of returning a path",
          isinstance(raised, mom.UnmeasurableInputError),
          f"{type(raised).__name__}: {raised}")
    check("the raised error carries the cause and the pass-1 fields",
          raised is not None and "400 ms EBU R128 gating block" in str(raised)
          and "input_i=-inf" in getattr(raised, "fields_text", ""),
          str(raised))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print()
if fails:
    print(f"RESULT: FAIL ({len(fails)})")
    for f in fails:
        print(f"  - {f}")
    sys.exit(1)
print("RESULT: PASS")
