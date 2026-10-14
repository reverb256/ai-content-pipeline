The autonomous loop. Per architecture section 11.

Deliverables:
1. `music/oracle.py` — daily scan. Emits scored cards to the `music` board. Inputs:
   lane performance, genre ROI from the analyst, platform policy change signals,
   trend signals. Scoring must be data-driven, not vibes.
2. `music/scheduler/` — cron/timer definitions for the music board:
   - music-oracle (daily)
   - music-pipeline-driver (every 30 min)
   - music-weekly-digest (weekly)
   - music-policy-watch (daily — platform AI-policy changes; this is the fastest-moving
     fact in the domain and a stale policy gets accounts terminated)
3. **Install on nexus, NOT zephyr.** Workstation crons pause when the workstation sleeps;
   a self-running business cannot sleep with the laptop. Verify nexus is always-on.
4. Wire `scripts/automation/pipeline-driver.sh` with `BOARD=music`.
5. Autonomy-rung state file per lane (`music/autonomy.yaml`) implementing the ladder in
   section 11.2: advisory -> supervised -> monitored -> full, with promotion evidence tracked.
6. Failure handling per section 11.4: cooldown/backoff, gate-failure returns to maker,
   credential expiry -> digest, sustained failure -> pause the lane and page. Never loop.

Acceptance: run the oracle once and show real scored cards created on the music board;
show the scheduler installed on nexus with `systemctl --user list-timers` or the cron
equivalent; show a DRY_RUN driver pass routing music stages correctly.

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
