#!/bin/bash
# grid.sh reps ms...   -> lines: ms kind att
R=$1; shift
for ms in "$@"; do
  PLAY_DELAY="$((ms*48))/48000" ~/.local/bin/echo-softvol-up >/dev/null 2>&1; sleep 2
  for i in $(pactl list short sink-inputs | awk '{print $1}'); do pactl move-sink-input $i echo_softvol 2>/dev/null; done
  python3 measure.py music >/dev/null 2>&1
  for k in chirp music; do for n in $(seq $R); do
    a=$(python3 measure.py $k 2>/dev/null | rg -o 'attenuation=[-0-9.]+' | cut -d= -f2); echo "$ms $k $a"
  done; done
done
