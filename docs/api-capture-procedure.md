# API Capture Procedure

> How to capture the API catalogs (platforms/*.md) and generate direct-call
> clients. The content system does this itself per campaign, but the procedure
> is documented here so it is reproducible.

## Why

DOM scraping is slow, brittle, and token-heavy. Reading the site's own API
calls (JSON the site already produces for itself) is fast, structured, and
authenticated with the real session.

## Capture via CDP (the working method, verified 2026-08-29)

1. Ensure the media-browser is running:
   ```bash
   systemctl --user start media-browser.service
   bash scripts/browser/check-media-browser.sh
   ```
2. Browse the target platform in the CDP browser (it has the real reverb256
   session).
3. Attach to a tab and listen for `Network.requestWillBeSent` events, filtering
   for API-looking URLs (`graphql`, `i/api`, `/api/`, JSON responses).
   See `scripts/api/capture-endpoints.py`.
4. Record: method, URL template (path params identified), required headers,
   auth pattern (cookie / bearer / CSRF).
5. Update `platforms/<name>.md` with the catalog.
6. Generate the typed client (see `har-to-api-client` skill / `scripts/api/`).

## Direct-Call Rules

- Auth: session cookies from the CDP browser (HttpOnly included)
- CSRF: include `ct0`-style tokens where required
- If a direct call 403s, the browser provides the full header set — replay
  through the browser or add the missing headers
- Never hardcode secrets; the browser session IS the credential store

## Re-Capture Cadence

- Re-capture when endpoints start 401/404-ing (API drift)
- X rotates endpoints and adds headers; check monthly
- Substack/YouTube/LinkedIn: capture dashboard flows when we start using them

## Pitfalls

- `document.cookie` does NOT show HttpOnly cookies — use CDP
  `Network.getAllCookies` for the full jar
- Bare `fetch` from page context may 403 without the complete header set
- CDP `Network.getResponseBody` may be empty for gzip/brotli — prefer
  Playwright `page.route()` or capture at request time
- CORS preflights (OPTIONS) clutter captures; filter them
- Static assets dominate; filter to the API host(s) before analysis
