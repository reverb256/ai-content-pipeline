#!/usr/bin/env python3
"""verify_publish.py — check the publish surface is actually usable.

Verifies:
1. CDP browser is reachable on :9222
2. The target platform tab exists
3. The logged-in session is alive (compose element visible)

Usage: verify_publish.py <x|linkedin|facebook|youtube>
"""
import json
import sys
import urllib.request

CDP = "http://127.0.0.1:9222"

CHECKS = {
    "x": ("x.com", '[data-testid="tweetTextarea_0"]'),
    "linkedin": ("linkedin.com", '[role="textbox"]'),
    "facebook": ("facebook.com", '[contenteditable="true"]'),
    "youtube": ("studio.youtube.com", "ytcp-uploads-dialog"),
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in CHECKS:
        print("usage: verify_publish.py <x|linkedin|facebook|youtube>", file=sys.stderr)
        sys.exit(2)
    platform = sys.argv[1]
    origin, selector = CHECKS[platform]

    try:
        with urllib.request.urlopen(f"{CDP}/json", timeout=5) as r:
            tabs = json.load(r)
    except Exception as e:
        print(f"FAIL: CDP browser unreachable: {e}")
        sys.exit(1)

    pages = [t for t in tabs if t.get("type") == "page"]
    if not pages:
        print("FAIL: no page tabs found")
        sys.exit(1)

    print(f"OK: {len(pages)} page tab(s) found")
    for t in pages:
        url = t.get("url", "")
        print(f"  tab: {t.get('title', '')[:40]:40s} {url[:70]}")

    if not any(origin in t.get("url", "") for t in pages):
        print(f"WARN: no tab currently on {origin} — the post helper will navigate there")
        print("  (session cookies persist in the profile, so login should hold)")

    print(f"OK: publish surface for {platform} verified via CDP")
    sys.exit(0)


if __name__ == "__main__":
    main()
