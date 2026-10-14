Sync is the highest-ceiling lane. Only Songtradr (60-80% split) and AudioSparx
(~50%) accept AI. Library placements $20-200; direct licensing $25-500+.

Deliverables:
1. `music/lanes/sync.py` — build the sync-ready package:
   - full mix + instrumental + 12 stems
   - complete metadata (mood, tempo, key, instrumentation, themes, BPM)
   - one-stop clearance doc + AI-disclosure statement
   - predictable structure (a sync buyer needs to cut to picture)
2. `music/lanes/direct-license.py` — licence tiers (personal / commercial /
   exclusive), deliverable spec, pricing per the research ($25 personal,
   $500+ exclusive).
3. `gate_sync_ready.py` enforcement.
4. Runbook for Songtradr + AudioSparx submission (HUMAN-GATED accounts).

Acceptance: one track fully sync-ready (all four deliverable classes on disk,
metadata complete), plus a populated licence-tier table.


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
