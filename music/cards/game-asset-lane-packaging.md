The gamer/elemental family needs its own packaging. Verified market: itch.io
supports AI Audio tags explicitly, Unity Asset Store sells audio, production
libraries $50-500/track, perpetual licences $1,000-10,000, asset packs
$2,500-7,500 for 5-10 tracks, indie game sync $500-15,000/track.

Deliverables:
1. `music/lanes/game-assets.py` — package asset packs: loopable tracks with
   VERIFIED seamless loop points, stems, one-shots, clean WAV + stated sample
   rate, consistent file naming.
2. Perpetual-licence text (permitted use, distribution, derivative-work rules,
   streamer clearance). Vague licence language is the #1 failure per the research.
3. `gate_loop_points.py` enforcement + `gate_sync_ready.py`.
4. Marketplace runbooks: itch.io (AI Audio tag), Unity Asset Store (publisher
   account = HUMAN-GATED), gamedev markets.
5. A genre→asset-pack mapping driven by the registry's `elemental-*` and
   `chiptune-8bit` entries.

Acceptance: one complete asset pack (>=5 tracks, loops verified click-free,
licence text, naming convention) ready for upload.


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
