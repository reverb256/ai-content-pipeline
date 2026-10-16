# Virtual Reflections — Suno album record

**The album exists. It was never missing.** An earlier audit concluded the
account held 0 clips and that the album was on an inaccessible account. Both
were wrong, and the cause is recorded below so it cannot mislead again.

## Album

| | |
|---|---|
| Title | Virtual Reflections |
| Description | Reflections on my own VRChat experiences. |
| Suno album id | `21e76d85-15f3-42d7-92a6-cf8a35248795` |
| URL | https://suno.com/album/21e76d85-15f3-42d7-92a6-cf8a35248795 |
| Owner | @reverb256 (display: Reverb256) |
| Status | **Draft** — not published |
| Created | 2026-10-08 |
| Tracks | 6 · ~20:27 total |
| Model | V6-WILD throughout |

## Tracks

| # | Title | Likes | Length | Suno song id |
|---|-------|-------|--------|--------------|
| 1 | Welcome | 7 | 0:51 | `af1e57f0-6595-460b-a0e7-7bb0bdd41f37` |
| 2 | These Worlds Are Made of Light | 5 | 3:29 | `63ce63d8-9888-4626-a431-d225ff9019cb` |
| 3 | Erasing the Distance | 9 | 3:24 | `23937711-dbfe-4612-95a7-39a20a64379b` |
| 4 | This Small Forever | 3 | 5:08 | `51c07d53-6eca-431a-886e-36f9c482abef` |
| 5 | World of Blue | 2 | 2:22 | `4e23725e-e4ec-4b55-ad72-ed965fa822db` |
| 6 | Sincerely | 8 | 5:13 | `6db57655-f2c7-4929-b6ad-3ab948155962` |

Song pages: `https://suno.com/song/<id>`

## Account — Premier, verified live

Read from `/api/billing/info/` on `studio-api-prod.suno.com`, 2026-10-09:

```
plan_key:            premier
name:                Premier Plan
is_active:           true
is_past_due:         false
monthly_limit:       10000
monthly_usage:       390
credits:             15 remaining
subscription_anchor: 2026-10-08T12:03:14Z
renews_on:           2026-11-08T12:03:14Z
```

Capabilities the pipeline depends on, all present in the plan's feature list:
`commercial_rights`, `get_stems`, `studio`, `max_mode`, `custom_models`.

The plan text states commercial use rights for songs made while subscribed, and
10,000 credits (up to 2,000 songs) refreshing monthly.

## Why the earlier audit was wrong

Three separate mistakes, each of which alone would have produced a false
negative:

1. **Wrong session.** The audit drove a headless Chromium logged in through
   Google SSO as `reverb256458`. The album is on the account logged in through
   **Discord** (`@reverb256`). These are different accounts; the SSO one is
   empty, and it is the one that was measured.

2. **Wrong host.** Every API call went to `https://suno.com/api/...`, which
   returns a Next.js 404 page. The real API is
   `https://studio-api-prod.suno.com/api/...`. A 404 HTML page reads a lot like
   an empty library if only the status code is checked.

3. **Filters left on.** The library UI held two active filters and rendered
   "No songs found". An empty view was read as an empty account.

Two further details worth keeping, because they are what made the fix possible:

- `~/.config/zen/default` is a **stale leftover** copy. The live profile is
  `~/.zen/8axfpgq0.Default (release)`. Reading the stale one yields month-old
  cookies and false conclusions.
- Suno authenticates with the Clerk `__session` cookie **as a bearer token**.
  Some endpoints (`/api/session/`, `/api/profiles/...`) accept the cookie alone;
  `/api/billing/info/` and `/api/feed/v3` require
  `Authorization: Bearer <value of __session>`. The cookie is not httpOnly, so
  it is readable from page JS.

## What this means for the pipeline

Nothing about the plan needs revising for account capability: Premier is
present, commercial rights are present, stems and Studio are present. The
60-standard-downloads/month cap described in the lane architecture is a
**standard-tier** limit; Studio exports ride the subscription.

The album is **Draft**, so it is private. Publishing is a release-gate decision
and belongs to j_kro.
