#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export SUNOLOCAL_DB="$TMP/jobs.sqlite3"
python3 - <<'PY'
from music.sunolocal import store
from music.sunolocal.spec import SunoGenerateRequest

store.init_db()
req = SunoGenerateRequest(prompt="test", style="ambient", lyrics="[Verse]\nhello", duration=15)
jid = store.create_job(req)
assert jid, "no job id"
row = store.get_job(jid)
assert row is not None and row["status"] == "pending", row
store.update_job_status(jid, "completed", {"audio_url": "/api/v1/audio?path=x", "bytes": 123})
row = store.get_job(jid)
assert row["status"] == "completed", row
assert "audio_url" in row["result"], row["result"]
assert store.get_job("no-such-id") is None, "negative control failed: unknown id returned a row"
jobs = store.list_jobs()
assert any(j["job_id"] == jid for j in jobs), jobs
print("G2-OK")
PY
