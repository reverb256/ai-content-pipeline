`scripts/automation/pipeline-driver.sh` is hardcoded to BOARD="faceless-youtube"
(line 19) with a hardcoded stage→bot map for the YouTube lane. Make it generic.

Requirements:
1. `BOARD` from env (`BOARD` or `--board`), default unchanged (faceless-youtube) so
   the existing lane keeps working byte-for-byte.
2. Stage→bot map read from a per-board config file (e.g. `music/stages.yaml` for the
   music board) instead of the inline case statement. Keep the faceless-youtube map
   as a config file too so both lanes are data-driven.
3. `running_bots()` pattern must cover the music bots.
4. `DRY_RUN=1` must prove routing without launching bots.

Acceptance: `BOARD=faceless-youtube DRY_RUN=1 bash scripts/automation/pipeline-driver.sh`
produces the SAME routing as before the change (diff the DRY_RUN output against a
pre-change capture), and `BOARD=music DRY_RUN=1 ...` routes the music stages to the
music bots. Show both outputs.


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
