#!/usr/bin/env python3
"""gate_loudness regression checks — the ruler is ebur128 integrated, not
volumedetect mean_volume.

Standing rule (FAILURE -> TEST). Card t_9546841b found `gate_loudness`
measuring `ffmpeg volumedetect` mean_volume — a plain RMS mean, no
K-weighting, no gating — while the architecture spec, the campaign
MANIFEST.json and the pipeline's own `loudnorm=I=-14:TP=-1.0:LRA=11`
normalizer all speak EBU R128 LUFS. The two rulers disagreed on the verdict:
of the five Virtual Reflections masters, the RMS ruler failed three that
measure -13.6 / -13.3 / -12.8 LUFS (welcome, world-of-blue, sincerely), and
it would have passed a tone whose RMS sits on the target while its loudness
does not.

These checks pin the ruler in BOTH directions with synthesized fixtures, so a
silent reversion to volumedetect cannot pass:

  A. a master at -14.0 LUFS integrated must PASS, although its volumedetect
     mean_volume is -16.3 dB — the old RMS ruler would have FAILED it.
  B. a master whose volumedetect mean_volume is -14.1 dB must FAIL, because
     its integrated loudness is -11.8 LUFS — the old RMS ruler would have
     PASSED it.
  C. a silent file must FAIL with the -inf reason, never crash.
  D. the gate's own measurement must match an independent ffmpeg ebur128 run
     to 0.1 LU, and its --json must report `measured_lufs` / `ruler`, with no
     mean_volume-style key left behind.

Fixture calibration (measured on this host, ffmpeg 9.0.2, five levels to
confirm linearity): a 440 Hz sine rendered with `-af volume=XdB` measures
integrated X-21.8 LUFS and volumedetect mean_volume X-24.1 dB. The pre-fix
suite fixtures sat at volume=10 dB — mean_volume -14.1 dB, i.e. pinned to the
RMS ruler — and read -11.8 LUFS once the gate measured correctly.

Run: PYTHONPATH=. .venv/bin/python music/tests/test_gate_loudness.py
(also runs under a bare python3; only ffmpeg/ffprobe and the stdlib are used)
"""

import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
GATE = REPO / "music" / "gates" / "gate_loudness.py"

INTEGRATED_RE = re.compile(r"\bI:\s*(-?[\d.]+|-inf)\s*LUFS", re.IGNORECASE)
MEAN_RE = re.compile(r"mean_volume:\s*(-?[\d.]+)\s*dB")

fails: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not ok else ""))
    if not ok:
        fails.append(name)


def tone(path: pathlib.Path, volume_db: float) -> None:
    """A 10 s 440 Hz tone at the given gain — the fixture generator."""
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
         "-i", "sine=frequency=440:duration=10",
         "-af", f"volume={volume_db}dB", "-ar", "44100", "-ac", "2",
         str(path)],
        check=True, capture_output=True, text=True, timeout=120)


def silence(path: pathlib.Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
         "-i", "anullsrc=r=44100:cl=stereo", "-t", "3", str(path)],
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


def independent_mean(path: pathlib.Path) -> float:
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
         "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True, timeout=600)
    m = MEAN_RE.search(proc.stderr or "")
    if not m:
        raise RuntimeError(f"independent volumedetect found no mean for {path}")
    return float(m.group(1))


def run_gate(path: pathlib.Path, *extra: str) -> tuple:
    proc = subprocess.run([sys.executable, str(GATE), "--master", str(path),
                           *extra],
                          capture_output=True, text=True, timeout=900)
    return proc.returncode, proc.stdout + proc.stderr


# ---------------------------------------------------------------------------
if not GATE.is_file():
    print(f"FAIL  gate present  [{GATE} does not exist]")
    sys.exit(1)
if not shutil.which("ffmpeg"):
    print("FAIL  ffmpeg present  [not on PATH]")
    sys.exit(1)

tmp = pathlib.Path(tempfile.mkdtemp(prefix="gate-loudness-test-"))
try:
    lufs_true = tmp / "lufs_true.wav"      # case A: -14.0 LUFS, -16.3 dB RMS
    rms_true = tmp / "rms_true.wav"        # case B: -11.8 LUFS, -14.1 dB RMS
    silent = tmp / "silent.wav"            # case C
    tone(lufs_true, 7.8)
    tone(rms_true, 10.0)
    silence(silent)

    # --- 1. the fixtures really do discriminate the two rulers -------------
    print()
    print("1. the fixtures discriminate the two rulers (independent ffmpeg)")
    a_lufs, a_mean = independent(lufs_true), independent_mean(lufs_true)
    b_lufs, b_mean = independent(rms_true), independent_mean(rms_true)
    check(f"A measures {a_lufs:.1f} LUFS (target -14 +-1 -> PASS expected)",
          abs(a_lufs - -14.0) <= 1.0, f"{a_lufs}")
    check(f"A mean_volume {a_mean:.1f} dB would FAIL the retired RMS ruler",
          abs(a_mean - -14.0) > 1.0, f"{a_mean}")
    check(f"B measures {b_lufs:.1f} LUFS (target -14 +-1 -> FAIL expected)",
          abs(b_lufs - -14.0) > 1.0, f"{b_lufs}")
    check(f"B mean_volume {b_mean:.1f} dB would PASS the retired RMS ruler",
          abs(b_mean - -14.0) <= 1.0, f"{b_mean}")

    # --- 2. the gate's verdicts --------------------------------------------
    print()
    print("2. the gate's verdicts follow ebur128 integrated loudness")
    rc_a, out_a = run_gate(lufs_true, "--target", "streaming")
    check("A (-14.0 LUFS) PASSES", rc_a == 0, f"rc={rc_a} {out_a.strip()[-200:]}")
    rc_b, out_b = run_gate(rms_true, "--target", "streaming")
    check("B (-11.8 LUFS) FAILS — a regression to volumedetect flips this",
          rc_b == 1, f"rc={rc_b} {out_b.strip()[-200:]}")
    rc_c, out_c = run_gate(silent, "--target", "streaming")
    floor = re.search(r"integrated\s+(-inf|-?[\d.]+)\s*LUFS", out_c)
    floor_val = None
    if floor and floor.group(1).lower() != "-inf":
        floor_val = float(floor.group(1))
    check("silent file FAILS at the ebur128 silence floor, no traceback",
          rc_c == 1 and "Traceback" not in out_c
          and (floor_val is None or floor_val <= -60.0),
          f"rc={rc_c} {out_c.strip()[-200:]}")
    # ffmpeg 9.0.2's ebur128 floors digital silence at -70.0 LUFS instead of
    # emitting -inf, so the gate fails silence on the deviation. Its -inf
    # branch stays as a guard for builds that do emit -inf (measured here).
    check("silence by either route reads far below the target "
          "(-70.0 LUFS or -inf), never a near-target value",
          floor is not None and (floor_val is None or floor_val <= -60.0),
          f"parsed={floor.group(0) if floor else None!r}")
    rc_nf, out_nf = run_gate(tmp / "does-not-exist.wav", "--target", "streaming")
    check("missing file exits 2 (the gate's documented usage-error code), "
          "no traceback",
          rc_nf == 2 and "no such file" in out_nf and "Traceback" not in out_nf,
          f"rc={rc_nf}")

    # --- 3. the gate reports the ruler it uses ------------------------------
    print()
    print("3. the gate's measurement and its JSON name the ebur128 ruler")
    rc_j, out_j = run_gate(lufs_true, "--target", "streaming", "--json")
    try:
        doc = json.loads(out_j)
    except json.JSONDecodeError:
        doc = {}
        check("--json is valid JSON", False, out_j.strip()[-200:])
    if doc:
        check("--json is valid JSON", True)
        check("--json carries measured_lufs",
              "measured_lufs" in doc, f"keys={sorted(doc)}")
        check("--json carries ruler naming ebur128",
              "ebur128" in str(doc.get("ruler", "")).lower(),
              f"ruler={doc.get('ruler')!r}")
        check("--json has no mean_volume-era key",
              not [k for k in doc if "mean_volume" in k], f"keys={sorted(doc)}")
        check("--json value matches the independent ebur128 run to 0.1 LU",
              abs(float(doc.get("measured_lufs", 0)) - a_lufs) <= 0.1,
              f"gate={doc.get('measured_lufs')} independent={a_lufs}")

    # --- 4. the retired dialect must not come back --------------------------
    print()
    print("4. the gate's CODE (not its history) no longer measures the "
          "retired dialect")
    src = GATE.read_text()
    # the docstring is allowed to name the retired ruler; the code is not
    body = src[src.index('"""', src.index('"""') + 3) + 3:]
    check("no volumedetect call left in the gate body",
          "volumedetect" not in body)
    check("no mean_volume left in the gate body",
          "mean_volume" not in body)
    check("the gate body runs ebur128",
          "ebur128=peak=true" in body)
    check("the retired ruler survives only as documented history",
          "volumedetect" in src and "volumedetect" not in body)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print()
if fails:
    print(f"RESULT: FAIL ({len(fails)})")
    for f in fails:
        print(f"  - {f}")
    sys.exit(1)
print("RESULT: PASS")
