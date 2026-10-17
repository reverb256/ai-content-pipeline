#!/usr/bin/env bash
# fleet-route-probe.sh — the SCHEDULED home of the fleet routing probe.
#
# Card t_7d75bafd. `scripts/fleet-route.py probe` already existed, and measured
# 2026-10-16 `~/.hermes/state/fleet-route/` DID NOT EXIST — nothing ran it. So the
# whole fleet could sit on a primary that answers HTTP 400 MissingSessionID (29 of
# 32 profiles did) with no signal anywhere, and the only reason anyone found out
# was a music card that happened to walk the reviewer panel. This script is that
# missing home, modelled on music/scripts/run_gate_matrix.sh for the music lane.
#
# Order of operations
# -------------------
#   1. AUDIT (offline, ~1 s): `fleet-route.py audit --strict` over every profile on
#      this host. It flags a DEAD-PROVIDER primary, a measured-dead slug, a chain
#      entry whose provider has no credential (every commandcode entry — the key is
#      absent from ~/.hermes/.env), an ENDPOINT-MISMATCH (model.base_url that does
#      not belong to model.provider — what the v2 model-health rotator left behind),
#      a missing endpoint, and a profile with no fallback at all.
#   2. PROBE (live, ~1-3 min): every model in every primary + chain gets a real
#      chat call (256 tokens; an answer needs content OR reasoning_content). This
#      is what catches a provider that is up but serving nothing — e.g. HTTP 200
#      with an empty body. A model that answers only a QUOTA error (HTTP 429/402,
#      e.g. `openrouter-free` free-models-per-day-high-balance on the fleet's one
#      SHARED daily free quota) is counted and printed as QUOTA, NOT as a routing
#      defect: it happens every day before 00:00 UTC and it is how an alert feed
#      stops being read if it fires for it. A route that CANNOT answer at all
#      (400/403/404/5xx, empty body, missing key) is FAIL and fails the run.
#   3. SCHEDULE (offline): assert the timer that runs this very probe is armed and
#      its last status is fresh (scripts/check_fleet_route_probe_scheduled.py). A
#      check nobody runs is inert (t_049c6a26) — including this one.
#   4. RECORD: one summary line in performance/fleet-route-probe.log, a
#      machine-readable performance/fleet-route-probe.status.json, and the full
#      output in performance/fleet-route-probe-last-run.txt.
#   5. REPORT a failure where a human sees it: post to the fleet alert feed (the
#      same nexus:9799 receiver verify-fleet.sh and the music gate matrix post to).
#      A log line alone is not a signal.
#   6. EXIT: 0 = the fleet's routing is whole, 1 = a ROUTING defect (audit flags or
#      probe FAILs), 2 = the schedule itself is not armed. Distinct codes so a
#      broken schedule is never read as a routing defect.
#
# Environment
#   FLEET_ROUTE_REPO            repo root            (default: parent of this script)
#   FLEET_ROUTE_LOG             run log              (default $REPO/performance/fleet-route-probe.log)
#   FLEET_ROUTE_STATUS          status JSON          (default $REPO/performance/fleet-route-probe.status.json)
#   FLEET_ROUTE_OUT             full output          (default $REPO/performance/fleet-route-probe-last-run.txt)
#   FLEET_ROUTE_HERMES_HOME     Hermes root          (default ~/.hermes)
#   FLEET_ROUTE_ALERT_URL       fleet alert feed; "" = skip (default http://127.0.0.1:9799/alerts)
#   FLEET_ROUTE_DRILL=1         skip the alert leg; mark the status drill=true.
#                               There is no card leg on purpose: fleet routing has no
#                               owning board, the alert feed is the human channel and
#                               the unit's own failed state is the operator channel.
#   FLEET_ROUTE_PHASES          subset of "audit,probe,schedule" (default all three).
#                               A git hook or a quick manual run sets "audit,schedule"
#                               and pays no API call.
#   PY                          interpreter (default /usr/bin/python3; the Hermes
#                               bundled python has no PyYAML, which is the
#                               t_d3b9e218 trap)
set -uo pipefail

REPO="${FLEET_ROUTE_REPO:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PY="${PY:-/usr/bin/python3}"
HROOT="${FLEET_ROUTE_HERMES_HOME:-$HOME/.hermes}"
LOG="${FLEET_ROUTE_LOG:-$REPO/performance/fleet-route-probe.log}"
STATUS="${FLEET_ROUTE_STATUS:-$REPO/performance/fleet-route-probe.status.json}"
OUT="${FLEET_ROUTE_OUT:-$REPO/performance/fleet-route-probe-last-run.txt}"
ALERT_URL="${FLEET_ROUTE_ALERT_URL-http://127.0.0.1:9799/alerts}"
DRILL="${FLEET_ROUTE_DRILL:-0}"
PHASES="${FLEET_ROUTE_PHASES:-audit,probe,schedule}"
CMD="$REPO/scripts/fleet-route.py"
CHECK="$REPO/scripts/check_fleet_route_probe_scheduled.py"

TS="$(date -Is)"
START="$(date +%s)"
say() { printf '%s\n' "$*" | tee -a "$LOG"; }

[ -f "$CMD" ] || { echo "FAIL: no fleet-route.py at $CMD" >&2; exit 2; }
mkdir -p "$(dirname "$LOG")" "$(dirname "$STATUS")" "$(dirname "$OUT")"

{
  echo "fleet routing probe — $TS"
  echo "host=$(hostname)  repo=$REPO  head=$(git -C "$REPO" rev-parse --short HEAD 2>/dev/null || echo none)"
  echo "hermes=$HROOT  interpreter=$PY  phases=$PHASES"
} > "$OUT"

want() { case ",$PHASES," in *",$1,"*) return 0 ;; *) return 1 ;; esac; }

audit_rc=0
audit_flagged=0
if want audit; then
  {
    echo
    echo "---- 1. audit: every profile's primary, endpoint and chain (--strict) ----"
    HERMES_HOME="$HROOT" "$PY" "$CMD" audit --strict
  } >> "$OUT" 2>&1 || audit_rc=$?
  audit_flagged="$(grep -c '⚠' "$OUT" 2>/dev/null || true)"
  audit_flagged="${audit_flagged:-0}"
  say "$TS — audit: rc=$audit_rc flagged=$audit_flagged (section 1 in $OUT)"
fi

probe_rc=0
probe_ok=0
probe_fail=0
probe_quota=0
if want probe; then
  {
    echo
    echo "---- 2. live probe: every model in every primary + chain ----"
    HERMES_HOME="$HROOT" "$PY" "$CMD" probe
  } >> "$OUT" 2>&1 || probe_rc=$?
  probe_ok="$(grep -c '^OK ' "$OUT" 2>/dev/null || true)"
  probe_fail="$(grep -c '^FAIL ' "$OUT" 2>/dev/null || true)"
  probe_quota="$(grep -c '^QUOTA ' "$OUT" 2>/dev/null || true)"
  probe_ok="${probe_ok:-0}"
  probe_fail="${probe_fail:-0}"
  probe_quota="${probe_quota:-0}"
  say "$TS — probe: rc=$probe_rc ok=$probe_ok fail=$probe_fail quota=$probe_quota (section 2 in $OUT)"
fi

sched_rc=0
if want schedule; then
  {
    echo
    echo "---- 3. the schedule that runs this probe ----"
    "$PY" "$CHECK" --repo "$REPO" --allow-missing-status
  } >> "$OUT" 2>&1 || sched_rc=$?
  say "$TS — schedule: rc=$sched_rc (section 3 in $OUT)"
fi

# Routing defects first: a broken schedule must not hide a broken fleet.
rc=0
state="ok: routing whole"
if [ "$audit_rc" -ne 0 ] || [ "$probe_rc" -ne 0 ] || [ "$audit_flagged" -gt 0 ]; then
  rc=1
  state="ROUTING: $audit_flagged profile(s) carry an audit flag (rc=$audit_rc) and/or $probe_fail model(s) did not answer (rc=$probe_rc)"
elif [ "$sched_rc" -ne 0 ]; then
  rc=2
  state="SCHEDULE: the probe is not armed or its status is stale (rc=$sched_rc) — the routing state is unknown, not necessarily broken"
fi

DURATION=$(( $(date +%s) - START ))

if [ "$rc" -ne 0 ]; then
  {
    echo "--- failing lines (run $TS, rc=$rc); full output: $OUT"
    grep -E '^(FAIL|  - |  ⚠|FAIL |!!|   )' "$OUT" | head -40
  } | tee -a "$LOG"
fi

head_sha="$(git -C "$REPO" rev-parse --short HEAD 2>/dev/null || echo none)"
j() { printf '%s' "$1" | tr -d '"\\' | tr '\n' ' '; }
cat > "$STATUS" <<JSON
{
  "run_at": "$TS",
  "host": "$(hostname)",
  "repo": "$REPO",
  "repo_head": "$head_sha",
  "hermes_home": "$HROOT",
  "phases": "$PHASES",
  "rc": $rc,
  "state": "$(j "$state")",
  "audit_rc": $audit_rc,
  "audit_flagged": $audit_flagged,
  "probe_rc": $probe_rc,
  "probe_ok": $probe_ok,
  "probe_fail": $probe_fail,
  "probe_quota": $probe_quota,
  "schedule_rc": $sched_rc,
  "duration_s": $DURATION,
  "drill": $([ "$DRILL" = "1" ] && echo true || echo false),
  "output_file": "$OUT",
  "log_file": "$LOG"
}
JSON

say "$TS — fleet routing probe: rc=$rc $state probes_ok=$probe_ok probes_fail=$probe_fail duration=${DURATION}s${DRILL:+ drill=$DRILL}"

if [ "$rc" -ne 0 ] && [ "$DRILL" = "1" ]; then
  say "$TS — DRILL: alert leg skipped (FLEET_ROUTE_DRILL=1); status marked drill=true"
elif [ "$rc" -ne 0 ]; then
  if [ -n "$ALERT_URL" ]; then
    payload="$(printf '{"alerts":[{"status":"firing","labels":{"alertname":"FleetRouteProbeFailed","severity":"warning","component":"fleet-route-probe"},"annotations":{"summary":"fleet routing probe rc=%s: %s — see %s"}}]}' \
      "$rc" "$(j "$state")" "$LOG")"
    if curl -s -m 10 -X POST -H 'Content-Type: application/json' -d "$payload" "$ALERT_URL" >/dev/null 2>&1; then
      say "$TS — alert posted to $ALERT_URL"
    else
      say "$TS — WARN: alert feed unreachable ($ALERT_URL); log + status written"
    fi
  fi
fi

exit "$rc"
