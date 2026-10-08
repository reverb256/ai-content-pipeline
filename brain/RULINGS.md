# RULINGS.md

> **The most important file in the brain.** Every human correction becomes a
> permanent ruling here. Every bot reads this file before starting work.
> Corrections compound — the system does not repeat the same mistake.

## How To Use

- When j_kro rejects, revises, or corrects an output, the editor (or the
  relevant bot) records the correction here as a ruling.
- A ruling is a specific, observable rule. Not "be better" — "never open with
  a question mark" or "never use unsupported superlatives."
- Rulings are permanent until j_kro explicitly reverses them. Do not remove a
  ruling to make a draft pass.
- Every bot reads this file at the start of every task.

---

## Rulings

### Style & Voice

- (none yet)

### Claims & Evidence

- (none yet)

### Platform & Distribution

- (none yet)

### Process

- (none yet)

### Music

No j_kro music-quality corrections have been recorded yet. The reviewer
panel (music/rubrics/, built 2026-10-08) is calibrated to enforce these
standing corpus anchors — every future j_kro correction to a music
output MUST be recorded here as a ruling, per the corrections-compound
rule.

Standing anchors the panel already enforces (from researched production
convention, full citations in `music/rubrics/*.json`):

- **Genre authenticity is measured, not vibes.** Tempo pockets (trance
  136-142, jungle 160-175, chill-lounge 70-90, sentimental piano 50-90,
  anisong opening 130-180 / ending 70-120 BPM), 32-bar dance structure,
  chiptune's exact 2A03 five-voice constraint. A track outside its
  pocket is out of genre however pleasant it sounds.
- **The anisong final-chorus key change is load-bearing.** An
  anime-opening generation without the key-changed final chorus is OUT
  of genre — reject it (registry note, enforced at weight 3).
- **Clipped masters are never genre-authentic.** max_volume at 0 dBFS is
  a defect in every family.
- **Sync/utility products must loop and leave speech room.** Beds: no
  lead melody under speech, energy steady, seams invisible; loops state
  BPM and key.
- **Protest lyrics need a chantable chorus and a named target.** Vague
  fury with no concrete image fails the genre's function.
- **Masters hit lane loudness targets:** -14 streaming / -16 sync,
  +/-1 dB, measured (volumedetect dialect).

How the panel makes decisions (research basis: PoLL arXiv:2404.18796;
RoPoLL arXiv:2606.30931; Evaluation-Illusion arXiv:2603.11027 — all read
in full 2026-10-08):

- A panel of small judges from disjoint model families beats one large
  judge (PoLL).
- Scores aggregate by GEOMETRIC MEDIAN across the panel (RoPoLL):
  robust to one contaminated judge, tuning-free, 1/2 breakdown point.
- A single judge's reject-signal flag does not fail a track; a MAJORITY
  of the panel must hit it.
- Panel disagreement (overall spread >= 3.0) routes to human triage, not
  an automatic verdict.
- Judges receive MEASURED evidence (ffmpeg + numpy), never filenames or
  vibes — and must mark what they cannot verify.

---

## Proposed Rulings (pending human approval)

When the editor or a bot proposes a new ruling from a performance lesson, it is
listed here. It becomes a permanent ruling ONLY after j_kro approves it.

- (none yet)
