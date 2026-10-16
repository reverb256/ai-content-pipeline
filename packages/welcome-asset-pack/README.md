# Asset Pack: welcome-asset-pack

**Source track:** /home/j_kro/Projects/ai-content-pipeline/campaigns/virtual-reflections/masters/welcome.wav
**BPM:** 184.57
**Key:** C major
**Sample rate:** 44100 Hz
**Bit depth:** 16-bit
**Genre:** chill-lounge
**Created:** 2026-10-14T07:44:31.968698+00:00

## Contents

| Type   | Count | Description |
|--------|-------|-------------|
| Loops  | 5  | Seamless, bar-aligned, click-free (measured seam discontinuity). |
| Stems  | 12  | Time-aligned, 12-channel stem pack. |
| One-shots | 8  | Isolated hits: kick, snare, hat, riser, impact. |
| SFX    | 6  | Elemental: fire, water, earth, air. |

## File naming

type_index_attribute.bpm.bpm_key.key.wav

## Loop click-free verification (measured)

Every loop's seam discontinuity is measured as the sample delta at the wrap
point, reported in dBFS. A value below -60 dBFS indicates a click that is
inaudible under normal monitoring. The manifest JSON records each loop's
measured `seam_discontinuity_db`.

## Stems

Stems are derived via Harmonic/Percussive Source Separation (HPSS) using a
scipy STFT + median-filter pipeline. When the campaign provides 12 Studio
stems, those take priority over derived stems.

## Licence

see music/licences/perpetual_game_asset_v1.txt — multi-tier (personal / commercial / exclusive).
