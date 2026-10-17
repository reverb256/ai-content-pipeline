# Site Registry

> Every platform/account the AI content pipeline can act on, with session
> status, capabilities per bot, and re-auth paths. Verified live 2026-08-29
> via the CDP browser (real reverb256 profile).
>
> **This is the source of truth for "what can the system do where."** If a
> session dies, fix it and update this file. The bots read this before
> touching a platform.

## Session Verification

Verified 2026-08-29 through the headless CDP Chromium (media-browser.service,
port 9222, real reverb256 profile).

| Site | Account | Signed In | Capabilities | Notes |
|------|---------|-----------|--------------|-------|
| GitHub | reverb256 | ✅ | read, create repos/issues/PRs, push | The repo hub; bots commit here |
| X | reverb256 | ✅ | search, read timeline, post (via captured API) | Primary discovery + distribution |
| Gmail | reverb256@gmail.com | ✅ | read email (via browser) | Notifications, verification |
| YouTube | reverb256@gmail.com | ✅ | watch history, sub feed, studio (via CDP) | Channel: **youtube.com/@Reverb256** (exists, logged in). Full API via OAuth (todo — publishbot needs Google Cloud project + OAuth consent) |
| LinkedIn | jeremy-undefined | ✅ | feed, post, profile (via CDP) | Secondary/B2B surface |
| Substack | (reverb256) | ✅ | dashboard, publications, subs (via CDP + API) | Owned audience surface |
| Google Search Console | reverb256 | ✅ | search performance, indexing | Blog/SEO analytics |
| Google Analytics | reverb256 | ✅ | site analytics | Blog/portfolio analytics |
| Reddit | — | ❌ (blocked by network security) | — | Headless fingerprint blocked; needs stealth or manual session |
| Hacker News | — | ❌ (not logged in) | — | Login needed if we want Show HN |

## Bot → Platform Capability Matrix

| Bot | Can read | Can write | Can publish |
|-----|----------|-----------|-------------|
| scout | X search, web | kanban, campaigns | — |
| researcher | X, web, GitHub, YouTube | campaigns/research.md | — |
| strategist | brain, research | campaigns/angle.md | — |
| writer | brain, angle, research | campaigns/flagship.md | — |
| distributor | angle, flagship, platforms/ | campaigns/distribution/ | — |
| editor | everything | campaigns/review.md, RULINGS.md (proposed) | — |
| **HUMAN (j_kro)** | everything | — | **X, LinkedIn, Substack, YouTube, blog** |

## Re-Auth Paths

If a session dies:

| Site | Fix |
|------|-----|
| All (general) | The media-browser runs the real Chromium profile. Sign in again in a headed Chromium with the same profile: `chromium --user-data-dir=~/.config/chromium`, then re-check with `scripts/browser/check-sessions.sh` |
| X | X rotates tokens; re-capture the API catalog if CreateTweet/SearchTimeline 401s |
| YouTube | OAuth via MCP (pauling-ai) once; re-auth in browser if cookie session dies |
| Reddit | Headless fingerprint blocked. Needs stealth mode or manual login in a real browser, then capture cookies |
| HN | Login once in the Chromium profile (create account or use existing) |

## Site Registry Script

`scripts/browser/check-sessions.sh` — checks all sites via CDP and prints the
status table. Run it when a bot reports a platform failing.

## Rules

1. **This file is the truth.** Bots must check `registry.md` before acting on
   a platform. If a capability is not listed, the bot asks.
2. **Never hardcode credentials.** Sessions live in the browser profile. The
   registry records status, not secrets.
3. **Update on change.** When a session is added/removed/fixed, update this
   file in the same commit.
4. **Publishing stays human.** No bot publishes. The registry's write
   capabilities feed the review queue; the human presses the button (or
   approves the distributor's pre-staged post).
