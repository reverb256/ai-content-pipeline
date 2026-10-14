Build the release packaging + submission path.

Deliverables:
1. `music/lanes/streaming.py` — package a release for DistroKid (primary,
   $24.99/yr, unlimited, no caps, no exclusions) and TuneCore (secondary, Suno
   partner-model tracks eligible since 2026-09-08).
2. Required metadata: title, artist, ISRC, genre, artwork, master, AI-disclosure
   flag, lyrics, explicit flag.
3. `gate_release_ready.py` enforcement before packaging.
4. A submission runbook — the actual upload is HUMAN-GATED (account + fee =
   money decision). Do not attempt to create accounts.
5. Never the same track through two distributors (duplicate listings trip
   Spotify's spam filter).

Acceptance: a complete, gate-passing release package on disk for one track, with
the ISRC and metadata shown. Runbook documented.


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
