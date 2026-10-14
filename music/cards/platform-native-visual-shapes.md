Music needs different video shapes than the existing faceless-YouTube lane.

Deliverables in `music/visuals/`:
1. `album-30-60min` — long-form album video (the 2-3x-earning shape). Static or
   slowly-evolving visual + tracklist + timestamps.
2. `mix-60min` — DJ-mix style with tracklist overlay (trance, jungle-dnb).
3. `loop-10min` — seamless looping visual for gaming-music channels and
   game-asset previews.
4. `single-4min` — lyric video.
5. One visual style per registry `visual_style` entry (element fire/water/earth/air,
   pixel-scene, dark-fantasy, lofi-room-rain, neon-horizon, urban-grain,
   soft-window-light, documentary-grain).

Critical: `gate_youtube_authentic` must pass — the visuals must VARY between
uploads. A templated identical visual across 100 uploads is exactly what the
inauthentic-content policy targets.

Acceptance: render each of the 4 shapes at real duration from a real audio file,
with ffprobe output proving dimensions + duration.


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
