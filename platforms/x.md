# X Platform Playbook + API Catalog

> X is the discovery + real-time surface. It is also the first platform where
> we interact via captured API endpoints rather than DOM.

## Platform Playbook

See `brain/playbooks/platforms.md` for the full platform rules. X-specific:

- 3-5 posts/day sustained, spaced 3+ hours
- 1 thread/week (7-12 tweets, hook at tweet 1)
- Links in the first reply, never in the main post
- 0-2 hashtags
- 10-20 thoughtful replies/day to accounts 10-100x our size
- Reply to every reply in the first hour after posting
- Post when audience is active (check analytics)

## Interaction Mode

X interacts via the captured internal API through the headless CDP browser
(real reverb256 session). See `scripts/api/` and the capture procedure in
`docs/`.

## API Catalog (captured 2026-08-29 from live session)

Base: `https://x.com`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/i/api/graphql/{id}/SearchTimeline` | GET | Search timeline (query, count, cursor) |
| `/i/api/graphql/{id}/TweetDetail` | GET | Tweet detail |
| `/i/api/graphql/{id}/UserByScreenName` | GET | User by handle |
| `/i/api/graphql/{id}/CreateTweet` | POST | Post a tweet |
| `/i/api/graphql/xF6sXnKJfS2AOylzxRjf6A/DataSaverMode` | GET | Session init |
| `/i/api/graphql/0qFmnKTY3JwBZnqDdQrtHw/CreateWebSessionBind` | GET | Session bind |
| `/i/api/graphql/1KZj_GRTxmPaSrk8jIb1Yw/CreatorStudioTabBarItemQuery` | GET | Creator Studio |
| `/i/api/1.1/graphql/viewer_context.json` | GET | Viewer context |
| `/i/api/1.1/hashflags.json` | GET | Campaign flags |
| `/i/api/1.1/flow/timeline.json` | GET | Home timeline |

**Auth:** session cookies (`auth_token` HttpOnly, `ct0` CSRF) + specific
headers. Direct calls need the full header set; the CDP browser provides it.
Bare `fetch` from page context returns 403 without the complete headers.

## Search Operators (the scout's toolkit)

Full recipe library: `queries/x-search-recipes.md`. Core operators:

```
"exact phrase" | from:user | to:user | filter:links | filter:videos
min_faves:N | min_retweets:N | min_replies:N | since:YYYY-MM-DD | until:YYYY-MM-DD
lang:en | -keyword | ? | near:"city" within:15mi | -filter:replies
```

## Re-Capture Cadence

X rotates endpoints and adds headers. If API calls start 401/404-ing, re-capture
the flow: browse X in the CDP browser while capturing network traffic, update
this catalog. Procedure: `docs/api-capture-procedure.md`.
