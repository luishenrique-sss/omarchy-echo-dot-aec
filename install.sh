#!/bin/bash
# Install the echo-cancel bridge for one Bluetooth speaker.
# Usage: BT_MAC=AA:BB:CC:DD:EE:FF [MIC=alsa_input...] ./install.sh
set -euo pipefail
die() { echo "install.sh: $*" >&2; exit 1; }
cd "$(dirname "$0")"

[ -n "${BT_MAC:-}" ] || die "set BT_MAC (bluetoothctl devices)"
[[ "$BT_MAC" =~ ^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$ ]] || die "BT_MAC looks invalid: $BT_MAC"
for c in pactl pw-play pw-record pipewire flock bluetoothctl; do
  command -v "$c" >/dev/null || die "missing $c (see Prerequisites in README.md)"
done

CFG="$HOME/.config/echo-softvol"; CAL="$HOME/.local/share/echo-softvol"
mkdir -p "$HOME/.local/bin" "$HOME/.config/systemd/user" "$CFG" "$CAL"

# 1. Scripts
install -m 755 bin/echo-softvol-up bin/echo-softvol-watch "$HOME/.local/bin/"

# 2. Config read by the service
{ echo "BT_MAC=$BT_MAC"; [ -n "${MIC:-}" ] && echo "MIC=$MIC"; } > "$CFG/env"

# 3. Calibration (before the service starts, so the first connect is calibrated)
cp calib/calib.py "$CAL/"
if [ ! -x "$CAL/venv/bin/python" ]; then
  if python3 -c 'import numpy' 2>/dev/null; then
    python3 -m venv --system-site-packages "$CAL/venv"
  elif command -v uv >/dev/null; then
    uv venv "$CAL/venv" && uv pip install --python "$CAL/venv/bin/python" numpy
  else
    echo "install.sh: numpy not found; calibration disabled (fixed 120 ms)" >&2
  fi
fi

# 4. Service (last)
cp systemd/echo-softvol-watcher.service "$HOME/.config/systemd/user/"
systemctl --user daemon-reload
systemctl --user enable --now echo-softvol-watcher.service
echo "Installed. Select the 'Echo-cancelled mic' input in your call app."
