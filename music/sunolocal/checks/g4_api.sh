#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
TMP="$(mktemp -d)"
export SUNOLOCAL_DB="$TMP/jobs.sqlite3"
export SUNOLOCAL_ARTIFACTS="$TMP/artifacts"
export SUNOLOCAL_ENGINE="fixture"
PORT="${SUNOLOCAL_TEST_PORT:-8123}"
python3 -m uvicorn music.sunolocal.studio:app --host 127.0.0.1 --port "$PORT" --log-level warning &
PID=$!
cleanup() { kill "$PID" 2>/dev/null || true; wait "$PID" 2>/dev/null || true; rm -rf "$TMP"; }
trap cleanup EXIT
ready=""
for _ in $(seq 1 100); do
  if curl -sf -m 2 "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then ready=1; break; fi
  sleep 0.2
done
if [ -z "$ready" ]; then echo "server not ready"; exit 1; fi
PORT="$PORT" python3 - <<'PY'
import json, os, time, urllib.error, urllib.request

BASE = f"http://127.0.0.1:{os.environ['PORT']}"

def req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method,
                               headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=15) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw.decode() or "{}")
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw.decode() or "{}")
        except json.JSONDecodeError:
            return e.code, {"raw": raw.decode(errors="replace")}

st, body = req("GET", "/health")
assert st == 200 and body.get("status") == "ok", (st, body)

st, body = req("GET", "/api/v1/models")
assert st == 200, (st, body)
assert {"ace", "yue2"} <= set(body["engines"]), body

st, body = req("POST", "/api/v1/generate", {
    "customMode": True, "instrumental": False, "style": "synthwave",
    "lyrics": "[Chorus]\nshine on", "duration": 12, "engine": "fixture",
})
assert st == 200 and body.get("task_id"), (st, body)
tid = body["task_id"]

deadline = time.time() + 30
status = None
body = {}
while time.time() < deadline:
    st, body = req("GET", f"/api/v1/task/{tid}")
    assert st == 200, (st, body)
    status = body.get("status")
    if status in ("completed", "failed"):
        break
    time.sleep(0.25)
assert status == "completed", (status, body)
url = body.get("audio_url") or ""
assert url.startswith("/api/v1/audio"), body

with urllib.request.urlopen(BASE + url, timeout=10) as resp:
    audio = resp.read()
assert audio[:4] == b"RIFF" and audio[8:12] == b"WAVE" and len(audio) > 44, (len(audio), audio[:16])

for ep in ("/api/v1/lyrics", "/api/v1/stems", "/api/v1/extend", "/api/v1/cover"):
    st, body = req("POST", ep, {})
    assert st == 501, (ep, st, body)

st, body = req("GET", "/api/v1/audio?path=/etc/hostname")
assert st == 404, (st, body)

st, body = req("GET", "/api/v1/task/nope")
assert st == 404, (st, body)

print("G4-OK")
PY
