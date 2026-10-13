#!/bin/bash
# Dev-only. grid.sh reps ms...   -> lines: ms kind att
# Plays test sounds on the speaker. Needs MIC set and the bridge installed.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
R=$1; shift
for ms in "$@"; do
  PLAY_DELAY="$((ms*48))/48000" "$HOME/.local/bin/echo-softvol-up" >/dev/null 2>&1; sleep 2
  python3 "$DIR/measure.py" music >/dev/null 2>&1   # warm-up
  for k in chirp music; do for _ in $(seq "$R"); do
    a=$(python3 "$DIR/measure.py" "$k" 2>/dev/null | grep -o 'attenuation=[-0-9.]*' | cut -d= -f2); echo "$ms $k $a"
  done; done
done
