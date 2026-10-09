#!/usr/bin/env python3
"""Suno generation + Studio export for the genre-generic music pipeline.

This is the one genuinely new component of the music lane (card
t_3fa2d716). It drives suno.com through Chrome DevTools Protocol
against the logged-in browser session — Suno has no official API, so
the browser IS the API.

WHAT IT DOES
  1. Reads the genre registry (music/genres.yaml) and resolves
     genre -> style prompt (from music/prompts/<genre>.md) + lyrics
     (from music/lyrics/<genre>/<slug>/lyrics.suno.txt). No genre is
     ever hardcoded here; adding a genre is a data change only.
  2. Runs gate_quota BEFORE generating (hard stop at the ledger's
     hard_stop_at; warn at warn_at).
  3. Attaches to the CDP Chromium on :9222, opens suno.com/create,
     fills Title / Lyrics / Styles via native setter + execCommand,
     and clicks Create (synthetic btn.click() fires the real
     handler: POST /api/c/check {"ctype":"generation"} — verified
     live).
  4. Polls for the completed clip through TWO independent
     channels:
       a. the page's OWN studio-api responses, captured at the
          CDP Network layer (the page's app sends auth that
          bare in-page fetches lack — free-tier endpoints like
          /api/project/me answer 401 to a plain cookie fetch
          but 200 to the app's own calls);
       b. the DOM: clip cards on the create page carry
          <audio src> elements, so a finished generation is
          readable without any API call.
     Polling is navigation-resistant: each probe is one short
     eval; if the tab bounces to sign-in mid-generation, the
     script returns to /create (the session cookie is still
     valid) and keeps polling.
     CAPTCHA WALL (verified live, free tier): Suno answers
     /api/c/check with {"required": true, "captcha_version": 2}
     and loads hCaptcha assets, but the widget never mounts in
     the automation context, so generation never proceeds. The
     script detects this and exits 3 with an honest report
     instead of looping or faking a result. Resolve the captcha
     in the live browser and re-run, or use a Premier session.
  5. EXPORTS THROUGH SUNO STUDIO ONLY. The standard download button
     is capped at 60/month on Premier and does not exist on free
     tier; this script never touches it. Audio is fetched through
     the clip's own audio_url inside the authenticated page context
     (the Studio path), then carried out over CDP as base64.
  6. Records the generation into the quota ledger (credits used,
     studio exports) and writes a manifest per track.

FAILURE RULE: on any failure it exits non-zero and NEVER falls back
to the standard download button. There is no such code path. The
script NEVER fabricates a result.

Usage:
  # real run (fills form, clicks Create, exports, records ledger)
  python3 music/suno-gen.py --genre chill-lounge --track-dir music/lyrics/chill-lounge/amber-hour

  # fill-only (verify the form mechanics without spending a credit)
  python3 music/suno-gen.py --genre chill-lounge --track-dir ... --fill-only

  # dry (registry + quota gate only, no browser)
  python3 music/suno-gen.py --genre chill-lounge --track-dir ... --dry

Exit codes: 0 success, 1 gate/generation failure, 2 usage/registry
error, 3 captcha wall (generation submitted but Suno requires a
human-solved captcha).
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import re
import socket
import struct
import sys
import time
import urllib.request
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("FATAL: PyYAML required (pip install pyyaml)", file=sys.stderr)
    raise

REPO = Path(__file__).resolve().parents[1]
GENRES_YAML = REPO / "music" / "genres.yaml"
LANES_YAML = REPO / "music" / "lanes.yaml"
LEDGER = REPO / "music" / "quota-ledger.json"
PROMPTS_DIR = REPO / "music" / "prompts"
OUTPUT_DIR = REPO / "music" / "generated"

# The logged-in CDP Chromium the pipeline already runs
# (scripts/browser/start-media-browser.sh, systemd media-browser.service).
CDP_PORT = int(os.environ.get("SUNO_CDP_PORT", "9222"))
CREATE_URL = "https://suno.com/create"
API_BASE = "https://studio-api-prod.suno.com"


# --------------------------------------------------------------------------
# 1. Registry + quota gate (data layer; no browser needed)
# --------------------------------------------------------------------------

def load_registry() -> dict:
    if not GENRES_YAML.exists():
        raise SystemExit(
            f"FATAL: genre registry missing at {GENRES_YAML}. "
            "Build the data layer first (card: genre + lane registries)."
        )
    with open(GENRES_YAML) as f:
        return yaml.safe_load(f)


def resolve_genre(registry: dict, genre: str) -> dict:
    genres = (registry.get("genres") or {})
    if genre not in genres:
        raise SystemExit(
            f"FATAL: genre '{genre}' not in registry. Known: {sorted(genres)}"
        )
    return genres[genre]


def load_style_prompt(genre: str) -> str:
    """Pull the Suno style field out of the genre's prompt template.
    The template is data (music/prompts/<genre>.md); this parser only
    extracts the fenced '## Style field' block."""
    path = PROMPTS_DIR / f"{genre}.md"
    if not path.exists():
        raise SystemExit(f"FATAL: prompt template missing: {path}")
    text = path.read_text()
    m = re.search(r"## Style field.*?```text\n(.*?)```", text, re.S)
    if not m:
        raise SystemExit(f"FATAL: no '## Style field' block in {path}")
    return m.group(1).strip()


def load_track(track_dir: Path, instrumental: bool = False) -> dict:
    """Load a track's title + Suno-tagged lyrics from the lyrics stage.
    Rejects any sheet whose provenance header is not human-original.

    instrumental=True is for the genres whose own templates specify no vocals
    (chiptune, the elementals, commentary beds, epic-orchestral-boss and others
    - 8 of the 12 genre templates). Suno's instrumental path is an EMPTY lyrics
    box, so there is no sheet to load and none is required. Requiring one was
    the reason those templates could never be validated: the generator demanded
    a human-original lyric sheet for a genre that has no lyrics.
    """
    title_file = track_dir / "title.txt"
    manifest = track_dir / "manifest.json"
    if not title_file.exists():
        raise SystemExit(f"FATAL: track dir incomplete (no title.txt): {track_dir}")

    if instrumental:
        meta = json.loads(manifest.read_text()) if manifest.exists() else {}
        # A marker, not a guess: a missing lyric sheet could equally mean "not
        # written yet", and silently rendering an instrumental for a genre that
        # is supposed to sing would be worse than stopping.
        if not (meta.get("instrumental") or (track_dir / "instrumental").exists()):
            raise SystemExit(
                f"FATAL: --instrumental given but {track_dir} is not marked instrumental.\n"
                "       Add \"instrumental\": true to manifest.json, or create an "
                "empty file named 'instrumental' in the track dir."
            )
        title = title_file.read_text().strip()
        return {"title": title, "lyrics": "", "manifest": meta, "sheet": ""}

    suno_sheet = track_dir / "lyrics.suno.txt"
    if not suno_sheet.exists():
        raise SystemExit(f"FATAL: track dir incomplete: {track_dir}")
    raw = suno_sheet.read_text()
    headers = [ln for ln in raw.splitlines() if ln.startswith("#")]
    if not any("provenance: human-original" in h for h in headers):
        raise SystemExit(
            f"FATAL: {suno_sheet} lacks a 'provenance: human-original' header. "
            "Suno-generated lyrics are not copyrightable and are rejected here."
        )
    lyrics = "\n".join(
        ln for ln in raw.splitlines() if not ln.startswith("#")
    ).strip()
    if not lyrics:
        raise SystemExit(f"FATAL: empty lyric sheet: {suno_sheet}")
    title = title_file.read_text().strip()
    meta = {}
    if manifest.exists():
        meta = json.loads(manifest.read_text())
    return {"title": title, "lyrics": lyrics, "manifest": meta, "sheet": raw}


def load_ledger() -> dict:
    if not LEDGER.exists():
        raise SystemExit(f"FATAL: quota ledger missing at {LEDGER}")
    with open(LEDGER) as f:
        return json.load(f)


def gate_quota(ledger: dict) -> dict:
    """gate_quota: executable check of the quota ledger BEFORE any
    generation or export. Hard stop at hard_stop_at; warn at warn_at.
    Returns the (possibly updated) ledger."""
    used = ledger.get("standard_downloads_used", 0)
    limit = ledger.get("standard_downloads_limit", 60)
    warn_at = ledger.get("warn_at", 55)
    hard_stop_at = ledger.get("hard_stop_at", 58)
    period = ledger.get("period", dt.date.today().strftime("%Y-%m"))

    # period rollover: a new month resets the standard-download counter
    today = dt.date.today().strftime("%Y-%m")
    if period != today:
        ledger["period"] = today
        ledger["standard_downloads_used"] = 0
        used = 0

    if used >= hard_stop_at:
        raise SystemExit(
            f"FATAL gate_quota: standard downloads {used}/{limit} >= hard stop "
            f"{hard_stop_at}. Route exports through Studio or halt. "
            "This run did not generate."
        )
    if used >= warn_at:
        print(f"WARN gate_quota: standard downloads {used}/{limit} >= warn_at {warn_at}")
    return ledger


def record_generation(ledger: dict, track: dict, genre: str, clip: dict,
                      audio_path: Path, studio_export: bool) -> dict:
    """Record a generation into the quota ledger. Studio exports are
    unlimited and do NOT touch the standard-download counter."""
    ledger.setdefault("generations", [])
    entry = {
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
        "genre": genre,
        "title": track["title"],
        "clip_id": clip.get("id"),
        "audio_path": str(audio_path),
        "audio_bytes": audio_path.stat().st_size if audio_path.exists() else 0,
        "studio_export": studio_export,
        "standard_download_used": False,  # Studio path: never a standard download
        "credits_used": 1,
        "source": clip.get("source", "unknown"),
    }
    ledger["generations"].append(entry)
    ledger["credits_used"] = ledger.get("credits_used", 0) + 1
    if studio_export:
        ledger["studio_exports"] = ledger.get("studio_exports", 0) + 1
    with open(LEDGER, "w") as f:
        json.dump(ledger, f, indent=2)
    return entry


# --------------------------------------------------------------------------
# 2. Zero-dependency CDP client (RFC 6455, masked client frames)
# --------------------------------------------------------------------------

class CDPError(Exception):
    pass


class CDPConn:
    """One WebSocket connection to a CDP endpoint. Handshake is sent
    WITHOUT an Origin header (Chromium rejects foreign origins on the
    browser WS unless --remote-allow-origins is set); client frames
    are masked per RFC 6455."""

    def __init__(self, host: str, port: int, path: str, timeout: float = 90):
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.sock.settimeout(timeout)
        self.buf = b""
        import os as _os
        key = base64.b64encode(_os.urandom(16)).decode()
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
    """Browser-level CDP session on the debugging port. Every
    event received is buffered in .events so callers can scan
    network traffic the page itself generates."""

    def __init__(self, port: int = CDP_PORT):
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


# --------------------------------------------------------------------------
# 3. Suno browser automation
# --------------------------------------------------------------------------

class SunoTab:
    """Attached to the suno.com page target. Re-attaches on navigation."""

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
                "Target.createTarget", {"url": CREATE_URL}, timeout=30
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

    def navigate(self, url: str = CREATE_URL) -> None:
        self.cdp.call("Page.navigate", {"url": url}, timeout=30)
        self.cdp.wait_event("Page.loadEventFired", timeout_s=90)
        time.sleep(4)

    def safe_eval(self, expression: str, await_promise: bool = False,
                  timeout: float = 30):
        """Eval with navigation recovery: if the page navigated mid-eval,
        re-attach and retry. JS exceptions are wrapped as
        JsException so callers can inspect the message."""
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


class JsError(Exception):
    """The page-side expression threw. .msg holds the in-page
    message (e.g. 'Failed to fetch'), .details the full
    CDP exceptionDetails dict."""

    def __init__(self, details: dict):
        self.details = details
        text = details.get("text", "unknown")
        exc = details.get("exception", {})
        desc = exc.get("description", "") if isinstance(exc, dict) else ""
        self.msg = f"{text}: {desc}" if desc else text
        super().__init__(self.msg[:200])


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
  const titleInputs = [...document.querySelectorAll('input[placeholder*="Song Title"]')];
  if (!titleInputs.length) return JSON.stringify({err: 'no title input'});
  const tEl = titleInputs[0];
  tEl.focus(); tEl.select(); setNativeValue(tEl, title);
  out.title = tEl.value;
  await sleep(300);
  const lyricsEl = document.querySelector('[aria-label="Lyrics editor"]');
  if (!lyricsEl) return JSON.stringify({err: 'no lyrics editor'});
  lyricsEl.focus();
  document.execCommand('selectAll', false, null);
  document.execCommand('insertText', false, lyrics);
  // let the controlled component flush the insert, then verify
  await sleep(1500);
  out.lyricsLen = lyricsEl.innerText.length;
  if (out.lyricsLen < lyrics.length * 0.9) {
    // React may not have flushed yet: re-focus and retry once
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
           !t.placeholder.includes('Describe'));
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
    (b) => (b.getAttribute('aria-label') || '') === 'Create song');
  if (!btn) return JSON.stringify({err: 'no Create button'});
  btn.scrollIntoView({block: 'center'});
  const r = btn.getBoundingClientRect();
  if (r.width === 0 || r.height === 0) return JSON.stringify({err: 'Create button off-screen'});
  return JSON.stringify({x: r.x + r.width / 2, y: r.y + r.height / 2});
})()
"""

# DOM poll. Finished generations render on the create page as clip
# cards carrying <audio src> elements. On Suno the generated card
# always echoes the TITLE inside the clip itself, next to its own
# audio element — so the match must live INSIDE an audio-bearing
# subtree, and must be inside the lyrics editor or a clip card,
# never a header/nav ancestor (the header text "HomeExplore
# CreateStudioLibrary" also contains "Create" and the page's
# root div contains the whole page). Excluding the input/form
# avoids matching the still-filled title field before submit.
DOM_POLL_JS = """
((title) => {
  const out = {href: location.href,
               generating: /generat/i.test(document.body.innerText),
               clips: [], anyAudio: []};
  document.querySelectorAll('audio[src]').forEach((a) => out.anyAudio.push(a.src));
  const navLabels = new Set(['home','explore','create','studio','library']);
  const lowers = title.toLowerCase();
  const tokens = lowers.split(/[^a-z0-9]+/).filter((w) => w.length >= 4 && !navLabels.has(w));
  if (!tokens.length) return JSON.stringify({...out, err: 'title has no usable tokens'});
  const audioNodes = [...document.querySelectorAll('audio[src]')];
  audioNodes.forEach((audio) => {
    const card = audio.closest('[class*="clip"], [class*="card"], [class*="item"]') || audio.parentElement;
    if (!card) return;
    // the whole audio-bearing subtree must NOT contain the form
    if (card.querySelector('input[placeholder*="Song Title"], [aria-label="Lyrics editor"]')) return;
    const ct = (card.textContent || '').trim().toLowerCase();
    if (!ct || !tokens.every((w) => ct.includes(w))) return;
    // find the smallest text node carrying the title inside the card
    let titleText = '';
    [...card.querySelectorAll('*')].forEach((el) => {
      if (titleText) return;
      if (el.children.length > 0) return;
      const t = (el.textContent || '').trim();
      const tl = t.toLowerCase();
      if (t && tokens.every((w) => tl.includes(w))) titleText = t.slice(0, 80);
    });
    out.clips.push({title: titleText || title, audio: audio.src});
  });
  return JSON.stringify(out);
})
"""

# Studio export: fetch the clip audio inside the authenticated page
# (the Studio path — the same fetch the site's own download control
# uses), then carry the bytes out as base64. Never the standard
# download button.
FETCH_AUDIO_JS = """
(async (url) => {
  const r = await fetch(url, {credentials: 'include'});
  if (!r.ok) return JSON.stringify({err: 'HTTP ' + r.status});
  const buf = await r.arrayBuffer();
  const bytes = new Uint8Array(buf);
  let bin = '';
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    bin += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
  }
  return JSON.stringify({b64: btoa(bin), mime: r.headers.get('content-type') || 'audio/mpeg'});
})
"""


def extract_clip_from_body(body: str, title: str) -> dict | None:
    """Walk a studio-api JSON response for an object whose title
    matches and that carries an audio/video URL."""
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return None
    found: list[dict] = []

    def scan(obj):
        if isinstance(obj, dict):
            if title.lower() in str(obj.get("title") or "").lower():
                audio = (
                    obj.get("audio_url")
                    or obj.get("video_url")
                    or (obj.get("metadata") or {}).get("audio_url")
                )
                if audio:
                    found.append({
                        "id": obj.get("id"),
                        "title": obj.get("title"),
                        "audio_url": audio,
                        "status": obj.get("status"),
                    })
            for v in obj.values():
                scan(v)
        elif isinstance(obj, list):
            for v in obj:
                scan(v)

    scan(data)
    return found[0] if found else None


def click_create(tab: SunoTab) -> dict:
    """Click the Create button.

    VERIFIED MECHANICS (live, 2026-10-08):
      - A synthetic btn.click() from JS fires the real handler
        (POST /api/c/check {"ctype":"generation"}).
      - Suno then answers {"required": true, "captcha_version": 2}
        and loads hCaptcha challenge assets. On free tier the
        captcha widget does not mount in the automation context
        and generation never proceeds — this is a hard wall,
        not a retryable failure. poll_for_clip detects it and
        raises CaptchaWall so the caller can report it honestly.
    """
    box = json.loads(tab.safe_eval(CLICK_COORDS_JS, timeout=30))
    if "err" in box:
        raise CDPError(f"create click: {box['err']}")
    time.sleep(1)
    box = json.loads(tab.safe_eval(CLICK_COORDS_JS, timeout=30))
    if "err" in box:
        raise CDPError(f"create click (2nd read): {box['err']}")
    x, y = int(box["x"]), int(box["y"])
    cdp = tab.cdp
    cdp.call("Input.dispatchMouseEvent",
             {"type": "mouseMoved", "x": x, "y": y, "button": "left", "clickCount": 1},
             timeout=30)
    time.sleep(0.3)
    cdp.call("Input.dispatchMouseEvent",
             {"type": "mousePressed", "x": x, "y": y, "button": "left", "clickCount": 1},
             timeout=30)
    time.sleep(0.1)
    cdp.call("Input.dispatchMouseEvent",
             {"type": "mouseReleased", "x": x, "y": y, "button": "left", "clickCount": 1},
             timeout=30)
    # The trusted mouse events alone do not fire the handler in
    # the automation context; the synthetic click does.
    click_el = """
    (() => {
      const btn = [...document.querySelectorAll('button')].find(
        (b) => (b.getAttribute('aria-label') || '') === 'Create song');
      if (!btn) return 'no button';
      btn.click();
      return 'clicked';
    })()
    """
    result = tab.safe_eval(click_el, timeout=30)
    return {"x": x, "y": y, "click_result": result}


class CaptchaWall(Exception):
    """Suno answered /api/c/check with captcha required and the
    widget never mounted — generation cannot proceed without a
    human solving the captcha. This is a hard wall, not a
    transient failure."""


def detect_captcha_wall(tab: SunoTab) -> bool:
    """True when /api/c/check answered captcha-required and no
    generation followed. Reads the captured c/check response."""
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


def poll_for_clip(tab: SunoTab, title: str, timeout_s: float = 300,
                  on_log=print) -> dict:
    """Poll for the completed clip through two channels: the page's own
    studio-api responses (captured at the CDP Network layer, read via
    Network.getResponseBody — the app's calls carry auth that bare
    in-page fetches lack) and the DOM (clip cards carry <audio src>).
    Navigation-resistant: if the tab bounces to sign-in mid-generation,
    return to /create (the session cookie is still valid) and continue."""
    deadline = time.time() + timeout_s
    started = time.time()
    last_log = 0.0
    seen_rids: set[str] = set()
    wall_checked = False
    while time.time() < deadline:
        # --- captcha wall: /api/c/check answered required ---
        if not wall_checked and time.time() - started > 15:
            wall_checked = True
            if detect_captcha_wall(tab):
                raise CaptchaWall(
                    "Suno /api/c/check returned captcha required "
                    "(captcha_version 2). The hCaptcha widget does "
                    "not mount in the automation context, so "
                    "generation cannot proceed without a human "
                    "solving the captcha. This is a hard wall on "
                    "the free-tier session, not a retryable error."
                )
        # --- channel A: DOM poll ---
        dom = None
        try:
            raw = tab.safe_eval("(" + DOM_POLL_JS + ")(" + json.dumps(title) + ")", timeout=25)
            dom = json.loads(raw)
        except CDPError as e:
            on_log(f"  dom poll err: {str(e)[:80]}")
        except JsError as e:
            on_log(f"  dom poll js err: {e.msg[:80]}")
        if dom:
            if "sign-in" in dom.get("href", ""):
                on_log("  tab bounced to sign-in; returning to /create (session cookie still valid)")
                tab.navigate(CREATE_URL)
                continue
            for clip in dom.get("clips", []):
                on_log(f"  DOM clip card: '{clip['title'][:40]}' with audio element")
                return {"id": "dom", "title": clip["title"],
                        "audio_url": clip["audio"], "status": "dom",
                        "source": "dom"}
        # --- channel B: the page's own studio-api responses ---
        for ev in tab.cdp.events:
            if ev.get("method") != "Network.responseReceived":
                continue
            p = ev.get("params", {})
            resp = p.get("response", {})
            url = resp.get("url", "")
            if "studio-api" not in url:
                continue
            rid = p.get("requestId")
            if rid is None or rid in seen_rids:
                continue
            seen_rids.add(rid)
            body = ""
            try:
                body = tab.cdp.call(
                    "Network.getResponseBody", {"requestId": rid}, timeout=15
                ).get("body", "")
            except CDPError:
                pass
            if not body or title.lower() not in body.lower():
                continue
            clip = extract_clip_from_body(body, title)
            if clip:
                on_log(f"  API response {url[:70]} [{resp.get('status')}] carries the clip")
                clip["source"] = "api"
                return clip
        if time.time() - last_log > 30:
            n_api = len(seen_rids)
            gen = dom.get("generating") if dom else None
            on_log(f"  t+{int(time.time()-started)}s: dom_clips={len(dom.get('clips', [])) if dom else '?'} "
                   f"anyAudio={len(dom.get('anyAudio', [])) if dom else '?'} "
                   f"api_responses={n_api} generating={gen}")
            last_log = time.time()
        time.sleep(6)
    raise CDPError(f"no completed clip for '{title}' within {timeout_s}s")


def export_audio_studio(tab: SunoTab, clip: dict) -> tuple[bytes, str]:
    """Export through the Studio path: fetch the clip's audio_url inside
    the authenticated page and carry the bytes out over CDP. NEVER the
    standard download button."""
    url = clip.get("audio_url") or clip.get("video_url")
    if not url:
        raise CDPError("clip has no audio_url or video_url to export")
    raw = tab.safe_eval(f"({FETCH_AUDIO_JS})({json.dumps(url)})",
                        await_promise=True, timeout=120)
    data = json.loads(raw)
    if "err" in data:
        raise CDPError(f"studio export fetch failed: {data['err']}")
    return base64.b64decode(data["b64"]), data.get("mime", "audio/mpeg")


# --------------------------------------------------------------------------
# 4. Orchestration
# --------------------------------------------------------------------------

def cmd_generate(args) -> int:
    registry = load_registry()
    genre_entry = resolve_genre(registry, args.genre)
    style = load_style_prompt(args.genre)
    track = load_track(args.track_dir, instrumental=args.instrumental)
    ledger = load_ledger()

    print(f"genre:    {args.genre} (family {genre_entry.get('family')})")
    print(f"title:    {track['title']}")
    print(f"style:    {len(style)} chars from prompts/{args.genre}.md")
    if args.instrumental:
        # Suno's instrumental path is an empty lyrics box. Say that plainly, so
        # a reader of the log does not read the blank as a missing sheet.
        print("lyrics:   (none - instrumental, the lyrics box is left empty)")
    else:
        print(f"lyrics:   {len(track['lyrics'])} chars, provenance-checked")

    # gate_quota BEFORE any generation or export
    ledger = gate_quota(ledger)
    print(f"quota:    standard {ledger.get('standard_downloads_used')}/"
          f"{ledger.get('standard_downloads_limit')} "
          f"(warn {ledger.get('warn_at')}, hard-stop {ledger.get('hard_stop_at')})")
    print(f"          credits used so far: {ledger.get('credits_used')}, "
          f"studio exports: {ledger.get('studio_exports')}")

    if args.dry:
        print("dry run: registry + quota gate passed; no browser, no generation")
        return 0

    cdp = CDP(CDP_PORT)
    tab = SunoTab(cdp)
    tab.navigate(CREATE_URL)

    fill = tab.safe_eval(
        "(" + FILL_JS + ")(" + json.dumps(track["title"]) + ", "
        + json.dumps(track["lyrics"]) + ", " + json.dumps(style) + ")",
        await_promise=True, timeout=60,
    )
    fill_data = json.loads(fill)
    if "err" in fill_data:
        raise CDPError(f"form fill failed: {fill_data['err']}")
    if args.instrumental:
        # The inverse check: for an instrumental the editor must be EMPTY. If
        # something left text in it - a stale form, a previous run - Suno would
        # sing it, and the run would produce a vocal track for a genre that has
        # none.
        if fill_data.get("lyricsLen", 0) != 0:
            raise CDPError(
                f"instrumental run but the lyrics editor holds "
                f"{fill_data.get('lyricsLen')} chars - clear it and retry"
            )
    elif fill_data.get("lyricsLen", 0) < len(track["lyrics"]) * 0.9:
        raise CDPError(
            f"lyrics fill incomplete: editor holds {fill_data.get('lyricsLen')} "
            f"of {len(track['lyrics'])} chars"
        )
    print(f"filled:   title='{fill_data['title']}' "
          f"lyrics={fill_data['lyricsLen']} chars style={fill_data['styleLen']} chars")

    if args.fill_only:
        print("fill-only: form verified on the live page; not clicking Create")
        return 0

    click = click_create(tab)
    print(f"create:   trusted CDP click at ({click['x']}, {click['y']}), "
          f"handler fired: {click.get('click_result')}")

    try:
        clip = poll_for_clip(tab, track["title"], timeout_s=args.timeout)
    except CaptchaWall as e:
        print(f"CAPTCHA WALL: {e}", file=sys.stderr)
        print("The generation was submitted but Suno requires a",
              file=sys.stderr)
        print("captcha that cannot be solved in automation. No clip",
              file=sys.stderr)
        print("was produced; no credits were consumed; nothing was",
              file=sys.stderr)
        print("exported. Resolve the captcha in the live browser and",
              file=sys.stderr)
        print("re-run, or use a Premier session where the check may",
              file=sys.stderr)
        print("not gate generation.", file=sys.stderr)
        return 3
    print(f"clip:     id={clip.get('id')} status={clip.get('status')} source={clip.get('source')}")

    audio, mime = export_audio_studio(tab, clip)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ext = ".mp3" if "mpeg" in mime else ".wav"
    slug = re.sub(r"[^a-z0-9]+", "-", track["title"].lower()).strip("-")
    audio_path = OUTPUT_DIR / f"{args.genre}-{slug}{ext}"
    audio_path.write_bytes(audio)
    print(f"export:   {len(audio)} bytes via STUDIO path -> {audio_path}")
    print(f"          mime={mime} (standard download button NEVER used)")

    entry = record_generation(ledger, track, args.genre, clip, audio_path,
                              studio_export=True)

    manifest = {
        "schema": "music/suno-generation-manifest v1",
        "generated_at": entry["ts"],
        "genre": args.genre,
        "title": track["title"],
        "clip_id": clip.get("id"),
        "audio_path": str(audio_path),
        "audio_bytes": len(audio),
        "mime": mime,
        "export_path": "studio",
        "standard_download_used": False,
        "style_prompt_chars": len(style),
        "lyrics_chars": len(track["lyrics"]),
        "cdp_port": CDP_PORT,
        "clip_source": clip.get("source"),
    }
    manifest_path = OUTPUT_DIR / f"{args.genre}-{slug}.manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"ledger:   generation recorded (credits {entry['credits_used']}, "
          f"studio export)")
    print(f"manifest: {manifest_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Suno CDP generation + Studio export")
    ap.add_argument("--genre", required=True, help="genre key from music/genres.yaml")
    ap.add_argument("--track-dir", required=True, type=Path,
                    help="lyrics-stage track dir (title.txt + lyrics.suno.txt)")
    ap.add_argument("--instrumental", action="store_true",
                    help="no vocals: the lyrics box is left empty (Suno's "
                         "instrumental path). The track dir must be marked "
                         "instrumental in manifest.json.")
    ap.add_argument("--fill-only", action="store_true",
                    help="fill the form and stop before Create (no credit spent)")
    ap.add_argument("--dry", action="store_true",
                    help="registry + quota gate only, no browser")
    ap.add_argument("--timeout", type=float, default=300,
                    help="seconds to wait for generation completion (default 300)")
    args = ap.parse_args(argv)
    try:
        return cmd_generate(args)
    except SystemExit:
        raise
    except Exception as e:
        print(f"FATAL: {type(e).__name__}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
