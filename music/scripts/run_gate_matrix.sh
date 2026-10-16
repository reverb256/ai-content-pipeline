#!/usr/bin/env bash
# run_gate_matrix.sh — the SCHEDULED home of the music gate acceptance matrix.
#
# Card t_b16b9046. music/gates/check_gate_suite.sh is the acceptance matrix for
# all 10 music gates, and TWO documents told operators to run it by hand
# (music/gates/README.md, brain/runbooks/music-game-assets.md) — while NOTHING
# ran it. Measured 2026-10-16: no .github/workflows, no scripts/ caller, and the
# music units run the pipeline and the render, never the gates. A gate that
# regressed was therefore found only by accident: the PyYAML false-BAD
# (t_d3b9e218) was caught because a brief happened to run the suite by hand.
#
# This script is that missing home. music/scheduler/music-gate-matrix.{service,
# timer} runs it daily at 06:20 on nexus and installs it into
# ~/.config/systemd/user/ like the lane's other units.
#
# Order of operations
# -------------------
#   1. PRUNE $GATE_SCRATCH, then let the suite rebuild its fixtures. The suite
#      synthesizes every fixture with ffmpeg and measures 61 s end to end
#      (2026-10-16), so a stale fixture can never mask a fixture-builder
#      regression — the failure mode `build_fixtures()` exists for.
#   2. RUN the suite with ONE interpreter that can `import yaml`. The bundled
#      Hermes interpreter has no PyYAML, which made two healthy gates report BAD
#      (t_d3b9e218). The unit pins PY=/usr/bin/python3; this script defaults to
#      the same and refuses to pretend a wrong-interpreter run is a gate defect.
#   2b. CHECK THE REVIEW STAGE'S OWN JUDGES (card t_3d84acfe): an offline
#      membership check (music/scripts/check_panel_membership.py) plus a live
#      judge probe (music/rubrics/probe_judges.py), appended to the same output
#      file. A panel that reaches no judge makes gate_quality unpassable for
#      EVERY asset, and that state used to be invisible — the panel runs only
#      when a human runs it. A panel failure exits 3, so it is never read as a
#      gate defect.
#   2c. CHECK THE RENDER LOG (card t_d6b0cb36): music/quota-ledger.json is "the
#      pipeline's only durable render log" in its own words, and it held ONE
#      entry while EIGHT `.rendered` markers certified a delivered render — seven
#      delivered masters (chill-lounge-slow-gold, commentary-beds-lo-fi-jazz-
#      bed/-sting, elemental-earth-chamber-loop, elemental-fire-emberfall,
#      final-round, sentimental-piano-room-with-the-light-going) were absent
#      while /var/lib/sunolocal/artifacts/ held every one of them. The music
#      existed; the LOG was short, because nothing kept the two in step: the
#      render pod cannot write this file (its payload is a readOnly ConfigMap and
#      the ledger is a file in this repo — `grep -rn quota-ledger ~/mining-k8s`
#      finds nothing), so every card that queued a genre had to remember to append
#      an entry by hand. music/scripts/check_render_ledger.py is the missing
#      step, and this is its scheduled home. It exits 4, so a log that is out of
#      step is never read as a gate defect.
#   3. RECORD one summary line in performance/music-gate-matrix.log and a
#      machine-readable performance/music-gate-matrix.status.json. Those are the
#      files music-weekly-digest.service reads, so the result reaches the weekly
#      digest instead of dying in a journal.
#   4. REPORT a failure where a human sees it, not only in a log: post to the
#      fleet alert feed (the same nexus:9799 receiver verify-fleet.sh posts to)
#      and file — or re-comment on — a card on the music board. A log line alone
#      is not a signal.
#   5. EXIT with the suite's own status, so the unit shows failed
#      (`systemctl --user status music-gate-matrix.service`), verify-fleet.sh
#      section 12 sees Result != success, and a gate regression cannot be
#      "finished green".
#
# Env contract
# ------------
#   PY                          interpreter for every gate   (default /usr/bin/python3)
#   GATE_SCRATCH                fixture dir (pruned each run) (default $HOME/.cache/music-gate-fixtures)
#   GATE_MATRIX_LOG             run log                     (default $REPO/performance/music-gate-matrix.log)
#   GATE_MATRIX_STATUS          status JSON                 (default $REPO/performance/music-gate-matrix.status.json)
#   GATE_MATRIX_OUT             full suite output           (default $REPO/performance/music-gate-matrix-last-run.txt)
#   GATE_MATRIX_ALERT_URL       fleet alert feed; "" = skip  (default http://127.0.0.1:9799/alerts)
#   GATE_MATRIX_BOARD           kanban board               (default music)
#   GATE_MATRIX_CARD_ASSIGNEE   fixer for the failure card (default nexus-core)
#   GATE_MATRIX_CARD_INITIAL_STATUS  '' = ready (default) | blocked (drills)
#   GATE_MATRIX_DRILL=1         skip the alert + card legs; mark the log/status as a drill.
#                               For deliberate fault injection only — a drill must not
#                               fire a synthetic alert or park a fake card on the board.
#   PANEL_CHECKS                "0" = skip the panel judge phase (default 1 = run it).
#   RENDER_PLANS_DIR            the render rail's own plans directory, where the
#                               `.rendered` markers live (default /var/lib/music-plans).
#                               The leg runs unconditionally: when the directory is not
#                               there the check exits 3 and the leg FAILS, because a
#                               directory that cannot be read is not a log that is in step.
#   RENDER_LEDGER               the render log to check against
#                               (default $REPO/music/quota-ledger.json)
#   RENDER_LOG_CHECKS           "0" = skip the render-log phase (default 1 = run it).
#                               For a host that has no render rail at all — never to
#                               silence a red one.
set -uo pipefail

REPO="${GATE_MATRIX_REPO:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
SUITE="$REPO/music/gates/check_gate_suite.sh"
PY="${PY:-/usr/bin/python3}"
SCRATCH="${GATE_SCRATCH:-$HOME/.cache/music-gate-fixtures}"
LOG="${GATE_MATRIX_LOG:-$REPO/performance/music-gate-matrix.log}"
STATUS="${GATE_MATRIX_STATUS:-$REPO/performance/music-gate-matrix.status.json}"
OUT="${GATE_MATRIX_OUT:-$REPO/performance/music-gate-matrix-last-run.txt}"
ALERT_URL="${GATE_MATRIX_ALERT_URL-http://127.0.0.1:9799/alerts}"
BOARD="${GATE_MATRIX_BOARD:-music}"
CARD_ASSIGNEE="${GATE_MATRIX_CARD_ASSIGNEE:-nexus-core}"
CARD_STATUS="${GATE_MATRIX_CARD_INITIAL_STATUS:-}"
DRILL="${GATE_MATRIX_DRILL:-0}"
HERMES_BIN="${HERMES_BIN:-$(command -v hermes || true)}"
[ -n "$HERMES_BIN" ] || HERMES_BIN="$HOME/.local/bin/hermes"

TS="$(date -Is)"
START="$(date +%s)"
mkdir -p "$(dirname "$LOG")" "$(dirname "$STATUS")" "$(dirname "$OUT")"

say() { printf '%s\n' "$1" | tee -a "$LOG"; }

if [ ! -f "$SUITE" ]; then
  say "$TS — FATAL: no gate suite at $SUITE (wrong checkout? see card t_41f354be)"
  exit 2
fi

# --- 1. prune the fixture dir -----------------------------------------------
say "$TS — gate matrix run starting (repo=$REPO interpreter=$PY scratch=$SCRATCH)"
rm -rf "$SCRATCH"
mkdir -p "$SCRATCH"

# --- 2. run the suite -------------------------------------------------------
PY="$PY" GATE_SCRATCH="$SCRATCH" bash "$SUITE" > "$OUT" 2>&1
rc=$?
# The suite's own verdict line, kept before the panel sections are appended
# below (the status file must report the GATE verdict, not the last panel line).
suite_verdict="$(tail -n 1 "$OUT" 2>/dev/null || echo '(no output)')"

# --- 2b. the REVIEW stage's own judges (card t_3d84acfe) --------------------
# `gate_quality` validates the review.json that music/rubrics/panel.py writes,
# so a panel that reaches NO judge makes the quality gate unpassable for every
# asset. Measured 2026-10-16: that was the state for days, and nothing noticed,
# because the panel runs only when a human runs it. These two checks are the
# missing detector:
#   * check_panel_membership.py — OFFLINE: the panel's profiles exist, resolve,
#     come from disjoint model families, and keep a same-family fallback chain.
#   * probe_judges.py — LIVE: asks each member's chain the panel's own question
#     and fails when fewer than MIN_VALID_JUDGES members answer.
# Their output is appended to $OUT, so the failure lands in the same log, the
# same status JSON and the same board card as a gate failure. Set
# PANEL_CHECKS=0 to skip the live half (it makes real API calls).
panel_rc=0
if [ "${PANEL_CHECKS:-1}" != "0" ]; then
  {
    echo
    echo "---- panel membership (offline: profile configs + routing spec) ----"
    "$PY" "$REPO/music/scripts/check_panel_membership.py" --repo "$REPO"
  } >> "$OUT" 2>&1 || panel_rc=1
  {
    echo
    echo "---- panel judge liveness (live judge-shaped calls) ----"
    "$PY" "$REPO/music/rubrics/probe_judges.py"
  } >> "$OUT" 2>&1 || panel_rc=1
  say "$TS — panel judges: rc=$panel_rc (review stage; sections in $OUT)"
  panel_verdict="$(tail -n 1 "$OUT" 2>/dev/null || echo '(no panel output)')"
  # rc=3 says "the gates may be fine; the reviewer panel cannot run". Keeping
  # it distinct stops a panel defect from being read as a gate defect.
  if [ "$panel_rc" -ne 0 ] && [ "$rc" -eq 0 ]; then
    rc=3
  fi
fi

# --- 2c. the render log (card t_d6b0cb36) -----------------------------------
# gate_quota reads this file's COUNTERS. Nothing read its `renders:` list, which
# its own `_renders_note` calls "the pipeline's only durable render log": measured
# 2026-10-16 it held ONE entry while EIGHT `.rendered` markers certified a
# delivered render, so seven delivered masters were absent from the log while
# /var/lib/sunolocal/artifacts/ held every one of them. The rail cannot write the
# file (a readOnly ConfigMap payload and a ledger in THIS repo), so the log went
# short every time a card forgot the hand-written step. This is the missing
# detector — the same shape as the panel leg above, and distinct from a gate
# failure for the same reason: a log that is out of step must never be read as a
# broken gate.
unset ledger_verdict
ledger_rc=0
if [ "${RENDER_LOG_CHECKS:-1}" != "0" ]; then
  {
    echo
    echo "---- the render log (markers vs the ledger's renders: list, card t_d6b0cb36) ----"
    "$PY" "$REPO/music/scripts/check_render_ledger.py" --check \
      --plans "${RENDER_PLANS_DIR:-/var/lib/music-plans}" \
      --ledger "${RENDER_LEDGER:-$REPO/music/quota-ledger.json}"
  } >> "$OUT" 2>&1 || ledger_rc=$?
  say "$TS — render log: rc=$ledger_rc (markers vs the ledger; section in $OUT)"
  ledger_verdict="$(tail -n 1 "$OUT" 2>/dev/null || echo '(no render log output)')"
  # rc=1 is the incident this card is about: a delivered render the log does not
  # carry. rc=3 says the leg could not answer at all (no plans directory, an
  # unreadable ledger) — reported the same way, because an unanswerable check is
  # not a pass.
  if [ "$ledger_rc" -ne 0 ] && [ "$rc" -eq 0 ]; then
    rc=4
  fi
fi

DURATION=$(( $(date +%s) - START ))

passed="$(grep -cE '^PASS ' "$OUT" || true)"
expected="$(grep -cE '^FAILS ' "$OUT" || true)"
bad="$(grep -cE '^BAD ' "$OUT" || true)"
fatal="$(grep -cE '^FATAL' "$OUT" || true)"
panel_fails="$(grep -cE '^FAIL (check_panel_membership|probe_judges)' "$OUT" || true)"
ledger_fails="$(grep -cE '^FAIL check_render_ledger' "$OUT" || true)"
interp="$(grep -m1 '^interpreter: ' "$OUT" 2>/dev/null | sed 's/^interpreter: //' || true)"
verdict="$suite_verdict"

case "$rc" in
  0) state="OK" ;;
  1) state="BROKEN: $bad check(s) misbehaved" ;;
  2) state="REFUSED: the suite would not run" ;;
  3) state="PANEL: the reviewer panel cannot run ($panel_fails panel check(s) failed) — the gates themselves are not implicated" ;;
  4) state="RENDER LOG: the log is not in step with the delivered renders ($ledger_fails render-log check(s) failed) — the gates and the panel are not implicated" ;;
  *) state="ERROR: unexpected exit $rc" ;;
esac

say "$TS — gate matrix: rc=$rc $state pass=$passed expected_failures=$expected misbehaved=$bad fatal=$fatal panel_fails=$panel_fails ledger_rc=$ledger_rc ledger_fails=$ledger_fails interpreter=${interp:-$PY} duration=${DURATION}s${DRILL:+ drill=$DRILL}"

if [ "$rc" -ne 0 ]; then
  {
    echo "--- failing checks (run $TS, rc=$rc); full output: $OUT"
    grep -E '^(BAD|FATAL|FAIL (check_panel_membership|probe_judges|check_render_ledger))' -A 2 "$OUT" | head -60
  } | tee -a "$LOG"
fi

# --- 3. machine-readable status (the weekly digest reads this) --------------
head_sha="$(git -C "$REPO" rev-parse --short HEAD 2>/dev/null || echo none)"
j() { printf '%s' "$1" | tr -d '"\\' | tr '\n' ' '; }
cat > "$STATUS" <<JSON
{
  "run_at": "$TS",
  "repo": "$REPO",
  "repo_head": "$head_sha",
  "suite": "$SUITE",
  "interpreter": "$(j "${interp:-$PY}")",
  "scratch": "$SCRATCH",
  "rc": $rc,
  "state": "$(j "$state")",
  "verdict": "$(j "$verdict")",
  "passed": ${passed:-0},
  "expected_failures": ${expected:-0},
  "misbehaved": ${bad:-0},
  "fatal": ${fatal:-0},
  "panel_rc": ${panel_rc:-0},
  "panel_fails": ${panel_fails:-0},
  "panel_verdict": "$(j "${panel_verdict:-(not run)}")",
  "ledger_rc": ${ledger_rc:-0},
  "ledger_fails": ${ledger_fails:-0},
  "ledger_verdict": "$(j "${ledger_verdict:-(not run)}")",
  "duration_s": $DURATION,
  "drill": $([ "$DRILL" = "1" ] && echo true || echo false),
  "output_file": "$OUT",
  "log_file": "$LOG"
}
JSON

# --- 4. report a failure where a human sees it ------------------------------
card_body="$(mktemp "${TMPDIR:-/tmp}/gate-matrix-card.XXXXXX")"
cat > "$card_body" <<BODY
# Scheduled music gate matrix FAILED ($state)

The scheduled gate-matrix run found a gate that does not behave. Card \`t_b16b9046\`
wired \`music/gates/check_gate_suite.sh\` into \`music-gate-matrix.timer\`
(daily 06:20 on nexus) — this card is filed by the runner itself.

- run: $TS (rc=$rc, $state)
- runner: \`music/scripts/run_gate_matrix.sh\` on $REPO @ $head_sha
- interpreter: ${interp:-$PY}
- counts: pass=$passed expected_failures=$expected misbehaved=$bad fatal=$fatal panel_fails=$panel_fails ledger_rc=$ledger_rc ledger_fails=$ledger_fails
- full suite output: \`$OUT\`
- run log: \`$LOG\`

Failing checks:

\`\`\`
$(grep -E '^(BAD|FATAL|FAIL (check_panel_membership|probe_judges|check_render_ledger))' -A 2 "$OUT" | head -60)
\`\`\`

Reproduce: \`bash music/gates/check_gate_suite.sh\` must exit 0 with
\`OK: every gate passed its good artifact and failed its broken one\`.
For rc=3 (a panel failure, not a gate failure):
\`/usr/bin/python3 music/scripts/check_panel_membership.py\` and
\`/usr/bin/python3 music/rubrics/probe_judges.py\` must both exit 0.
For rc=4 (the render log, not a gate failure): a render the rail delivered has no
entry in music/quota-ledger.json's renders: list (the RED lines name each one),
or the leg could not read the markers at all (its exit 3). Record the delivered
renders with

    /usr/bin/python3 music/scripts/check_render_ledger.py --record --stem <stem>

which derives the entry from live state, or --backfill for all of them at once;
then --check must exit 0. Do NOT hand-write an entry, and do NOT write one for a
.refused marker — a refusal is a draft waiting on a human.
Fix the gate (or its fixture) or re-point the judges, do not weaken the check.
BODY

if [ "$rc" -ne 0 ] && [ "$DRILL" = "1" ]; then
  say "$TS — DRILL: alert + card legs skipped (GATE_MATRIX_DRILL=1); status marked drill=true"
elif [ "$rc" -ne 0 ]; then
  # 4a. fleet alert feed — the same receiver verify-fleet.sh posts to.
  if [ -n "$ALERT_URL" ]; then
    payload="$(printf '{"alerts":[{"status":"firing","labels":{"alertname":"MusicGateMatrixFailed","severity":"warning","component":"music-gate-matrix"},"annotations":{"summary":"music gate matrix rc=%s: %s — see %s"}}]}' \
      "$rc" "$(j "$state")" "$LOG")"
    if curl -s -m 10 -X POST -H 'Content-Type: application/json' -d "$payload" "$ALERT_URL" >/dev/null 2>&1; then
      say "$TS — alert posted to $ALERT_URL"
    else
      say "$TS — WARN: alert feed unreachable ($ALERT_URL); log + status written"
    fi
  fi

  # 4b. music board — file, or re-comment on, the failure card. The dedupe is
  #     text-based on purpose: an open card with the same subject must be
  #     annotated, not duplicated (one card per incident, not one per run).
  if [ -x "$HERMES_BIN" ]; then
    if existing="$("$HERMES_BIN" kanban --board "$BOARD" list 2>/dev/null \
                    | awk '$3 != "done" && /gate matrix FAILED/ {print; exit}')"; then
      if [ -n "$existing" ]; then
        card_id="$(printf '%s' "$existing" | grep -oE 't_[0-9a-f]+' | head -1)"
        if [ -n "$card_id" ] && "$HERMES_BIN" kanban --board "$BOARD" comment "$card_id" \
             "$(cat "$card_body")" >/dev/null 2>&1; then
          say "$TS — re-commented on the open failure card $card_id"
        else
          say "$TS — WARN: could not comment on $existing"
        fi
      else
        create_args=()
        [ -n "$CARD_STATUS" ] && create_args+=(--initial-status "$CARD_STATUS")
        if card_id="$("$HERMES_BIN" kanban --board "$BOARD" create \
                 "music: gate matrix FAILED — $state ($TS)" \
                 --body-file "$card_body" --assignee "$CARD_ASSIGNEE" --priority 5 \
                 "${create_args[@]}" --json 2>/dev/null \
                 | grep -oE 't_[0-9a-f]+' | head -1)" && [ -n "$card_id" ]; then
          say "$TS — filed failure card $card_id on the $BOARD board (assignee $CARD_ASSIGNEE)"
        else
          say "$TS — WARN: could not file a failure card on the $BOARD board"
        fi
      fi
    else
      say "$TS — WARN: kanban board $BOARD unreadable ($HERMES_BIN); log only"
    fi
  else
    say "$TS — WARN: no hermes CLI at $HERMES_BIN; log only"
  fi
fi
rm -f "$card_body"

# --- 5. the suite's status is this run's status ------------------------------
exit "$rc"
