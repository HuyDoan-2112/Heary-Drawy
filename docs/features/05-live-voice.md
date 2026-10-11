# 05 - Independent live hold-to-talk

Status: **not started**  
Dependencies: [01](01-foundation.md) + [02](02-rooms-and-rounds.md); LiveKit access and actual devices  
References: [architecture](../architecture.md), [API](../api.md), [lifecycle](../round-lifecycle.md), [testing](../testing.md)

## Deliverable

Two authorized devices hear each other's original voice live while either/both hold their mic buttons. Release stops transmission. AI is not in the delivery path.

## Scope and ownership

Own frontend voice module, backend media permission/hold module, and associated tests. Coordinate canonical socket messages and startup wiring.

- One pair-scoped LiveKit room, microphone-only human tracks, scoped subscribe-only joining tokens, independent publication grants per participant.
- Explicit permission/playback unlock and readiness; reuse one mic capture path without an always-open publication.
- Local release/cancel immediately stops transmit. Backend confirms grants, revokes publication, and compensates canceled delayed grants.
- Per-participant hold IDs/epochs/deadlines, connection health, background/lifecycle handling, restart reconciliation.
- Pause on revocation/provider failures; never rely only on token expiry/UI state.

Perform this two-device risk spike soon after 02; do not wait for completed AI, canvas polish, or the full Round UI.

## Out of scope

STT, model coaching, audio recording/replay, camera/video/screen-share, public voice rooms, and an always-open call.

## Acceptance

- [ ] Real HTTPS Safari audio works both directions and with both participants holding concurrently.
- [ ] Partner hears before any AI analysis; first/last words, echo, and observable start/stop latency are checked.
- [ ] Release-before-grant, cancellation, backgrounding, lost socket, phase exit, and Room closure stop/cancel transmission.
- [ ] Provider revocation actually removes publication; revoked-token behavior is tested against pinned SDK/API.
- [ ] Pair isolation and unauthorized third-session publication/subscription attempts are denied.
- [ ] Reconnect/restart never automatically reopens a microphone.
- [ ] Poor-network/cross-network and TURN behavior are exercised where available; gaps recorded.
- [ ] Backend-crash cooperative cutoff limitation is explicit; no false malicious-client guarantee.

## Handoff

Expose separately identified authorized tracks to 06 without adding another browser recorder. Record SDK/device/network evidence and unresolved deployment-wide cutoff gates.

Evidence: none yet.
