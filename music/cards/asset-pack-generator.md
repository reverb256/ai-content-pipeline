Asset packs are the highest-automation, lowest-gatekeeper revenue lane. They monetize
work already done for the sync lane.

Build `music/assets/pack.py` — derive packs from finished tracks:
1. **Loop packs** — extract seamless loops. Detect musically clean loop boundaries
   (bar-aligned), verify NO CLICK at the seam (measure the sample discontinuity at the
   wrap point), write BPM + key metadata.
2. **Stem packs** — consume the 12 Studio stems, time-aligned, named consistently.
3. **One-shots / SFX** — isolate hits from stems (kick, snare, hat, riser, impact).
   Also generate SFX where the genre calls for it (elemental: fire whoosh, water drip,
   earth rumble, air gust).
4. **Pack manifest** — JSON + human-readable README: track list, BPM, key, sample rate,
   file naming convention, licence tier pointer.
5. **Licence text** — multi-tier (personal / commercial / exclusive) with EXPLICIT
   permitted use, distribution, and derivative-work rules. Vague licence language is the
   documented #1 failure mode.

Packaging spec (from research): clean WAV, stated sample rate, consistent naming,
loops seamless + click-free with stated BPM/key, stems time-aligned.

Acceptance: one complete pack (>=5 loops + stems + >=5 one-shots) with every loop
verified click-free by measurement, plus the licence text. Show the measurement output.

---

## Context (read before starting)

Repo: /home/j_kro/Projects/ai-content-pipeline
Architecture: brain/playbooks/music-lane-architecture.md  ← READ FIRST (sections 10-13)
Platform research: brain/research/music-monetization-2026.md

## Hard constraints
- Suno Premier: 60 STANDARD downloads/month. Suno STUDIO downloads are UNLIMITED.
  All exports go through Studio. Never the standard download button.
- Suno has NO official API. Generation = CDP automation on the logged-in Premier session.
- GENRE-GENERIC: genres are DATA (music/genres.yaml), never code.
- Playwright + API watchers + scraping are AUTHORIZED (j_kro 2026-10-08) as the
  mechanism for any lane lacking an API. Prefer a real API where one exists.
- Banned platforms: Pond5, AudioJungle/Envato, Artlist, Epidemic Sound, Soundstripe,
  PremiumBeat, Musicbed, Bandcamp, Beatport, CD Baby.
- Gates must EXECUTE the artifact. Grep-gates are defects.
- No stubs. No TODOs. Complete code verified by real execution.

## Report back
Exact commands, real output, file paths. A claim without tool output is not done.
