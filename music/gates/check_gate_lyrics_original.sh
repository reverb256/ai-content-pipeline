#!/usr/bin/env bash
# Regression checks for gate_lyrics_original + the lyrics stage.
# Encodes the acceptance matrix of card "original-lyrics pipeline
# (copyrightability)" and the 2026-10-08 incident where '#' provenance
# header lines were parsed as lyric body (fixed in parse_sections;
# this suite is the check that would have caught it).
#
# Usage: bash music/gates/check_gate_lyrics_original.sh
# Exit 0 = all checks behaved as expected (PASS where expected,
# FAIL where expected). Exit 1 = a check misbehaved.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO"
fails=0

expect_pass() { # label, then command
  local label="$1"; shift
  if "$@" >/tmp/gate_check_out.$$ 2>&1; then
    echo "PASS  $label"
  else
    echo "FAIL  $label (expected exit 0, got $?)"
    sed 's/^/      /' /tmp/gate_check_out.$$
    fails=$((fails+1))
  fi
}

expect_fail() { # label, expected-exit, then command
  local label="$1"; local want="$2"; shift 2
  local got=0
  "$@" >/tmp/gate_check_out.$$ 2>&1 || got=$?
  if [ "$got" -eq "$want" ]; then
    echo "FAILS $label (exit $want, as expected)"
  else
    echo "BAD   $label (expected exit $want, got $got)"
    sed 's/^/      /' /tmp/gate_check_out.$$
    fails=$((fails+1))
  fi
}

GATE="python3 music/gates/gate_lyrics_original.py"
LYR="python3 music/lyrics/lyrics.py"

# --- acceptance: 3 genres PASS with authorship claims ---------------------
expect_pass "chill-lounge track passes" $GATE --track-dir music/lyrics/chill-lounge/amber-hour --strict
expect_pass "trance track passes"       $GATE --track-dir music/lyrics/trance/signal-before-dawn --strict
expect_pass "activist track passes"     $GATE --track-dir music/lyrics/activist/what-runs-beneath --strict

# --- acceptance: gate fails a Suno-generated lyric --------------------------
expect_fail "suno-generated lyric rejected (bare file)" 1 \
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
expect_fail "post-claim edit rejected (hash mismatch)" 1 \
  $GATE --track-dir "$tmpd"

# --- unclaimed scaffold cannot pass -----------------------------------------
mkdir -p "$tmpd/unclaimed"
cp music/lyrics/activist/what-runs-beneath/lyrics.suno.txt "$tmpd/unclaimed/"
expect_fail "unclaimed sheet rejected (no manifest)" 1 \
  $GATE --track-dir "$tmpd/unclaimed"
mkdir -p "$tmpd/suno-claim"
cp music/gates/fixtures/suno-generated-umbrellas-in-space.txt "$tmpd/suno-claim/lyrics.suno.txt"
cp music/lyrics/activist/what-runs-beneath/manifest.json "$tmpd/suno-claim/"
expect_fail "claim refused over suno-generated sheet" 1 \
  $LYR claim --track-dir "$tmpd/suno-claim" --author "j_kro"

# --- usage errors ------------------------------------------------------------
expect_fail "no target is a usage error" 2 $GATE
expect_fail "both targets is a usage error" 2 \
  $GATE --track-dir music/lyrics --lyrics-file music/lyrics/lyrics.py

if [ "$fails" -eq 0 ]; then
  echo "OK: all 11 checks behaved as expected"
  exit 0
fi
echo "BROKEN: $fails check(s) misbehaved"
exit 1
