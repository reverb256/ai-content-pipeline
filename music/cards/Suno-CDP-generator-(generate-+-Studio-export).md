The one genuinely new component. Build `music/suno-gen.py`.

Requirements:
- Drive Suno via CDP browser automation against the logged-in Premier session.
  Reuse the pattern in the `suno-studio` community skill (GitHub Jpalmer95/suno-studio):
  navigate to suno.com/create, enable Custom Mode, fill Title/Style/Lyrics/More
  Options, click Create, poll 30-90s for completion, extract audio URLs.
- Read the genre registry to build the prompt (never hardcode genre prompts).
- Write [metatags] ([Intro], [Verse], [Chorus]) into lyrics.
- EXPORT THROUGH SUNO STUDIO — the unlimited path. Standard downloads are capped at
  60/month and MUST NOT be used by the pipeline.
- Call gate_quota before generating/exporting.
- Record every generation into the quota ledger (credits used, studio exports).
- On failure: never fall back to the standard download button.

Acceptance: a real generation of one chill-lounge track, exported via Studio, with
the audio file on disk and the ledger incremented. Show the file path + size + the
ledger before/after.


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
