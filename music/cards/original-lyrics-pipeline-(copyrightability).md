Original lyrics are the single biggest legal upgrade — human authorship makes a
track registrable and acceptable to distributors that reject 100%-AI content, and
enables SOCAN registration (partially-AI works are accepted; fully-AI is not).

Build the lyrics stage:
1. `music/lyrics/` per-genre lyric generation driven by the writer profile —
   ORIGINAL human-directed lyrics, never Suno-generated ones.
2. Record a human-authorship claim per track (who wrote, when, what was
   AI-assisted) in the track manifest.
3. `music/gates/gate_lyrics_original.py` must verify the claim exists and the
   lyrics were not produced by Suno's lyric generator.
4. Document the SOCAN registration path for a partially-AI work in
   `music/docs/pro-registration.md` (SOCAN, since j_kro is Canadian).

Acceptance: 3 genres with complete original lyrics + authorship claims, gate passes
on all 3 and fails on a Suno-generated lyric.


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
