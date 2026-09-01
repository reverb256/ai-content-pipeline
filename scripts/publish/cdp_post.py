#!/usr/bin/env python3
"""cdp_post.py — drive the real Chromium (media-browser) to post on a platform.

Pure-stdlib CDP client (no pip deps) so this runs on any host. The proven
path for acting as reverb256 on X/YouTube/LinkedIn/Facebook is the real
profile Chromium on :9222 (media-browser.service). It navigates to the
compose surface, types the post, and submits. Never fabricates API calls.

Usage:
  cdp_post.py <platform> <text> [media_path]
  Platforms: x, linkedin, facebook, youtube (studio)
"""
import base64
import hashlib
import json
import os
import socket
import struct
import sys
import time
import urllib.request

CDP_URL_DEFAULT = "http://127.0.0.1:9222"
CDP_BASE = os.environ.get("CDP_URL", CDP_URL_DEFAULT)


# ── Minimal RFC6455 websocket client (client frames only) ────────────────
def ws_connect(url):
    """Open a websocket to a ws:// CDP target URL (stdlib only)."""
    from urllib.parse import urlparse

    u = urlparse(url)
    host, port = u.hostname, u.port or 80
    path = u.path or "/"
    key = base64.b64encode(os.urandom(16)).decode()
    sock = socket.create_connection((host, port), timeout=15)
    req = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        "Sec-WebSocket-Version: 13\r\n\r\n"
    )
    sock.sendall(req.encode())
    # Read HTTP response headers
    buf = b""
    while b"\r\n\r\n" not in buf:
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionError("websocket handshake failed")
        buf += chunk
    if b"101" not in buf.split(b"\r\n", 1)[0]:
        raise ConnectionError(f"websocket upgrade rejected: {buf[:200]!r}")
    return sock


def ws_send(sock, payload: bytes):
    """Send a text frame (opcode 0x1)."""
    header = bytearray()
    header.append(0x81)  # FIN + text
    length = len(payload)
    if length < 126:
        header.append(0x80 | length)
    elif length < 65536:
        header.append(0x80 | 126)
        header += struct.pack(">H", length)
    else:
        header.append(0x80 | 127)
        header += struct.pack(">Q", length)
    mask = os.urandom(4)
    header += mask
    masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    sock.sendall(bytes(header) + masked)


def ws_recv(sock) -> bytes:
    """Read one frame; return unmasked payload (text/binary)."""
    def read(n):
        data = b""
        while len(data) < n:
            chunk = sock.recv(n - len(data))
            if not chunk:
                raise ConnectionError("socket closed")
            data += chunk
        return data

    b1, b2 = read(2)
    opcode = b1 & 0x0F
    length = b2 & 0x7F
    if length == 126:
        length = struct.unpack(">H", read(2))[0]
    elif length == 127:
        length = struct.unpack(">Q", read(8))[0]
    masked = b2 & 0x80
    mask = read(4) if masked else b""
    payload = read(length)
    if masked:
        payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    if opcode == 8:  # close
        raise ConnectionError("websocket closed by peer")
    return payload


# ── CDP helpers ────────────────────────────────────────────────────────────
class CDP:
    def __init__(self, ws_url):
        self.sock = ws_connect(ws_url)
        self.msg_id = 0

    def call(self, method, params=None):
        self.msg_id += 1
        mid = self.msg_id
        ws_send(self.sock, json.dumps({"id": mid, "method": method, "params": params or {}}).encode())
        while True:
            payload = ws_recv(self.sock)
            try:
                resp = json.loads(payload.decode())
            except Exception:
                continue
            if resp.get("id") == mid:
                if "error" in resp:
                    raise RuntimeError(f"CDP {method}: {resp['error']}")
                return resp.get("result", {})

    def js(self, expr):
        res = self.call("Runtime.evaluate", {"expression": expr, "returnByValue": True})
        return res.get("result", {}).get("value")

    def wait_selector(self, selector, timeout=25):
        deadline = time.time() + timeout
        s = json.dumps(selector)
        while time.time() < deadline:
            if self.js(f"!!document.querySelector({s}) && document.querySelector({s}).offsetParent !== null"):
                return True
            time.sleep(0.5)
        return False


def get_ws_url():
    with urllib.request.urlopen(f"{CDP_BASE}/json", timeout=5) as r:
        tabs = json.load(r)
    for t in tabs:
        if t.get("type") == "page":
            return t["webSocketDebuggerUrl"]
    raise RuntimeError("no page tab in CDP browser")


def insert_and_submit(cdp, text, textarea_selector, submit_selector=None, submit_text=None):
    # Focus the editor first
    cdp.js(
        f"const el = document.querySelector({json.dumps(textarea_selector)});"
        f"el.focus(); el.click();"
    )
    time.sleep(0.5)
    # Use native CDP Input.insertText — React editors respond to real input events
    cdp.call("Input.insertText", {"text": text})
    time.sleep(1)
    if submit_selector:
        # Click via CDP Input domain at the element's center (real pointer event)
        box = cdp.js(f"""(() => {{
            const b = document.querySelector({json.dumps(submit_selector)});
            if (!b) return null;
            const r = b.getBoundingClientRect();
            return JSON.stringify({{x: r.x + r.width/2, y: r.y + r.height/2, disabled: b.getAttribute('aria-disabled')}});
        }})()""")
        if not box:
            raise RuntimeError(f"submit selector not found: {submit_selector}")
        box = json.loads(box)
        if box.get("disabled") == "true":
            raise RuntimeError("submit button is disabled — text may not be in the editor")
        cdp.call("Input.dispatchMouseEvent", {"type": "mousePressed", "x": box["x"], "y": box["y"], "button": "left", "clickCount": 1})
        cdp.call("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": box["x"], "y": box["y"], "button": "left", "clickCount": 1})
    elif submit_text:
        cdp.js(
            "Array.from(document.querySelectorAll('[role=\"button\"], button'))"
            f".find(b => b.innerText.trim() === {json.dumps(submit_text)})?.click()"
        )
    return True


def post_x(cdp, text, media_path=None):
    cdp.js("location.href='https://x.com/compose/post'")
    time.sleep(4)
    if not cdp.wait_selector('[data-testid="tweetTextarea_0"]'):
        raise RuntimeError("X compose box not found — is the session logged in?")
    insert_and_submit(cdp, text, '[data-testid="tweetTextarea_0"]',
                      submit_selector='[data-testid="tweetButtonInline"]')
    # Verify submission: URL should leave /compose/post or the button disappears
    time.sleep(3)
    url = cdp.js("location.href") or ""
    button_gone = not cdp.js("!!document.querySelector('[data-testid=\"tweetButtonInline\"]')")
    if "/compose/post" in url or not button_gone:
        raise RuntimeError("X post did not submit — button still present, check login/compose state")
    return {"platform": "x", "status": "submitted"}


def post_linkedin(cdp, text, media_path=None):
    cdp.js("location.href='https://www.linkedin.com/feed/'")
    time.sleep(4)
    if not cdp.wait_selector('[role="textbox"]'):
        raise RuntimeError("LinkedIn composer not found — is the session logged in?")
    insert_and_submit(cdp, text, '[role="textbox"]', submit_text="Post")
    return {"platform": "linkedin", "status": "submitted"}


def post_facebook(cdp, text, media_path=None):
    cdp.js("location.href='https://www.facebook.com/'")
    time.sleep(4)
    if not cdp.wait_selector('[contenteditable="true"]'):
        raise RuntimeError("Facebook composer not found — is the session logged in?")
    insert_and_submit(cdp, text, '[contenteditable="true"]', submit_text="Post")
    return {"platform": "facebook", "status": "submitted"}


def post_youtube(cdp, text, media_path=None):
    cdp.js("location.href='https://studio.youtube.com/'")
    time.sleep(4)
    if not cdp.wait_selector("ytcp-uploads-dialog, ytcp-text-input", timeout=10):
        # Studio loaded but no dialog open — that's fine; navigate the Create button
        cdp.js("Array.from(document.querySelectorAll('ytcp-button')).find(b => b.innerText.includes('Create'))?.click()")
        time.sleep(2)
    return {"platform": "youtube", "status": "studio-open",
            "note": "Upload requires the media file; use the studio Create/Upload flow"}


PLATFORMS = {
    "x": post_x,
    "linkedin": post_linkedin,
    "facebook": post_facebook,
    "youtube": post_youtube,
}


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    platform = sys.argv[1].lower()
    text = sys.argv[2]
    media = sys.argv[3] if len(sys.argv) > 3 else None
    if platform not in PLATFORMS:
        print(f"unknown platform: {platform}", file=sys.stderr)
        sys.exit(2)
    cdp = CDP(get_ws_url())
    try:
        cdp.call("Page.enable")
        cdp.call("Runtime.enable")
        result = PLATFORMS[platform](cdp, text, media)
        print(json.dumps(result))
    finally:
        try:
            cdp.sock.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
