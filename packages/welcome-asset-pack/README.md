# Asset Pack: welcome-asset-pack

**Title:** Welcome Loop Pack
**Artist:** Reverb256
**Genre:** chill-lounge
**Mood:** reflective
**BPM:** 184.57
**Key:** C major
**Sample rate:** 44100 Hz
**Bit depth:** 16-bit
**Source track:** /home/j_kro/ai-content-pipeline/packages/welcome-asset-pack/source/welcome-reconstructed.wav
**Created:** 2026-10-16T19:51:24.452879+00:00

## Contents

| Type   | Count | Description |
|--------|-------|-------------|
| Loops  | 5  | Bar-aligned seamless loops (measured seam, see below). |
| Stems  | 12  | Time-aligned stems of the source track. |
| One-shots | 7  | Isolated hits: kick, snare, hat, riser, impact. |
| SFX    | 6  | Elemental: fire, water, earth, air. |

## File naming

type_index_attribute.bpm.bpm_key.key.wav

## Loops

Every loop is bar-aligned at 184.57 BPM and is at least 2 s long, so it is
musical in a game engine. Each loop's seam is built by crossfading the loop's
tail into the source material that immediately precedes the loop start, so the
wrap is continuous (no click, no fade to silence). `loop_points.json` carries
one entry per loop; `seam_method` in `manifest.json` records how each seam was
built.

Measure it — do not trust this file:

```
python3 music/gates/gate_loop_points.py --pack-dir <this pack>
```

## Stems

Stems are derived via Harmonic/Percussive Source Separation (HPSS) using a
scipy STFT + median-filter pipeline. When the campaign provides Studio stems,
those take priority over derived stems.

## Gate the pack before publishing

```
python3 music/gates/gate_sync_ready.py --package-dir <this pack> --lane game-assets
python3 music/gates/gate_loop_points.py --pack-dir <this pack>
```

## Documents in this pack

- `clearance_doc.pdf` — who cleared this audio for resale.
- `ai_disclosure.txt` — the AI role, for the marketplace AI tag
  (`brain/runbooks/music-game-assets.md`: itch.io requires `AI-Generated`).
- `LICENCE.txt` — Perpetual Music Asset Licence (v1.0) (music/licences/perpetual_game_asset_v1.txt), shipped byte-for-byte.
  sha256 e1dd51ae29489c15b4321b250965dc9e81110882de394ec257389a153b5ebfbd.
