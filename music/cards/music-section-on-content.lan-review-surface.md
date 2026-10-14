The human approval surface must cover music, not just video/audio-drama.

Deliverables:
1. Add a music section to the content.lan site (/opt/content-site/media/) that
   lists music tracks awaiting approval with YAML-frontmatter sidecars
   (`status: awaiting-approval`).
2. Audio player inline so j_kro can listen before approving.
3. Wire the existing approval API (:8791) so approving a music sidecar unblocks
   the mapped kanban publish card.
4. Note the known 3-bug pattern in the existing surface (parseListing regex vs
   textContent, `file.md` vs `file.mp4.md` sidecar convention, API running but
   UI never calling it) — do not repeat them. See the
   `automated-content-machine` skill reference content-lan-approval-surface.md.

Acceptance: curl the live content.lan URL and show a music track listed with a
working player; flip a sidecar via the API and show the card unblock.


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
