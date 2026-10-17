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
#   2d. CHECK THE CAMPAIGN MEDIA (card t_8f515be3): `campaigns/virtual-reflections/`
#      kept its record in git and its media outside it - 11 media files lived only in
#      the WIP ref `origin/wip/atlas-backup-20261014`, 5 more (both copies of
#      sincerely.wav, both of this-small-forever.wav and this-small-forever.mp4) in
#      NO ref at all, while MANIFEST.json named audio_file/master_file paths git did
#      not hold and a verification run's package carried two symlinks into a pruned
#      scratch dir. Nothing ran that compared the record to the repo. This is its
#      scheduled home. It exits 5, so a corpus that disagrees with its own record is
#      never read as a gate, panel or render-log defect.
#   2e. CHECK THE SHARED-TREE COMMIT FENCE (card t_6d0b7dd7): this tree is ONE
#      working tree that every concurrently running card commits to (8 cards
#      `running` at 18:13 CDT on 2026-10-16), so a whole-index commit carries
#      whatever a sibling has staged — commit 545faa3 swept four files card
#      t_96dfc521 had staged, and commit 5cb2e3d reverted card t_450e7f39's
#      landing 7 s after it landed. music/scripts/git_commit_fence.sh refuses
#      that commit; music/scripts/check_commit_fence_armed.py asserts the fence
#      is ARMED on both lane repos AND that its mining-k8s copy is byte-equal.
#      A hook is file state plus one local config key, and neither is versioned:
#      nothing else notices when a clone, a `git config --unset` or a lost exec
#      bit disarms it. It exits 6, so a disarmed fence is never read as a gate,
#      panel, render-log or media defect.
#   2f. CHECK THE SHARED-TREE STALE-WRITE GUARD (card t_8dadd6cb): the fence
#      above judges the SCOPE of a commit and cannot see CONTENT, so it allows
#      the commit that dropped a shipped hunk — measured, commit edeef61 named
#      its paths (private index, fence ALLOW) and lost section 13 of
#      music/gates/check_gate_suite.sh that 9082ce3 had shipped, re-landed as
#      a31deb2. music/scripts/check_stale_write.py --staged refuses a whole-file
#      write whose content is OLDER than the branch's own bytes for that path,
#      naming the commit and the card that own the dropped bytes; it is armed in
#      .githooks/pre-commit and .githooks/pre-push. This leg is the detector for
#      two states a hook cannot report on its own: the guard DISARMED, and a
#      stale write that LANDED anyway (a rebase/cherry-pick/stash bypasses
#      pre-commit, and an override can bypass it deliberately). It reads
#      COMMITS, not the working tree, so a sibling mid-edit cannot move its
#      verdict — the residual leg 2e cannot say for itself. It exits 7, so a
#      stale write is never read as a gate, panel, render-log, media or fence
#      defect.
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
#   MEDIA_CORPUS_CHECKS         "0" = skip the campaign-media phase (default 1 = run it).
#                               For a checkout with no campaign media - never to silence
#                               a record that names files git does not hold.
#   COMMIT_FENCE_CHECKS         "0" = skip the shared-tree commit-fence phase (default 1
#                               = run it). For a host with no ~/mining-k8s checkout, where
#                               the fence's copy cannot be measured - never to silence a
#                               fence that has been disarmed.
#   STALE_WRITE_CHECKS          "0" = skip the shared-tree stale-write phase (default 1
#                               = run it). For a checkout with no history to audit -
#                               never to silence a guard that has been disarmed or a
#                               stale write that landed.
#   STALE_WRITE_WINDOW          how far back the stale-write audit reads (default
#                               "24 hours ago"; any `git log --since` date works).
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

# --- 2d. the campaign media (card t_8f515be3) -------------------------------
# `campaigns/*/MANIFEST.json` is the campaign's own record, and it names the file
# for every track: audio_file, master_file, source_mp4_file. Measured 2026-10-16:
# the Virtual Reflections record named 10 files git did not hold (8 of them carried
# only by a WIP ref, 2 by NO ref at all - both copies of sincerely.wav), and the
# repo carried two package "masters" that were symlinks into a pruned scratch dir
# (79/82 B: git stores the target string). Nothing compared the record to the repo.
# This is the missing detector - the same shape as the legs above, and distinct
# from a gate failure for the same reason: a record that names files nobody holds
# must never be read as a broken gate.
unset media_verdict
media_rc=0
if [ "${MEDIA_CORPUS_CHECKS:-1}" != "0" ]; then
  {
    echo
    echo "---- the campaign media the record names (card t_8f515be3) ----"
    "$PY" "$REPO/music/scripts/check_media_corpus_tracked.py" --check --repo "$REPO"
  } >> "$OUT" 2>&1 || media_rc=$?
  say "$TS - campaign media: rc=$media_rc (the record vs the repo; section in $OUT)"
  media_verdict="$(tail -n 1 "$OUT" 2>/dev/null || echo '(no media corpus output)')"
  # rc=1 is the incident: the record names media git does not hold, a package
  # "master" is a symlink, or media sits in the tree that no commit holds.
  # rc=3 says the leg could not answer at all (no git checkout) - reported the
  # same way, because an unanswerable check is not a pass.
  if [ "$media_rc" -ne 0 ] && [ "$rc" -eq 0 ]; then
    rc=5
  fi
fi

# --- 2e. the shared-tree commit fence (card t_6d0b7dd7) ----------------------
# This checkout is ONE working tree that every concurrently running card commits
# to: measured 2026-10-16 18:13 CDT, 8 cards `running` on the music board, all of
# them committing into /home/j_kro/ai-content-pipeline. A commit that uses the
# SHARED index carries whatever a sibling has staged: commit 545faa3 swept four
# files card t_96dfc521 had staged (t_42bc85ba), and commit 5cb2e3d committed a
# stale copy of card t_450e7f39's files, reverting its landing 6eb5a23 seven
# seconds after it landed. music/scripts/git_commit_fence.sh refuses a
# whole-index commit (or `git commit -a`) in the primary worktree; it is armed as
# .githooks/pre-commit through `git config core.hooksPath .githooks`.
#
# A hook is FILE state plus one LOCAL config key, and neither travels with the
# tree - a fresh clone, a `git config --unset` or a lost exec bit disarms it
# silently. check_commit_fence_armed.py is the detector for that: it asserts the
# fence exists, is executable, the hook names it, the mining-k8s copy is
# byte-equal, and the fence's own 15-case planted-defect suite passes. It is the
# "already fixed upstream"/"working on the host" gap check_scheduler_units.py
# exists for (t_41f354be), applied to the fence.
unset fence_verdict
fence_rc=0
if [ "${COMMIT_FENCE_CHECKS:-1}" != "0" ]; then
  {
    echo
    echo "---- the shared-tree commit fence is armed (card t_6d0b7dd7) ----"
    "$PY" "$REPO/music/scripts/check_commit_fence_armed.py" --repo "$REPO"
  } >> "$OUT" 2>&1 || fence_rc=$?
  say "$TS - commit fence: rc=$fence_rc (armed on both lane repos; section in $OUT)"
  fence_verdict="$(tail -n 1 "$OUT" 2>/dev/null || echo '(no fence output)')"
  # rc=1 is the incident this card is about: a commit in the shared tree can
  # carry a sibling's staged work again, because the fence that refuses it is no
  # longer armed. rc=3 says the leg could not answer at all (no lane or no
  # mining-k8s checkout) - reported the same way, because an unanswerable check
  # is not a pass.
  if [ "$fence_rc" -ne 0 ] && [ "$rc" -eq 0 ]; then
    rc=6
  fi
fi

# --- 2f. the shared-tree stale-write guard (card t_8dadd6cb) -----------------
# The fence in 2e judges the SCOPE of a commit (which paths its index carries).
# It cannot judge CONTENT, so on 2026-10-16 it allowed the commit that dropped a
# shipped hunk: edeef61 named its paths, used a private index, and lost section 13
# of music/gates/check_gate_suite.sh that 9082ce3 had shipped (re-landed as
# a31deb2). That is a stale whole-file write - a card read the file, edited it,
# and wrote it back whole after a sibling had committed to it.
#
# music/scripts/check_stale_write.py refuses that write: it names the origin
# commit and the card whose bytes the change drops, and it accepts a DECLARED
# drop ("Stale-write-dropped: <sha>" in the commit message). It is armed in
# .githooks/pre-commit (--staged) and .githooks/pre-push (--push).
#
# This leg is the detector for the two states a hook cannot report on its own:
#   * the guard is DISARMED (a hook is file state plus one local config key, and
#     neither travels with the tree), and
#   * a stale write LANDED anyway - `git rebase`, `git cherry-pick` and
#     `git stash pop` do not run pre-commit, and an override can bypass it.
# It reads COMMITS (`git rev-list`), never the working tree, so a sibling card
# mid-edit cannot move its verdict. That is deliberate: leg 2e's own doc records
# that reading the live tree made the same drill green at 18:21 and red at 18:24
# while another card had 122 uncommitted lines in play.
unset stale_verdict
stale_rc=0
if [ "${STALE_WRITE_CHECKS:-1}" != "0" ]; then
  window="${STALE_WRITE_WINDOW:-24 hours ago}"
  since="$(git -C "$REPO" rev-list -1 --before="$window" HEAD 2>/dev/null || true)"
  if [ -z "$since" ]; then
    since="$(git -C "$REPO" rev-list --max-parents=0 HEAD 2>/dev/null | tail -1 || true)"
  fi
  {
    echo
    echo "---- the shared-tree stale-write guard is armed (card t_8dadd6cb) ----"
    "$PY" "$REPO/music/scripts/check_stale_write.py" --armed --repo "$REPO" --skip-selftest
  } >> "$OUT" 2>&1
  stale_armed_rc=$?
  {
    echo
    echo "---- stale writes among the commits landed in the window ----"
    echo "     window: everything since $window (base ${since:-none})"
    "$PY" "$REPO/music/scripts/check_stale_write.py" --since "${since:-HEAD}" \
      --repo "$REPO"
  } >> "$OUT" 2>&1
  stale_audit_rc=$?
  stale_rc=0
  [ "$stale_armed_rc" -eq 0 ] || stale_rc="$stale_armed_rc"
  [ "$stale_audit_rc" -eq 0 ] || stale_rc="$stale_audit_rc"
  say "$TS - stale-write guard: armed_rc=$stale_armed_rc audit_rc=$stale_audit_rc (window: $window)"
  # The one line worth putting in the state string: the first stale write the
  # audit named, or the guard's own verdict when there was none. `tail` alone can
  # land on a blank line (measured: the state string came out empty).
  stale_verdict="$(grep -m1 '^REFUSE ' "$OUT" 2>/dev/null || true)"
  [ -n "$stale_verdict" ] || stale_verdict="$(grep -m1 '^check_stale_write' "$OUT" 2>/dev/null || true)"
  [ -n "$stale_verdict" ] || stale_verdict="$(grep -m1 '^note  ' "$OUT" 2>/dev/null || true)"
  [ -n "$stale_verdict" ] || stale_verdict="(no stale-write output)"
  # rc=1 is a stale write that landed in the window (someone bypassed the guard,
  # or the guard was disarmed while it happened); rc=3 is a guard that is not
  # armed. Both are reported: an unanswerable check is not a pass.
  if [ "$stale_rc" -ne 0 ] && [ "$rc" -eq 0 ]; then
    rc=7
  fi
fi

# --- 2g. the tempo acceptance names its field (card t_f5f703ea) --------------
# Every genre queue card this lane wrote was accepted on "measured tempo is
# within a few BPM of 92 (do not trust the plan — measure the audio)". That
# bullet names no FIELD, and until 90c4d0c (card t_ed609eb0) the named tool could
# not satisfy it for a percussion-free genre at all: measure.py folded 0.5/1.0/2.0
# only from its whole-band argmax, and on the elemental-air render that argmax sat
# at the 60 BPM END of the lag range, so the 92 BPM anchor never entered
# bpm_candidates (bpm 60.1, conf 0.369). The two closed cards carry the corrected
# wording in their COMMENTS (246, 247) — a worker cannot edit another card's body,
# so the rule needed a detector as well as the authoritative text in
# music/rubrics/README.md, "The acceptance rule for a percussion-free genre".
#
# check_tempo_acceptance_field.py reads the LIVE board read-only (open cards —
# the ones a worker will still be judged by; closed cards are the record) plus
# music/briefs/**/*.md, and FAILs a tempo acceptance that names none of
# ac_at_anchor / bpm_candidates / bpm_pulse. Its 8-case selftest pins the incident
# wording as a FAIL and the canonical bullet as a PASS. The exit code is 8, so a
# wording defect is never read as a broken gate (1), panel (3), render log (4),
# media corpus (5) or fence (6/7) defect.
unset tempo_verdict
tempo_rc=0
if [ "${TEMPO_ACCEPTANCE_CHECKS:-1}" != "0" ]; then
  {
    echo
    echo "---- the tempo acceptance names its field (card t_f5f703ea) ----"
    "$PY" "$REPO/music/scripts/check_tempo_acceptance_field.py" --repo "$REPO" \
      --db "${KANBAN_BOARD_DB:-$HOME/.hermes/kanban/boards/music/kanban.db}"
  } >> "$OUT" 2>&1 || tempo_rc=$?
  say "$TS - tempo acceptance: rc=$tempo_rc (board + briefs; section in $OUT)"
  tempo_verdict="$(tail -n 1 "$OUT" 2>/dev/null || echo '(no tempo-acceptance output)')"
  # rc=1 is the incident: a lane text states an audio tempo acceptance that names
  # no field. rc=3 says the leg could not answer at all (no board db) - reported
  # the same way, because an unanswerable check is not a pass.
  if [ "$tempo_rc" -ne 0 ] && [ "$rc" -eq 0 ]; then
    rc=8
  fi
fi

DURATION=$(( $(date +%s) - START ))
passed="$(grep -cE '^PASS ' "$OUT" || true)"
expected="$(grep -cE '^FAILS ' "$OUT" || true)"
bad="$(grep -cE '^BAD ' "$OUT" || true)"
fatal="$(grep -cE '^FATAL' "$OUT" || true)"
panel_fails="$(grep -cE '^FAIL (check_panel_membership|probe_judges)' "$OUT" || true)"
ledger_fails="$(grep -cE '^FAIL check_render_ledger' "$OUT" || true)"
media_fails="$(grep -cE '^FAIL check_media_corpus_tracked' "$OUT" || true)"
tempo_fails="$(grep -cE '^FAIL check_tempo_acceptance_field' "$OUT" || true)"
interp="$(grep -m1 '^interpreter: ' "$OUT" 2>/dev/null | sed 's/^interpreter: //' || true)"
verdict="$suite_verdict"

case "$rc" in
  0) state="OK" ;;
  1) state="BROKEN: $bad check(s) misbehaved" ;;
  2) state="REFUSED: the suite would not run" ;;
  3) state="PANEL: the reviewer panel cannot run ($panel_fails panel check(s) failed) — the gates themselves are not implicated" ;;
  4) state="RENDER LOG: the log is not in step with the delivered renders ($ledger_fails render-log check(s) failed) — the gates and the panel are not implicated" ;;
  5) state="MEDIA: the campaign record names media the repo does not hold ($media_fails media check(s) failed) - the gates, the panel and the render log are not implicated" ;;
  6) state="FENCE: the shared-tree commit fence is not armed ($(printf '%s' "$fence_verdict" | cut -c1-120)) - the gates, the panel, the render log and the media corpus are not implicated" ;;
  7) state="STALE WRITE: the shared-tree guard is disarmed, or a stale write landed ($(printf '%s' "$stale_verdict" | cut -c1-120)) - the gates, the panel, the render log, the media corpus and the fence are not implicated" ;;
  8) state="TEMPO ACCEPTANCE: a lane text states an audio tempo acceptance that names no field ($tempo_fails claim(s), card t_f5f703ea) - the gates, the panel, the render log, the media corpus and the fence are not implicated" ;;
  *) state="ERROR: unexpected exit $rc" ;;
esac

say "$TS — gate matrix: rc=$rc $state pass=$passed expected_failures=$expected misbehaved=$bad fatal=$fatal panel_fails=$panel_fails ledger_rc=$ledger_rc ledger_fails=$ledger_fails media_rc=$media_rc media_fails=$media_fails interpreter=${interp:-$PY} duration=${DURATION}s${DRILL:+ drill=$DRILL}"

if [ "$rc" -ne 0 ]; then
  {
    echo "--- failing checks (run $TS, rc=$rc); full output: $OUT"
    grep -E '^(BAD|FATAL|REFUSE|FAIL (check_panel_membership|probe_judges|check_render_ledger|check_tempo_acceptance_field|check_commit_fence))' -A 2 "$OUT" | head -60
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
  "fence_rc": ${fence_rc:-0},
  "fence_verdict": "$(j "${fence_verdict:-(not run)}")",
  "stale_write_rc": ${stale_rc:-0},
  "stale_write_verdict": "$(j "${stale_verdict:-(not run)}")",
  "tempo_rc": ${tempo_rc:-0},
  "tempo_fails": ${tempo_fails:-0},
  "tempo_verdict": "$(j "${tempo_verdict:-(not run)}")",
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
- counts: pass=$passed expected_failures=$expected misbehaved=$bad fatal=$fatal panel_fails=$panel_fails ledger_rc=$ledger_rc ledger_fails=$ledger_fails tempo_rc=$tempo_rc tempo_fails=$tempo_fails
- full suite output: \`$OUT\`
- run log: \`$LOG\`

Failing checks:

\`\`\`
$(grep -E '^(BAD|FATAL|REFUSE|FAIL (check_panel_membership|probe_judges|check_render_ledger|check_media_corpus_tracked|check_commit_fence|check_tempo_acceptance_field))' -A 2 "$OUT" | head -60)
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
For rc=5 (the campaign media, not a gate failure): every file \`campaigns/*/MANIFEST.json\`
names for an exported track must be TRACKED in this repo, a package under
\`music/packages/streaming/\` must hold bytes rather than a symlink, and media in the
working tree must not be untracked - an untracked master is one \`git clean\` from gone.
Reproduce: \`/usr/bin/python3 music/scripts/check_media_corpus_tracked.py --check\`.
For rc=6 (the shared-tree commit fence is not armed, not a gate failure): a
whole-index commit in this shared working tree can carry a sibling card's staged
work again (commit 545faa3 swept four files card t_96dfc521 had staged; commit
5cb2e3d reverted card t_450e7f39's landing 7 s after it landed). Re-arm it:
\`git config core.hooksPath .githooks\` in this repo and in ~/mining-k8s, run
\`chmod +x .githooks/pre-commit music/scripts/git_commit_fence.sh\`, and copy the
source of record over the mining-k8s copy
(\`cp music/scripts/git_commit_fence.sh ~/mining-k8s/scripts/git_commit_fence.sh\`).
Reproduce: \`/usr/bin/python3 music/scripts/check_commit_fence_armed.py\` must exit 0;
\`bash music/scripts/test_git_commit_fence.sh\` must print 15 PASS lines.
For rc=7 (the shared-tree stale-write guard, not a gate failure): a card wrote a
WHOLE file from a snapshot it read earlier, so commits landed that put back bytes
older than the branch's own — commit edeef61 dropped section 13 of
\`music/gates/check_gate_suite.sh\` that 9082ce3 had shipped (re-landed as
a31deb2). Two states produce rc=7: the guard is not armed, or a stale write
landed in the window (a rebase/cherry-pick/stash does not run pre-commit, and an
override can bypass it on purpose). Re-arm it: \`git config core.hooksPath
.githooks\` and \`chmod +x .githooks/pre-commit .githooks/pre-push\`. Each landed
stale write is named in the log with the origin commit and its card; a DELIBERATE
drop is declared in the commit message with \`Stale-write-dropped: <sha>\`, which
the audit reads as declared rather than as a stale write. Reproduce:
\`/usr/bin/python3 music/scripts/check_stale_write.py --armed\` must exit 0 and
\`bash music/scripts/test_check_stale_write.py\` must print 37 PASS lines.
For rc=8 (a lane text states an audio tempo acceptance that names no field, not a
gate failure): every genre queue card this lane wrote was accepted on the bullet
"measured tempo is within a few BPM of 92 (do not trust the plan - measure the
audio)" - a bullet that names no field of the tool it points at, and that the named
tool could not satisfy for a percussion-free genre at all until 90c4d0c (card
t_ed609eb0: the whole-band argmax sat at the 60 BPM edge, so the anchor never
entered bpm_candidates, and the same tool read a control that is really 120 BPM as
60.1). Carry the canonical bullet VERBATIM from music/rubrics/README.md, section
"The acceptance rule for a percussion-free genre": judge the tempo by
ac_at_anchor.verdict == "supported" (a candidate within 3 BPM of the anchor at
ac >= 0.25, or the anchor's own lag ac >= 0.25 within +-10 % of its period), never
on the bare bpm field; and where bpm_pulse == "none" the tool cannot see a pulse -
decide the tempo by the stem or ear check and say so in the card, never a silent
FAIL and never a pass. Reproduce:
/usr/bin/python3 music/scripts/check_tempo_acceptance_field.py must exit 0; its
--selftest prints 8 PASS lines and pins the retired wording as a FAIL.

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
