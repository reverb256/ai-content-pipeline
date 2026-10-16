#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
python3 -c 'from music.sunolocal import spec, store, translate; print("G1-OK")'
