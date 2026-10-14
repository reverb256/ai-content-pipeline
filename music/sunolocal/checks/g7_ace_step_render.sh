#!/usr/bin/env bash
# G7: ACE-Step live render via acestep_plan.py against comfyui-zephyr
#
# Preconditions:
#   1. ComfyUI (comfyui-zephyr) must be running and reachable at
#      http://localhost:32188  (port 32188, NOT the default 8188).
#   2. The ACE-Step custom nodes must be installed in that ComfyUI instance.
#   3. Models (acestep-v15-turbo, vae, Qwen3-Embedding, acestep-5Hz-lm-1.7B)
#      must already be provisioned on the ComfyUI pod.
#   4. ffprobe must be on PATH.
#
# This script FAILS LOUDLY if ComfyUI is unreachable — it does NOT fall back
# to a fixture or skip the check.
#
# Output: FLAC file in ~/Music/acestep/ (ComfyUI saves there via mounted volume).
# Prints exactly "G7-OK" on success, exits nonzero on any failure.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

COMFY_URL="${COMFY_URL:-http://localhost:32188}"
PLAN_FILE="$(mktemp /tmp/g7_plan_XXXXXX.json)"
OUTPUT_DIR="$HOME/Music/acestep"

cleanup() { rm -f "$PLAN_FILE"; }
trap cleanup EXIT

# --- Precondition: ComfyUI must be reachable ---------------------------------
echo "G7: checking ComfyUI at $COMFY_URL ..."
if ! curl -sf -m 5 "$COMFY_URL/system_stats" >/dev/null 2>&1; then
    echo "G7 FAIL: ComfyUI not reachable at $COMFY_URL" >&2
    echo "        Is comfyui-zephyr running? Check: curl $COMFY_URL/system_stats" >&2
    exit 1
fi
echo "G7: ComfyUI is up."

# --- Write the plan (from the verified E2E manifest) --------------------------
cat > "$PLAN_FILE" <<'PLAN'
{
  "caption": "A short instrumental intro building into an energetic electronic rock anthem with soaring synthesizers and driving drums, inspired by 1980s cyberpunk soundtracks",
  "lyrics": "[Instrumental]\n",
  "bpm": 128,
  "key": "Am",
  "duration": 30,
  "timesignature": "4/4",
  "title": "Neon Chase",
  "authorship": "human (j_kro)"
}
PLAN

# --- Run the renderer ---------------------------------------------------------
echo "G7: rendering via acestep_plan.py (seed=42, duration=30s) ..."
export COMFY_URL
python3 music/scripts/acestep_plan.py "$PLAN_FILE" --seed 42 --name "g7_ace_render" --timeout 300 --allow-empty
RC=$?
if [ "$RC" -ne 0 ]; then
    echo "G7 FAIL: acestep_plan.py exited with code $RC" >&2
    exit 1
fi

# --- Find the output FLAC ----------------------------------------------------
# acestep_plan.py saves via ComfyUI SaveAudio -> ~/Music/acestep/g7_ace_render_00001.flac
OUTPUT_FLAC="$OUTPUT_DIR/g7_ace_render_00001.flac"
if [ ! -f "$OUTPUT_FLAC" ]; then
    # Try to find any recent g7_ace_render*.flac
    OUTPUT_FLAC=$(find "$OUTPUT_DIR" -name 'g7_ace_render*.flac' -newer "$PLAN_FILE" -print -quit 2>/dev/null || true)
fi
if [ -z "$OUTPUT_FLAC" ] || [ ! -f "$OUTPUT_FLAC" ]; then
    echo "G7 FAIL: no output FLAC found in $OUTPUT_DIR" >&2
    exit 1
fi
echo "G7: output found: $OUTPUT_FLAC"

# --- Verify with ffprobe ------------------------------------------------------
echo "G7: verifying with ffprobe ..."
FFPROBE_JSON=$(ffprobe -v error -show_entries stream=codec_name,sample_rate,channels -show_entries format=duration,size -of json "$OUTPUT_FLAC")
RC=$?
if [ "$RC" -ne 0 ]; then
    echo "G7 FAIL: ffprobe could not read $OUTPUT_FLAC" >&2
    exit 1
fi

# Check codec is FLAC
CODEC=$(echo "$FFPROBE_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['streams'][0]['codec_name'])")
if [ "$CODEC" != "flac" ]; then
    echo "G7 FAIL: expected FLAC codec, got '$CODEC'" >&2
    exit 1
fi

# Check duration is ~30s (tolerance: 28-32s)
DURATION=$(echo "$FFPROBE_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(float(d['format']['duration']))")
DURATION_OK=$(python3 -c "print(1 if 28.0 <= $DURATION <= 32.0 else 0)")
if [ "$DURATION_OK" != "1" ]; then
    echo "G7 FAIL: duration ${DURATION}s outside tolerance [28, 32]" >&2
    exit 1
fi

# Check non-silent (mean volume above -60 dB)
VOLUME=$(ffmpeg -i "$OUTPUT_FLAC" -af volumedetect -f null /dev/null 2>&1 | grep mean_volume | awk '{print $5}')
VOLUME_OK=$(python3 -c "print(1 if float('${VOLUME:-99}') > -60.0 else 0)")
if [ "$VOLUME_OK" != "1" ]; then
    echo "G7 FAIL: output appears silent (mean_volume=${VOLUME:-unknown} dB)" >&2
    exit 1
fi

echo "G7: FLAC=$OUTPUT_FLAC duration=${DURATION}s mean_volume=${VOLUME}dB"
echo "G7-OK"