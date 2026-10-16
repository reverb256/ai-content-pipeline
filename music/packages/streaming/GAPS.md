# Virtual Reflections — streaming package gaps

Conclusion: four of five packages are complete except for cover art. Cover art
is j_kro's creative gate. Do not generate it here. The loudness ruler conflict
this file opened is resolved (card `t_9546841b`: `gate_loudness` measures EBU
R128 integrated loudness, not `volumedetect` RMS). Under that ruler two masters
still fail on a real loudness overshoot — see gap 2, which is now a
mastering-accuracy finding rather than a ruler artifact.

Campaign: `campaigns/virtual-reflections/` · generated 2026-10-16 · task
`t_93852e1f`.

## Per-track state

| slug | title | tr# | `gate_release_ready` | `gate_loudness` (ebur128, current ruler) | mean_volume (retired ruler) | ISRC | artwork |
|---|---|---|---|---|---|---|---|
| welcome | Welcome | 1 | FAIL — artwork only | PASS −13.6 LUFS (+0.4) | −15.50 dB → FAIL | CARVB2652921 | missing |
| these-worlds-are-made-of-light | These Worlds Are Made of Light | 2 | FAIL — artwork only | **FAIL −12.9 LUFS (+1.1)** | −14.10 dB → PASS | CARVB2652922 | missing |
| erasing-the-distance | Erasing the Distance | 3 | **PASS** | PASS −13.1 LUFS (+0.9) | −14.90 dB → PASS | CARVB2652923 | present, 3000×3000 RGB |
| world-of-blue | World of Blue | 5 | FAIL — artwork only | PASS −13.3 LUFS (+0.7) | −15.70 dB → FAIL | CARVB2652925 | missing |
| sincerely | Sincerely | 6 | FAIL — artwork only | **FAIL −12.8 LUFS (+1.2)** | −15.40 dB → FAIL | CARVB2652926 | missing |

Every package holds `master.wav`, `lyrics.txt`, `ai_disclosure.txt`,
`manifest.json` and `prep-sheet.md`. `erasing-the-distance` also holds
`artwork.jpg`. Each failure above names one reason and no other: the four
non-artwork packages pass every other artifact check.

## Gap 1 — cover art for 4 of 5 tracks (j_kro creative gate)

Decision needed: who makes four covers, or does the album ship with the one
cover that exists. The card forbids generating, downloading or fabricating art,
so no package carries a placeholder. Each manifest records
`"artwork": "pending — j_kro creative gate"`.

Evidence that this is a real gate, not a formality: the only artwork on disk
is `erasing-the-distance/artwork.jpg` — 3000×3000, RGB, JPEG, 848,027 bytes.
The other four tracks have no image anywhere under the campaign. A raw Suno
lyric-video frame does not qualify (watermark + baked-in lyric text, and the
source video is portrait 824×1464).

## Gap 2 — ruler RESOLVED, two masters still hot (open, j_kro gate)

Resolution: card `t_9546841b` changed the gate's ruler. `gate_loudness` now
measures EBU R128 integrated loudness (`ffmpeg -af ebur128=peak=true`), target
−14 LUFS ±1 — the unit the lane spec, `MANIFEST.json` and the `loudnorm`
normalization all use. The `volumedetect` mean_volume ruler is retired: it is a
plain RMS mean, and on these masters it disagreed with LUFS by 1.2 to 2.6 dB.

Before and after, same five masters, same command:

| slug | before (mean_volume, −14 ±1) | after (ebur128 integrated, −14 ±1) |
|---|---|---|
| welcome | FAIL −15.50 dB | **PASS** −13.6 LUFS (+0.4) |
| these-worlds-are-made-of-light | PASS −14.10 dB | **FAIL** −12.9 LUFS (+1.1) |
| erasing-the-distance | PASS −14.90 dB | **PASS** −13.1 LUFS (+0.9) |
| world-of-blue | FAIL −15.70 dB | **PASS** −13.3 LUFS (+0.7) |
| sincerely | FAIL −15.40 dB | **FAIL** −12.8 LUFS (+1.2) |

The swap is not a rubber stamp: it flips three verdicts and two masters fail
under either ruler. The two remaining failures are a real measurement of the
masters — `these-worlds-are-made-of-light` +1.1 LU and `sincerely` +1.2 LU over
the −14 LUFS target, outside the ±1 window.

What the campaign record shows, not an inference: all six tracks carry
`master_normalization: loudnorm=I=-14:TP=-1.0:LRA=11`. Only
`this-small-forever` carries a `master_normalization_detail` (a two-pass
measured run, `measured_I=-12.59`, `offset=-1.41`) — and it is the one master
that landed on −14.0 LUFS exactly. For calibration, single-pass
`loudnorm=I=-16` on a 440 Hz steady tone lands on −16.0 LUFS exactly, so the
overshoot is content-dependent rather than a fixed offset.

Open: card `t_c10a8513` (blocked — j_kro's decision). Widen the streaming
window, or re-normalize those two masters two-pass. Do not modify campaign
masters before that decision lands.

## Gap 3 — track 4 is out of scope

`this-small-forever` has no exported master. `MANIFEST.json` records
`exported: false` and the failure reason on the Suno side. Its lyrics exist on
disk. A sibling card owns the export. Its ISRC is reserved as
`CARVB2652924` by the scheme below, but no package exists yet.

## ISRC scheme

Twelve characters, `CARVB26` + `5292` + album track number. The locked
precedent `CARVB2652923` (Erasing the Distance, track 3) is reproduced
unchanged; track 4 reserves `CARVB2652924`.

Validity comes from IFPI International ISRC Agency Bulletin 2015/01 (rev 3,
aligned to ISO 3901:2019): 12 characters, element 1 (pos 1-2) A-Z, element 2
(3-5) A-Z/0-9, element 3 (6-7) 0-9, element 4 (8-12) 0-9.

**ISO 3901 defines no check digit.** A previous revision of
`music/gates/gate_release_ready.py`'s docstring and of the
`music-distribution-automation` skill's `references/distrokid-prep-tooling.md`
claimed one and gave an algorithm for it. Following that claim produces a
13-character code, which the Bulletin rules invalid. This card corrected the
gate docstring. The skill reference still carries the claim — it lives in
another profile's skill tree, which this card must not edit.

Self-assigned ISRCs are not authoritative. A real ISRC comes from a registrant
code issued by an ISRC agency. Replace these with the DistroKid-assigned codes
after a live release if DistroKid mints them.

## Script fixes made in this card

1. `music/scripts/distrokid_prep.py` read only a `lyrics` key for the
   Instrumental field. The campaign manifests carry
   `lyrics_authored`/`lyrics_author`, so every sheet said **Instrumental = Yes**
   for a vocal track — a value a human copies into the live form. Now the
   manifest's explicit `instrumental` flag wins, then the builder schema, then
   the campaign schema.
2. The same sheet hardcoded songwriter type `Music and lyrics`, so Welcome
   (spoken word, `songwriter_type: "Music"`) was wrong. The sheet now reads the
   manifest.
3. The sheet's sub-genre line ignored the manifest's declared sub-genre and
   printed blank. It now resolves `Chill Out` to DistroKid value `36`.
4. The sheet's AI clause read "(instrumental AI-rendered)". These tracks are
   not instrumentals. Now "(music AI-rendered)".
5. `music/gates/gate_release_ready.py` docstring corrected for the ISRC check
   digit (comment only — no behaviour change; the code already matched the
   Bulletin).

Regression check: `PYTHONPATH=. .venv/bin/python
music/tests/test_distrokid_prep.py` — 28 checks, all PASS. It asserts the
Instrumental resolution, the sheet values, and the Bulletin's ISRC rules over
the five packages. The loudness ruler now has its own check:
`music/tests/test_gate_loudness.py` (card `t_9546841b`) builds one LUFS-true and
one RMS-true fixture and fails if the gate reverts to the retired ruler.

## Unverified

- DistroKid accepts these ISRCs. No upload ran — submission is human-gated.
- Apple Music lyrics-form rules (no "Chorus 2x", no numerals 1-10) were not
  checked against the lyrics files. `welcome/lyrics.txt` is empty by design.
- The loudness follow-up card `t_9546841b` has now run: `gate_loudness`
  measures EBU R128 integrated loudness (see gap 2). What stays open is the
  two-hot-masters decision on card `t_c10a8513` (blocked, j_kro gate).
