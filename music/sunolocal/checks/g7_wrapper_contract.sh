#!/usr/bin/env bash
# G7: pipeline-wrapper contract — the wrapper must find audio_url in the task
# payload the service actually returns.
#
# Regression test for the t_36ca4e7c incident (2026-10-14): the wrapper shipped
# in t_a77c505b looked for a nested result.audio_url, but studio.py merges the
# job result into the TOP LEVEL of GET /api/v1/task/<id>. The first live render
# through the deployed service failed with "Completed but no audio_url". The
# t_a77c505b acceptance was never executed, so nothing caught the shape
# mismatch. This check pins the contract: it exercises the real wrapper logic
# against the real task-payload shape, with the engine stubbed to fixture.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
TMP="$(mktemp -d)"
export SUNOLOCAL_DB="$TMP/jobs.sqlite3"
export SUNOLOCAL_ARTIFACTS="$TMP/artifacts"
export SUNOLOCAL_ENGINE="fixture"
PORT="${SUNOLOCAL_TEST_PORT:-8147}"
python3 -m uvicorn music.sunolocal.studio:app --host 127.0.0.1 --port "$PORT" --log-level warning &
PID=$!
cleanup() { kill "$PID" 2>/dev/null || true; wait "$PID" 2>/dev/null || true; rm -rf "$TMP"; }
trap cleanup EXIT
ready=""
for _ in $(seq 1 100); do
  if curl -sf -m 2 "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then ready=1; break; fi
  sleep 0.2
done
if [ -z "$ready" ]; then echo "FAIL g7: server not ready"; exit 1; fi

# 1) Contract pin: a completed task must expose audio_url TOP-LEVEL.
PORT="$PORT" python3 - <<'PY'
import json, os, time, urllib.request

BASE = f"http://127.0.0.1:{os.environ['PORT']}"

def req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method,
                               headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=15) as resp:
        return json.loads(resp.read() or b"{}")

task = req("POST", "/api/v1/generate", {"prompt": "g7 contract pin", "duration": 2})
tid = task["task_id"]
payload = {}
for _ in range(60):
    payload = req("GET", f"/api/v1/task/{tid}")
    if payload.get("status") in ("completed", "failed"):
        break
    time.sleep(0.25)
if payload.get("status") != "completed":
    print(f"FAIL g7: task did not complete: {payload}")
    raise SystemExit(1)
if not payload.get("audio_url"):
    print("FAIL g7: completed task payload has NO top-level audio_url "
          "(the wrapper depends on it — see t_36ca4e7c)")
    raise SystemExit(1)
print(f"OK g7: top-level audio_url present: {payload['audio_url']}")
PY

# 2) Live wrapper run against the fixture engine, if the wrapper is present.
#    $ROOT = helm/charts/sunolocal/files, the wrapper lives in the sibling
#    music-pipeline chart: ../../music-pipeline/files/music/scripts/.
WRAPPER="${SUNOLOCAL_WRAPPER_SCRIPT:-$ROOT/../../music-pipeline/files/music/scripts/acestep_plan.py}"
if [ -f "$WRAPPER" ]; then
  export SUNOLOCAL_WRAPPER_OUT="$TMP"
  export SUNOLOCAL_ENGINE="fixture"
  cat > "$TMP/plan.json" <<'JSON'
{
  "title": "g7 wrapper contract",
  "caption": "fixture engine smoke",
  "lyrics": "[Verse]\none line so the plan is not empty\n",
  "bpm": 120,
  "key": "C major",
  "duration": 2,
  "timesignature": "4"
}
JSON
  if SUNOLOCAL_HOST="http://127.0.0.1:$PORT" python3 "$WRAPPER" "$TMP/plan.json" \
      --name g7-contract --allow-empty --timeout 60 \
      > "$TMP/wrapper.log" 2>&1; then
    if grep -q "audio saved to" "$TMP/wrapper.log"; then
      saved="$(grep 'audio saved to' "$TMP/wrapper.log" | awk '{print $NF}')"
      if [ -f "$saved" ]; then
        echo "OK g7: wrapper end-to-end: $saved"
      else
        echo "FAIL g7: wrapper reported success but file missing: $saved"
        exit 1
      fi
    else
      echo "FAIL g7: wrapper exited 0 without 'audio saved to'"
      cat "$TMP/wrapper.log"
      exit 1
    fi
  else
    echo "FAIL g7: wrapper run failed"
    cat "$TMP/wrapper.log"
    exit 1
  fi
else
  echo "skip g7: wrapper script not found at $WRAPPER (contract pin above still ran)"
fi
echo "PASS g7"
