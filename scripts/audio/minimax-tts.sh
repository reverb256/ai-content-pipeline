#!/usr/bin/env bash
# minimax-tts.sh — CLI wrapper for MiniMax Speech T2A (synchronous HTTP).
# Primary emotive TTS for the audio-drama track.
#
# Reads MINIMAX_API_KEY from the environment (or ~/.hermes/.env).
# Exits non-zero on auth/quota/API failure so the storyteller can fall back.
#
# Usage:
#   minimax-tts.sh --text "Line of dialogue." --out /tmp/line.mp3
#   minimax-tts.sh -t "..." -o out.mp3 -v English_expressive_narrator \
#       -e sad -s spacious_echo -m speech-2.8-hd --speed 1.0
#
# Options:
#   -t, --text         text to synthesize (required)
#   -o, --out          output audio path (default ./minimax-tts.mp3)
#   -v, --voice        MiniMax voice id (default English_expressive_narrator)
#   -e, --emotion      happy|sad|angry|fearful|disgusted|surprised|calm|fluent|whisper
#   -s, --sound-effect spacious_echo|auditorium_echo|lofi_telephone|robotic
#   -m, --model        speech-2.8-hd (default) | speech-2.8-turbo | speech-02-hd | speech-02-turbo
#   -r, --rate         sample rate 8000|16000|22050|24000|32000|44100 (default 44100)
#   -c, --channel      1 (mono, default) | 2 (stereo)
#   --speed            voice speed 0.5-2.0 (default 1.0)
#   --pitch            voice pitch -12..12 (default 0)
#   --vol              voice volume 0.1-10 (default 1.0)
#   --lang             language_boost, default auto
#   --pauses           insert <#0.5#> pause markers at sentence boundaries
#   --format           mp3 (default) | wav | flac | pcm | opus
#   -h, --help         show this help
#
# Environment:
#   MINIMAX_API_KEY   API key (required). Loaded from ~/.hermes/.env if unset.
#
# Exit codes:
#   0 success
#   2 usage error
#   3 missing API key
#   4 HTTP/API error (auth, quota, rate limit, invalid input) — fallback should kick in
set -euo pipefail

API_URL="https://api.minimax.io/v1/t2a_v2"
ENV_FILE="${HERMES_ENV_FILE:-$HOME/.hermes/.env}"
DEFAULT_VOICE="English_expressive_narrator"
DEFAULT_MODEL="speech-2.8-hd"

usage() { sed -n '2,38p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

# --- load MINIMAX_API_KEY (env first, then ~/.hermes/.env) ---
if [ -z "${MINIMAX_API_KEY:-}" ] && [ -f "$ENV_FILE" ]; then
  set +e
  # shellcheck disable=SC1090
  source "$ENV_FILE" >/dev/null 2>&1
  set -e
fi
if [ -z "${MINIMAX_API_KEY:-}" ]; then
  echo "ERROR: MINIMAX_API_KEY not set (env or $ENV_FILE)." >&2
  exit 3
fi

# --- parse args ---
TEXT=""; OUT=""; VOICE="$DEFAULT_VOICE"; EMOTION=""; SOUND_EFFECT=""; MODEL="$DEFAULT_MODEL"
RATE=44100; CHANNEL=1; SPEED=1.0; PITCH=0; VOL=1.0; LANG="auto"; PAUSES=0; FORMAT="mp3"

while [ $# -gt 0 ]; do
  case "$1" in
    -t|--text)         TEXT="$2"; shift 2 ;;
    -o|--out)          OUT="$2"; shift 2 ;;
    -v|--voice)        VOICE="$2"; shift 2 ;;
    -e|--emotion)      EMOTION="$2"; shift 2 ;;
    -s|--sound-effect) SOUND_EFFECT="$2"; shift 2 ;;
    -m|--model)        MODEL="$2"; shift 2 ;;
    -r|--rate)         RATE="$2"; shift 2 ;;
    -c|--channel)      CHANNEL="$2"; shift 2 ;;
    --speed)           SPEED="$2"; shift 2 ;;
    --pitch)           PITCH="$2"; shift 2 ;;
    --vol)             VOL="$2"; shift 2 ;;
    --lang)            LANG="$2"; shift 2 ;;
    --pauses)          PAUSES=1; shift ;;
    --format)          FORMAT="$2"; shift 2 ;;
    -h|--help)         usage 0 ;;
    *) echo "ERROR: unknown option: $1" >&2; usage 2 ;;
  esac
done

[ -n "$TEXT" ] || { echo "ERROR: --text is required" >&2; usage 2; }
[ -n "$OUT" ]  || OUT="${PWD}/minimax-tts.mp3"
mkdir -p "$(dirname "$OUT")"

# --- validate emotion / sound effect against the API enums ---
VALID_EMOTIONS="happy sad angry fearful disgusted surprised calm fluent whisper"
VALID_SFX="spacious_echo auditorium_echo lofi_telephone robotic"
if [ -n "$EMOTION" ] && ! echo " $VALID_EMOTIONS " | grep -q " $EMOTION "; then
  echo "ERROR: unknown emotion '$EMOTION'. Valid: $VALID_EMOTIONS" >&2; exit 2
fi
if [ -n "$SOUND_EFFECT" ] && ! echo " $VALID_SFX " | grep -q " $SOUND_EFFECT "; then
  echo "ERROR: unknown sound effect '$SOUND_EFFECT'. Valid: $VALID_SFX" >&2; exit 2
fi

# --- build the JSON payload ---
VOICE_SETTING="{\"voice_id\":\"$VOICE\",\"speed\":$SPEED,\"vol\":$VOL,\"pitch\":$PITCH"
if [ -n "$EMOTION" ]; then
  VOICE_SETTING="$VOICE_SETTING,\"emotion\":\"$EMOTION\""
fi
VOICE_SETTING="$VOICE_SETTING}"

AUDIO_SETTING="{\"sample_rate\":$RATE,\"bitrate\":128000,\"format\":\"$FORMAT\",\"channel\":$CHANNEL}"

MODIFY=""
if [ -n "$SOUND_EFFECT" ]; then
  MODIFY=",\"voice_modify\":{\"sound_effects\":\"$SOUND_EFFECT\"}"
fi

# Optional pause markers: <#0.5#> between sentences gives the narrator breathing room.
if [ "$PAUSES" = "1" ]; then
  TEXT="$(printf '%s' "$TEXT" | sed 's/\. /.<#0.5#> /g; s/\? /?<#0.5#> /g; s/! /!<#0.5#> /g')"
fi

PAYLOAD="{\"model\":\"$MODEL\",\"text\":$(jq -Rn --arg t "$TEXT" '$t')"
PAYLOAD="$PAYLOAD,\"stream\":false,\"language_boost\":\"$LANG\""
PAYLOAD="$PAYLOAD,\"voice_setting\":$VOICE_SETTING"
PAYLOAD="$PAYLOAD,\"audio_setting\":$AUDIO_SETTING"
PAYLOAD="$PAYLOAD,\"output_format\":\"hex\"$MODIFY}"
# output_format=hex → response JSON contains hex-encoded audio; decode to file.
# (output_format=url would return a 24h link; hex avoids an extra download hop.)

echo "[minimax-tts] model=$MODEL voice=$VOICE emotion=${EMOTION:-auto} sfx=${SOUND_EFFECT:-none} len=${#TEXT}ch" >&2

RESP="$(curl -sS --max-time 120 -X POST "$API_URL" \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")"

# --- parse and check for API error ---
STATUS="$(printf '%s' "$RESP" | jq -r '.base_resp.status_code // "parse-error"' 2>/dev/null || echo parse-error)"
if [ "$STATUS" != "0" ]; then
  MSG="$(printf '%s' "$RESP" | jq -r '.base_resp.status_msg // "unknown"' 2>/dev/null || echo unknown)"
  echo "ERROR: MiniMax T2A failed (status_code=$STATUS): $MSG" >&2
  # 1004 auth, 1008 insufficient balance, 1002/1039 rate limit, 1042 bad input.
  # Any of these should trigger the fallback provider upstream.
  exit 4
fi

HEX="$(printf '%s' "$RESP" | jq -r '.data.audio // empty' 2>/dev/null || true)"
if [ -z "$HEX" ]; then
  echo "ERROR: MiniMax T2A returned success but no audio data." >&2
  exit 4
fi

printf '%s' "$HEX" | xxd -r -p > "$OUT"

# --- verify output is real audio ---
SIZE="$(wc -c < "$OUT" || echo 0)"
if [ "$SIZE" -lt 100 ]; then
  echo "ERROR: decoded audio too small (${SIZE}B) — output invalid." >&2
  rm -f "$OUT"
  exit 4
fi
if command -v ffprobe >/dev/null 2>&1; then
  DUR="$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT" 2>/dev/null || echo "?")"
  echo "[minimax-tts] wrote $OUT (${SIZE}B, ${DUR}s)" >&2
fi
echo "$OUT"
