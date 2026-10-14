The two FULLY automatable storefronts. Build both adapters.

1. `music/publish/itchio.py` — drive the official **butler CLI** (`butler push`).
   - Auth via butler API key (stored per the fleet secrets convention, never in the repo).
   - Push asset packs + music bundles as channels.
   - Tag AI Audio where applicable (itch.io explicitly supports AI Audio tags).
   - Prefer the official GitHub Action pattern for reference.

2. `music/publish/gumroad.py` — official Gumroad API:
   - `POST /v2/products` (native_type=digital) to create the product
   - `POST /files/presign` + file upload
   - set price, cover thumbnail, description
   - store the access_token per the secrets convention
   - Reference the community pipelines (gumroad-autopilot, gumroad-automation-pipeline)
     for the exact call sequence, but implement against the OFFICIAL API.

3. Both adapters: upload as DRAFT/private by default. A lane autonomy-rung flag decides
   whether a product goes live.

4. `gate_release_ready.py` must pass before either adapter runs.

Acceptance: a real draft product created on Gumroad and a real butler push to a
test/draft channel on itch.io, with the API responses shown. If an account is not yet
provisioned, implement fully, prove the call path with a dry-run against the documented
schema, and say exactly which credential is missing.

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
