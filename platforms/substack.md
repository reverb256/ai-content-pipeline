# Substack Platform Playbook

> Substack is the owned audience surface. Email lands in inboxes — no
> algorithm between us and the reader.

## Platform Rules

- 1 high-quality issue/week + 2-4 Notes/day
- Free content = the "what". Paid content = the "how" (paid not active yet)
- Notes are the discovery engine (>35% of subs come from Notes for many)
- Recommendations: recommend similar publications + ask for reciprocation
- SEO: keyword-rich titles, meta descriptions, internal links, evergreen
  posts that answer specific searches

## Interaction Mode

Substack interacts via the CDP browser (real reverb256 session) or its web
dashboard.

## API Catalog (captured 2026-08-29 via CDP)

Base: `https://substack.com`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/firehose/batch` | POST | Feed batch (posts, Notes) |
| `/api/v1/activity/unread` | GET | Unread activity count |
| `/api/v1/subscriptions/page_v2` | GET | Subscriptions (signed-in data) |

More endpoints (publication stats, publish flow, Notes) to capture when we
start publishing.

## Re-Capture Cadence

Capture the dashboard + publish flows when we start publishing. Re-capture
when endpoints 401/404.
