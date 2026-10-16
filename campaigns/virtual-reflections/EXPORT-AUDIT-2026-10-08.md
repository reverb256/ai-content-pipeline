# Virtual Reflections — Export Audit (2026-10-08)

## TASK: export, preserve, rights record

## FINDINGS — what is actually true

### Suno account state (measured, via CDP on headless Chromium :9222,
### user-data-dir /home/j_kro/.config/chromium, Google SSO as reverb256@gmail.com)

- **Logged-in Suno account:** reverb256458 (reverb256@gmail.com)
  - user id: 41564348-c179-40ca-a1f9-beff0ef2c894
  - Source: `GET https://studio-api-prod.suno.com/api/session/` (authenticated, in-page fetch)
- **total_clips: 0** — the account holds ZERO songs/clips.
  - Source: same session endpoint, `"total_clips": 0`
- **feed/v3** (`POST https://studio-api-prod.suno.com/api/feed/v3`) with ALL
  filters set to `Any` (disliked/trashed/liked/public/fullSong/upload),
  user.presence=True, userId=41564348...:
  - Response: `{"clips": [], "has_more": false}`
- **Library UI** (suno.com/me): "No songs found", "0:00" player.
- **Billing** (`GET /api/billing/info/`): `is_active: false`,
  `subscription_type: false`, `credits: 0`, `monthly_limit: 100`.
  Not a Premier/Pro subscription on this account.

### Conclusion
The "Virtual Reflections" album is **NOT on the reverb256458 Suno account.**
Nothing to export from this account. Export count found: 0.

### Second Google account
The Google account chooser listed two accounts:
- reverb256@gmail.com (signed in, Suno account above — empty)
- snyper256@gmail.com (showed "Signed out" after Google sign-out)

Attempted switch to snyper256@gmail.com:
- Google account chooser auto-redirects to reverb256 (SSO session).
- After Google sign-out, snyper256 requires interactive email+password login.
- Headless Chromium is rejected by Google sign-in
  (`/v3/signin/rejected`) — bot detection. snyper256 password is not
  available to this agent (vault has no suno/google login; Bitwarden
  locked/unavailable in session).
- **Cannot verify whether the album lives on snyper256's Suno account.**

### What was NOT done (honest gaps)
1. **Export: 0 tracks exported.** Album not found on the accessible account.
2. **No WAV files downloaded.** No local audio/ or stems/ populated.
3. **No manifest built** — no tracks to manifest.
4. **No rights record built** — no track list to attribute.
5. **No mastering measured** — no audio to measure with volumedetect.
6. **Studio vs standard download:** moot — nothing to download.
   (Standard button is capped at 60/month; Studio is the unlimited path
   once tracks are located.)

### What is needed to proceed (j_kro decision)
- Confirm which Suno account holds "Virtual Reflections":
  - If snyper256@gmail.com: sign in interactively (Google blocks headless),
    or export from that session and place files in
    campaigns/virtual-reflections/audio/ + stems/.
  - If a different Suno handle entirely: provide the handle/URLs.
- Or: provide the Suno song URLs directly (suno.com/song/<id>) so the
  export can be driven per-track.

## Environment notes
- Headless Chromium CDP on :9222, profile /home/j_kro/.config/chromium.
- Google SSO works for reverb256 (persisted cookies); snyper256 is signed out.
- No suno-gen.py exists yet in the repo (music/ has no suno-gen.py).
- VRAM 4316/8192 MiB (53%), RAM 10 GB available — no local GPU work needed
  (Suno is a network operation).

## Verification commands (re-runnable)
- session: in-page fetch GET studio-api-prod.suno.com/api/session/
- feed: POST studio-api-prod.suno.com/api/feed/v3 (filters all Any)
- billing: GET studio-api-prod.suno.com/api/billing/info/
