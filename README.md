# omarchy-echo-dot-aec

Acoustic echo cancellation for a **Bluetooth speaker + laptop mic** on Linux with **PipeWire**, so people on a call (Discord, Meet…) don't hear your music back.

![Echo Dot → laptop mic, before/after PipeWire WebRTC AEC](docs/aec-post.png)

Full measurements: [docs/aec-graph.png](docs/aec-graph.png) · 20 s explainer video: [docs/aec-video.mp4](docs/aec-video.mp4)

## Problem

Audio played on a Bluetooth speaker (here an Amazon Echo Dot over A2DP) is picked up by the laptop mic and sent back into the call. A plain `pactl load-module module-echo-cancel` only removed 0.4–2.5 dB in our tests.

## How it works

- A standalone PipeWire process loads `libpipewire-module-echo-cancel` with the WebRTC backend (`aec/libspa-aec-webrtc`, AEC3).
- Playback goes straight to the Bluetooth sink (no extra loopback, no added listening latency).
- `buffer.play_delay` delays **only the AEC reference**, to line it up with the Bluetooth + room delay.
- WebRTC options: `noise_suppression` and `high_pass_filter` on, `gain_control` off.
- Two virtual devices: output **Echo** (`echo_softvol`) and input **Echo-cancelled mic** (`echo_mic`). Pick that input in your call app.
- A systemd user service sets everything up when the speaker connects and tears it down when it disconnects. A `flock` prevents duplicate instances.


## Prerequisites

```bash
sudo pacman -S --needed pipewire pipewire-pulse wireplumber bluez bluez-utils webrtc-audio-processing util-linux python python-numpy
```

(`uv` works instead of `python-numpy`.) Tested on Omarchy (Arch, Hyprland via uwsm), kernel 7.2.5, PipeWire 1.6.8, BlueZ 5.87, webrtc-audio-processing 1.3. Check yours with `uname -r`, `pipewire --version`, `bluetoothctl --version`.

Scope: **one** Bluetooth speaker per install.

## Install

```bash
git clone https://github.com/luishenrique-sss/omarchy-echo-dot-aec
cd omarchy-echo-dot-aec
bluetoothctl devices                        # speaker MAC
pactl list short sources | grep alsa_input  # mic name (optional; default = first alsa_input)
BT_MAC=AA:BB:CC:DD:EE:FF MIC=alsa_input.YOUR_MIC_SOURCE ./install.sh
```

`install.sh` copies the scripts to `~/.local/bin`, writes `~/.config/echo-softvol/env` (read by the service via `EnvironmentFile`), installs calibration, then enables `echo-softvol-watcher.service` (a user service tied to `graphical-session.target`, which uwsm starts on Omarchy).

Then:
- In your call app (Discord, Meet…) pick the input **Echo-cancelled mic**.
- Play audio to the output **Echo** (the default after setup). Audio sent straight to the Bluetooth sink is not cancelled.
- Your previous default mic and speaker volume are saved in `~/.local/state/echo-softvol/` and restored on disconnect/uninstall.

[`config/aec.conf.example`](config/aec.conf.example) shows the PipeWire config the script generates.

## Verify (for humans and agents)

```bash
systemctl --user status echo-softvol-watcher.service
pactl list short sources | grep echo_mic
pactl list short sinks   | grep echo_softvol
tail ~/.local/share/echo-softvol/calib.log
cat /tmp/echo-softvol-aec.log
```

## Calibration and timing

**Heads-up:** on each connect the script plays 3 short, quiet sweeps (~5 s total) on the speaker, at its current volume (before the speaker is set to 100%). It cross-correlates the mic with the sink monitor and sets `play_delay = median measured delay − 12 ms`, clamped to 60–200 ms. If that fails, it falls back to 120 ms. Results are logged to `~/.local/share/echo-softvol/calib.log`.

Skip calibration with `ECHO_CALIBRATE=0` in `~/.config/echo-softvol/env`, or force a value with `PLAY_DELAY=5760/48000` (120 ms).

Measured timing on this setup:
- Bluetooth + room delay from 5 log sweeps: **132.5 ± 0.5 ms** (deconvolution).
- The short on-connect calibration reads 116–169 ms across single runs, so it uses the median of 3.
- On-connect calibration: ~5 s (3 quiet sweeps).
- Full benchmark (`tests/sweep.py` + `tests/grid.sh`): ~6 s per measurement; 151 measurements took ~16 min.
- CPU: the AEC PipeWire process (WebRTC AEC3 + noise suppression, 48 kHz) uses ~25–30% of one core (`top`, 3 samples), ~0.1% RAM (15 MB RSS).
- All numbers measured on one machine (Intel i5-13450HX, 16 threads, Omarchy). Expect different values elsewhere.

## Results

Measured with `tests/sweep.py` and `tests/grid.sh` (dev-only, not needed to use the bridge; they play loud test sounds) (chirp and music-like noise, `buffer.play_delay` 0–200 ms):

| | mean ± SD | median | n |
|---|---|---|---|
| chirp | 23.1 ± 6.4 dB | 25.0 dB | 73 |
| music-like noise | 22.3 ± 4.9 dB | 23.2 dB | 73 |

- Between 0 and 200 ms the delay setting made no difference larger than the run-to-run spread. AEC3 estimates the delay internally.
- In the recording shown above, the mic level went from −37.9 dBFS to −57.5 dBFS (19.6 dB). The mic noise floor without playback was −49.3 dBFS.

**Caveat:** noise suppression was **on** in all runs, so these numbers are echo cancellation **plus** noise suppression. Echo-only attenuation has not been measured yet.

## Uninstall

```bash
./uninstall.sh
```

It stops the service, restores your previous default mic and speaker volume, and removes the scripts, config, state, calibration, `/tmp/echo-softvol-aec.log` and `$XDG_RUNTIME_DIR/echo-softvol.lock`.

License: [MIT](LICENSE).
