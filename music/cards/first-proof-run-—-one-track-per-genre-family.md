Prove the whole pipeline end-to-end. This is the acceptance test for the lane.

Run ONE track through every stage for each family: ambient (chill-lounge), edm
(trance), acoustic (sentimental-piano), utility (commentary-beds), gamer
(elemental-fire). Six families, six tracks.

Per track: brief -> genre-select -> lyrics -> generate -> curate -> stems ->
master -> gate -> package -> visual -> (private) publish -> track.

Requirements:
- Real Suno generation via the CDP generator, exported via Studio.
- Real gates passing (show the output of each).
- Private upload only — public publish is j_kro's gate.
- Report the exact artifact paths and the measured results.

This card depends on the registries, generator, gates, and mix/master cards.
Acceptance: 6 tracks, every stage evidenced, and an honest list of what did not
work. A partial honest result beats a claimed complete one.


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
