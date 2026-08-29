#!/usr/bin/env python3
"""Capture API endpoints from a CDP browser tab.

Usage:
    python3 scripts/api/capture-endpoints.py <url-pattern> [--duration 8]

Connects to the media-browser CDP (default :9222), finds a tab matching the
URL pattern, enables the Network domain, reloads the page, and prints the
API-looking requests (graphql, /api/, i/api, JSON).

Verified working 2026-08-29 against X (captured SearchTimeline, TweetDetail,
viewer_context, Creator Studio endpoints).
"""
import argparse
import asyncio
import json
import sys
import urllib.request

DEFAULT_PORT = 9222
API_HINTS = ("graphql", "/api/", "i/api", "json", "timeline", "search")


def get_browser_ws(port: int) -> str:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=3) as r:
        return json.loads(r.read())["webSocketDebuggerUrl"]


def get_tab_ws(port: int, pattern: str):
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=3) as r:
        tabs = json.loads(r.read())
    for t in tabs:
        if t.get("type") == "page" and pattern.lower() in t.get("url", "").lower():
            return t["webSocketDebuggerUrl"], t["url"]
    raise SystemExit(f"No tab matching {pattern!r} found. Open it in the media-browser first.")


async def capture(port: int, pattern: str, duration: int) -> None:
    import websockets

    tab_ws, tab_url = get_tab_ws(port, pattern)
    print(f"Capturing API calls on {tab_url[:80]} for {duration}s...")

    async with websockets.connect(tab_ws, open_timeout=10) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Network.enable", "params": {}}))
        await ws.recv()
        await ws.send(json.dumps({"id": 2, "method": "Page.reload", "params": {}}))

        seen = set()
        deadline = asyncio.get_event_loop().time() + duration
        while asyncio.get_event_loop().time() < deadline:
            try:
                msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=0.5))
            except asyncio.TimeoutError:
                continue
            if msg.get("method") != "Network.requestWillBeSent":
                continue
            url = msg["params"]["request"]["url"]
            method = msg["params"]["request"]["method"]
            if not any(h in url for h in API_HINTS):
                continue
            key = (method, url.split("?")[0])
            if key in seen:
                continue
            seen.add(key)
            print(f"{method}  {url[:140]}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("url_pattern", help="substring of the tab URL to capture (e.g. x.com)")
    p.add_argument("--port", type=int, default=DEFAULT_PORT)
    p.add_argument("--duration", type=int, default=8)
    args = p.parse_args()

    try:
        get_browser_ws(args.port)
    except Exception as e:
        sys.exit(f"media-browser CDP not reachable on :{args.port} ({e}). "
                 "Start it: systemctl --user start media-browser.service")

    asyncio.run(capture(args.port, args.url_pattern, args.duration))


if __name__ == "__main__":
    main()
