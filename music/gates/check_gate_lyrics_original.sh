#!/usr/bin/env bash
# Regression checks for gate_lyrics_original + the lyrics stage.
# Encodes the acceptance matrix of card "original-lyrics pipeline
# (copyrightability)" and the 2026-10-08 incident where '#' provenance
# header lines were parsed as lyric body (fixed in parse_sections;
# this suite is the check that would have caught it).
#
# 2026-10-16 (card t_53da62e5): this suite was itself broken in the fleet shell.
# It invoked the bare `python3`, which on nexus is the Hermes bundled interpreter
# with no PyYAML, so gate_lyrics_original and lyrics.py died on `import yaml`
# BEFORE running any check: 6 checks misbehaved, and the three "FAILS ... as
# expected" lines were the crash, not a refusal. Two fixes: the interpreter is
# now explicit ($PY, defaulting to /usr/bin/python3 — the interpreter the systemd
# units use and the one with PyYAML), and the refusal checks call expect_refuse,
# which requires the tool's own refusal wording, so a crash can never be scored
# as a correct refusal again. Anisong checks added: a Japanese-script sheet with
# the genre's key-change tag is exactly what the anisong family must produce, and
# both a token measure that read it as 0 and a strict tag list that rejected
# "[Final Chorus — KEY CHANGE UP ONE SEMITONE/TONE]" made the human-authorship
# claim unrecordable.
#
# Usage: bash music/gates/check_gate_lyrics_original.sh   [PY=/path/to/python3]
# Exit 0 = all checks behaved as expected (PASS where expected,
# FAIL where expected). Exit 1 = a check misbehaved.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO"
fails=0
checks=0

PY="${PY:-/usr/bin/python3}"
echo "interpreter: $PY ($("$PY" --version 2>&1))"

expect_pass() { # label, then command
  local label="$1"; shift
  checks=$((checks+1))
  if "$@" >/tmp/gate_check_out.$$ 2>&1; then
    echo "PASS  $label"
  else
    echo "FAIL  $label (expected exit 0, got $?)"
    sed 's/^/      /' /tmp/gate_check_out.$$
    fails=$((fails+1))
  fi
}

expect_fail() { # label, expected-exit, then command (usage errors: no refusal wording)
  local label="$1"; local want="$2"; shift 2
  local got=0
  checks=$((checks+1))
  "$@" >/tmp/gate_check_out.$$ 2>&1 || got=$?
  if [ "$got" -eq "$want" ]; then
    echo "FAILS $label (exit $want, as expected)"
  else
    echo "BAD   $label (expected exit $want, got $got)"
    sed 's/^/      /' /tmp/gate_check_out.$$
    fails=$((fails+1))
  fi
}

expect_refuse() { # label, expected-exit, then command: must refuse BY NAME
  local label="$1"; local want="$2"; shift 2
  local got=0 out
  checks=$((checks+1))
  out="$("$@" 2>&1)" || got=$?
  if ! printf '%s' "$out" | grep -qE '^(FAIL|FAIL:)'; then
    echo "BAD   $label (exit $got but no FAIL refusal — did the tool crash?)"
    printf '%s\n' "$out" | sed 's/^/      /'
    fails=$((fails+1))
  elif [ "$got" -ne "$want" ]; then
    echo "BAD   $label (refused, but exit $got, expected $want)"
    fails=$((fails+1))
  else
    echo "FAILS $label (exit $want with a refusal, as expected)"
  fi
}

GATE="$PY music/gates/gate_lyrics_original.py"
LYR="$PY music/lyrics/lyrics.py"

# --- acceptance: 3 genres PASS with authorship claims ---------------------
expect_pass "chill-lounge track passes" $GATE --track-dir music/lyrics/chill-lounge/amber-hour --strict
expect_pass "trance track passes"       $GATE --track-dir music/lyrics/trance/signal-before-dawn --strict
expect_pass "activist track passes"     $GATE --track-dir music/lyrics/activist/what-runs-beneath --strict

# --- acceptance: gate fails a Suno-generated lyric --------------------------
expect_refuse "suno-generated lyric rejected (bare file)" 1 \
  $GATE --lyrics-file music/gates/fixtures/suno-generated-umbrellas-in-space.txt

# --- incident regression: '#' provenance headers are not lyric body ---------
# (2026-10-08: headers were parsed as untagged lines; claim/gate false-failed)
expect_pass "comment-header sheet still parses+passes" \
  $GATE --track-dir music/lyrics/chill-lounge/amber-hour --strict

# --- tamper detection: edited-after-claim text fails -----------------------
tmpd="$(mktemp -d)"
trap 'rm -rf "$tmpd" /tmp/gate_check_out.$$' EXIT
cp music/lyrics/trance/signal-before-dawn/manifest.json "$tmpd/"
head -c 400 music/lyrics/trance/signal-before-dawn/lyrics.suno.txt > "$tmpd/lyrics.suno.txt"
expect_refuse "post-claim edit rejected (hash mismatch)" 1 \
  $GATE --track-dir "$tmpd"

# --- unclaimed scaffold cannot pass -----------------------------------------
mkdir -p "$tmpd/unclaimed"
cp music/lyrics/activist/what-runs-beneath/lyrics.suno.txt "$tmpd/unclaimed/"
expect_refuse "unclaimed sheet rejected (no manifest)" 1 \
  $GATE --track-dir "$tmpd/unclaimed"
mkdir -p "$tmpd/suno-claim"
cp music/gates/fixtures/suno-generated-umbrellas-in-space.txt "$tmpd/suno-claim/lyrics.suno.txt"
cp music/lyrics/activist/what-runs-beneath/manifest.json "$tmpd/suno-claim/"
expect_refuse "claim refused over suno-generated sheet" 1 \
  $LYR claim --track-dir "$tmpd/suno-claim" --author "j_kro"

# --- anisong: Japanese script + the genre's key-change tag (2026-10-16) ------
# The sheet is the committed anime-opening draft (music/lyrics/anime-opening/
# becoming): Japanese script, 10 sections, the template's key-change tag. Before
# the lyrics.py fix the gate refused it with "0 unique words" and an unknown
# section tag, and `claim` — which runs validate_sheet(strict=True) — refused it
# with the same two reasons, so the human-authorship claim was unrecordable for
# any in-genre anisong sheet.
expect_pass "japanese anisong sheet passes the sheet checks" \
  $GATE --lyrics-file music/lyrics/anime-opening/becoming/lyrics.suno.txt --strict
mkdir -p "$tmpd/ja-claim"
cp music/lyrics/anime-opening/becoming/lyrics.suno.txt "$tmpd/ja-claim/"
cp music/lyrics/anime-opening/becoming/manifest.json "$tmpd/ja-claim/"
expect_pass "claim records over a copy of the anisong sheet" \
  $LYR claim --track-dir "$tmpd/ja-claim" --author "regression-probe"

# --- the unit-level checks for the same two defects -------------------------
expect_pass "language + section-tag regressions (music/tests)" \
  $PY -m unittest music.tests.test_lyrics_gate_language

# --- direction text that WRAPS (card t_bc6a0c00, 2026-10-16) -----------------
# The genre templates' tag sheets are directions in parentheses and no lyrics.
# A direction can wrap onto a second line, and that continuation does not start
# with "(" — so the placeholder rule, which rejected a line only when it began
# AND ended with a parenthesis, read it as a lyric: the epic-orchestral-boss
# sheet produced 3 problems instead of 14 and cleared this gate. The suite reads
# that sheet from music/prompts/ and asserts both this gate and the renderer's
# own refusal (acestep_plan.py, which the render CronJob runs without
# --allow-empty) report every one of its 8 sections empty.
expect_pass "wrapped direction lines are not lyrics (music/tests)" \
  $PY -m unittest music.tests.test_acestep_sheet_guard

# --- usage errors ------------------------------------------------------------
expect_fail "no target is a usage error" 2 $GATE
expect_fail "both targets is a usage error" 2 \
  $GATE --track-dir music/lyrics --lyrics-file music/lyrics/lyrics.py

if [ "$fails" -eq 0 ]; then
  echo "OK: all $checks checks behaved as expected"
  exit 0
fi
echo "BROKEN: $fails of $checks check(s) misbehaved"
exit 1
