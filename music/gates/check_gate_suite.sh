#!/usr/bin/env bash
# Acceptance matrix for the executable gate suite (music/gates/).
#
# For EACH gate: one PASS on a good artifact and one FAIL on a
# deliberately broken one. Exit 0 only when every gate behaved
# as expected.
#
# Usage: bash music/gates/check_gate_suite.sh
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO"
GATES="$REPO/music/gates"
SCRATCH="${GATE_SCRATCH:-/tmp/music-gate-fixtures}"
fails=0

# ------------------------------------------------------------------
# interpreter resolution (incident 2026-10-16, card t_d3b9e218)
# ------------------------------------------------------------------
# Bare `python3` is NOT safe here. In a worker shell it resolves to the
# Hermes bundled interpreter (~/.hermes/tools/python-3.14.7+*/bin/python3),
# which has no PyYAML. gate_lyrics_original imports music/lyrics/lyrics.py,
# which imports yaml, so those two checks died with
#   ModuleNotFoundError: No module named 'yaml'
# and the suite reported "BROKEN: 2 check(s) misbehaved" for a gate that was
# actually fine. Resolve ONE interpreter that can `import yaml` and use it
# for every check; refuse to run rather than report a false BAD.
# Honour an explicit PY= override when it works; else prefer /usr/bin/python3.
if [ -n "${PY:-}" ] && "$PY" -c 'import yaml' >/dev/null 2>&1; then
  :
else
  PY=""
  for cand in /usr/bin/python3 python3; do
    if "$cand" -c 'import yaml' >/dev/null 2>&1; then PY="$cand"; break; fi
  done
fi
if [ -z "$PY" ]; then
  echo "FATAL: no python3 with PyYAML found (tried \$PY, /usr/bin/python3, python3)" >&2
  echo "       gate_lyrics_original needs it; refusing to report a false BAD." >&2
  exit 2
fi
echo "interpreter: $PY"

# ------------------------------------------------------------------
# generator dependency guard (incident 2026-10-16, card t_5ed495eb)
# ------------------------------------------------------------------
# The pack fixtures are built by the REAL generator (music/assets/pack.py) on
# purpose: the defect this suite now covers was generator-vs-gate drift, so a
# hand-written fixture would hide it. pack.py imports numpy + scipy. On the
# lane host /usr/bin/python3 has numpy (distro) but scipy had to be installed
# for the user site. Refuse to run rather than report a false BAD or skip the
# pack checks in silence.
if ! "$PY" -c 'import numpy, scipy' >/dev/null 2>&1; then
  echo "FATAL: $PY cannot import numpy+scipy, so music/assets/pack.py cannot run" >&2
  echo "       install for that interpreter, e.g.:" >&2
  echo "       uv pip install --python $PY \\" >&2
  echo "         --target ~/.local/lib/python3.14/site-packages --no-deps scipy" >&2
  exit 2
fi

mkdir -p "$SCRATCH"

# ------------------------------------------------------------------
# helpers
# ------------------------------------------------------------------
pass() { # label, then command
  local label="$1"; shift
  if "$@" >/tmp/gate_out.$$ 2>&1; then
    echo "PASS  $label"
  else
    echo "BAD   $label (expected exit 0, got $?)"
    sed 's/^/        /' /tmp/gate_out.$$
    fails=$((fails+1))
  fi
}

fail_expected() { # label, expected-exit, then command
  local label="$1"; local want="$2"; shift 2
  local got=0
  "$@" >/tmp/gate_out.$$ 2>&1 || got=$?
  if [ "$got" -eq "$want" ]; then
    echo "FAILS $label (exit $want, as expected)"
  else
    echo "BAD   $label (expected exit $want, got $got)"
    sed 's/^/        /' /tmp/gate_out.$$
    fails=$((fails+1))
  fi
}

say() { echo; echo "## $1"; }

fail_reason() { # label, expected-exit, output pattern, then command
  local label="$1"; local want="$2"; local pat="$3"; shift 3
  local got=0
  "$@" >/tmp/gate_out.$$ 2>&1 || got=$?
  if [ "$got" -ne "$want" ]; then
    echo "BAD   $label (expected exit $want, got $got)"
    sed 's/^/        /' /tmp/gate_out.$$
    fails=$((fails+1))
  elif ! grep -qF -- "$pat" /tmp/gate_out.$$; then
    # An exit code alone does not say WHY a gate refused. Card t_bab8aa19 was a
    # gate that PASSED a broken artifact, so its check must read the refusal:
    # "a faded tail fails" is only true if the gate said it failed for the
    # LEVEL, not because the fixture was accidentally clicky.
    echo "BAD   $label (exit $want, as expected, but the output never said: $pat)"
    sed 's/^/        /' /tmp/gate_out.$$
    fails=$((fails+1))
  else
    echo "FAILS $label (exit $want, refused for \"$pat\", as expected)"
  fi
}

# A fixture builder that dies must stop the suite. Otherwise every case that
# reads its output fails for the wrong reason ("no such package directory")
# and `fail_expected` records it as a pass — a check that passes vacuously.
# Measured: the pack fixtures failed to build and 6 pack cases still reported
# "as expected" (card t_5ed495eb).
build_fixtures() { # label, then command
  local label="$1"; shift
  if ! "$@" >/tmp/gate_fix.$$ 2>&1; then
    echo "FATAL: $label fixtures could not be built — refusing to run the"
    echo "       suite against missing fixtures (that is how a check passes"
    echo "       vacuously)."
    sed 's/^/        /' /tmp/gate_fix.$$
    rm -f /tmp/gate_fix.$$
    exit 2
  fi
}

# ------------------------------------------------------------------
# 0. build fixtures (audio is synthesized with ffmpeg; nothing is
#    trusted from disk — every gate re-measures it)
# ------------------------------------------------------------------
say "building fixtures"
F="$SCRATCH"

# masters at three loudness levels (volumedetect-verified below)
ffmpeg -y -v error -f lavfi -i "sine=frequency=440:duration=10" \
  -af "volume=10dB" -ar 44100 -ac 2 "$F/streaming_master.wav"
ffmpeg -y -v error -f lavfi -i "sine=frequency=440:duration=10" \
  -af "volume=8dB" -ar 44100 -ac 2 "$F/sync_master.wav"
ffmpeg -y -v error -f lavfi -i "sine=frequency=440:duration=10" \
  -af "volume=12dB" -ar 44100 -ac 2 "$F/loud_master.wav"

# four stems, time-aligned to the master
for s in drums bass keys vox; do
  ffmpeg -y -v error -f lavfi -i "sine=frequency=440:duration=10" \
    -ar 44100 -ac 2 "$F/stem_$s.wav"
done

# artwork
ffmpeg -y -v error -f lavfi -i "color=c=0x224488:s=3000x3000:d=1" \
  -frames:v 1 "$F/artwork.jpg"

# clearance doc (real PDF header)
printf '%%PDF-1.4\nfake clearance doc\n' > "$F/clearance.pdf"

# disclosure
cat > "$F/disclosure.txt" <<'EOF'
AI disclosure: music generated with Suno AI (Premier).
Lyrics are original, human-authored.
EOF

# metadata
cat > "$F/metadata.json" <<'EOF'
{
  "metadata": {
    "title": "Test Tone Suite",
    "artist": "Music Producer",
    "bpm": 120,
    "key": "A minor",
    "mood": "energetic",
    "genre": "chill-lounge"
  }
}
EOF

# release metadata (valid ISRC: CC-OOO-YY-NNNNN)
cat > "$F/release_metadata.json" <<'EOF'
{
  "metadata": {
    "title": "Test Tone Suite",
    "artist": "Music Producer",
    "isrc": "CA-AB2-26-00001",
    "genre": "chill-lounge",
    "ai_disclosure": "AI-generated music, human-directed"
  }
}
EOF

# --- sync packages -------------------------------------------------
GOOD_SYNC="$F/good_sync"; BAD_SYNC="$F/bad_sync"
mkdir -p "$GOOD_SYNC/stems" "$BAD_SYNC/stems"
cp "$F/streaming_master.wav" "$GOOD_SYNC/full_mix.wav"
ffmpeg -y -v error -f lavfi -i "sine=frequency=440:duration=10" \
  -af "volume=6dB" -ar 44100 -ac 2 "$GOOD_SYNC/instrumental.wav"
cp "$F/clearance.pdf" "$GOOD_SYNC/clearance_doc.pdf"
cp "$F/disclosure.txt" "$GOOD_SYNC/ai_disclosure.txt"
cp "$F/metadata.json" "$GOOD_SYNC/manifest.json"
for s in drums bass keys vox; do
  cp "$F/stem_$s.wav" "$GOOD_SYNC/stems/stem_$s.wav"
done
# broken: one fake stem (text), one truncated stem, copied instrumental
cp -r "$GOOD_SYNC/." "$BAD_SYNC/"
printf 'text-not-audio' > "$BAD_SYNC/stems/stem_bass.wav"
head -c 300 "$F/streaming_master.wav" > "$BAD_SYNC/stems/stem_keys.wav"
cp "$F/streaming_master.wav" "$BAD_SYNC/instrumental.wav"

# --- release packages ----------------------------------------------
GOOD_REL="$F/good_release"; BAD_REL="$F/bad_release"
mkdir -p "$GOOD_REL" "$BAD_REL"
cp "$F/streaming_master.wav" "$GOOD_REL/master.wav"
cp "$F/artwork.jpg" "$GOOD_REL/artwork.jpg"
cp "$F/release_metadata.json" "$GOOD_REL/manifest.json"
cp "$F/disclosure.txt" "$GOOD_REL/ai_disclosure.txt"
cp "$F/streaming_master.wav" "$BAD_REL/master.wav"
printf 'not-an-image' > "$BAD_REL/artwork.jpg"
cat > "$BAD_REL/manifest.json" <<'EOF'
{"metadata": {"title": "T", "artist": "A",
  "isrc": "XX-INVALID-ISRC", "genre": "g",
  "ai_disclosure": "yes"}}
EOF
printf 'x' > "$BAD_REL/ai_disclosure.txt"

# --- quality (independent review) packages --------------------------
GOOD_QUAL="$F/good_quality"; BAD_QUAL="$F/bad_quality"
mkdir -p "$GOOD_QUAL" "$BAD_QUAL"
MASTER_SHA="$(sha256sum "$F/streaming_master.wav" | cut -d' ' -f1)"
cp "$F/streaming_master.wav" "$GOOD_QUAL/master.wav"
cat > "$GOOD_QUAL/review.json" <<EOF
{"master": {"sha256": "$MASTER_SHA", "path": "master.wav"},
 "reviewer_model": "deepseek-chat",
 "producer_model": "suno-v4.5",
 "verdict": "pass",
 "findings": ["structure clear", "loudness within spec"],
 "reviewed_at": "2026-10-08T08:45:00",
 "reviewer": "reviewer-deepseek"}
EOF
cp "$F/streaming_master.wav" "$BAD_QUAL/master.wav"
cat > "$BAD_QUAL/review.json" <<EOF
{"master": {"sha256": "$MASTER_SHA", "path": "master.wav"},
 "reviewer_model": "suno-v4.5",
 "producer_model": "suno-v4.5",
 "verdict": "pass",
 "findings": [],
 "reviewed_at": "2026-10-08T08:45:00",
 "reviewer": "producer-self"}
EOF

# --- human approval packages ----------------------------------------
GOOD_APPR="$F/good_approval"; BAD_APPR="$F/bad_approval"
mkdir -p "$GOOD_APPR" "$BAD_APPR"
cp "$F/streaming_master.wav" "$GOOD_APPR/master.wav"
touch -d "2026-10-08 08:00:00 UTC" "$GOOD_APPR/master.wav"
cat > "$GOOD_APPR/approval.json" <<EOF
{"approver": "j_kro",
 "approved_at": "2026-10-08T09:00:00+00:00",
 "action": "approve-public",
 "artifact": {"sha256": "$MASTER_SHA", "path": "master.wav"},
 "note": "angle approved for streaming"}
EOF
cp "$F/streaming_master.wav" "$BAD_APPR/master.wav"
cat > "$BAD_APPR/approval.json" <<EOF
{"approver": "publishbot",
 "approved_at": "2026-10-08T09:00:00+00:00",
 "action": "approve-public",
 "artifact": {"sha256": "deadbeef", "path": "master.wav"},
 "note": "auto"}
EOF

# --- loop packages (seamless 220 Hz vs phase-slip 220.5 Hz) --------
GOOD_LOOP="$F/good_loop"; BAD_LOOP="$F/bad_loop"
mkdir -p "$GOOD_LOOP" "$BAD_LOOP"
build_fixtures "loop" "$PY" "$GATES/_loop_fixtures.py" "$F"
cp "$F/loop_seamless.wav" "$GOOD_LOOP/master.wav"
cp "$F/loop_broken.wav" "$BAD_LOOP/master.wav"
for d in "$GOOD_LOOP" "$BAD_LOOP"; do
  cat > "$d/loop_points.json" <<'EOF'
{"loop_start_s": 5.0, "loop_end_s": 10.0, "seamless": true}
EOF
done

# --- the fade-out tail (card t_bab8aa19) ---------------------------
# A third broken loop, and a different KIND of break: the tail fades out
# smoothly over 1.6 s, so the junction curvature stays under its ceiling
# (measured 2.21x) and the old gate PASSED it as "seamless" while its last
# 1 s measured 8.8 dB below its first 1 s. This is the artifact class the
# `game-assets` lane must never ship (music/rubrics/gamer.json reject_signals:
# "fade-out or truncated ending on a game-loop claim").
FADED_LOOP="$F/faded_loop"
mkdir -p "$F/faded_loop"
cp "$F/loop_faded.wav" "$FADED_LOOP/master.wav"
cat > "$FADED_LOOP/loop_points.json" <<'EOF'
{"loop_start_s": 5.0, "loop_end_s": 10.0, "seamless": true}
EOF

# --- the three end-guard fixtures (card t_8297d2c6) ------------------------
# The 1.0 s fade: level ruler blind (4.7 dB), end guard refuses it.
# The quiet loop (-28 dB, above the -50 dB floor): must still PASS.
# The both-ends-silent loop: the symmetric hole of the level ruler.
for name in faded_short quiet silent_ends; do
  dir="$F/${name}_loop"
  mkdir -p "$dir"
  cp "$F/loop_${name}.wav" "$dir/master.wav"
  cat > "$dir/loop_points.json" <<'EOF'
{"loop_start_s": 5.0, "loop_end_s": 10.0, "seamless": true}
EOF
done
FADED_SHORT_LOOP="$F/faded_short_loop"
QUIET_LOOP="$F/quiet_loop"
SILENT_ENDS_LOOP="$F/silent_ends_loop"

# --- asset packs (generator-built + conforming + broken) -----------
# Built by music/assets/pack.py for the generator pack: see card t_5ed495eb.
build_fixtures "asset pack" "$PY" "$GATES/_pack_fixtures.py" "$F"

# --- youtube visual packages ------------------------------------------
GOOD_YT="$F/good_yt"; BAD_YT="$F/bad_yt"
mkdir -p "$GOOD_YT" "$BAD_YT"
build_fixtures "visual" "$PY" "$GATES/_visual_fixtures.py" "$F"
cp "$F/good_visual.mp4" "$GOOD_YT/visual.mp4"
cp "$F/disclosure.txt" "$GOOD_YT/disclosure.txt"
cp "$F/raw_dump.mp4" "$BAD_YT/visual.mp4"

# quota ledgers
cat > "$F/warn_ledger.json" <<'EOF'
{"period": "2026-10", "standard_downloads_used": 56,
 "standard_downloads_limit": 60, "studio_exports": 10,
 "credits_used": 1000, "credits_limit": 10000,
 "warn_at": 55, "hard_stop_at": 58}
EOF
cat > "$F/stop_ledger.json" <<'EOF'
{"period": "2026-10", "standard_downloads_used": 59,
 "standard_downloads_limit": 60, "studio_exports": 10,
 "credits_used": 1000, "credits_limit": 10000,
 "warn_at": 55, "hard_stop_at": 58}
EOF

# ------------------------------------------------------------------
# 1. gate_quota
# ------------------------------------------------------------------
say "gate_quota"
pass "quota passes at 0/60 (real ledger)" \
  "$PY" "$GATES/gate_quota.py"
pass "quota warns (exit 0) at 56/60" \
  "$PY" "$GATES/gate_quota.py" --ledger "$F/warn_ledger.json"
fail_expected "quota HARD STOPS at 59/60" 1 \
  "$PY" "$GATES/gate_quota.py" --ledger "$F/stop_ledger.json"

# ------------------------------------------------------------------
# 2. gate_lyrics_original (existing gate — regression)
# ------------------------------------------------------------------
say "gate_lyrics_original"
pass "chill-lounge lyrics pass (human claim)" \
  "$PY" "$GATES/gate_lyrics_original.py" \
  --track-dir music/lyrics/chill-lounge/amber-hour --strict
pass "trance lyrics pass (human claim)" \
  "$PY" "$GATES/gate_lyrics_original.py" \
  --track-dir music/lyrics/trance/signal-before-dawn --strict
fail_expected "suno-generated lyric rejected" 1 \
  "$PY" "$GATES/gate_lyrics_original.py" \
  --lyrics-file "$GATES/fixtures/suno-generated-umbrellas-in-space.txt"

# ------------------------------------------------------------------
# 3. gate_stems_present
# ------------------------------------------------------------------
say "gate_stems_present"
pass "4 aligned stems pass" \
  "$PY" "$GATES/gate_stems_present.py" \
  --master "$F/streaming_master.wav" --stems-dir "$GOOD_SYNC/stems"
fail_expected "fake + truncated stems fail" 1 \
  "$PY" "$GATES/gate_stems_present.py" \
  --master "$F/streaming_master.wav" --stems-dir "$BAD_SYNC/stems"

# ------------------------------------------------------------------
# 4. gate_loudness
# ------------------------------------------------------------------
say "gate_loudness"
pass "streaming master (-14 dB) passes" \
  "$PY" "$GATES/gate_loudness.py" \
  --master "$F/streaming_master.wav" --target streaming
pass "sync master (-16 dB) passes" \
  "$PY" "$GATES/gate_loudness.py" \
  --master "$F/sync_master.wav" --target sync
fail_expected "loud master (-12 dB) fails honestly" 1 \
  "$PY" "$GATES/gate_loudness.py" \
  --master "$F/loud_master.wav" --target streaming

# ------------------------------------------------------------------
# 5. gate_quality
# ------------------------------------------------------------------
say "gate_quality"
pass "independent review (different model) passes" \
  "$PY" "$GATES/gate_quality.py" --package-dir "$GOOD_QUAL"
fail_expected "same-model review is not independent" 1 \
  "$PY" "$GATES/gate_quality.py" --package-dir "$BAD_QUAL"

# ------------------------------------------------------------------
# 6. gate_sync_ready
# ------------------------------------------------------------------
say "gate_sync_ready"
pass "complete sync package passes" \
  "$PY" "$GATES/gate_sync_ready.py" --package-dir "$GOOD_SYNC"
fail_expected "broken stems + copied instrumental fail" 1 \
  "$PY" "$GATES/gate_sync_ready.py" --package-dir "$BAD_SYNC"
fail_expected "direct-license lane requires license tiers" 1 \
  "$PY" "$GATES/gate_sync_ready.py" --package-dir "$GOOD_SYNC" \
  --lane direct-license

# --- the lane name the registry assigns it (card t_d9983bb9) ---------------
# `music/lanes.yaml` gives sync-documentary `gate: gate_sync_ready`, but the
# gate's argparse rejected the name and exited 2 — a USAGE error a stage reads
# as a gate FAILURE. The lane's `requires:` are byte-for-byte the `sync` set,
# so the lane name must run the same checks, and an empty package must fail
# with exit 1 (never 2), with output identical to the `--lane sync` path.
EMPTY_PKG="$F/empty_pkg"; mkdir -p "$EMPTY_PKG"
pass "sync-documentary: the lane's own gate accepts its name" \
  "$PY" "$GATES/gate_sync_ready.py" --package-dir "$GOOD_SYNC" \
  --lane sync-documentary
fail_expected "sync-documentary on an empty package fails 1, not the incident rc=2" 1 \
  "$PY" "$GATES/gate_sync_ready.py" --package-dir "$EMPTY_PKG" \
  --lane sync-documentary
sync_sd_out="$SCRATCH/sync_empty.out"; syncdoc_out="$SCRATCH/syncdoc_empty.out"
"$PY" "$GATES/gate_sync_ready.py" --package-dir "$EMPTY_PKG" --lane sync \
  >"$sync_sd_out" 2>&1
"$PY" "$GATES/gate_sync_ready.py" --package-dir "$EMPTY_PKG" \
  --lane sync-documentary >"$syncdoc_out" 2>&1
if diff -q "$sync_sd_out" "$syncdoc_out" >/dev/null; then
  echo "SAME  sync-documentary prints the same requirement lines as --lane sync"
else
  echo "BAD   sync-documentary and --lane sync print different requirement lines"
  diff "$sync_sd_out" "$syncdoc_out" | sed 's/^/        /'
  fails=$((fails+1))
fi

# ------------------------------------------------------------------
# 7. gate_release_ready
# ------------------------------------------------------------------
say "gate_release_ready"
pass "complete release package passes" \
  "$PY" "$GATES/gate_release_ready.py" --package-dir "$GOOD_REL"
fail_expected "fake artwork + invalid ISRC fail" 1 \
  "$PY" "$GATES/gate_release_ready.py" --package-dir "$BAD_REL"

# ------------------------------------------------------------------
# 8. gate_loop_points
# ------------------------------------------------------------------
say "gate_loop_points"
pass "seamless loop (1.6x curvature) passes" \
  "$PY" "$GATES/gate_loop_points.py" \
  --master "$GOOD_LOOP/master.wav" \
  --loop-points "$GOOD_LOOP/loop_points.json" \
  --scratch "$SCRATCH/loop_scratch"
fail_expected "phase-slip loop (6.0x curvature) fails" 1 \
  "$PY" "$GATES/gate_loop_points.py" \
  --master "$BAD_LOOP/master.wav" \
  --loop-points "$BAD_LOOP/loop_points.json" \
  --scratch "$SCRATCH/loop_scratch"
# The fade-out tail must be refused FOR THE LEVEL, not for a click: the same
# fixture measures 2.21x curvature (under the 3.0x ceiling). Card t_bab8aa19.
fail_reason "faded loop tail fails on the LEVEL ruler, not the curvature one" 1 \
  "loop level drops" \
  "$PY" "$GATES/gate_loop_points.py" \
  --master "$FADED_LOOP/master.wav" \
  --loop-points "$FADED_LOOP/loop_points.json" \
  --scratch "$SCRATCH/loop_scratch"

# --- the short fade, the hole the level ruler cannot see (t_8297d2c6) ------
# A 1.0 s fade-out tail is SMOOTH (curvature passes it) and its 1.0 s / 6 dB
# level delta is only 4.7 dB (the level ruler passes it, by arithmetic: a
# linear fade of length d >= L reads (L/d)/sqrt(3)). The END guard is the
# ruler that refuses it: inside its last 1.0 s the first half sits 8.5 dB
# above the second. The refusal must NAME the ramp — if this case ever exits
# 0, the false PASS of card t_8297d2c6 has returned.
fail_reason "a 1.0s fade-out tail fails on the END RAMP, not the level" 1 \
  "loop end ramps" \
  "$PY" "$GATES/gate_loop_points.py" \
  --master "$FADED_SHORT_LOOP/master.wav" \
  --loop-points "$FADED_SHORT_LOOP/loop_points.json" \
  --scratch "$SCRATCH/loop_scratch"
# ... and the same artifact's level measurement must still be UNDER the
# ceiling, so the suite proves which ruler decided.
if "$PY" "$GATES/gate_loop_points.py" \
     --master "$FADED_SHORT_LOOP/master.wav" \
     --loop-points "$FADED_SHORT_LOOP/loop_points.json" \
     --scratch "$SCRATCH/loop_scratch" >/tmp/gate_out.$$ 2>&1; then
  echo "BAD   the 1.0s fade case passed the gate"
  fails=$((fails+1))
elif grep -qF "loop level drops" /tmp/gate_out.$$; then
  echo "BAD   the 1.0s fade was refused by the LEVEL ruler — it is no longer the short-fade case"
  sed 's/^/        /' /tmp/gate_out.$$
  fails=$((fails+1))
else
  echo "FAILS the 1.0s fade is refused for the END RAMP while its level delta stays under the ceiling"
fi

# --- the end guard must not punish a quiet (nonzero) ending ---------------
# -28 dB is quiet and it clears the lane's -50 dB floor, so the end guard
# must leave it alone: quiet is not silence (card t_8297d2c6).
pass "a quiet but NONZERO loop ending still passes (above the -50 dB floor)" \
  "$PY" "$GATES/gate_loop_points.py" \
  --master "$QUIET_LOOP/master.wav" \
  --loop-points "$QUIET_LOOP/loop_points.json" \
  --scratch "$SCRATCH/loop_scratch"
# ... and a loop silent at BOTH ends is refused FOR THE SILENCE: two silent
# ends match each other, which is exactly the elemental-air master the level
# ruler accepted (head-1s -59.5 dB, tail-1s -58.7 dB, delta 0.8 dB).
fail_reason "a loop silent at both ends fails on the silence floor" 1 \
  "is silence" \
  "$PY" "$GATES/gate_loop_points.py" \
  --master "$SILENT_ENDS_LOOP/master.wav" \
  --loop-points "$SILENT_ENDS_LOOP/loop_points.json" \
  --scratch "$SCRATCH/loop_scratch"

# ------------------------------------------------------------------
# 8b. the standalone loop-seam report (cards t_97494e6a, t_88879c37)
# ------------------------------------------------------------------
# `music/scripts/loop_seam_check.py` delegates its curvature ruler to
# gate_loop_points and used to read the DELEGATED RUN'S EXIT STATUS as the curvature
# verdict. That gate now runs THREE rulers, so a level-only refusal was printed as a
# CURVATURE failure: measured 2026-10-16 on a 2.21x loop (UNDER the 3.0x ceiling) the
# tool printed `curvature: FAIL 2.21x` and printed the gate's level-fix line as
# curvature evidence. Its own --selftest — the finding written down as an executable
# expectation — went red and STAYED red, because nothing ran it. That is the same
# shape as this suite's reason to exist (t_b16b9046): a check with no runner rots
# silently, and a brief ends up quoting the rot.
#
# These cases are what makes the fix a check rather than a claim:
#   * the selftest runs HERE, and its documented expectation is NOT edited to match a
#     broken tool — A both rulers PASS; B curvature PASS 2.21x / level FAIL 8.9 dB
#     (the fade is still caught); C and D curvature FAIL. A future ruler change that
#     moves any of those is RED here, not in a brief.
#   * on the faded fixture the tool's report must say the curvature ruler PASSes and
#     the LEVEL ruler is the one refusing (before the fix: `curvature: FAIL 2.21x`).
#   * the 1.0s fade is the false-pass guard on the tool itself: both of the tool's own
#     rulers PASS it (curvature 2.21x, level 4.7 dB) while the gate's end-ramp guard
#     refuses it — so the tool must report the gate's refusal instead of a pass. A
#     tool that agrees to a false pass is worse than the defect it was written for.
say "loop_seam_check (cards t_97494e6a, t_88879c37)"
pass "loop_seam_check --selftest: A both PASS, B curvature PASS 2.21x + level FAIL 8.9 dB, C/D curvature FAIL" \
  "$PY" "$REPO/music/scripts/loop_seam_check.py" --selftest
fail_reason "loop_seam_check on a faded loop: the CURVATURE ruler says PASS (2.21x is under the ceiling)" 1 \
  "curvature: PASS" \
  "$PY" "$REPO/music/scripts/loop_seam_check.py" \
  --master "$FADED_LOOP/master.wav" \
  --loop-points "$FADED_LOOP/loop_points.json" \
  --scratch "$SCRATCH/loop_scratch"
fail_reason "loop_seam_check on a faded loop: the LEVEL ruler is the one that refuses it" 1 \
  "level    : FAIL" \
  "$PY" "$REPO/music/scripts/loop_seam_check.py" \
  --master "$FADED_LOOP/master.wav" \
  --loop-points "$FADED_LOOP/loop_points.json" \
  --scratch "$SCRATCH/loop_scratch"
fail_reason "loop_seam_check never outvotes the gate: a 1.0s fade passes both its rulers, the gate's end ramp refuses it" 1 \
  "gate     : FAIL" \
  "$PY" "$REPO/music/scripts/loop_seam_check.py" \
  --master "$FADED_SHORT_LOOP/master.wav" \
  --loop-points "$FADED_SHORT_LOOP/loop_points.json" \
  --scratch "$SCRATCH/loop_scratch"

# ------------------------------------------------------------------
# 8c. asset packs — gate_sync_ready pack mode + gate_loop_points sweep
#     (card t_5ed495eb: the generator's own output must pass the gate it is
#      built for, every loop must be seam-checked, and the pack shape must
#      NOT weaken the per-track shape the sync lane still requires)
# ------------------------------------------------------------------
say "gate_sync_ready (pack mode, lane game-assets)"
pass "generator-built pack passes (pack mode)" \
  "$PY" "$GATES/gate_sync_ready.py" \
  --package-dir "$F/pack" --lane game-assets
pass "explicit --mode pack on the same pack" \
  "$PY" "$GATES/gate_sync_ready.py" \
  --package-dir "$F/pack" --lane game-assets --mode pack
pass "hand-built conforming pack passes (pack mode)" \
  "$PY" "$GATES/gate_sync_ready.py" \
  --package-dir "$F/pack_synth" --lane game-assets
fail_expected "a pack is NOT a sync package (per-track shape enforced)" 1 \
  "$PY" "$GATES/gate_sync_ready.py" --package-dir "$F/pack" --lane sync
fail_expected "pack: a 1.0s loop point breaks the 2s floor" 1 \
  "$PY" "$GATES/gate_sync_ready.py" \
  --package-dir "$F/pack_bad_span" --lane game-assets
fail_expected "pack: a clicky loop is not seamless (seam measured)" 1 \
  "$PY" "$GATES/gate_sync_ready.py" \
  --package-dir "$F/pack_bad_seam" --lane game-assets
fail_reason "pack: a faded loop is not seamless (LEVEL ruler, not curvature)" 1 \
  "loop level drops" \
  "$PY" "$GATES/gate_sync_ready.py" \
  --package-dir "$F/pack_bad_fade" --lane game-assets
fail_expected "pack: manifest counts must match the files on disk" 1 \
  "$PY" "$GATES/gate_sync_ready.py" \
  --package-dir "$F/pack_bad_count" --lane game-assets
fail_expected "pack: metadata without sample_rate fails" 1 \
  "$PY" "$GATES/gate_sync_ready.py" \
  --package-dir "$F/pack_bad_meta" --lane game-assets
fail_expected "pack: no loop_points.json fails" 1 \
  "$PY" "$GATES/gate_sync_ready.py" \
  --package-dir "$F/pack_bad_noloops" --lane game-assets
fail_expected "pack: no clearance_doc fails" 1 \
  "$PY" "$GATES/gate_sync_ready.py" \
  --package-dir "$F/pack_bad_noclear" --lane game-assets
fail_expected "pack: a substituted licence is not the licence of record" 1 \
  "$PY" "$GATES/gate_sync_ready.py" \
  --package-dir "$F/pack_bad_licence" --lane game-assets

say "gate_loop_points --pack-dir (checks EVERY loop)"
pass "generator-built pack: every loop seamless" \
  "$PY" "$GATES/gate_loop_points.py" \
  --pack-dir "$F/pack" --scratch "$SCRATCH/loop_scratch"
pass "hand-built conforming pack: every loop seamless" \
  "$PY" "$GATES/gate_loop_points.py" \
  --pack-dir "$F/pack_synth" --scratch "$SCRATCH/loop_scratch"
fail_expected "sweep fails when one loop is a phase-slip loop" 1 \
  "$PY" "$GATES/gate_loop_points.py" \
  --pack-dir "$F/pack_bad_seam" --scratch "$SCRATCH/loop_scratch"
fail_reason "sweep fails when one loop is a faded loop (LEVEL ruler)" 1 \
  "loop level drops" \
  "$PY" "$GATES/gate_loop_points.py" \
  --pack-dir "$F/pack_bad_fade" --scratch "$SCRATCH/loop_scratch"
fail_expected "sweep fails on a 1.0s loop point" 1 \
  "$PY" "$GATES/gate_loop_points.py" \
  --pack-dir "$F/pack_bad_span" --scratch "$SCRATCH/loop_scratch"
fail_expected "sweep fails with no loop_points.json" 1 \
  "$PY" "$GATES/gate_loop_points.py" \
  --pack-dir "$F/pack_bad_noloops" --scratch "$SCRATCH/loop_scratch"

# ------------------------------------------------------------------
# 9. gate_youtube_authentic
# ------------------------------------------------------------------
say "gate_youtube_authentic"
pass "varied visual passes (5 distinct scenes, low similarity)" \
  "$PY" "$GATES/gate_youtube_authentic.py" \
  --visual "$GOOD_YT/visual.mp4" \
  --upload-index "$F/upload_index.json" \
  --min-distinct-frames 4
fail_expected "raw dump (static image) fails" 1 \
  "$PY" "$GATES/gate_youtube_authentic.py" \
  --visual "$BAD_YT/visual.mp4" \
  --upload-index "$F/upload_index.json" \
  --min-distinct-frames 4

# ------------------------------------------------------------------
# 10. gate_human_approval
# ------------------------------------------------------------------
say "gate_human_approval"
pass "j_kro approval (hash-bound, dated) passes" \
  "$PY" "$GATES/gate_human_approval.py" \
  --package-dir "$GOOD_APPR"
fail_expected "bot approval + wrong hash fails" 1 \
  "$PY" "$GATES/gate_human_approval.py" \
  --package-dir "$BAD_APPR"
fail_expected "no approval record fails" 1 \
  "$PY" "$GATES/gate_human_approval.py" \
  --package-dir "$GOOD_SYNC"

# ------------------------------------------------------------------
# 11. the render rail's loop check (card t_b21aeb51)
# ------------------------------------------------------------------
# The render rail wrote its success `.rendered` marker on `rc=0` alone, and
# every ACE render ends in 1.5-6.2 s of digital silence, so the rail certified
# masters that cannot carry a seamless-loop claim (elemental-fire "Emberfall":
# head-1s -25.1 dB, tail-1s -58.7 dB, delta 33.6 dB). The rail now runs
# music/scripts/loop_close.py after a render of a loop-claiming plan. These two
# cases are what makes that a check rather than a claim:
#   * the FROZEN pre-fix artifact (music/tests/fixtures/loop_silence_tail.wav,
#     15.000 s = 10 s of that master + 5 s of digital silence, sha256 51473534…)
#     must still FAIL, and must fail FOR THE LEVEL/SILENCE reason;
#   * the whole loop_close suite must stay green — it binds the ported loop
#     builder to music/assets/pack.py (constants, bar count, bitwise-identical
#     crossfade/edge fade), binds the PyYAML-free registry reader to PyYAML, and
#     builds a loop out of a silence-tailed render that passes BOTH rulers.
say "the render rail's loop check (music/scripts/loop_close.py)"
fail_reason "frozen pre-fix rail output fails the rail's loop check (silence tail)" 1 \
  "is silence" \
  "$PY" "$REPO/music/scripts/loop_close.py" --check-only \
  --master "$REPO/music/tests/fixtures/loop_silence_tail.wav"
pass "loop_close suite: pack.py parity, registry reader, frozen fixture, close/refuse" \
  "$PY" -m unittest music.tests.test_loop_close

# ------------------------------------------------------------------
# 12. the render output contract (card t_320bae4c)
# ------------------------------------------------------------------
# A finished render has ONE documented path - /var/lib/music-plans/<plan-stem>.<ext>
# on the node, /plans/<plan-stem>.<ext> in the render pod - and the rail only
# writes its success `.rendered` marker when the file is THERE. Measured before
# that check existed: the wrapper's copy went to the pod's /tmp, so
# `kubectl cp <pod>:/tmp/...flac .` said NotFound and the rail reported the
# render as done anyway; the pack stage was told to read "where the brief says"
# and nothing said. These three cases are what makes the contract a check:
#   * a plan nothing was rendered for must FAIL, naming the path it looked in;
#   * a rail whose own mount is no longer the documented host path must be rc 3
#     (DRIFT), not a pass - that is the "a future change cannot silently move it"
#     half, and the file being present must not rescue it;
#   * the selftest proves all of it on real files AND compares the chart's own
#     `outHostPath` against the constant.
mkdir -p "$SCRATCH"
say "the render output contract (music/scripts/check_render_landed.py)"
fail_reason "a render that landed nowhere fails the contract check" 1 \
  "MISSING" \
  "$PY" "$REPO/music/scripts/check_render_landed.py" --check \
  --plans "$SCRATCH" --stem no-such-render-landed
fail_reason "a rail moved off the documented host path is rc 3, not a pass" 3 \
  "MOVED" \
  "$PY" "$REPO/music/scripts/check_render_landed.py" --check \
  --plans "$SCRATCH" --stem no-such-render-landed --host-path /var/lib/other-plans
pass "render output contract: red/green/moved on real files + the chart's outHostPath" \
  "$PY" "$REPO/music/scripts/check_render_landed.py" --selftest

# ------------------------------------------------------------------
# 13. the render rail's marker state machine (card t_69cab80b)
# ------------------------------------------------------------------
# The rail decided from `if <stem>.rendered exists: skip "already rendered"` and
# wrote BOTH outcomes to that one path (`""` for a render, `refused\n` for a
# draft refusal), and nothing ever removed it. Five live markers in
# /var/lib/music-plans said `refused`, and the rail's own log (job
# music-pipeline-render-29869781, 2026-10-16 16:41) printed
#   skip epic-orchestral-boss-the-last-gate (already rendered)
# for a plan whose lyrics are a scaffold - so "a human must write the sheet" was
# reported as "finished" for every draft in the queue. These cases are what makes
# the fix a check rather than a claim:
#   * a refusal stored in `.rendered` (the live bytes: `refused\n`) must be
#     ATTEMPTED, and its message must never say "already rendered";
#   * a refusal of the SAME plan must be skipped, and the plan CHANGING must
#     re-attempt it - the card's own regression case, refused -> changed ->
#     attempted;
#   * the states that cost GPU time or need a human's eyes (`.looprefused`,
#     `.noartifact`) must stay sticky through a plan change;
#   * `--check` must be RED on the conflated shape and green on a fingerprinted
#     refusal (the live check the card asks for, on a fixture so it is
#     deterministic);
#   * the chart must CALL the state machine and must not write `.rendered` or
#     `.refused` itself, which is how the two states shared one file.
say "the render rail's marker state machine (music/scripts/render_state.py)"
pass "render_state selftest: a refusal is re-entered on change, sticky states stay sticky" \
  "$PY" "$REPO/music/scripts/render_state.py" --selftest
pass "render_state suite: refused -> changed plan -> attempted, and the live bytes" \
  "$PY" -m unittest music.tests.test_render_state
CHART="${MINING_K8S:-$REPO/../mining-k8s}/helm/charts/music-pipeline/templates/cronjob-render.yaml"
if [ -f "$CHART" ]; then
  pass "the rail asks the state machine what a marker means (--decide)" \
    grep -qF -- "--decide" "$CHART"
  pass "the rail records every outcome through it (--record --state)" \
    grep -qF -- "--record" "$CHART"
  fail_expected "the rail no longer writes a .rendered marker itself" 1 \
    grep -qF -- 'marker_path(stem, "rendered").write_text' "$CHART"
  fail_expected "the rail no longer prints 'already rendered' for a marker" 1 \
    grep -qF -- 'print(f"skip   {stem} (already rendered)' "$CHART"
else
  echo "SKIP  the chart is not at $CHART on this host (set MINING_K8S=...)"
fi

# ------------------------------------------------------------------
# 14. the planner's own regression suite (card t_96dfc521)
# ------------------------------------------------------------------
# `music/tests/test_planner.py` had NO scheduled home: no .github/workflows, no
# caller in this suite, and the music units run the pipeline and the render,
# never the planner — so a rail regression was found only when a card happened
# to run it by hand. It is the acceptance matrix for the planner, which is what
# every other section here is for a gate, so it runs here (and therefore in
# `music/scripts/run_gate_matrix.sh`, the daily systemd timer).
#
# Section 6 of that file is card t_96dfc521's check: the duration rail admits the
# registry's own 16.0 s kit sting (`MIN_DURATION_S` 30 -> 16) and still refuses
# the off-grid 15 s cutdown, elemental-earth's 600 s `loop-10min` shape (card
# t_909069f0) still plans, and a refused duration writes NO plan file for the
# render rail to pick up. Section 7 is card t_3497b627's style-field check.
say "the planner regression suite (music/tests/test_planner.py)"
pass "planner: every genre plans + the duration rail admits 16 s and refuses 15 s (t_96dfc521)" \
  "$PY" "$REPO/music/tests/test_planner.py"

# ------------------------------------------------------------------
# 15. the render log (card t_d6b0cb36)
# ------------------------------------------------------------------
# `music/quota-ledger.json` says of its own `renders:` list that it is "the
# pipeline's only durable render log". Measured on nexus 2026-10-16 that log held
# ONE entry while EIGHT `.rendered` markers certified a delivered render: seven
# delivered masters (chill-lounge-slow-gold, commentary-beds-lo-fi-jazz-bed,
# commentary-beds-lo-fi-jazz-sting, elemental-earth-chamber-loop,
# elemental-fire-emberfall, final-round,
# sentimental-piano-room-with-the-light-going) were absent while
# /var/lib/sunolocal/artifacts/ held every one of them. The music existed; the LOG
# was short, because nothing kept the two in step - and nothing could: the render
# pod mounts its payload readOnly from the chart's ConfigMap and its only writable
# volume is the plans hostPath, the ledger is a file in THIS repo (read by
# music/oracle.py:load_quota), and `grep -rn quota-ledger ~/mining-k8s` finds
# nothing. So the answer is a check, not an auto-write (card t_d6b0cb36, decision
# 1), and these cases are what makes it one:
#   * a delivered render with no ledger entry must be RED, and the message must
#     name the command that fixes it;
#   * a `refused` marker needs NO entry - "Do NOT write a ledger entry for a
#     `refused` marker: those are drafts waiting on a human";
#   * a plan outside the genre registry (the rail's own smoke plan is genre
#     `test`) is a NOTE, not a RED;
#   * --record must derive the entry from live state and RE-RUNNING IT MUST NOT
#     DOUBLE-RECORD (the card's own condition), while leaving every quota counter
#     untouched;
#   * the check must be green after --record, and a replaced master must be a
#     NOTE rather than a silent pass;
#   * a ledger the check cannot read, and a plans directory that is not there,
#     must both be NON-ZERO (rc 3): "no markers" is not "in step".
# The live half (the real /var/lib/music-plans against the real ledger) is NOT
# run here, deliberately: this suite is the fixture-based acceptance matrix, and
# a live assertion inside it would report a drifted log as a BROKEN gate. That
# half is section 2c of music/scripts/run_gate_matrix.sh, where it exits 4 and is
# therefore never read as a gate defect either.
say "the render log (music/scripts/check_render_ledger.py, card t_d6b0cb36)"
pass "render ledger selftest: no entry is RED, a refusal needs none, --record cannot double-record" \
  "$PY" "$REPO/music/scripts/check_render_ledger.py" --selftest
fail_reason "the render ledger check is rc 3, not a pass, when the ledger will not read" 3 \
  "FAIL check_render_ledger" \
  "$PY" "$REPO/music/scripts/check_render_ledger.py" --check --plans "$SCRATCH" \
  --ledger "$SCRATCH/no-such-ledger.json"
fail_reason "an absent plans dir is rc 3, not a pass ('no markers' is not 'in step')" 3 \
  "FAIL check_render_ledger" \
  "$PY" "$REPO/music/scripts/check_render_ledger.py" --check \
  --plans "$SCRATCH/no-such-plans" --ledger "$REPO/music/quota-ledger.json"

# ------------------------------------------------------------------
# 16. the planner carries a HUMAN SHEET into the plan (card t_e69368ff)
# ------------------------------------------------------------------
# `--lyrics-mode draft` writes a SCAFFOLD (the tags plus the template's craft
# notes, and no singable line), and the render rail refuses a scaffold on
# purpose - so every draft entry in the queue reached the rail and stopped
# there. Measured on the queued trance entry (card t_a7a7d998): the plan carried
# 9 section tags and 0 singable lines, `.refused` was recorded for it, and the
# human-authored sheet for that same track already existed and was already
# claimed (`music/lyrics/trance/signal-before-dawn`, sha256 e667e248..., gate
# `gate_lyrics_original` PASS) - with no planner input that could put it into
# the plan. `--lyrics-mode ai` is not the fix: AI words void the authorship
# claim the sheet exists to make.
#
# `--lyrics-file` carries the sheet VERBATIM (bytes read, utf-8 decoded, so the
# plan's lyrics hash IS the sheet's manifest hash) and binds the authorship line
# to the sheet's path and sha256. These cases are what makes that a check rather
# than a claim:
#   * the plan built from the sheet passes the RENDER RAIL's own guard
#     (`acestep_plan.py` without --allow-empty) end to end, while a plan built
#     without the sheet is still refused with rc 4;
#   * a sheet with no claim, a claim whose hash no longer covers the file, an
#     `ai` claim, an empty sheet, and a sheet for another genre are all rc 2 and
#     write NO plan - the render rail reads plan files, so a refused sheet must
#     not leave one behind (card t_96dfc521's rule);
#   * the CHART PAYLOAD's planner copy carries the flag, because the CronJob
#     mounts a copy of the payload, not this repo (card t_a14e5d52's drift).
say "the planner carries a human-authored sheet (music/tests/test_planner_lyrics_file.py)"
pass "planner --lyrics-file: sheet carried verbatim, the rail's guard accepts it, a scaffold is still refused (t_e69368ff)" \
  "$PY" -m unittest music.tests.test_planner_lyrics_file

# ------------------------------------------------------------------
# 17. the render rail's backfill (card t_d7f6d053)
# ------------------------------------------------------------------
# The rail closes the delivered loop for the plan it has JUST rendered, so every
# plan rendered BEFORE that step existed (card t_b21aeb51) keeps its `.rendered`
# marker, is skipped, and never gets its loop. Measured live 2026-10-16: 7
# `.rendered` markers in /var/lib/music-plans with no render at the documented
# path - elemental-earth's 600 s `loop-10min` claim among them, on a card
# (t_909069f0) already CLOSED on an acceptance nobody could check. The bytes were
# still in the engine's own store, so the fix is a backfill, not a re-render:
# recover the master to the documented path and close the loop with the same
# music/scripts/loop_close.py the rail runs.
#
# These cases are what makes that a check rather than a claim: the backfill must
# REFUSE a mapping it cannot name (a title alone can belong to two plans), use
# the ENGINE's extension, be a no-op on the second run, and never write the
# engine's store - and the chart must run it, mount that store read-only, and
# let a refusal be reported instead of failing the render loop.
say "the render rail's backfill (music/scripts/backfill_render.py)"
pass "backfill selftest: refuses what it cannot name, recovers, closes, no-ops" \
  "$PY" "$REPO/music/scripts/backfill_render.py" --selftest
pass "backfill suite: mapping rules, engine ext, no-op re-run, store untouched" \
  "$PY" -m unittest music.tests.test_backfill_render
pass "the backfill reads the engine's store READ-ONLY (sqlite mode=ro)" \
  grep -qF -- '?mode=ro' "$REPO/music/scripts/backfill_render.py"
fail_expected "the backfill never opens the engine's store read-write" 1 \
  grep -qF -- 'mode=rw' "$REPO/music/scripts/backfill_render.py"

CHART_DIR="${MINING_K8S:-$REPO/../mining-k8s}/helm/charts/music-pipeline"
if [ -f "$CHART_DIR/templates/cronjob-render.yaml" ]; then
  pass "the rail runs the backfill" \
    grep -qF -- 'backfill_render.py' "$CHART_DIR/templates/cronjob-render.yaml"
  pass "the rail runs it BEFORE the ComfyUI probe (a backfill needs no GPU)" \
    awk '/BACKFILL, "--all"/ {b=NR} /system_stats/ {c=NR} END {exit !(b && c && b < c)}' \
    "$CHART_DIR/templates/cronjob-render.yaml"
  pass "a backfill that cannot run is REPORTED, not fatal to the render loop" \
    grep -qF -- 'the backfill did not run (' "$CHART_DIR/templates/cronjob-render.yaml"
  pass "the rail mounts the engine's store read-only" \
    grep -qF -- 'readOnly: true' "$CHART_DIR/templates/cronjob-render.yaml"
  pass "the chart names the store it mounts and points the job at it" \
    grep -qF -- 'storeMountPath' "$CHART_DIR/values.yaml"
  pass "the chart's payload carries the backfill AND the check knows its name" \
    grep -qF -- 'check_file music/scripts/backfill_render.py' "$CHART_DIR/check-payload-sync.sh"
  pass "the payload copy IS the lane's script, byte for byte" \
    cmp -s "$REPO/music/scripts/backfill_render.py" \
    "$CHART_DIR/files/music/scripts/backfill_render.py"
else
  echo "SKIP  the chart is not at $CHART on this host (set MINING_K8S=...)"
fi

# ------------------------------------------------------------------
rm -f /tmp/gate_out.$$
if [ "$fails" -eq 0 ]; then
  echo
  echo "OK: every gate passed its good artifact and failed its broken one"
  exit 0
fi
echo
echo "BROKEN: $fails check(s) misbehaved"
exit 1
