# Campaign: Virtual Reflections

**Type:** music album (narrative work — NOT a genre-registry volume lane)
**Status:** discovery
**Owner:** j_kro (creative direction) · music-producer (operational layer)
**Created:** 2026-10-08

---

## Why this is the most valuable music asset in the operation

Every generic AI genre lane fights the same wall: fully-AI work is not
copyrightable, not registrable with a PRO, and rejected by distributors and
sync libraries that screen for AI provenance.

**This album does not fight that wall.** The experiences are j_kro's own. Lyrics
written from real VRChat experience are human-authored. That changes the legal
posture of the whole work:

| Property | Generic AI lane | Virtual Reflections |
|---|---|---|
| US copyright registration | Not registrable | **Registrable** (human-authored lyrics) |
| SOCAN registration | Rejected (fully-AI) | **Accepted** (partially-AI works accepted) |
| Distributor screening | Flagged as 100%-AI | Passes on human authorship |
| Sync / licensing | High scrutiny | Clears on provenance |
| Bandcamp (bans AI) | Banned | Human-authored work — different question |
| Audience | None | **VRChat community — large, underserved, personal-story hungry** |

The album is also the only asset here with a *reason to exist* beyond volume.
That is what makes it sellable.

---

## Operational risk — act on this now

**The album lives on suno.com only. Nothing is local.** That is fragile:

- **60 standard downloads/month** (Premier). Do not spend them casually.
- **Suno changed its ToS twice in 2026** (September changes added download
  metering and model retirement). ToS changes are the norm, not the exception.
- Account loss, model retirement, or a policy change puts unrecoverable work at
  risk. Retired models cannot generate new songs; existing songs stay, but the
  export path is the only durable copy.

**Action: export deliberately through Suno Studio (unlimited downloads), in WAV.**
Never the capped standard download button. One song = one download regardless of
format, and stems ride along with the song's single download — so export the
song AND its stems in one pass.

---

## Sonic identity — MULTI-GENRE (j_kro decision, 2026-10-08)

**The album is multi-genre by design.** This is a decision with real consequences,
not just a style note.

### What it means for the pipeline

The genre registry (`music/genres.yaml`) is the album's **palette**. The album is a
*view over* the registry, not a separate lane — each track selects a registry genre
for its prompt template and visual style. Adding a genre to the registry makes it
available to the album automatically. No album-specific code.

### Why multi-genre is an advantage here

| Lane | Consequence |
|---|---|
| **Sync** | Each track pitches to a *different* brief. A multi-genre album is a sync catalogue, not one submission. This multiplies placements. |
| **Playlists** | Different tracks land on different Spotify/Apple mood playlists. One album, many discovery surfaces. |
| **Audience** | The VRChat community spans every genre. Multi-genre matches the actual crowd. |
| **Catalogue value** | A single-genre album is one asset. A multi-genre album is N assets under one name. |

### The cost — and how it is paid

Multi-genre albums fail when they read as a **compilation** instead of a work. The
usual fix is sonic consistency; that is not available here.

**The coherence device is the narrative.** The through-line is what makes it an
album. If a listener cannot feel the arc, multi-genre becomes a weakness rather
than a strength. This is the single highest-risk element of the record.

### Operational requirements

- **Per-track genre metadata.** Every track carries its registry genre for
  distributor metadata and playlist targeting. Do not tag the album generically.
- **Album-level primary genre.** Streaming platforms want one. Pick the genre with
  the most tracks (or the one that best represents the arc) and use it at album level.
- **Mastering consistency.** Genres differ, loudness must not. Every track masters to
  the same target (-14 LUFS streaming) so the album does not jump in level.
- **Sequencing matters more than usual.** Order carries the arc when the sound cannot.

---

## Narrative arc — intimate → explosive (j_kro, 2026-10-08)

**The range runs from emotional and sentimental to "anime opening style."**

### The arc has a shape worth naming

That range is not arbitrary — it is the **emotional grammar of an anime series
itself**. Quiet character moments, ballads, and endings sit at one end; the
triumphant opening sits at the other. Building an album along that axis means the
record has a native dramatic form rather than an imposed one.

This matters because it solves the multi-genre coherence problem. The coherence
device is **not** sonic consistency (unavailable in a multi-genre album). It is the
**arc**: intimate → explosive. A listener feels the build even as the genre changes
underneath them. That is what makes it an album.

```
  track 1 ─────────────────────────────────────────────► track N
  sentimental / piano / ballad        →        anime opening / J-rock
  60–120 BPM                                    130–180 BPM
  endings territory                             openings territory
  sparse, close, personal                       dense, orchestral, triumphant
```

### Genre palette (multi-genre — registry genres as the vocabulary)

| Position in arc | Registry genre | Territory |
|---|---|---|
| Intimate end | `sentimental-piano` | 60–120 BPM, sparse, close-mic |
| Intimate end | `chill-lounge` | ambient, reflective |
| Middle | `elemental-*` | texture and atmosphere |
| Explosive end | **`anime-opening`** (new) | 130–180 BPM, J-rock/J-pop |
| Explosive end | **`anime-ending`** (new) | 70–120 BPM, emotional ballad |

### ANISONG CRAFT REFERENCE — get this right or it reads as fake

Researched 2026-10-08. The idiom has measurable conventions. A generic "epic rock"
prompt does not produce an anime opening; these do.

| Element | Convention |
|---|---|
| **Tempo** | Openings **130–180 BPM** (J-rock often 170+). Endings **70–120 BPM** |
| **The chord progression** | **IV–V–iii–vi** ("royal road" / 王道進行) — nicknamed *"the anime progression."* A 2023 *Music Theory Spectrum* study found it across a large share of Japan's best-selling songs for decades. Opens on the subdominant, lands on the minor vi |
| **The signature move** | **Final chorus jumps up a key.** This is the genre's defining gesture — omit it and the track reads as generic rock |
| **Structure** | Written to survive a **90-second TV edit** — maximum information density, no wasted bars |
| **Layers** | Dense orchestral + synth; busy drums, melodic bass, piano AND strings together |
| **Vocals** | Japanese vocals. For Suno, write lyrics in **Japanese script** for correct pronunciation |
| **Suno tags** | `anime opening, j-rock, powerful guitars, dynamic arrangement, Japanese vocals, epic build, energetic, dramatic` |

Source genre name: **anison** — anime music with its own production conventions,
fan economy, and chart system.

### Commercial consequence of the explosive end

The anime-adjacent lanes are under-served and pay well:

- **Games sync** — the least crowded major sync buyer. Trailer licences run
  $10,000–100,000+; indie game tracks $500–15,000. Roblox opened self-serve
  licensing in 2026.
- **UGC platforms** — Roblox deals with UMG and Too Lost signal a real market.
- **Anime licensing market** — music segment ≈ $1.22B.
- **Artists with licensing-ready catalogues report sync inquiries at ~4×** the
  rate of those without one. This album, with per-track genre metadata and stems,
  *is* a licensing-ready catalogue.

### Creative direction (music-producer, 2026-10-08 — full ownership assumed)

**Through-line:** *The journey of self-discovery and transformation through virtual worlds — from the quiet moments of connection to the explosive joy of becoming someone new.*

VRChat is a space where identity is fluid, where the shy can be bold, where the isolated can find community. The album traces that arc: starting in the intimate, sentimental space of late-night conversations and quiet worlds, building through moments of wonder and belonging, and culminating in the triumphant, explosive energy of the anime opening — the moment you put on the headset and become who you want to be.

**Arc shape:** intimate → explosive (three acts)

| Act | Tracks | Emotional territory | Sonic palette |
|---|---|---|---|
| **I. Arrival** | 1–3 | Loneliness, curiosity, first connections | sentimental-piano, chill-lounge |
| **II. Belonging** | 4–6 | Wonder, community, identity exploration | elemental-*, trance, jungle |
| **III. Becoming** | 7–9 | Triumph, transformation, explosive joy | anime-opening, anime-ending |

**Track count:** 9 tracks (3 per act) — a proper album length with room for the arc to breathe.

**Album-level primary genre:** sentimental-piano (most tracks, and the emotional core of the work).

**Sequencing principle:** Each act ends on a track that bridges to the next act's energy. Track 3 → 4 is the first lift; track 6 → 7 is the explosion into anime opening territory.

## Track list

| # | Title | Act | Experience it comes from | Sonic direction | Lyrics | Stems | Exported |
|---|---|---|---|---|---|---|---|
| 1 | First Login | I. Arrival | The first time you put on the headset — wonder, disorientation, possibility | sentimental-piano | ☐ | ☐ | ☐ |
| 2 | Quiet Worlds | I. Arrival | Exploring alone at 2am — peaceful spaces, ambient beauty, solitude | chill-lounge | ☐ | ☐ | ☐ |
| 3 | Someone's There | I. Arrival | The first real conversation with a stranger — connection, surprise, warmth | sentimental-piano | ☐ | ☐ | ☐ |
| 4 | Avatar Dreams | II. Belonging | Becoming someone new — identity fluidity, freedom, self-expression | elemental-air | ☐ | ☐ | ☐ |
| 5 | The Club | II. Belonging | VRChat dance communities — energy, belonging, collective joy | trance | ☐ | ☐ | ☐ |
| 6 | Elemental | II. Belonging | Wonder and exploration — the magic of virtual worlds, awe | jungle | ☐ | ☐ | ☐ |
| 7 | Opening Theme | III. Becoming | The explosive moment of becoming — triumph, transformation, anime opening energy | anime-opening | ☐ | ☐ | ☐ |
| 8 | Becoming | III. Becoming | The full realization — who you are in virtual space, confidence, joy | anime-opening | ☐ | ☐ | ☐ |
| 9 | Reflections | III. Becoming | Looking back — the journey, gratitude, the bittersweet beauty of virtual connection | anime-ending | ☐ | ☐ | ☐ |

## Rights posture

- **lyrics authorship:** original, by j_kro — record date + which parts are AI-assisted
- **PRO:** SOCAN (Canadian). Register as a partially-AI-generated work.
- **US Copyright:** register claiming only the human-authored portions; disclose AI parts.
- **AI disclosure:** required at upload on distributors and YouTube.

## Visual identity

- **cover art:** <one strong image, not a template>
- **per-track visuals:** <lyric video / visualizer / none>
- **the VRChat angle:** <avatars, worlds, or in-headset footage — with consent for any
  third party depicted>

## Release plan

- **distributor:** DistroKid (no AI caps, no exclusions, explicit disclosure step)
- **direct:** own site / Gumroad (Bandcamp bans AI — but human-authored is a
  different question; check before assuming)
- **YouTube:** long-form album video (30–60 min) earns 2–3× single tracks
- **sync:** Songtradr / AudioSparx once stems + clearance docs exist
- **community:** VRChat itself — the audience is where the story came from

## Handoff contract

- **j_kro returns:** narrative arc, track list, sonic palette, approval of angle
- **music-producer returns:** export + backup, stems, master, metadata, package
- **editor returns:** review (separate profile — maker never self-reviews)
- **analyst returns:** performance

## Human gates

Creative direction, track list, and publish approval are **j_kro's**. The
operational layer (export, preserve, master, package, distribute) is
music-producer's. A bot never decides what this album is about.
