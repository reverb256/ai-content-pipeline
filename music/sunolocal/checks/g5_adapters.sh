#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

cat > "$TMP/good_acestep.py" <<'PY'
import json, os, sys, wave
from pathlib import Path

args = sys.argv[1:]
name = args[args.index("--name") + 1]
plan = json.loads(Path(args[0]).read_text())
assert plan["caption"] == "stub-check", plan
out = Path(os.environ["FAKE_ACESTEP_OUT"])
out.mkdir(parents=True, exist_ok=True)
p = out / (name + ".wav")
with wave.open(str(p), "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(8000)
    w.writeframes(b"\x00\x00" * 400)
print("stub wrote", p)
PY

cat > "$TMP/bad_acestep.py" <<'PY'
import sys
print("simulated renderer failure", file=sys.stderr)
sys.exit(3)
PY

export FAKE_ACESTEP_OUT="$TMP/out"
export SUNOLOCAL_ACESTEP_OUTPUT="$TMP/out"
export GOOD_STUB="$TMP/good_acestep.py"
export BAD_STUB="$TMP/bad_acestep.py"

python3 - <<'PY'
import json, os, threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from music.sunolocal.adapters import yue2_http
from music.sunolocal.adapters.ace_comfy import render_acestep

plan = {"caption": "stub-check", "lyrics": "", "bpm": 120, "key": "C major", "duration": 10, "timesignature": "4"}

os.environ["SUNOLOCAL_ACESTEP_SCRIPT"] = os.environ["GOOD_STUB"]
audio, mime, meta = render_acestep(plan, seed=7)
assert mime == "audio/wav" and audio[:4] == b"RIFF" and len(audio) > 44, (mime, len(audio))
assert meta["engine"] == "ace" and meta["stem"].startswith("suno-"), meta

os.environ["SUNOLOCAL_ACESTEP_SCRIPT"] = os.environ["BAD_STUB"]
try:
    render_acestep(plan, seed=7)
    raise AssertionError("expected renderer failure to raise")
except RuntimeError as exc:
    assert "rc=3" in str(exc), exc
os.environ["SUNOLOCAL_ACESTEP_SCRIPT"] = os.environ["GOOD_STUB"]

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(n) or b"{}")
        if body.get("style") == "poison":
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"boom")
            return
        data = b"fLaC" + b"\x00" * 128
        self.send_response(200)
        self.send_header("Content-Type", "audio/flac")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

srv = HTTPServer(("127.0.0.1", 0), Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
os.environ["YUE2_BASE_URL"] = f"http://127.0.0.1:{srv.server_address[1]}"

audio, mime, meta = yue2_http.render_yue2({"id": "stub", "style": "ambient", "lyrics": "la"})
assert audio[:4] == b"fLaC" and mime == "audio/flac", (audio[:8], mime)

try:
    yue2_http.render_yue2({"id": "stub", "style": "poison", "lyrics": "la"})
    raise AssertionError("expected HTTP 500 to raise")
except RuntimeError as exc:
    assert "500" in str(exc), exc

srv.shutdown()
print("G5-OK")
PY
