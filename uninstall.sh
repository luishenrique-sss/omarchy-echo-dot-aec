#!/bin/bash
# Remove the echo-cancel bridge and restore the previous default mic and speaker volume.
set -uo pipefail
systemctl --user disable --now echo-softvol-watcher.service 2>/dev/null || true
[ -x "$HOME/.local/bin/echo-softvol-up" ] && "$HOME/.local/bin/echo-softvol-up" down
rm -f "$HOME/.local/bin/echo-softvol-up" "$HOME/.local/bin/echo-softvol-watch" \
      "$HOME/.config/systemd/user/echo-softvol-watcher.service" \
      /tmp/echo-softvol-aec.log "${XDG_RUNTIME_DIR:-/tmp}/echo-softvol.lock"
rm -rf "$HOME/.config/echo-softvol" "$HOME/.local/share/echo-softvol" "${XDG_STATE_HOME:-$HOME/.local/state}/echo-softvol"
systemctl --user daemon-reload
echo "Uninstalled."
