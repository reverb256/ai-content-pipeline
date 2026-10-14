Build the declarative data layer every other music component reads.

Deliverables:
1. `music/genres.yaml` — genre registry exactly per the architecture doc §2.
   Must include the elemental/gamer family (fire/water/earth/air), chiptune-8bit,
   epic-orchestral-boss, jungle-dnb, plus chill-lounge, trance, sentimental-piano,
   commentary-beds, activist. Each block: family, prompt_template, visual_style,
   lanes, cadence, video_shape, notes.
2. `music/lanes.yaml` — lane registry per §3, including the `game-assets` lane
   (itch.io / Unity Asset Store / gamedev markets).
3. `music/quota-ledger.json` — per §6, with warn_at 55 / hard_stop_at 58.
4. `music/registry.py` — loader + validator. Must: parse both YAMLs, validate that
   every `lanes:` entry exists in lanes.yaml, every `prompt_template` and
   `visual_style` path resolves, and FAIL LOUDLY with a non-zero exit on any
   dangling reference. Print the resolved genre count.

Acceptance: `python3 music/registry.py validate` exits 0 and prints the genre +
lane counts. Introduce a deliberate bad reference and confirm it exits non-zero.


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
