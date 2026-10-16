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
| `gate_sync_ready.py` | Two shapes (card t_5ed495eb). The lane set comes from `music/lanes.yaml` — every lane whose `gate:` is `gate_sync_ready` (today: `sync`, `sync-documentary`, `direct-license`, `game-assets`) is runnable by name, and each lane's `requires:` tokens are mapped to a check (an unmapped token fails the run — card t_d9983bb9). `--mode track` (default for `sync`/`sync-documentary`/`direct-license`): ffprobes stems + master + instrumental; instrumental must differ from the master; manifest metadata; real PDF clearance doc; AI disclosure; `license_tiers` when the lane requires it. `--mode pack` (default for `--lane game-assets`): ffprobes EVERY audio file, `pack_manifest` counts vs the files on disk, `metadata` + a stated sample rate checked against each file, stems mutually time-aligned, per-loop loop points (span >= 2 s), every loop's seam measured, clearance + disclosure + licence | 0 / 1 / 2 |
| `gate_release_ready.py` | ffprobes the master, PIL-verifies the artwork, ISO 3901 ISRC syntax, manifest metadata + ai_disclosure | 0 / 1 / 2 |
| `gate_loop_points.py` | Renders the loop windows and measures junction curvature (second difference): a click at the wrap spikes the ratio. Seamless <= 3.0x. Single mode: `--master` + `--loop-points`. Pack mode: `--pack-dir <pack>` verifies EVERY loop in the pack's `loop_points.json`, one ratio per loop | 0 / 1 / 2 |
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
it is reproducible from a clean checkout. The asset-pack
fixtures include one pack built by the REAL generator
(`music/assets/pack.py`, which needs numpy + scipy) — the
suite refuses to run (exit 2) when a fixture builder fails
or those imports are missing, so a check can never pass
against a fixture that was never written.

Individual gates:

```
python3 music/gates/gate_quota.py
python3 music/gates/gate_stems_present.py \
    --master master.wav --stems-dir stems/
python3 music/gates/gate_loudness.py \
    --master master.wav --target streaming
python3 music/gates/gate_sync_ready.py \
    --package-dir <pkg> --lane sync
python3 music/gates/gate_sync_ready.py \
    --package-dir <pkg> --lane sync-documentary   # any lane whose
                                                  # gate: is this gate
python3 music/gates/gate_sync_ready.py \
    --package-dir <pack> --lane game-assets    # pack mode
python3 music/gates/gate_loop_points.py \
    --master master.wav --loop-points loop_points.json
python3 music/gates/gate_loop_points.py \
    --pack-dir <pack>                          # every loop in the pack
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
- `check_gate_suite.sh` — the full acceptance matrix
  (this directory's contract). Since card t_5ed495eb it
  also covers the asset-pack lane: a generator-built pack
  passes both gates, and a pack that breaks any one
  requirement (loop span, seam, counts, metadata sample
  rate, loop points, clearance) fails.
- `../scripts/check_gate_lane_surface.py` — the gate↔lane
  contract (card t_d9983bb9, incident: `sync-documentary`
  declared `gate_sync_ready` in `music/lanes.yaml` while
  the gate's argparse rejected the lane name and exited
  **2**, which a stage reads as a gate FAILURE). It asserts
  that every lane's declared gate exists, that every gate
  accepts by name every lane that declares it (exit 0/1,
  never 2), that each lane's `requires:` tokens each map to
  a check the gate can evidence, that the `visual` stage's
  gate is resolved from the genre's lanes rather than named
  in `music/stages.yaml`, and — with a real ffmpeg-built
  fixture — that `--lane sync-documentary` PASSES a good
  sync package and fails an empty one byte-identically to
  `--lane sync`.

## Reading the lane registry from a gate

`_lane_registry.py` reads `music/lanes.yaml` with the
standard library only. It exists because every stage prompt
calls a gate as `python3 music/gates/<gate>.py`, and bare
`python3` in a worker shell is the Hermes bundled
interpreter, which has **no PyYAML** (measured 2026-10-16) —
a gate that needs PyYAML would die with `ModuleNotFoundError`
in exactly the shell a worker uses. `check_gate_lane_surface.py`
parses the same file with PyYAML through `music/registry.py`
and fails when the two readings disagree, so a reformat the
scanner cannot follow is caught by a check rather than by a
gate.

