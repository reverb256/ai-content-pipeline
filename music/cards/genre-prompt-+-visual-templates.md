Write one prompt template per registry genre in `music/prompts/<genre>.md`.

Each template must contain:
- Style field text (<=1000 chars) describing the dynamic journey
- Lyrics guidance with [metatags] structure
- More Options: weirdness, style influence, exclusions
- Genre-specific craft notes (what makes the genre read as authentic)

Genres to cover: chill-lounge, trance, jungle-dnb, sentimental-piano,
commentary-beds, activist, elemental-fire, elemental-water, elemental-earth,
elemental-air, chiptune-8bit, epic-orchestral-boss.

Quality bar: a Suno generation from each template must be recognisably IN genre.
Generic "epic music" prompts are a defect. Cite the genre's real production
conventions (e.g. jungle = amen breaks + ragga vocals + 160-175 BPM).

Acceptance: 12 template files, each with all four sections, each validated by
generating one track and confirming the genre reads correctly.


## Context (read before starting)

Repo: /home/j_kro/Projects/ai-content-pipeline
Architecture: brain/playbooks/music-lane-architecture.md  ← READ THIS FIRST
Platform research: brain/research/music-monetization-2026.md

## Hard constraints
- Suno Premier: 60 STANDARD downloads/month. Suno STUDIO downloads are UNLIMITED.
  Every export path must go through Studio. Never the standard download button.
- Suno has NO official API. Generation = CDP browser automation on the logged-in
  Premier session (see the suno-studio pattern). No paid reseller proxies.
- The pipeline is GENRE-GENERIC. Genres are DATA (music/genres.yaml), never code.
  Adding a genre must require zero script edits.
- Banned platforms — do NOT build for these: Pond5, AudioJungle/Envato, Artlist,
  Epidemic Sound, Soundstripe, PremiumBeat, Musicbed, Bandcamp (Jan 2026),
  Beatport (Aug 2026), CD Baby.
- Gates must EXECUTE the artifact (parse/measure/render). A gate that greps a file
  for a feature name is a defect — it passes while the artifact is broken.
- No stubs. No TODOs. Complete code, verified by real execution.

## Report back
Evidence in the report: exact commands run, real output, file paths.
A claim without tool output is not done.
