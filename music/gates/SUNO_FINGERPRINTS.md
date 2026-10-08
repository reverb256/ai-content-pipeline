# Suno lyric-generator fingerprints — gate_lyrics_original detection layer

**Purpose.** `gate_lyrics_original.py` must reject lyrics produced by Suno's
lyric generator ("Write with Suno": the classic "Full Song" model and the ReMi
model). The gate cannot see how a file was produced — it can only execute the
artifact. So detection runs on two classes of signal:

1. **Provenance markers** — text a Suno-assisted file carries that a
   human-original file never does.
2. **Known example outputs** — lines from Suno's own published example lyrics.
   These catch the most likely failure mode: a worker pasting a Suno example
   (or output) into a track and claiming authorship.

This file documents every marker in `SUNO_GEN_MARKERS`
(`music/lyrics/lyrics.py`): what it is, its source, and why it discriminates.
Update this file whenever you add a marker.

**Honest limits.** Marker scanning cannot prove a lyric is human-authored.
A paraphrased Suno lyric with no known line will pass the scan. The
authorship claim in the manifest is the legal artifact; the marker scan is a
tripwire against the common failure (pasted generator output), not proof of
originality. Plagiarism of human work is a separate risk the gate does not
cover — that needs an external originality pass if it becomes a concern.

---

## Provenance markers

| Marker | What it catches | Source |
|---|---|---|
| `provenance:suno` | A provenance header line naming Suno generation (e.g. someone honestly tags a file `# provenance: suno-generated`) | Convention of this pipeline's own header format |
| `write with suno` | UI text pasted from the Suno lyrics modal ("Write with Suno" is the button in Custom mode) | help.suno.com/en/articles/3599681 (What is ReMi?) |
| `remi` | Mentions of Suno's ReMi lyric model (also catches a track *about* ReMi — acceptable false positive; rename the song if that hurts) | help.suno.com/en/articles/3599681; suno.com/blog/v4 |

## Known example outputs — "Umbrellas in Space"

Suno's classic Full Song lyric model, published example ("Umbrellas in Space"
by @liars_track), reproduced in a public Suno walkthrough verified 2026-10-08:
https://note.com/office441/n/n9648c43f7bdf

The full lyric is stored as a regression fixture:
`music/gates/fixtures/suno-generated-umbrellas-in-space.txt`
The gate MUST fail that fixture (12 markers hit).

| Marker | Line in the example |
|---|---|
| `umbrellas in space` | Chorus/V4 hook + title |
| `intergalactic traveler` | V1: "Intergalactic traveler with an earthly feed" |
| `walking on the stars with my umbrella` | V1 line 1 |
| `asteroids may stumble` | V1: "Asteroids may stumble but I'll take the lead" |
| `dancing in zero-g` | Chorus: "Dancing in zero-g light years from yesterday" |
| `milky way confetti` | V3: "Milky Way confetti fills my eyes with delight" |
| `umbrella twirling magic` | V3: "Umbrella twirling magic in the vastness of grey" |
| `aliens wave like friends` | Bridge: "Aliens wave like friends I've always known" |
| `gravity can't catch me` | Bridge: "Gravity can't catch me cause I've always flown" |
| `dance beneath the nebula` | Bridge: "Dance beneath the nebula our tempo so grand" |
| `astral winds can't touch` | V2: "Astral winds can't touch the smirk on my face" |
| `moon beams and dreams` | V4: "Moonbeams and dreams I'm here as your guest" (matches spacing variants) |
| `craft a constellation with a sparkle` | Chorus: "Craft a constellation with a sparkle so bright" |

## What the gate measures (beyond markers)

- Parses the sheet into sections; requires >= 2 content sections.
- Measures unique words; requires >= 25.
- Requires Suno-style structure: section headers must be known metatags
  (`--strict`); untagged body text and placeholder lines are defects.
- Hash-binds the manifest claim to the on-disk file (sha256 in
  `manifest.files`), so editing the lyric after claiming breaks the gate.

## Regression

Run the full PASS/FAIL matrix:

    # must PASS (exit 0)
    python3 music/gates/gate_lyrics_original.py --track-dir music/lyrics/chill-lounge/amber-hour --strict
    python3 music/gates/gate_lyrics_original.py --track-dir music/lyrics/trance/signal-before-dawn --strict
    python3 music/gates/gate_lyrics_original.py --track-dir music/lyrics/activist/what-runs-beneath --strict
    # must FAIL (exit 1)
    python3 music/gates/gate_lyrics_original.py --lyrics-file music/gates/fixtures/suno-generated-umbrellas-in-space.txt
