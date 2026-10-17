#!/usr/bin/env python3
"""Asset-pack key regression checks. Run: python3 music/tests/test_pack_key.py

Standalone (no pytest), the same requirement the generator itself has: it runs
anywhere python3 + numpy + scipy do.

WHY THIS FILE EXISTS (card t_4906bc6e, card t_f65b0f4c)
-------------------------------------------------------
`estimate_key()` opened with a short-input early return that answered with a
hard-coded key it had not analysed:

    if len(x) < 2048:
        return "C minor"

`music/assets/pack.py` then wrote that value into the manifest `key`, into
`metadata.key` (the object every pack gate reads), into every loop record, into
loop_points.json, into the README and into the clearance document — a confident
claim about audio nobody measured, in the record this pack's licence rests on.
Card t_f65b0f4c fixed the same shape in the planner's plan.

Measured on nexus 2026-10-16 (numpy 2.5.3 / scipy, /usr/bin/python3) the pre-fix
function had TWO defects in that one branch:

  * under 2048 samples — the early return fired and returned "C minor" for a
    clip it never analysed;
  * 2048..4095 samples — the guard did NOT fire, `sps.stft` shrank nperseg to
    the input length, and the call raised
    `ValueError: noverlap must be less than nperseg`.

The analyser's usable length is its own STFT window (KEY_NPERSEG, 4096
samples). Below it there is no estimate to make, so `estimate_key` returns None
and the generator records the explicit "unknown" instead of a key.

NEGATIVE CONTROL (the FAILURE -> TEST rule). This file is RED against the pre-fix
code: sections 1 and 2 fail on the early return (the estimator answers
"C minor"/raises where the test requires None), which was measured by restoring
the old branch in a scratch copy of the tree.
"""

import importlib
import json
import pathlib
import struct
import subprocess
import sys
import tempfile
import wave

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
PACK = REPO / "music" / "assets" / "pack.py"

sys.path.insert(0, str(REPO))
pack = importlib.import_module("music.assets.pack")

fails: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}"
          + (f"  [{detail}]" if detail and not ok else ""))
    if not ok:
        fails.append(name)


def tone(n: int, sr: int, freqs=(220.0, 277.18, 329.63)) -> list[float]:
    """A real, non-silent signal: a triad summed, in [-1, 1]."""
    import numpy as np

    t = np.arange(n) / sr
    x = np.zeros(n)
    for f in freqs:
        x += np.sin(2 * np.pi * f * t)
    return (x / len(freqs) * 0.9).tolist()


def write_master(path: pathlib.Path, n: int, sr: int) -> pathlib.Path:
    """Write a 16-bit mono WAV with the stdlib, so the fixture does not depend
    on the module under test (nor on ffmpeg being on PATH)."""
    samples = tone(n, sr)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(b"".join(
            struct.pack("<h", max(-32767, min(32767, int(round(s * 32767)))))
            for s in samples))
    return path


def run_pack(master: pathlib.Path, out: pathlib.Path, *extra: str):
    cmd = [sys.executable, str(PACK), str(master), "--out", str(out),
           "--genre", "chill-lounge", "--bpm", "120", "--no-sfx",
           "--pack-name", out.name, "--title", "Key Contract Pack", *extra]
    return subprocess.run(cmd, capture_output=True, text=True)


VALID = set(pack.NOTE_NAMES)
# The analyser's window: read from the module under test, but tolerantly, so the
# NEGATIVE CONTROL run (this file against the pre-fix code) reports every failed
# section instead of dying on the missing constant.
WINDOW = getattr(pack, "KEY_NPERSEG", 4096)


def is_key(value) -> bool:
    return (isinstance(value, str) and " " in value
            and value.split(" ", 1)[0] in VALID
            and value.split(" ", 1)[1] in ("major", "minor"))


# ---------------------------------------------------------------------------
print("1. estimate_key has no key to report below its own window")

check("the module declares the analyser's window (KEY_NPERSEG)",
      hasattr(pack, "KEY_NPERSEG"), "no KEY_NPERSEG: the floor is unnamed")

# REGRESSION (2026-10-16, card t_4906bc6e). Every clip under the analyser's
# window must yield NO key. The pre-fix code answered "C minor" below 2048
# samples and raised ValueError between 2048 and 4095.
for n in (64, 1024, 2047, 2048, 2049, 4095):
    x = tone(n, 44100)
    try:
        got = pack.estimate_key(x, 44100)
        err = ""
    except Exception as exc:  # noqa: BLE001
        got, err = "raised", f"{type(exc).__name__}: {exc}"
    check(f"{n} samples yields no key claim (got {got!r})",
          got is None, err or f"returned {got!r}, expected None")

# ...and it must still measure a real clip: the fix is a floor, not a mute.
x = tone(WINDOW, 44100)
got = pack.estimate_key(x, 44100)
check(f"a clip at the window ({WINDOW} samples) is measured",
      is_key(got), f"returned {got!r}")

# ---------------------------------------------------------------------------
print()
print("2. the manifest records an explicit unknown, never a fabricated key")

tmp = pathlib.Path(tempfile.mkdtemp(prefix="pack-key-unknown-"))
# 4000 samples at 2000 Hz = 2.0 s: LONG enough for a bar-aligned loop at
# 120 BPM (MIN_LOOP_SPAN_S is 2.0 s) and SHORT of the 4096-sample analyser
# window. That is the only source shape reachable by the CLI that can hold a
# loop and still have nothing to measure.
short = write_master(tmp / "short_master.wav", 4000, 2000)
out_short = tmp / "pack-key-unknown"
r = run_pack(short, out_short)
stdout = r.stdout + r.stderr
check("the run reports key=unknown", "key=unknown" in stdout,
      "\n".join(ln for ln in stdout.splitlines() if "key=" in ln))
check("the run never claims C minor", "C minor" not in stdout)
# Measured: a 2.0 s source cannot supply the 5 loops the acceptance block
# requires, so the generator refuses AFTER writing the manifest — the manifest
# is the artifact under test here, and this pins the refusal honestly.
check("the run refuses a 2 s source (>=5 loops unmet), rc 1", r.returncode == 1,
      f"rc={r.returncode}: {stdout.strip().splitlines()[-1] if stdout.strip() else ''}")

manifest_path = out_short / "manifest.json"
check("the manifest was written before the refusal", manifest_path.is_file())
if manifest_path.is_file():
    m = json.loads(manifest_path.read_text())
    check("manifest key is the explicit unknown", m.get("key") == "unknown",
          repr(m.get("key")))
    check("metadata.key agrees with the manifest key",
          m["metadata"].get("key") == "unknown", repr(m["metadata"].get("key")))
    check("the manifest holds no fabricated key anywhere",
          "C minor" not in manifest_path.read_text())
    loops = m.get("loops") or []
    check("the pack holds a loop to label", len(loops) >= 1, str(len(loops)))
    check("every loop record carries the same label",
          all(lp.get("key") == "unknown" for lp in loops),
          repr([lp.get("key") for lp in loops]))
    check("every loop file name says key-unknown",
          all("key-unknown" in lp.get("path", "") for lp in loops),
          repr([lp.get("path") for lp in loops]))

    lp_path = out_short / "loop_points.json"
    check("loop_points.json was written", lp_path.is_file())
    if lp_path.is_file():
        index = json.loads(lp_path.read_text())
        entries = index.get("loops") or {}
        check("loop_points entries agree",
              bool(entries) and all(e.get("key") == "unknown"
                                    for e in entries.values()),
              repr([e.get("key") for e in entries.values()]))

    # The README and the clearance document are what a buyer reads.
    readme = (out_short / "README.md")
    check("the README states the unknown, not a key",
          readme.is_file() and "**Key:** unknown" in readme.read_text(),
          readme.read_text().splitlines()[-1] if readme.is_file() else "absent")
    pdf = out_short / "clearance_doc.pdf"
    pdf_text = pdf.read_bytes().decode("latin-1") if pdf.is_file() else ""
    check("the clearance document states 'Key unknown'", "Key unknown" in pdf_text)
    check("the clearance document claims no key of its own", "C minor" not in pdf_text)

# ---------------------------------------------------------------------------
print()
print("3. --key still wins when it is passed explicitly")

out_stated = tmp / "pack-key-stated"
r2 = run_pack(short, out_stated, "--key", "D Phrygian")
stdout2 = r2.stdout + r2.stderr
check("the run reports the stated key as stated",
      "key=D Phrygian (stated)" in stdout2,
      "\n".join(ln for ln in stdout2.splitlines() if "key=" in ln))
m2p = out_stated / "manifest.json"
check("the stated key reaches the manifest", m2p.is_file())
if m2p.is_file():
    m2 = json.loads(m2p.read_text())
    check("manifest key is the stated key", m2.get("key") == "D Phrygian",
          repr(m2.get("key")))
    check("metadata.key is the stated key",
          m2["metadata"].get("key") == "D Phrygian", repr(m2["metadata"].get("key")))
    loops2 = m2.get("loops") or []
    check("loop records carry the stated key",
          all(lp.get("key") == "D Phrygian" for lp in loops2),
          repr([lp.get("key") for lp in loops2]))
    check("loop file names carry the stated key",
          all("key-DPhrygian" in lp.get("path", "") for lp in loops2),
          repr([lp.get("path") for lp in loops2]))
    lp2 = out_stated / "loop_points.json"
    if lp2.is_file():
        entries2 = (json.loads(lp2.read_text()).get("loops") or {})
        check("loop_points entries carry the stated key",
              all(e.get("key") == "D Phrygian" for e in entries2.values()),
              repr([e.get("key") for e in entries2.values()]))

# ---------------------------------------------------------------------------
print()
print("4. a source the analyser CAN measure still gets its measured key")

# 2.0 s at 44100 Hz = 88200 samples, well above the window. This is the
# negative control for section 2's fix: it fails if the floor was implemented
# by making the analyser always answer nothing. 44.1 kHz because that is the
# rate the lane's own masters use (and pack.py's hpss() median-filter kernel is
# odd there; measured 2026-10-16, it is even at other rates such as 22050 Hz,
# which crashes the stem stage — filed as its own card, not this one).
measurable = write_master(tmp / "measurable_master.wav", 88200, 44100)
out_meas = tmp / "pack-key-measured"
r3 = run_pack(measurable, out_meas)
stdout3 = r3.stdout + r3.stderr
check("the run reports an estimated key", "(estimated)" in stdout3,
      "\n".join(ln for ln in stdout3.splitlines() if "key=" in ln))
check("the run does not report the unknown for a measurable source",
      "key=unknown" not in stdout3)
m3p = out_meas / "manifest.json"
check("the measurable run wrote a manifest", m3p.is_file())
if m3p.is_file():
    m3 = json.loads(m3p.read_text())
    x_meas, sr_meas = pack.load_wav(str(measurable))
    want = pack.estimate_key(x_meas, sr_meas)
    check(f"the manifest carries the analyser's own value ({want})",
          m3.get("key") == want, repr(m3.get("key")))
    check("the manifest key is a real key shape", is_key(m3.get("key")),
          repr(m3.get("key")))
    check("metadata.key agrees with the manifest key",
          m3["metadata"].get("key") == m3.get("key"))

# ---------------------------------------------------------------------------
print()
if fails:
    print(f"RESULT: FAIL ({len(fails)} check(s) misbehaved)")
    for f in fails:
        print(f"  - {f}")
    sys.exit(1)
print("RESULT: PASS (the pack's key is measured or explicit, and --key wins)")
