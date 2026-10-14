Write the `anime-opening` and `anime-ending` genre prompt templates.

These two genres are required by the Virtual Reflections album
(campaigns/virtual-reflections/CAMPAIGN.md) — the album's explosive end is anime
opening style. They are NOT in the original 12-genre batch, so they are yours to add.

## The idiom is measurable — generic "epic rock" fails it

Researched 2026-10-08. An anime opening is a specific production idiom with hard
conventions. A prompt that says "epic rock" produces generic rock, not an anison.
These are the conventions the template MUST encode:

| Element | Convention |
|---|---|
| **Tempo** | Openings **130–180 BPM** (J-rock often 170+). Endings **70–120 BPM** |
| **Chord progression** | **IV–V–iii–vi** — the "royal road" (王道進行), nicknamed *"the anime progression."* A 2023 Music Theory Spectrum study found it across a large share of Japan's best-selling songs for decades. Opens on the subdominant, lands on the minor vi |
| **THE SIGNATURE MOVE** | **Final chorus jumps up a key.** This is the genre's defining gesture. Omit it and the track reads as generic rock — this is the single most important line in the template |
| **Structure** | Written to survive a **90-second TV edit**. Maximum information density, no wasted bars |
| **Layers** | Dense orchestral + synth. Busy drums, melodic bass, piano AND strings together |
| **Vocals** | Japanese. For Suno, lyrics must be in **Japanese script** for correct pronunciation |

## Deliverables

1. `music/prompts/anime-opening.md` — the four required sections (style field ≤1000
   chars, lyrics guidance with [metatags], More Options, genre craft notes).
   The craft notes MUST include the key-change final chorus and the royal road.
2. `music/prompts/anime-ending.md` — same shape, 70–120 BPM, emotional ballad territory.
3. Register both in `music/genres.yaml` (coordinate with the registry card — if
   genres.yaml does not exist yet, write the blocks and note the dependency).
4. `music/visuals/anime-opening.md` and `music/visuals/anime-ending.md` — visual style.

## Quality bar

A Suno generation from each template must be recognisably anison — a listener who
knows the genre should not hesitate. Cite the conventions above in the template so
the reasoning survives.

## Context (read before starting)

Repo: /home/j_kro/Projects/ai-content-pipeline
Album campaign: campaigns/virtual-reflections/CAMPAIGN.md (the anisong craft table)
Architecture: brain/playbooks/music-lane-architecture.md
Platform research: brain/research/music-monetization-2026.md

## Hard constraints
- GENRE-GENERIC: genres are DATA (music/genres.yaml), never code.
- Suno Premier: 60 STANDARD downloads/month; Studio is UNLIMITED. Export via Studio.
- Gates must EXECUTE the artifact. Grep-gates are defects.
- No stubs. No TODOs. Complete work verified by real execution.

## Report back
Exact commands, real output, file paths. A claim without tool output is not done.
