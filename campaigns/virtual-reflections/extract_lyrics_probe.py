#!/usr/bin/env python3
"""Probe the Suno API via the running CDP Chromium to extract
lyrics + metadata for each Virtual Reflections track.

Research findings (2026-10-09):
- paperfoot/suno-cli API_INTELLIGENCE.md: Suno API base is
  studio-api-prod.suno.com. Auth = Clerk __session cookie as Bearer token.
- joeseesun/suno-api-private: GET /api/get?ids=<song_id> returns clip
  details. __session cookie value IS the JWT.
- Katorthoma/suno_metadata_collector: clip objects carry metadata.prompt
  (which contains the lyrics text in custom mode), metadata.duration,
  metadata.has_stem, title, created_at, audio_url, video_url.

This script attaches to the suno.com CDP tab on port 9222 and runs
in-page fetches (credentials: include) to /api/get?ids=<song_id>.
The page already has all auth - no cookie extraction needed.
Same pattern as FETCH_AUDIO_JS in music/suno-gen.py.
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path("/home/j_kro/Projects/ai-content-pipeline")
CDP_PORT = 9222
API_BASE = "https://studio-api-prod.suno.com"

TRACKS = [
    ("af1e57f0-6595-460b-a0e7-7bb0bdd41f37", "Welcome"),
    ("63ce63d8-9888-4626-a431-d225ff9019cb", "These Worlds Are Made of Light"),
    ("23937711-dbfe-4612-95a7-39a20a64379b", "Erasing the Distance"),
    ("51c07d53-6eca-431a-886e-36f9c482abef", "This Small Forever"),
    ("4e23725e-e4ec-4b55-ad72-ed965fa822db", "World of Blue"),
    ("6db57655-f2c7-4929-b6ad-3ab948155962", "Sincerely"),
]

FETCH_SONG_JS = """
(async (songId) => {
  const url = 'https://studio-api-prod.suno.com/api/get?ids=' + songId;
  const r = await fetch(url, {credentials: 'include'});
  const text = await r.text();
  return JSON.stringify({status: r.status, body: text});
})
"""


def get_pages():
    req = urllib.request.Request(f"http://localhost:{CDP_PORT}/json")
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def find_suno_tab(pages):
    for p in pages:
        if "suno.com" in p.get("url", "") and p.get("type") == "page":
            return p
    return None


def cdp_eval(ws_url, expression, timeout=30):
    """Evaluate JS in the CDP tab, return the result value."""
    import websocket
    ws = websocket.create_connection(ws_url, timeout=timeout)
    try:
        msg = {
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {
                "expression": expression,
                "awaitPromise": True,
                "returnByValue": True,
            }
        }
        ws.send(json.dumps(msg))
        result = json.loads(ws.recv())
        if "result" in result and "result" in result["result"]:
            val = result["result"]["result"].get("value")
            if val is not None:
                return val
        err = result.get("result", {}).get("exceptionDetails", {})
        if err:
            desc = err.get("exception", {}).get("description", "")
            raise RuntimeError(f"CDP eval error: {desc}")
        return None
    finally:
        ws.close()


def main():
    pages = get_pages()
    tab = find_suno_tab(pages)
    if not tab:
        print("FATAL: no suno.com tab found in CDP")
        sys.exit(1)

    ws_url = tab.get("webSocketDebuggerUrl")
    print(f"Found Suno tab: {tab['url'][:80]}")
    print(f"  WS: {ws_url[:60]}...")

    results = {}
    for song_id, title in TRACKS:
        print(f"\n=== {title} ({song_id}) ===")
        try:
            raw = cdp_eval(ws_url, f"({FETCH_SONG_JS})('{song_id}')", timeout=30)
            if raw is None:
                print("  ERROR: no return value")
                continue
            data = json.loads(raw)
            status = data.get("status")
            body = data.get("body", "")
            print(f"  HTTP {status}: {len(body)} bytes")
            if status == 200 and body:
                parsed = json.loads(body)
                # Save the full response
                results[title] = parsed
                # Extract key fields
                clips = parsed.get("clips") or parsed.get("data") or []
                if isinstance(clips, list) and clips:
                    clip = clips[0]
                    meta = clip.get("metadata", {})
                    prompt = meta.get("prompt", "")
                    lyrics_text = clip.get("lyrics") or clip.get("lyric") or ""
                    print(f"  title: {clip.get('title')}")
                    print(f"  created: {clip.get('created_at')}")
                    print(f"  duration: {meta.get('duration')}s")
                    print(f"  has_stem: {meta.get('has_stem')}")
                    print(f"  model: {clip.get('model_name')}")
                    print(f"  prompt (lyrics) length: {len(prompt)} chars")
                    if prompt:
                        print(f"  prompt preview: {prompt[:100]}...")
                    if lyrics_text:
                        print(f"  lyrics length: {len(lyrics_text)} chars")
                        print(f"  lyrics preview: {lyrics_text[:100]}...")
                else:
                    print(f"  No clips found in response: {body[:200]}")
            else:
                print(f"  Non-200 response: {body[:200]}")
        except Exception as e:
            print(f"  ERROR: {e}")
        time.sleep(0.5)

    # Save all results
    out_path = REPO / "campaigns/virtual-reflections/suno-api-probe.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved {len(results)} responses to {out_path}")


if __name__ == "__main__":
    main()
