#!/usr/bin/env python3
"""
Capture a Suno generation request payload from the live browser session.
This script attaches to the existing CDP Chromium (port 9222) used by
the media-browser.service, navigates to suno.com/create, fills a dummy
form, clicks Create, and captures the POST /api/c/check request that
contains the generation parameters.
It saves the request JSON as a fixture under music/sunolocal/fixtures/.
"""
import json
import os
import sys
import time
import base64
import socket
import struct
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "music"))

# ---- Copied CDP and SunoTab classes from suno-gen.py (trimmed) ----
class CDPError(Exception):
    pass

class CDPConn:
    def __init__(self, host: str, port: int, path: str, timeout: float = 90):
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.sock.settimeout(timeout)
        self.buf = b""
        key = base64.b64encode(os.urandom(16)).decode()
        req = (
            f"GET /{path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            f"Upgrade: websocket\r\n"
            f"Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(req.encode())
        while b"\r\n\r\n" not in self.buf:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise CDPError("connection closed during handshake")
            self.buf += chunk
        head, _, self.buf = self.buf.partition(b"\r\n\r\n")
        if b" 101 " not in b" " + head.split(b"\r\n")[0]:
            raise CDPError(f"handshake failed: {head[:300]!r}")

    def _recv_exact(self, n: int) -> bytes:
        while len(self.buf) < n:
            chunk = self.sock.recv(1 << 20)
            if not chunk:
                raise CDPError("socket closed")
            self.buf += chunk
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def _recv_frame(self):
        b1, b2 = self._recv_exact(2)
        opcode = b1 & 0x0F
        masked = bool(b2 & 0x80)
        plen = b2 & 0x7F
        mask = b""
        if plen == 126:
            plen = struct.unpack(">H", self._recv_exact(2))[0]
        elif plen == 127:
            plen = struct.unpack(">Q", self._recv_exact(8))[0]
        if masked:
            mask = self._recv_exact(4)
        payload = self._recv_exact(plen)
        if masked:
            payload = bytes(p ^ mask[i % 4] for i, p in enumerate(payload))
        if opcode == 0x8:
            raise CDPError("peer sent close frame")
        if opcode == 0x9:  # ping -> pong
            self._send_frame(0xA, payload)
            return None
        if opcode == 0xA:  # pong
            return None
        return payload

    def _send_frame(self, opcode: int, payload: bytes) -> None:
        import os as _os
        b1 = 0x80 | opcode
        plen = len(payload)
        mask = _os.urandom(4)
        if plen < 126:
            header = bytes([b1, 0x80 | plen])
        elif plen < 65536:
            header = bytes([b1, 0x80 | 126]) + struct.pack(">H", plen)
        else:
            header = bytes([b1, 0x80 | 127]) + struct.pack(">Q", plen)
        masked = bytes(p ^ mask[i % 4] for i, p in enumerate(payload))
        self.sock.sendall(header + mask + masked)

    def send_json(self, obj: dict) -> None:
        self._send_frame(0x1, json.dumps(obj).encode())

    def recv_json(self) -> dict:
        while True:
            payload = self._recv_frame()
            if payload is not None:
                return json.loads(payload.decode())

class CDP:
    def __init__(self, port: int = 9222):
        import urllib.request
        ver = json.load(
            urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=15)
        )
        ws_url = ver["webSocketDebuggerUrl"]
        rest = ws_url.split("://", 1)[1]
        hostport, path = rest.split("/", 1)
        self.host, portnum = hostport.split(":")
        self.ws = CDPConn(self.host, int(portnum), path)
        self.msg_id = 0
        self.session_id = None
        self.events: list[dict] = []

    def call(self, method: str, params: dict | None = None, timeout: float = 90) -> dict:
        self.msg_id += 1
        payload = {"id": self.msg_id, "method": method, "params": params or {}}
        if self.session_id:
            payload["sessionId"] = self.session_id
        self.ws.send_json(payload)
        deadline = time.time() + timeout
        self.ws.sock.settimeout(max(1, deadline - time.time()))
        while time.time() < deadline:
            try:
                resp = self.ws.recv_json()
            except (socket.timeout, TimeoutError):
                raise CDPError(f"TIMEOUT waiting for response to {method}")
            if "method" in resp:
                self.events.append(resp)
            if resp.get("id") == self.msg_id:
                if "error" in resp:
                    raise CDPError(f"{method}: {resp['error']}")
                return resp.get("result", {})
        raise CDPError(f"TIMEOUT waiting for response to {method}")

    def wait_event(self, name: str, timeout_s: float = 90) -> dict | None:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            self.ws.sock.settimeout(max(1, deadline - time.time()))
            try:
                resp = self.ws.recv_json()
            except (socket.timeout, TimeoutError):
                return None
            self.events.append(resp)
            if resp.get("method") == name:
                return resp.get("params", {})
        return None

    def eval_js(self, expression: str, await_promise: bool = False,
                timeout: float = 90):
        res = self.call(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True,
             "awaitPromise": await_promise},
            timeout=timeout,
        )
        if "exceptionDetails" in res:
            raise JsError(res["exceptionDetails"])
        return res.get("result", {}).get("value")


class JsError(Exception):
    def __init__(self, details: dict):
        self.details = details
        text = details.get("text", "unknown")
        exc = details.get("exception", {})
        desc = exc.get("description", "") if isinstance(exc, dict) else ""
        self.msg = f"{text}: {desc}" if desc else text
        super().__init__(self.msg[:200])

class SunoTab:
    def __init__(self, cdp: CDP):
        self.cdp = cdp
        self.target_id = None
        self.attach_or_create()

    def _find_suno_target(self) -> dict | None:
        targets = self.cdp.call("Target.getTargets", timeout=30)["targetInfos"]
        for t in targets:
            if t["type"] == "page" and "suno.com" in t.get("url", ""):
                return t
        return None

    def attach_or_create(self) -> None:
        page = self._find_suno_target()
        if not page:
            tgt = self.cdp.call(
                "Target.createTarget", {"url": "https://suno.com/create"}, timeout=30
            )
            time.sleep(4)
            page = self._find_suno_target()
            if not page:
                raise CDPError("could not open a suno.com tab")
        att = self.cdp.call(
            "Target.attachToTarget",
            {"targetId": page["targetId"], "flatten": True},
            timeout=30,
        )
        self.cdp.session_id = att["sessionId"]
        self.target_id = page["targetId"]
        self.cdp.call("Page.enable", timeout=30)
        self.cdp.call("Runtime.enable", timeout=30)
        self.cdp.call("Network.enable", timeout=30)

    def navigate(self, url: str = "https://suno.com/create") -> None:
        self.cdp.call("Page.navigate", {"url": url}, timeout=30)
        self.cdp.wait_event("Page.loadEventFired", timeout_s=90)
        time.sleep(4)

    def safe_eval(self, expression: str, await_promise: bool = False,
                  timeout: float = 30):
        for _ in range(3):
            try:
                return self.cdp.eval_js(
                    expression, await_promise=await_promise, timeout=timeout
                )
            except CDPError as e:
                msg = str(e)
                if "navigated" in msg or "closed" in msg:
                    self.attach_or_create()
                    time.sleep(2)
                    continue
                raise
        raise CDPError("safe_eval failed after navigation recovery")

# ---- JS snippets for form fill and click ----
FILL_JS = """
(async (title, lyrics, style) => {
  const setNativeValue = (el, value) => {
    const proto = Object.getPrototypeOf(el);
    const desc = Object.getOwnPropertyDescriptor(proto, 'value');
    desc.set.call(el, value);
    el.dispatchEvent(new Event('input', {bubbles: true}));
    el.dispatchEvent(new Event('change', {bubbles: true}));
  };
  const sleep = (ms) => new Promise(r => setTimeout(r, ms));
  const out = {};
  const titleInputs = [...document.querySelectorAll('input[placeholder*=\"Song Title\"]')];
  if (!titleInputs.length) return JSON.stringify({err: 'no title input'});
  const tEl = titleInputs[0];
  tEl.focus(); tEl.select(); setNativeValue(tEl, title);
  out.title = tEl.value;
  await sleep(300);
  const lyricsEl = document.querySelector('[aria-label=\"Lyrics editor\"]');
  if (!lyricsEl) return JSON.stringify({err: 'no lyrics editor'});
  lyricsEl.focus();
  document.execCommand('selectAll', false, null);
  document.execCommand('insertText', false, lyrics);
  await sleep(1500);
  out.lyricsLen = lyricsEl.innerText.length;
  if (out.lyricsLen < lyrics.length * 0.9) {
    lyricsEl.focus();
    await sleep(500);
    document.execCommand('selectAll', false, null);
    document.execCommand('insertText', false, lyrics);
    await sleep(2000);
    out.lyricsLen = lyricsEl.innerText.length;
  }
  await sleep(300);
  const styleAreas = [...document.querySelectorAll('textarea')].filter(
    (t) => t.placeholder && t.placeholder.includes(',') &&
           !t.getAttribute('aria-label') &&
           !t.placeholder.includes('Describe')
  );
  if (!styleAreas.length) return JSON.stringify({err: 'no style textarea'});
  const sEl = styleAreas[0];
  sEl.focus(); setNativeValue(sEl, style);
  out.styleLen = sEl.value.length;
  return JSON.stringify(out);
})
"""

CLICK_COORDS_JS = """
(() => {
  const btn = [...document.querySelectorAll('button')].find(
    (b) => (b.getAttribute('aria-label') || '') === 'Create song'
  );
  if (!btn) return JSON.stringify({err: 'no Create button'});
  btn.scrollIntoView({block: 'center'});
  const r = btn.getBoundingClientRect();
  if (r.width === 0 || r.height === 0) return JSON.stringify({err: 'Create button off-screen'});
  return JSON.stringify({x: r.x + r.width / 2, y: r.y + r.height / 2});
})
"""

def detect_captcha_wall(tab: SunoTab) -> bool:
    for ev in tab.cdp.events:
        if ev.get("method") != "Network.responseReceived":
            continue
        p = ev.get("params", {})
        resp = p.get("response", {})
        url = resp.get("url", "")
        if "c/check" not in url:
            continue
        rid = p.get("requestId")
        try:
            body = tab.cdp.call(
                "Network.getResponseBody", {"requestId": rid}, timeout=15
            ).get("body", "")
        except CDPError:
            body = ""
        if '"required": true' in body or '"required":true' in body:
            return True
    return False

def main():
    # Use an existing test track
    track_dir = REPO / "music" / "lyrics" / "chill-lounge" / "amber-hour"
    title_file = track_dir / "title.txt"
    lyrics_file = track_dir / "lyrics.suno.txt"
    if not title_file.exists() or not lyrics_file.exists():
        print(f"ERROR: missing track files in {track_dir}", file=sys.stderr)
        sys.exit(1)
    title = title_file.read_text().strip()
    lyrics = lyrics_file.read_text().strip()
    # Style prompt: we can take a generic one or from prompts directory
    style_prompt = (REPO / "music" / "prompts" / "chill-lounge.md").read_text()
    # Extract the style field from the prompt (simple: first non-empty line)
    style_lines = [l.strip() for l in style_prompt.splitlines() if l.strip() and not l.startswith("#")]
    style = style_lines[0] if style_lines else "chillout, downtempo, ambient"
    print(f"Title: {title}")
    print(f"Lyrics length: {len(lyrics)}")
    print(f"Style: {style}")

    cdp = CDP(9222)
    tab = SunoTab(cdp)
    tab.navigate("https://suno.com/create")
    # Fill form
    fill_js = f"({FILL_JS})({json.dumps(title)}, {json.dumps(lyrics)}, {json.dumps(style)})"
    fill_result = tab.safe_eval(fill_js, await_promise=True, timeout=30)
    fill_data = json.loads(fill_result)
    if "err" in fill_data:
        print(f"FORM FILL ERROR: {fill_data['err']}", file=sys.stderr)
        sys.exit(1)
    print(f"Filled: title={fill_data.get('title')} lyricsLen={fill_data.get('lyricsLen')} styleLen={fill_data.get('styleLen')}")
    # Click Create
    box = json.loads(tab.safe_eval(CLICK_COORDS_JS, timeout=30))
    if "err" in box:
        print(f"CLICK COORDS ERROR: {box['err']}", file=sys.stderr)
        sys.exit(1)
    x, y = int(box["x"]), int(box["y"])
    # Mouse down/up via CDP (not strictly needed; we also do synthetic click)
    cdp.call("Input.dispatchMouseEvent",
             {"type": "mouseMoved", "x": x, "y": y, "button": "left", "clickCount": 1},
             timeout=30)
    time.sleep(0.1)
    cdp.call("Input.dispatchMouseEvent",
             {"type": "mousePressed", "x": x, "y": y, "button": "left", "clickCount": 1},
             timeout=30)
    time.sleep(0.05)
    cdp.call("Input.dispatchMouseEvent",
             {"type": "mouseReleased", "x": x, "y": y, "button": "left", "clickCount": 1},
             timeout=30)
    # Synthetic click to fire handler
    click_el = """
    (() => {
      const btn = [...document.querySelectorAll('button')].find(
        (b) => (b.getAttribute('aria-label') || '') === 'Create song'
      );
      if (!btn) return 'no button';
      btn.click();
      return 'clicked';
    })()
    """
    click_result = tab.safe_eval(click_el, timeout=30)
    print(f"Click result: {click_result}")
    # Wait a bit then look for the generation request
    # We'll capture the Network.responseReceived events for /api/c/check
    deadline = time.time() + 30
    seen = False
    capture_dir = REPO / "music" / "sunolocal" / "fixtures"
    capture_dir.mkdir(parents=True, exist_ok=True)
    fixture_path = capture_dir / "suno_generate_request.json"
    while time.time() < deadline:
        for ev in tab.cdp.events:
            if ev.get("method") != "Network.responseReceived":
                continue
            p = ev.get("params", {})
            resp = p.get("response", {})
            url = resp.get("url", "")
            if "/api/c/check" not in url:
                continue
            rid = p.get("requestId")
            try:
                body = tab.cdp.call(
                    "Network.getResponseBody", {"requestId": rid}, timeout=10
                ).get("body", "")
            except CDPError:
                body = ""
            if body:
                try:
                    data = json.loads(body)
                    # Check if this is a generation request (has ctype: generation)
                    if data.get("ctype") == "generation":
                        # Save the request payload
                        with open(fixture_path, "w") as f:
                            json.dump(data, f, indent=2)
                        print(f"CAPTURED generation request -> {fixture_path}")
                        seen = True
                        break
                except json.JSONDecodeError:
                    pass
        if seen:
            break
        time.sleep(2)
    if not seen:
        print("WARNING: Did not capture a generation request; maybe captcha wall or timeout.")
        # Check for captcha wall
        if detect_captcha_wall(tab):
            print("CAPTCHA WALL DETECTED: Suno requires captchet; cannot proceed without human solve.")
            sys.exit(3)
        else:
            print("No captcha wall but no request captured.")
            sys.exit(1)
    print("Done.")

if __name__ == "__main__":
    main()