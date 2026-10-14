Build `music/gates/` — every gate EXERCISES the artifact.

Gates (per architecture §5):
- gate_quota.py        — reads quota-ledger.json; blocks at hard_stop_at
- gate_lyrics_original.py — lyrics exist AND are human-authored (not a Suno
                         generated lyric); human-authorship claim recorded
- gate_stems_present.py — >=4 stems, non-zero bytes, durations match master +/-0.5s
                         (use ffprobe, not file size guessing)
- gate_loudness.py     — MEASURE with ffmpeg volumedetect; -14 LUFS streaming /
                         -16 sync, within +/-1 dB. Must fail honestly on a loud master.
- gate_quality.py      — routes to an independent reviewer on a DIFFERENT model
                         than the producer
- gate_sync_ready.py   — stems + metadata + clearance doc + instrumental version
- gate_release_ready.py— ISRC + metadata + AI-disclosure flag + master + artwork
- gate_youtube_authentic.py — visual varies vs prior uploads; not a raw dump;
                         disclosure set
- gate_loop_points.py  — seamless loop verified for the game-assets lane

Each gate: exit 0 pass / non-zero fail, with a human-readable reason.
Acceptance: for EACH gate, show a PASS on a good artifact and a FAIL on a
deliberately broken one. Both runs in the report.


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
