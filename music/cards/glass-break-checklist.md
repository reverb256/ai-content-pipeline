Produce the ONE-TIME human checklist that makes the system self-run.

Per architecture section 12. Deliver `music/docs/GLASS-BREAK.md` — for each item: the exact
URL, the exact fields needed, the exact cost, where the resulting credential is stored, and
the verification command that proves it works.

Items:
1. DistroKid account ($24.99/yr) + credential
2. Gumroad account + API access_token
3. itch.io account + butler API key
4. Songtradr account (free tier) + API login
5. SOCAN registration (Canadian PRO — partially-AI works accepted, fully-AI not)
6. Payout + tax details on each surface
7. The publish-policy decision: the autonomy rung each lane starts at

Also deliver:
- `music/docs/credentials.md` — the credential MAP (names + locations only, NEVER values).
  Follow the fleet convention: secretspec on Omarchy hosts, sops for VPS hosts.
- A verification script `music/scripts/verify-credentials.sh` that checks each credential
  exists and is VALID (a real API call), printing PASS/FAIL per surface.

Acceptance: the checklist doc, the credential map, and the verify script run and
honestly reporting which credentials are present vs missing. Do NOT create any account
and do NOT ask for any credential value in chat.

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
