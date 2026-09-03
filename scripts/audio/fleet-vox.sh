#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# fleet-vox.sh — dispatch a VoxCPM render to a FLEET GPU (j_kro directive)
#
# j_kro STANDING AUTHORIZATION (2026-09-03): "it's FINE to pause the miners
# temporarily while inferencing." Miners resume immediately after (even on fail).
#
# Usage:
#   fleet-vox.sh --host nexus --gpu 0 --text "..." --out /tmp/x.mp3 [--quality q8]
#   fleet-vox.sh --host forge --gpu 1 --text "..." --out /tmp/y.mp3
#
# Flow:
#   1. Ensure the remote has the voxcpm stack (venv + script). Sync once if missing.
#   2. Pause the host's miner(s) (revenue-logged).
#   3. SSH: run voxcpm_generate.py with CUDA_VISIBLE_DEVICES=<gpu> (the 3090/4060).
#   4. ALWAYS resume the miner (trap on failure).
#   5. Copy the output back to the local path.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

HOST="" GPU_IDX="0" TEXT="" OUT="" QUALITY="q8" VOICE_DESC=""

while [ $# -gt 0 ]; do
  case "$1" in
    --host) HOST="$2"; shift 2 ;;
    --gpu) GPU_IDX="$2"; shift 2 ;;
    --text) TEXT="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    --quality) QUALITY="$2"; shift 2 ;;
    --voice-desc) VOICE_DESC="$2"; shift 2 ;;
    *) echo "unknown: $1"; exit 2 ;;
  esac
done

[ -n "$HOST" ] && [ -n "$TEXT" ] && [ -n "$OUT" ] || {
  echo "usage: fleet-vox.sh --host <host> --gpu <idx> --text <text> --out <path> [--quality q8]"
  exit 2
}

echo "═══ FLEET-VOX: $HOST GPU $GPU_IDX ═══"
MINER_UNIT=""
case "$HOST" in
  nexus)  MINER_UNIT="peakminer-nexus-3060ti.service" ;;
  forge)  MINER_UNIT="peakminer-dropin-forge-4060-0.service" ;;  # pause 4060-0; jobs use 4060-0
  *) echo "unknown host: $HOST (nexus|forge)"; exit 2 ;;
esac

# 0. Reachability
timeout 6 ssh "$HOST" true 2>/dev/null || { echo "FATAL: $HOST unreachable"; exit 1; }

# 1. Ensure voxcpm stack on remote (venv + wrapper script). Sync zephyr's copy once.
REMOTE_STACK_OK=$(timeout 10 ssh "$HOST" 'test -f ~/Projects/VoxCPM/.venv/bin/python && echo yes || echo no' 2>/dev/null || echo no)
if [ "$REMOTE_STACK_OK" != "yes" ]; then
  echo "── syncing voxcpm stack to $HOST (first time, ~2-4GB) ──"
  timeout 15 ssh "$HOST" 'mkdir -p ~/Projects/VoxCPM ~/Projects/ai-content-pipeline/scripts/audio' 2>/dev/null || true
  rsync -az --timeout=30 ~/Projects/VoxCPM/.venv "$HOST:~/Projects/VoxCPM/" 2>/dev/null || echo "WARN: venv rsync incomplete (may need full copy)"
  rsync -az ~/Projects/ai-content-pipeline/scripts/audio/voxcpm_generate.py "$HOST:~/Projects/ai-content-pipeline/scripts/audio/" 2>/dev/null
  # Model cache is the big one — check if HF model is present
  timeout 10 ssh "$HOST" 'test -d ~/.cache/huggingface/hub/models--openbmb--VoxCPM2 && echo model-present || echo model-missing' 2>/dev/null
fi

# 2. Pause the miner (STANDING AUTHORIZATION — j_kro)
echo "── pausing $HOST:$MINER_UNIT ──"
timeout 10 ssh "$HOST" "systemctl stop '$MINER_UNIT'" 2>/dev/null && echo "paused" || echo "(pause skipped — already stopped?)"

# 3. Ensure resume happens even on failure
RESUMED=0
resume_miner() {
  if [ "$RESUMED" = "0" ]; then
    echo "── RESUME $HOST:$MINER_UNIT ──"
    timeout 10 ssh "$HOST" "systemctl start '$MINER_UNIT'" 2>/dev/null && echo "resumed" || echo "WARN: resume failed"
    RESUMED=1
  fi
}
trap resume_miner EXIT

# 4. Run the render remotely on the target GPU
VOICE_ARG=""
[ -n "$VOICE_DESC" ] && VOICE_ARG="--voice-desc '$(echo "$VOICE_DESC" | sed "s/'/\\'/g")'"
REMOTE_OUT="/tmp/vox-out-$$.mp3"
echo "── render on $HOST GPU $GPU_IDX ──"
timeout 900 ssh "$HOST" "cd ~/Projects/ai-content-pipeline && CUDA_VISIBLE_DEVICES='$GPU_IDX' ~/Projects/VoxCPM/.venv/bin/python scripts/audio/voxcpm_generate.py --text '$(echo "$TEXT" | sed "s/'/\\'/g")' --out '$REMOTE_OUT' --quality '$QUALITY' $VOICE_ARG" 2>&1 | tail -5

# 5. Copy output back
if timeout 15 ssh "$HOST" "test -f '$REMOTE_OUT' && echo exists" 2>/dev/null | grep -q exists; then
  scp -q "$HOST:$REMOTE_OUT" "$OUT" 2>/dev/null && echo "OUTPUT: $OUT"
  timeout 10 ssh "$HOST" "rm -f '$REMOTE_OUT'" 2>/dev/null || true
else
  echo "ERROR: no output from remote render"
  exit 1
fi

# 6. resume_miner runs via trap
echo "═══ FLEET-VOX DONE ═══"
