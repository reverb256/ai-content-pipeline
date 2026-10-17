#!/usr/bin/env bash
# G8: YuE2 live render via direct pipeline call on the zephyr 3090
#
# Preconditions:
#   1. The zephyr 3090 GPU must have sufficient free VRAM (> 2 GiB free).
#   2. The YuE2 source tree must be available at /home/j_kro/Work/YuE/.
#   3. The YuE2 venv Python must have torch + yue2 dependencies installed.
#   4. ffprobe must be on PATH.
#
# This script FAILS LOUDLY if the GPU is busy or the environment is not set up.
# It does NOT fall back to a fixture or skip the check.
#
# Output: FLAC file in ~/Music/yue2/g8_yue2_render/audio.flac
# Prints exactly "G8-OK" on success, exits nonzero on any failure.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

YUE2_SRC="/home/j_kro/Work/YuE"
YUE2_VENV_PY="/home/j_kro/StabilityMatrix/Packages/ComfyUI/venv/bin/python"
REQUEST_FILE="$(mktemp /tmp/g8_request_XXXXXX.json)"
OUTPUT_DIR="$HOME/Music/yue2/g8_yue2_render"

cleanup() { rm -f "$REQUEST_FILE"; }
trap cleanup EXIT

# --- Precondition: GPU must have free VRAM ------------------------------------
echo "G8: checking GPU (zephyr 3090) ..."
GPU_INFO=$(nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader 2>/dev/null | grep "3090" || true)
if [ -z "$GPU_INFO" ]; then
    echo "G8 FAIL: NVIDIA GeForce RTX 3090 not found" >&2
    exit 1
fi
GPU_USED_MIB=$(echo "$GPU_INFO" | awk -F',' '{print $2}' | grep -oE '[0-9]+')
GPU_TOTAL_MIB=$(echo "$GPU_INFO" | awk -F',' '{print $3}' | grep -oE '[0-9]+')
GPU_FREE_MIB=$((GPU_TOTAL_MIB - GPU_USED_MIB))
# Need at least 2 GiB free for YuE2-3B inference
if [ "$GPU_FREE_MIB" -lt 2048 ]; then
    echo "G8 FAIL: 3090 has only ${GPU_FREE_MIB} MiB free (need >= 2048 MiB)" >&2
    exit 1
fi
echo "G8: 3090 has ${GPU_FREE_MIB} MiB free VRAM."

# --- Precondition: YuE2 source and venv must exist ------------------------------
if [ ! -d "$YUE2_SRC/src/yue2" ]; then
    echo "G8 FAIL: YuE2 source not found at $YUE2_SRC/src/yue2" >&2
    exit 1
fi
if [ ! -x "$YUE2_VENV_PY" ]; then
    echo "G8 FAIL: YuE2 venv Python not found at $YUE2_VENV_PY" >&2
    exit 1
fi
echo "G8: YuE2 source and venv found."

# --- Write the request (from the verified E2E manifest) ------------------------
cat > "$REQUEST_FILE" <<'REQ'
{
  "style": "Electronic, synthwave, energetic, 128 BPM, minor key, cyberpunk atmosphere",
  "lyrics": "[Verse 1]\nNeon lights are calling out my name\nElectric veins running through the rain\nDigital dreams in a analog world\nWatching all the stars get unfurled\n\n[Pre-Chorus]\nThe signal's getting stronger now\nWe're breaking through somehow\n\n[Chorus]\nWe are the children of the night\nBurning bright with electric light\nNothing's gonna hold us down\nWe're the sound of the future now\nWe are the children of the night",
  "cot": "full",
  "seed": 42,
  "id": "g8_yue2_render"
}
REQ

# --- Run the renderer ---------------------------------------------------------
echo "G8: rendering via YuE2 direct pipeline (seed=40, cot=full) ..."
rm -rf "$OUTPUT_DIR"
mkdir -p "$(dirname "$OUTPUT_DIR")"
export PYTHONPATH="$YUE2_SRC/src:${PYTHONPATH:-}"
export YUE2_OUTPUT_DIR="$OUTPUT_DIR"
"$YUE2_VENV_PY" "$YUE2_SRC/skills/yue2-music/scripts/run_yue2.py" \
    generate \
    --request "$REQUEST_FILE" \
    --cot full \
    --output "$OUTPUT_DIR" \
    --device cuda
RC=$?
if [ "$RC" -ne 0 ]; then
    echo "G8 FAIL: yue2 run exited with code $RC" >&2
    exit 1
fi

# --- Find the output FLAC ----------------------------------------------------
OUTPUT_FLAC="$OUTPUT_DIR/audio.flac"
if [ ! -f "$OUTPUT_FLAC" ]; then
    echo "G8 FAIL: no output FLAC found at $OUTPUT_FLAC" >&2
    exit 1
fi
echo "G8: output found: $OUTPUT_FLAC"

# --- Verify with ffprobe ------------------------------------------------------
echo "G8: verifying with ffprobe ..."
FFPROBE_JSON=$(ffprobe -v error -show_entries stream=codec_name,sample_rate,channels -show_entries format=duration,size -of json "$OUTPUT_FLAC")
RC=$?
if [ "$RC" -ne 0 ]; then
    echo "G8 FAIL: ffprobe could not read $OUTPUT_FLAC" >&2
    exit 1
fi

# Check codec is FLAC
CODEC=$(echo "$FFPROBE_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['streams'][0]['codec_name'])")
if [ "$CODEC" != "flac" ]; then
    echo "G8 FAIL: expected FLAC codec, got '$CODEC'" >&2
    exit 1
fi

# Check duration is reasonable (> 30s — YuE2 typically produces 2-3 min songs)
DURATION=$(echo "$FFPROBE_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(float(d['format']['duration']))")
DURATION_OK=$(python3 -c "print(1 if $DURATION > 30.0 else 0)")
if [ "$DURATION_OK" != "1" ]; then
    echo "G8 FAIL: duration ${DURATION}s too short (expected > 30s)" >&2
    exit 1
fi

# Check non-silent (mean volume above -60 dB)
VOLUME=$(ffmpeg -i "$OUTPUT_FLAC" -af volumedetect -f null /dev/null 2>&1 | grep mean_volume | awk '{print $5}')
VOLUME_OK=$(python3 -c "print(1 if float('${VOLUME:-99}') > -60.0 else 0)")
if [ "$VOLUME_OK" != "1" ]; then
    echo "G8 FAIL: output appears silent (mean_volume=${VOLUME:-unknown} dB)" >&2
    exit 1
fi

echo "G8: FLAC=$OUTPUT_FLAC duration=${DURATION}s mean_volume=${VOLUME}dB"
echo "G8-OK"