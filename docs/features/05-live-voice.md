# 05 - Hold-to-talk voice

Status: **demo version built (peer-to-peer); needs HTTPS (D1) and real-device checks**
Dependencies: [02](02-rooms-and-rounds.md)

## Demo version

The two devices send audio directly to each other over WebRTC; the room socket carries only connection setup (`apps/web/src/features/voice/voice.ts`). The mic is captured once after the "Turn on mic" tap (or again after a page reload), and voice connects only once the mic is ready, so the child who joins second is heard too. The track stays muted except while the player holds the talk button. Both can hold at once. Uses a public STUN server and no TURN relay, so both devices must be on the same Wi-Fi.

iOS Safari allows the microphone only on HTTPS pages (or localhost), so the web app must be served over HTTPS on the LAN - step D1 in the [implementation plan](../implementation-plan.md).

## Demo checks (part of D3)

- [ ] Each device hears the other while its button is held, in both directions and when both hold together.
- [ ] Releasing the button stops audio; no mic stays on after Done or leaving.
- [ ] Voice keeps working after Play again and role swap.
- [ ] Echo and volume are acceptable with the two devices in the same room.

## Later (deferred)

LiveKit with TURN for different networks, server-granted and revocable mic permission per hold, handling for backgrounding/lost sockets, and the hold identities that transcription in [06](06-transcription.md) would need.
