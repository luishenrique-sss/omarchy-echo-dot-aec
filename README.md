# omarchy-echo-dot-aec

Cancelamento de eco para quem usa um **alto-falante Bluetooth** (aqui, um Echo Dot) no Linux com **PipeWire** e conversa no Discord, Meet etc. ao mesmo tempo.

![Antes e depois](docs/aec-graph.png)

## O problema

A música sai do Echo Dot, o microfone do notebook capta e os seus amigos no Discord ouvem tudo de volta. A primeira "solução" era só um atraso fixo de 50 ms, que não resolvia.

## A solução

- Um processo PipeWire **nativo** com `libpipewire-module-echo-cancel` + `aec/libspa-aec-webrtc` (WebRTC AEC3).
- O som vai **direto** para o Bluetooth, sem loopback extra. Ou seja, nada de latência a mais no que você ouve.
- `buffer.play_delay = 4800/48000` (**100 ms**) atrasa **só a cópia de referência** do cancelador. Assim ela fica alinhada com a latência do Bluetooth A2DP (140–490 ms no total).
- Opções do WebRTC: `noise_suppression` e `high_pass_filter` ligadas, `gain_control` desligada.
- Ficam criados dois dispositivos:
  - saída **"Echo"** (`echo_softvol`), com volume por software;
  - entrada **"Mic-sem-eco"** (`echo_mic`). Use esta no Discord.
- Um serviço systemd de usuário monta tudo sozinho quando o alto-falante conecta e desmonta quando desconecta.

Testado em: Omarchy (Arch), PipeWire 1.6.8, webrtc-audio-processing 1.3.

## Rodadas de ajuste (medidas reais, bip cronometrado + ruído tipo música)

| Rodada | Atenuação do eco |
|---|---|
| `pactl load-module module-echo-cancel` | 0,4–2,5 dB |
| Nativo, sem atraso | 5–15 dB |
| Nativo, +50 ms | 22 / 18,5 dB |
| **Nativo, +100 ms (escolhido)** | **24–31 / 12–23 dB**, eco abaixo do ruído do mic |
| Nativo, +200 ms | 8 / 12 dB |
| Nativo, +400 ms | 3,5 / 5 dB |

(bip / música). O gráfico de cima vem de uma gravação real do teste com música: microfone cru × microfone depois do AEC.

## Instalação

```bash
git clone https://github.com/luishenrique-sss/omarchy-echo-dot-aec
cd omarchy-echo-dot-aec
bluetoothctl devices                        # anote o MAC do alto-falante
pactl list short sources | grep alsa_input  # anote o nome do microfone

mkdir -p ~/.local/bin ~/.config/systemd/user
cp bin/* ~/.local/bin/
cp systemd/echo-softvol-watcher.service ~/.config/systemd/user/
# edite BT_MAC (e, se quiser, MIC) em ~/.local/bin/echo-softvol-up e no .service
systemctl --user daemon-reload
systemctl --user enable --now echo-softvol-watcher.service
```

Depois, no Discord, escolha **Mic-sem-eco** como entrada. Como saída, use **Echo**.

Se a latência do seu alto-falante for outra, teste valores diferentes de atraso:
`PLAY_DELAY=2400/48000 ~/.local/bin/echo-softvol-up`, e meça com `tests/measure.py` (veja `tests/`).

## Reverter

```bash
systemctl --user disable --now echo-softvol-watcher.service
~/.local/bin/echo-softvol-up down
rm ~/.local/bin/echo-softvol-up ~/.local/bin/echo-softvol-watch ~/.config/systemd/user/echo-softvol-watcher.service
rm -rf ~/.config/echo-softvol
```

O guia completo está em [`docs/Guia_Eco_Alexa_Omarchy.pdf`](docs/Guia_Eco_Alexa_Omarchy.pdf).

---

### English summary

This setup fixes Bluetooth speaker echo on Linux/PipeWire. When music plays on a Bluetooth speaker (here an Echo Dot), the laptop mic picks it up and Discord friends hear it back. The fix is a standalone PipeWire instance running `module-echo-cancel` with the WebRTC AEC3 backend. Playback goes straight to the BT sink, and `buffer.play_delay = 100 ms` aligns only the AEC reference with A2DP latency. Measured echo attenuation is 24–31 dB on chirps and 12–23 dB on music, versus 0.4–2.5 dB with the plain `pactl` module. A systemd user service wires it up automatically on connect. Install and revert steps are above.

License: MIT.
