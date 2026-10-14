The existing mix/master work in storyteller.py targets audio DRAMA. Music needs
its own path. Extend, do not fork blindly.

Deliverables:
1. `music/mix/master.py` — loudness normalisation to -14 LUFS (streaming) or
   -16 LUFS (sync), true-peak limiting, measured with volumedetect.
2. Stem handling: consume Suno Studio's 12 time-aligned WAV stems; verify
   alignment (durations match +/-0.5s) and write a stem manifest.
3. Instrumental version generation (vocals-out) — MANDATORY for sync and
   direct-licensing lanes.
4. Seamless loop point detection for the game-assets lane (find a musically clean
   loop boundary, verify no click at the seam).
5. A music track must be DRY — no echo/reverb tail on the vocal stem (existing
   ruling Ruling 2026-09-03-03 applies to music vocals too).

Acceptance: one real track mastered to spec with volumedetect output shown, stems
aligned, instrumental produced, and a verified click-free loop.


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
