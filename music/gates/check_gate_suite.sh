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
python3 "$GATES/_loop_fixtures.py" "$F"
cp "$F/loop_seamless.wav" "$GOOD_LOOP/master.wav"
cp "$F/loop_broken.wav" "$BAD_LOOP/master.wav"
for d in "$GOOD_LOOP" "$BAD_LOOP"; do
  cat > "$d/loop_points.json" <<'EOF'
{"loop_start_s": 5.0, "loop_end_s": 10.0, "seamless": true}
EOF
done

# --- youtube visual packages ------------------------------------------
GOOD_YT="$F/good_yt"; BAD_YT="$F/bad_yt"
mkdir -p "$GOOD_YT" "$BAD_YT"
python3 "$GATES/_visual_fixtures.py" "$F"
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
  python3 "$GATES/gate_quota.py"
pass "quota warns (exit 0) at 56/60" \
  python3 "$GATES/gate_quota.py" --ledger "$F/warn_ledger.json"
fail_expected "quota HARD STOPS at 59/60" 1 \
  python3 "$GATES/gate_quota.py" --ledger "$F/stop_ledger.json"

# ------------------------------------------------------------------
# 2. gate_lyrics_original (existing gate — regression)
# ------------------------------------------------------------------
say "gate_lyrics_original"
pass "chill-lounge lyrics pass (human claim)" \
  python3 "$GATES/gate_lyrics_original.py" \
  --track-dir music/lyrics/chill-lounge/amber-hour --strict
pass "trance lyrics pass (human claim)" \
  python3 "$GATES/gate_lyrics_original.py" \
  --track-dir music/lyrics/trance/signal-before-dawn --strict
fail_expected "suno-generated lyric rejected" 1 \
  python3 "$GATES/gate_lyrics_original.py" \
  --lyrics-file "$GATES/fixtures/suno-generated-umbrellas-in-space.txt"

# ------------------------------------------------------------------
# 3. gate_stems_present
# ------------------------------------------------------------------
say "gate_stems_present"
pass "4 aligned stems pass" \
  python3 "$GATES/gate_stems_present.py" \
  --master "$F/streaming_master.wav" --stems-dir "$GOOD_SYNC/stems"
fail_expected "fake + truncated stems fail" 1 \
  python3 "$GATES/gate_stems_present.py" \
  --master "$F/streaming_master.wav" --stems-dir "$BAD_SYNC/stems"

# ------------------------------------------------------------------
# 4. gate_loudness
# ------------------------------------------------------------------
say "gate_loudness"
pass "streaming master (-14 dB) passes" \
  python3 "$GATES/gate_loudness.py" \
  --master "$F/streaming_master.wav" --target streaming
pass "sync master (-16 dB) passes" \
  python3 "$GATES/gate_loudness.py" \
  --master "$F/sync_master.wav" --target sync
fail_expected "loud master (-12 dB) fails honestly" 1 \
  python3 "$GATES/gate_loudness.py" \
  --master "$F/loud_master.wav" --target streaming

# ------------------------------------------------------------------
# 5. gate_quality
# ------------------------------------------------------------------
say "gate_quality"
pass "independent review (different model) passes" \
  python3 "$GATES/gate_quality.py" --package-dir "$GOOD_QUAL"
fail_expected "same-model review is not independent" 1 \
  python3 "$GATES/gate_quality.py" --package-dir "$BAD_QUAL"

# ------------------------------------------------------------------
# 6. gate_sync_ready
# ------------------------------------------------------------------
say "gate_sync_ready"
pass "complete sync package passes" \
  python3 "$GATES/gate_sync_ready.py" --package-dir "$GOOD_SYNC"
fail_expected "broken stems + copied instrumental fail" 1 \
  python3 "$GATES/gate_sync_ready.py" --package-dir "$BAD_SYNC"
fail_expected "direct-license lane requires license tiers" 1 \
  python3 "$GATES/gate_sync_ready.py" --package-dir "$GOOD_SYNC" \
  --lane direct-license

# ------------------------------------------------------------------
# 7. gate_release_ready
# ------------------------------------------------------------------
say "gate_release_ready"
pass "complete release package passes" \
  python3 "$GATES/gate_release_ready.py" --package-dir "$GOOD_REL"
fail_expected "fake artwork + invalid ISRC fail" 1 \
  python3 "$GATES/gate_release_ready.py" --package-dir "$BAD_REL"

# ------------------------------------------------------------------
# 8. gate_loop_points
# ------------------------------------------------------------------
say "gate_loop_points"
pass "seamless loop (1.6x curvature) passes" \
  python3 "$GATES/gate_loop_points.py" \
  --master "$GOOD_LOOP/master.wav" \
  --loop-points "$GOOD_LOOP/loop_points.json" \
  --scratch "$SCRATCH/loop_scratch"
fail_expected "phase-slip loop (6.0x curvature) fails" 1 \
  python3 "$GATES/gate_loop_points.py" \
  --master "$BAD_LOOP/master.wav" \
  --loop-points "$BAD_LOOP/loop_points.json" \
  --scratch "$SCRATCH/loop_scratch"

# ------------------------------------------------------------------
# 9. gate_youtube_authentic
# ------------------------------------------------------------------
say "gate_youtube_authentic"
pass "varied visual passes (5 distinct scenes, low similarity)" \
  python3 "$GATES/gate_youtube_authentic.py" \
  --visual "$GOOD_YT/visual.mp4" \
  --upload-index "$F/upload_index.json" \
  --min-distinct-frames 4
fail_expected "raw dump (static image) fails" 1 \
  python3 "$GATES/gate_youtube_authentic.py" \
  --visual "$BAD_YT/visual.mp4" \
  --upload-index "$F/upload_index.json" \
  --min-distinct-frames 4

# ------------------------------------------------------------------
# 10. gate_human_approval
# ------------------------------------------------------------------
say "gate_human_approval"
pass "j_kro approval (hash-bound, dated) passes" \
  python3 "$GATES/gate_human_approval.py" \
  --package-dir "$GOOD_APPR"
fail_expected "bot approval + wrong hash fails" 1 \
  python3 "$GATES/gate_human_approval.py" \
  --package-dir "$BAD_APPR"
fail_expected "no approval record fails" 1 \
  python3 "$GATES/gate_human_approval.py" \
  --package-dir "$GOOD_SYNC"

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
