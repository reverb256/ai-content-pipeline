#!/usr/bin/env python3
"""Export cookies from the CDP browser (real reverb256 session) to a
Netscape-format cookies.txt file for yt-dlp / social-video-mcp.

The CDP browser holds the REAL decrypted cookies (via the OS keyring), so
this sidesteps yt-dlp's partial v11 decryption entirely.

Usage:
    python3 scripts/api/export-cookies.py [--domain youtube.com] [--out /tmp/cookies.txt]

Defaults: all cookies, /tmp/browser-cookies.txt
"""
import argparse
import asyncio
import json
import sys
import urllib.request

DEFAULT_PORT = 9222


def get_tab_ws(port: int, domain_hint: str = ""):
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=3) as r:
        tabs = json.loads(r.read())
    pages = [t for t in tabs if t.get("type") == "page"]
    if domain_hint:
        for t in pages:
            if domain_hint in t.get("url", ""):
                return t["webSocketDebuggerUrl"]
    return pages[0]["webSocketDebuggerUrl"] if pages else None


async def fetch_cookies(ws_url: str):
    import websockets

    async with websockets.connect(ws_url, open_timeout=10) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Network.enable", "params": {}}))
        await ws.recv()
        await ws.send(json.dumps({"id": 2, "method": "Network.getAllCookies", "params": {}}))
        resp = json.loads(await ws.recv())
        return resp.get("result", {}).get("cookies", [])


def netscape_line(c: dict) -> str:
    # domain, includeSubdomains(TRUE/FALSE), path, secure(TRUE/FALSE), expiry, name, value
    domain = c.get("domain", "")
    include_sub = "TRUE" if domain.startswith(".") else "FALSE"
    secure = "TRUE" if c.get("secure") else "FALSE"
    expiry = int(c.get("expires", 0) or 0)
    name = c.get("name", "")
    value = c.get("value", "")
    # escape tabs/newlines in value (rare but breaks the format)
    value = value.replace("\t", "%09").replace("\n", "%0A")
    return f"{domain}\t{include_sub}\t{c.get('path', '/')}\t{secure}\t{expiry}\t{name}\t{value}"


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--domain", default="", help="only include cookies whose domain contains this")
    p.add_argument("--out", default="/tmp/browser-cookies.txt")
    p.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = p.parse_args()

    ws = get_tab_ws(args.port, args.domain)
    if not ws:
        sys.exit("No browser tab found — is media-browser running? systemctl --user start media-browser.service")

    cookies = asyncio.run(fetch_cookies(ws))
    if args.domain:
        cookies = [c for c in cookies if args.domain in c.get("domain", "")]

    with open(args.out, "w") as f:
        f.write("# Netscape HTTP Cookie File\n")
        f.write("# Exported from CDP browser (reverb256 session) — do not commit\n")
        for c in cookies:
            f.write(netscape_line(c) + "\n")

    print(f"Exported {len(cookies)} cookies to {args.out}")
    auth = sorted({c['name'] for c in cookies if c['name'] in (
        'SID', 'SSID', 'APISID', 'SAPISID', 'HSID', 'LOGIN_INFO', '__Secure-1PSID')})
    if auth:
        print("Auth cookies present:", ", ".join(auth))


if __name__ == "__main__":
    main()
