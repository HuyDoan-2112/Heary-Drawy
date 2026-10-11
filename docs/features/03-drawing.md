# 03 - Drawing and read-only live canvas

Status: **not started**  
Dependencies: [01](01-foundation.md) for isolated UI; [02](02-rooms-and-rounds.md) for authorized relay  
References: [API](../api.md), [data model](../data-model.md), [testing](../testing.md)

## Deliverable

Drawer finger strokes appear live in the Speaker's read-only canvas, with undo/clear, safe reconnect, and a frozen exportable submission.

## Scope and ownership

Own frontend drawing module, backend drawing relay/validation, and related tests. Coordinate migrations and socket-schema changes rather than editing shared files concurrently.

- Retained normalized strokes; pointer capture; bounded DPR-aware rendering; redraw after resize.
- Small accessible palette, undo, clear confirmation, and predictable-background PNG output.
- Bounded batched live operations over the existing authenticated WebSocket, monotonic revisions, duplicate handling, snapshot resync.
- Only Drawer edits; Speaker sees updates but cannot mutate.
- Submission freezes the server-acknowledged revision. Prefer authoritative server rendering for analyzed PNG; if client export is used, verify correspondence and document it.
- Explicit local draft cleanup/recovery, scoped to the active Room/Round and approved policy.

## Parallel boundary

Build the isolated canvas/read-only renderer using 01 fixtures while 02 is pending. Do not claim Pair authorization, live relay, or persisted recovery works until integrated with the real authority.

## Out of scope

Device-screen sharing, CRDT/multi-editor collaboration, microphones, secret object selection, scoring, and AI drawing generation.

## Acceptance

- [ ] Finger drawing, undo/clear, resize/orientation, and PNG export work on both actual devices.
- [ ] Speaker receives live updates; third participants and Speaker edits are denied.
- [ ] Duplicate/out-of-order operations safely acknowledge or resync without lost/corrupted work.
- [ ] Reconnect restores the permitted current drawing/revision.
- [ ] Submission rejects revision mismatch and freezes exactly the accepted image.
- [ ] Invalid/oversized/nonfinite point payloads are rejected.

## Handoff

Full-round multitouch acceptance belongs to [08](08-round-integration.md), after the real voice control from 05 exists. Do not claim drawing-while-talking has passed based on this feature's isolated canvas tests; record it during integration without making 03 depend circularly on 08.

Evidence: none yet.
