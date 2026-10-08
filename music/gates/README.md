# music/gates — the executable gate suite

Every gate EXERCISES the artifact it guards. A gate that
greps a file for a feature name is a defect — it passes
while the artifact is broken. These gates parse, measure,
and render (ffprobe / ffmpeg volumedetect / PCM analysis).

Architecture: `brain/playbooks/music-lane-architecture.md`
§5 (gates) and §3 (lane requirements).

## The gates

| Gate | What it executes | Pass / Fail |
|---|---|---|
| `gate_quota.py` | Reads `music/quota-ledger.json`; blocks at `hard_stop_at` (58/60), warns at `warn_at` (55) | 0 / 1 / 2 |
| `gate_lyrics_original.py` | Parses the lyric sheet, measures sections + unique words, scans Suno-generator markers, hash-binds the manifest claim (sha256) | 0 / 1 / 2 |
| `gate_stems_present.py` | ffprobes every stem: >= 4 stems, non-zero bytes, durations within +/-0.5 s of the master | 0 / 1 / 2 |
| `gate_loudness.py` | Runs `ffmpeg -af volumedetect`; -14 LUFS streaming / -16 sync, +/-1 dB. Fails honestly on a loud master | 0 / 1 / 2 |
| `gate_quality.py` | Verifies the review record: verdict present, reviewer model DIFFERENT from producer model, sha256-bound to the master | 0 / 1 / 2 |
| `gate_sync_ready.py` | ffprobes stems + master + instrumental; instrumental must differ from the master; manifest metadata; real PDF clearance doc; AI disclosure | 0 / 1 / 2 |
| `gate_release_ready.py` | ffprobes the master, PIL-verifies the artwork, ISO 3901 ISRC syntax, manifest metadata + ai_disclosure | 0 / 1 / 2 |
| `gate_loop_points.py` | Renders the loop windows and measures junction curvature (second difference): a click at the wrap spikes the ratio. Seamless <= 3.0x | 0 / 1 / 2 |
| `gate_youtube_authentic.py` | Samples + hashes frames: shot diversity (not a raw dump), Jaccard similarity vs prior uploads, disclosure | 0 / 1 / 2 |
| `gate_human_approval.py` | j_kro's gate — never auto-passes. Requires a dated, sha256-bound approval record naming a human approver | 0 / 1 / 2 |

Exit codes: 0 = PASS, 1 = FAIL (human-readable reasons on
stderr), 2 = usage error.

## Running the suite

```
# full acceptance matrix: every gate PASS on a good
# artifact and FAIL on a deliberately broken one
bash music/gates/check_gate_suite.sh
```

The suite builds its own fixtures (synthesized audio via
ffmpeg, rendered visuals via ffmpeg) in
`$GATE_SCRATCH` (default `/tmp/music-gate-fixtures`), so
it is reproducible from a clean checkout.

Individual gates:

```
python3 music/gates/gate_quota.py
python3 music/gates/gate_stems_present.py \
    --master master.wav --stems-dir stems/
python3 music/gates/gate_loudness.py \
    --master master.wav --target streaming
python3 music/gates/gate_sync_ready.py \
    --package-dir <pkg> --lane sync
python3 music/gates/gate_loop_points.py \
    --master master.wav --loop-points loop_points.json
...
```

## Honest limits

- `gate_loudness` measures volumedetect's mean_volume
  (RMS dB), per the architecture spec. That is not a
  gated BS.1770 LUFS reading — mastering-grade LUFS
  needs ebur128 / pyloudnorm (see FinalPass,
  sacrifunk-loudness patterns). The gate measures what
  the spec pins.
- `gate_lyrics_original` marker scanning cannot prove a
  lyric is human-authored; it is a tripwire against
  pasted Suno output. The authorship claim in the
  manifest is the legal artifact. See
  `SUNO_FINGERPRINTS.md`.
- `gate_loop_points` curvature ratio is calibrated on
  synthetic loops (clean 5 s-period = 1.6x, half-period
  phase slip = 6.0x). Real-world material may need a
  different `--click-ratio-max`.

## Regression history

- `check_gate_lyrics_original.sh` — the lyrics gate's
  own matrix (3 genre PASS, Suno fixture FAIL, tamper
  detection, unclaimed-sheet rejection).
- `check_gate_suite.sh` — the full 10-gate acceptance
  matrix (this directory's contract).
