Close the loop: measure which genre×lane combinations actually earn.

Deliverables:
1. `music/analytics/` — pull streams/revenue per track from: DistroKid reports,
   YouTube Analytics, sync platform statements, direct-sales records.
2. Per-genre and per-lane ROI: revenue per generation-hour, per credit, per
   upload. The anti-pattern to expose: spraying tracks with no campaign earns ~$0
   (under ~1,000 streams in a rolling 12 months pays nothing).
3. Feed results back into the genre registry cadence (a genre that earns gets
   more cadence; one that doesn't gets paused) — an oracle-style weight update.
4. Weekly music digest: what shipped, what earned, what is stuck on a human gate.
5. Every metric that cannot be measured must print `FAILED: <reason>` and exit
   non-zero — never a false 0.

Acceptance: a working digest over at least one real track, with the FAILED path
demonstrated on a missing metric.


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
