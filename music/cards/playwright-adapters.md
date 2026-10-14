Lanes with no official API. Playwright is authorized (j_kro 2026-10-08).

Build `music/publish/playwright/`:
1. `distrokid.py` — automate release upload on the logged-in session. Reference the two
   community implementations: `Sam-r-ai/Automated_Distrokid_Uploader` (webupload.py) and
   `hlushchukm/Distrokid` (unofficial Go wrapper from iOS app reversal). Read BOTH before
   writing. Do not invent selectors — derive them from the reference code and verify live.
2. `fab.py` — Fab/Unreal publisher portal submission (post-onboarding).
3. `unity.py` — Unity Asset Store publisher submission (post-onboarding).
4. `splice.py` — Splice/Loopmasters/ProducerLoops submission (form-based, semi-automated).

Requirements:
- Shared session helper: reuse the persistent browser profile so logins survive.
- Never hardcode credentials. Never attempt to CREATE accounts (human-gated).
- Idempotent: re-running must not create duplicate listings.
- Rate-limit aware: backoff on 429.
- Every adapter returns a verifiable handle (URL/id) so the caller can confirm.

Acceptance: DistroKid adapter proven to the point of a filled upload form in DRAFT
(do not submit a live release), with the browser state captured. Show the exact
selector source for each field.

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
