"""test_measure_bpm.py — regression checks for the tempo measurement.

Run: python3 music/rubrics/test_measure_bpm.py

INCIDENT THIS ENCODES — card t_ed609eb0 (2026-10-16)
----------------------------------------------------
`_bpm()` took the argmax lag of the whole-band onset-envelope
autocorrelation and folded 0.5 / 1.0 / 2.0 ONLY from that argmax. On the
elemental-air render (instrumental, 92 BPM anchor, no percussion by genre rule)
the argmax sat at the 60 BPM END of the lag search range, so the anchor never
entered the candidate set: `measure.py` returned bpm 60.1 (conf 0.369),
candidates [60.1, 120.2], and a reviewer reading only `bpm` saw a number that
was not the anchor, with no explanation. The same tool returned 60.1 (conf
0.706) for a commentary sting that is really 120 BPM.

Every instrumental ambient genre in the registry (elemental-air/earth/fire/
water, chill-lounge, sentimental-piano) is percussion-free or near it by its
own template, and the queue cards were accepted on "measured tempo within a few
BPM of the anchor" — a systematically unmeetable criterion.

After the fix, `measure.py` must either surface a candidate within a few BPM of
the requested anchor or report `bpm_pulse: none` / `bpm: null`. It must NEVER
silently report the band-edge value with no note.

Synthetic controls run always. The two real fixtures are the artifacts named in
the card and are skipped with a printed notice when they are absent.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import numpy as np
    import measure as M
except ModuleNotFoundError as e:
    print(f"FATAL: {e}. This test needs numpy. Run it with the interpreter "
          f"that has it (e.g. /usr/bin/python3), not the Hermes-managed "
          f"python3.", file=sys.stderr)
    sys.exit(2)

# getattr: the same test also runs against the pre-fix module as a negative
# control (it has no SR_DEFAULT and no anchor support).
SR = getattr(M, "SR_DEFAULT", 22050)
failures = []

# The fixtures named in card t_ed609eb0. Both are real ACE renders.
AIR = Path("/var/lib/sunolocal/artifacts/"
           "suno-0fa09abe521341629d4f4c59147ae72f.flac")      # anchor 92
STING = Path("/var/lib/sunolocal/artifacts/"
             "suno-0e3fb7b2728747ce816c3e6a760c3c69.flac")    # really 120


def check(name, cond, detail=""):
    if cond:
        print(f"  ok  {name}")
    else:
        print(f"  FAIL {name} {detail}")
        failures.append(name)


def synth_click_train(bpm=92.0, seconds=60):
    n = int(SR * seconds)
    x = np.zeros(n)
    for k in range(int(bpm / 60 * seconds) + 1):
        i = int(k * 60 / bpm * SR)
        if i < n:
            x[i:i + 200] += np.exp(-np.arange(min(200, n - i)) / 20.0)
    return x.astype(np.float32)


# 1. the tool reports the tempo a metronomic artifact actually has
print("[1] synthetic controls")
r = M._bpm(synth_click_train(92.0), SR, anchor_bpm=92)
check("a 92 BPM click train reports 92 BPM",
      r["bpm"] is not None and abs(r["bpm"] - 92.0) <= 3.0, str(r["bpm"]))
check("its pulse is measurable", r["bpm_pulse"] == "measurable")
check("the anchor block says supported",
      r["ac_at_anchor"]["verdict"] == "supported", str(r["ac_at_anchor"]))
check("a candidate sits within 3 BPM of the anchor",
      r["ac_at_anchor"]["candidate_within_3bpm"] is not None)

r = M._bpm(np.zeros(SR * 30, dtype=np.float32), SR)
check("a silent artifact reports no measurable pulse",
      r["bpm"] is None and r["bpm_pulse"] == "none", str(r["bpm"]))

rng = np.random.default_rng(7)
r = M._bpm((rng.standard_normal(SR * 60) * 0.1).astype(np.float32), SR)
check("white noise reports no measurable pulse, not a number",
      r["bpm"] is None and r["bpm_pulse"] == "none", str(r["bpm"]))

# 2. the band-restricted candidate set is the fix
print("[2] band-restricted candidates")
r = M._bpm(synth_click_train(92.0), SR)
check("bpm_bands carries every band",
      set(r["bpm_bands"]) == {n for n, _, _ in M.BPM_BANDS},
      str(sorted(r["bpm_bands"])))
check("every candidate names the band that supports it",
      all(c["best_band"] in r["bpm_bands"] for c in r["bpm_candidates"]))
check("candidates are ranked by prominence",
      all(r["bpm_candidates"][i]["prominence"]
          >= r["bpm_candidates"][i + 1]["prominence"]
          for i in range(len(r["bpm_candidates"]) - 1)))

# 3. the real fixtures named in the card
print("[3] card t_ed609eb0 fixtures")
if not AIR.is_file():
    print(f"  skip the fixtures: {AIR} is absent (run this on the host that "
          f"holds the sunolocal artifacts)")
else:
    r = M._bpm(M._load_mono(AIR), SR, anchor_bpm=92)
    old_value, old_conf = 60.1, 0.369
    ok = ((r["bpm"] is not None and abs(r["bpm"] - 92.0) <= 3.0)
          or r["bpm_pulse"] == "none")
    check("elemental-air: a candidate within 3 BPM of the 92 BPM anchor, "
          "or an explicit no-measurable-pulse",
          ok, f"bpm={r['bpm']} pulse={r['bpm_pulse']}")
    check("elemental-air: the fix replaces the old silent 60.1 headline",
          not (r["bpm"] == old_value and not r["bpm_note"]),
          f"bpm={r['bpm']} conf={r['bpm_confidence']} note={r['bpm_note']}")
    check("elemental-air: the anchor's own ac is reported",
          r["ac_at_anchor"]["ac"] is not None
          and r["ac_at_anchor"]["near"]["ac"] >= M.BPM_PULSE_AC_FLOOR,
          str(r["ac_at_anchor"]))
    check("elemental-air: the anchor verdict is supported",
          r["ac_at_anchor"]["verdict"] == "supported")
    check("elemental-air: the band-edge argmax is still VISIBLE (not hidden)",
          r["bpm_bands"]["full"]["argmax_bpm"] == old_value
          and abs(r["bpm_bands"]["full"]["argmax_ac"] - old_conf) < 0.05,
          str(r["bpm_bands"]["full"]))
    check("elemental-air: the 2-8 kHz band's top peak is the reported tempo",
          r["bpm_bands"]["high"]["argmax_bpm"] == r["bpm"]
          or r["ac_at_anchor"]["near"]["band"] == "high",
          f"high={r['bpm_bands']['high']['argmax_bpm']} bpm={r['bpm']}")
    check("elemental-air: a candidate within 3 BPM of the anchor is in the set",
          r["ac_at_anchor"]["candidate_within_3bpm"] is not None,
          str(r["ac_at_anchor"]["candidate_within_3bpm"]))

if not STING.is_file():
    print(f"  skip the sting fixture: {STING} is absent")
else:
    r = M._bpm(M._load_mono(STING), SR, anchor_bpm=120)
    check("the 120 BPM sting does not headline the 60 BPM half-tempo",
          r["bpm"] is not None and abs(r["bpm"] - 120.0) <= 5.0,
          str(r["bpm"]))
    edge = [c for c in r["bpm_candidates"] if c["edge"]]
    check("the band-edge half-tempo stays in the candidate list, flagged",
          bool(edge) and edge[0]["bpm"] == 60.1,
          str([c["bpm"] for c in edge]))
    check("its confidence is read at its OWN lag (0.55, not the old 0.448)",
          bool(edge) and edge[0]["ac"] > 0.70 and r["bpm_confidence"] > 0.50,
          f"edge={edge[0]['ac'] if edge else None} "
          f"bpm_conf={r['bpm_confidence']}")
    check("the folding behaviour is pinned: the 2x candidate is present",
          any(abs(c["bpm"] - 120.0) <= 5.0 for c in r["bpm_candidates"]))
    check("the anchor block says supported",
          r["ac_at_anchor"]["verdict"] == "supported")

print()
if failures:
    print(f"{len(failures)} FAILURES")
    sys.exit(1)
print("ALL CHECKS PASSED")
