# Implementation plan

Status: **demo-first.** The only current goal is a working two-device demo: one iPad and one iPhone playing a round together, operated by adults on the same Wi-Fi. Everything that does not serve that goal is deferred, not deleted.

## What already works (local, not yet checked on real devices)

Built in [02](features/02-rooms-and-rounds.md) plus the minimal round slice recorded there:

- Grown-up passcode unlocks each device; children pick a character/name and get paired.
- Random roles, short role intro, 3-round match with role swap on Play again.
- Server picks a secret 3D object per round; only the Speaker sees it (spin and zoom) until Reveal shows its picture to both.
- Drawer's strokes relay live to the Speaker's read-only canvas.
- Hold-to-talk voice: peer-to-peer WebRTC, signaled over the existing socket.
- Done reveals the picture beside the drawing with a neutral, unscored result (replaced by AI feedback in D2).

## Demo plan

| Step | Deliverable | Status |
| --- | --- | --- |
| D1 | **Reachable from devices.** One command serves the web app over HTTPS on the LAN (iOS Safari requires HTTPS for the microphone) and allows that origin on the API socket. | Built: `npm run demo` ([09](features/09-demo-hardening.md)). Checked with two headless browsers over the LAN address; real devices in D3 |
| D2 | **AI feedback.** Transcribe each hold-to-talk clip with Whisper on the laptop, then at Done ask DeepSeek for separate Speaker and Drawer feedback plus 1-3 team stars. Design in [06](features/06-transcription.md) and [07](features/07-feedback.md). | Built; Whisper checked end to end in two browsers; real DeepSeek reply and devices in D3 |
| D3 | **Real-device walkthrough.** On the actual iPad and iPhone: join, play 3 rounds in both role directions, talk while drawing, Play again, Done. Fix whatever breaks or looks wrong. Record device models/iOS versions and results in [testing.md](testing.md). | Not started |
| D4 | **Demo script.** Short README section: start command, passcode, what to tap, known limits. | Written: README "Run the two-device demo"; confirm from a fresh clone during D3 |

The demo is done when D3 passes on both devices with no stuck mic, no leaked picture to the Drawer, and no layout breakage.

## Deliberately deferred

These stay documented as future ideas. Do not build them for the demo.

| Deferred | Demo substitute | Brief |
| --- | --- | --- |
| LiveKit, TURN, server-side mic grants/revocation | Peer-to-peer WebRTC on one Wi-Fi network | [05](features/05-live-voice.md) |
| Live streaming transcription | Each clip transcribed after release with Whisper on the laptop | [06](features/06-transcription.md) |
| Curated tip library, reviewed long-term star rubric | DeepSeek writes short gentle lines; stars from a simple demo rule | [07](features/07-feedback.md) |
| Hosted deployment, host authorization, retention hardening | Laptop on the LAN, CLI passcode, local Postgres | [09](features/09-demo-hardening.md) |
| Drawing resync/revision guarantees beyond what exists | Current live relay | [03](features/03-drawing.md) |
| Bot partner | Exactly two players | [10](features/10-bot-partner.md) |
| Round timer, disconnect-timeout help screen | Adults restart if a device drops | [02](features/02-rooms-and-rounds.md) |

The demo sends drawings and transcripts (not audio) to the DeepSeek API. Real-child use stays blocked by [privacy-and-safety.md](privacy-and-safety.md); the demo uses adults only.

## Rules of thumb

- Fix only what blocks or visibly breaks the two-device demo.
- No new services, providers, or abstractions beyond those in this plan (local Whisper and DeepSeek).
- Mark device checks complete only after running them on the real iPad and iPhone.
