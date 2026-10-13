#!/bin/bash
# Dev-only. native.sh <play_delay|none> <monitor_mode true|false> [extra aec args]
mkdir -p "$HOME/aec-test"
pkill -f "pipewire -c $HOME/aec-test/ec2.conf"; sleep 0.5
PD=""; [ "$1" != none ] && PD="buffer.play_delay = $1"
cat > "$HOME/aec-test/ec2.conf" <<C
context.properties = { log.level = 2 default.clock.rate = 48000 default.clock.quantum = 1024 default.clock.min-quantum = 32 default.clock.max-quantum = 2048 }
context.spa-libs = { audio.convert.* = audioconvert/libspa-audioconvert support.* = support/libspa-support }
context.modules = [
 { name = libpipewire-module-rt flags = [ ifexists nofail ] }
 { name = libpipewire-module-protocol-native }
 { name = libpipewire-module-client-node }
 { name = libpipewire-module-adapter }
 { name = libpipewire-module-echo-cancel args = {
   library.name = aec/libspa-aec-webrtc
   monitor.mode = $2
   $PD
   aec.args = { webrtc.gain_control = false webrtc.high_pass_filter = true webrtc.noise_suppression = true $3 }
   capture.props = { node.name = ec2-capture target.object = ${MIC:-YOUR_MIC_SOURCE} node.dont-reconnect = true }
   source.props = { node.name = ec2_mic node.description = Echo-cancelled-mic-2 }
   sink.props = { node.name = ec2_out node.description = Echo-AEC2 }
   playback.props = { node.name = ec2-playback target.object = ${BT_SINK:-bluez_output.AA_BB_CC_DD_EE_FF.1} node.dont-reconnect = true }
 } }
]
C
nohup pipewire -c "$HOME/aec-test/ec2.conf" >/tmp/ec2.log 2>&1 &
sleep 2
