# Frontend UI implementation spec

Status: draft bridge from approved visual design to real application logic. No app code exists yet.

References: [product](product.md), [architecture](architecture.md), [API](api.md), [round lifecycle](round-lifecycle.md), [testing](testing.md), [implementation plan](implementation-plan.md), [frontend UI ticket map](frontend-ui-ticket-map.md), and approved design assets in [`artifact/README.md`](../artifact/README.md).

## Purpose

This spec turns the approved UI/UX artifacts into implementation-ready frontend behavior without changing the server-authoritative game rules. It is the bridge for building React/TypeScript screens against fixtures first, then wiring them to real backend contracts feature by feature.

Use this document to decide what each screen needs from real state, which commands it can send, what must stay fixture-only, and which product decisions must be reconciled before integration. Use the [frontend UI ticket map](frontend-ui-ticket-map.md) to split this spec into dependency-safe implementation tickets.

## Current implementation boundary

The repository currently has no runnable frontend, backend, package setup, or provider integration. Start with [Feature 01 - Foundation](features/01-foundation.md). UI screens may be implemented as fixture-backed components only after the workspace and typed contract fixtures exist.

Do not claim real rooms, voice, drawing relay, 3D delivery, AI feedback, or device acceptance until the dependent feature briefs are completed and their checks are recorded.

## Visual source of truth

Approved visual direction lives under `artifact/`:

- `artifact/screens/` - screenshot reference for each screen. Start here for visual matching.
- `artifact/design/*.dc.html` and `artifact/design/canvas.json` - detailed design source for sizes, color, copy, and layout.
- `artifact/assets/drawy/` - mascot SVG poses.
- `artifact/assets/avatars/` - pickable avatar SVGs.

Build the production UI in the app stack from [architecture](architecture.md): React + TypeScript + Vite, Tailwind/custom CSS, touch-first controls. Do not use the `.dc.html` files as production runtime code.

## Frontend routes and screens

Route names are implementation suggestions, not final API paths.

| Screen | Suggested route/state | Design reference | Depends on | Real commands/events |
| --- | --- | --- | --- | --- |
| Pick character | `/join` | `01-pick-character.png`, `Main.dc.html` | Feature 01 fixtures, Feature 02 real join | `POST /rooms/join`, session resume, nickname/avatar validation |
| Turn on mic | `/mic` or join step | `02-turn-on-mic.png` | Feature 01 fixture UI, Feature 05 real mic | Browser mic permission prompt, media-session request later |
| Pick mode | `/mode` | `03-pick-mode.png`, `02c-Mode.dc.html` | Feature 02 room state | Normal selected; Advanced visible but unavailable |
| Meet teammate | `/team` | `04-meet-teammate.png`, `02-Team.dc.html` | Feature 02 pairing | State snapshot with teammate nickname/avatar and assigned role |
| Role intro | round substate | `05a-role-intro-ipad.png` | Feature 02 round role | Local timed transition to play UI after reviewed lifecycle decision |
| Speaker play | round substate | `05b-speaker-ipad.png`, `05d-speaker-iphone.png` | Features 02, 03, 04, 05 | object access, read-only drawing updates, hold-to-talk commands |
| Drawer play | round substate | `05c-drawer-ipad.png`, `05e-drawer-iphone.png` | Features 02, 03, 05 | drawing operations, undo/clear, hold-to-talk, submission |
| Checking | round finalizing | `06-drawy-checking.png` | Feature 07 later | finalizing state and timeout/failure fallback |
| Result | feedback/exploring | `07-result.png` | Features 04, 07, 08 | feedback/result projection, reveal object access, Play again/Done |
| Grown-ups gate | separate adult route | `08-parents-phone.png`, `08-Grownups-Gate.dc.html` | Host authorization unresolved | No production host access until separate authorization is designed |

## State model for UI wiring

The frontend should treat backend state as authoritative. Local UI state is only for presentation details such as pressed buttons, transient animations, optimistic stroke drawing before acknowledgement, modal visibility, and retry affordances.

Minimum client state slices:

- `session`: guest token presence, current player ID, room ID, reconnect status.
- `room`: admitted participants visible to this player, teammate, avatar selections, mode if confirmed.
- `round`: role, phase, phase version, round ID, remaining time if confirmed, permissions.
- `object`: authorized reference access only when present in the role-filtered snapshot.
- `drawing`: retained normalized strokes, acknowledged revision, local in-flight operations, resync status.
- `voice`: mic permission status, active local hold IDs, remote speaking indicators, provider availability.
- `feedback`: role-specific child-safe sentences, shared stars or neutral/unscored state, sticker/reward data.

Never infer secret object identity from route params, asset filenames, preload tags, local fixtures, or hidden DOM. Drawer-before-Reveal projections must omit object ID, name, rubric, URLs, and model bytes entirely.

## Screen behavior details

### Pick character

- Show 10 avatars from the approved asset set.
- Avatar selection is required. Nickname entry follows product rules: nickname is a room-scoped display name, not authentication.
- Show already-picked avatars as unavailable only when the backend/fixture explicitly says so.
- Real join must normalize nicknames by trimming and case-folding server-side. A concurrent duplicate returns friendly `nickname_taken` copy.
- The Grown-ups button must not grant host privileges. It may open only the grown-up gate UI until a separate authorization mechanism exists.

### Turn on mic

- Explain that a grown-up should allow microphone access.
- Request browser microphone permission only from a clear user action.
- Permission does not publish audio by itself. Real publishing is still controlled by hold-to-talk in collaboration.
- If permission is denied, show a retry/help state rather than blocking the whole app with no escape.

### Pick mode

- Default is Normal.
- Advanced stays visible but unavailable for the demo. Use friendly copy: "Advanced pictures are coming soon!"
- Do not silently change object selection difficulty in production logic until a mode contract is added.

### Meet teammate

- Show teammate nickname/avatar from the role-filtered state.
- If pairing is pending, show a waiting state instead of inventing a bot. Bot Partner is Feature 10.
- `Let's play` starts or acknowledges the short role intro according to the role-intro timing policy.

### Role intro

- Designs show a short role intro, about 3 seconds, before play.
- The demo has no separate private preparation screen. After the role intro, the Round moves directly into collaboration.
- Speaker can inspect the object during collaboration. Drawer remains secret-blind before Reveal.

### Speaker play

- Display role chip `You talk`, music control, and time-left UI only if timing is confirmed or fixture-labeled.
- Show the private object/reference in the Photo card with rotate/zoom/reset controls and image fallback.
- Show the partner drawing live in a read-only dark frame with a live indicator and remote talking bars.
- The Speaker can hold to talk during collaboration. Releasing, pointer cancellation, socket loss, phase exit, or room close must stop/cancel the local hold.
- The Speaker must not be able to mutate drawing operations from this view.

### Drawer play

- Display role chip `You draw`, remote speaker talking strip, editable canvas, palette, undo, clear, hold-to-talk, and Done.
- Use normalized retained strokes with bounded point counts. Keep rendering DPR-aware and resilient to resize/orientation change.
- Clear must require confirmation at least where the design specifies it. Prefer confirmation consistently on small devices too unless later UX testing rejects it.
- Done submits the last acknowledged drawing revision. Do not submit an arbitrary PNG disconnected from the server revision.
- The Drawer view must not receive or preload object data before Reveal.

### Checking

- Show Drawy checking while the round is finalizing.
- Finalizing must have a timeout/failure path. Provider failure should become neutral/unscored feedback or a safe retry, not a poor score.
- Microphone and drawing edits are disabled in this state.

### Result and Discovery Reward

- Show shared team result, role-appropriate child copy, drawing vs reference after Reveal, sticker/reward, Play again, and Done.
- The Discovery Reward is available every round regardless of stars or AI availability.
- Play again uses both-ready acknowledgement. If one child is ready first, show friendly waiting copy such as "Waiting for Kiwi to be ready..." and "Mango wants to play again!"
- Do not require both children forever if one disconnects; use the reviewed timeout/help policy once decided.
- Role swap and next-round secret delivery are server decisions. The frontend requests Play again and renders the next snapshot.

### Grown-ups area

- The visual design includes parent-facing sample data. Production access is blocked until a separate host/grown-up authorization mechanism is defined.
- Never grant this area based on nickname, avatar, or possession of a child guest session alone.
- Keep detailed metrics out of child projections.

## Product decisions to reconcile before integration

The approved UI artifacts include decisions that are not yet reflected in the current product/lifecycle docs, or that conflict with them. Resolve these in the owning docs before accepting Feature 08.

| Decision | Current design direction | Current docs status | Blocks |
| --- | --- | --- | --- |
| Preparation | No separate preparation step; short role intro fades into play | Resolved for demo: role intro then collaboration | Feature 02 lifecycle, Feature 08 round integration |
| Mode selection | Normal button active; Advanced button visible but unavailable for now | Resolved for demo: no Advanced behavior yet | Feature 02 rooms/round setup, object selection |
| Feedback child copy | Show 1-3 stars when scoring succeeds; show friendly neutral/unscored result when AI/scoring is unavailable; two Drawy sentences from a prewritten bank | Resolved for demo: neutral/unscored is allowed when needed | Feature 07 feedback, Feature 08 result UI |
| Parent metrics | Detailed category scores for parents only | Host/grown-up authorization unresolved | Grown-up area, privacy gates |
| Time-left bar | Visible on play screens | Exact round timer and time-up behavior unresolved | Feature 02/08 lifecycle and UI |
| Play again/Done | Play again waits for both children, then swaps roles; Done exits | Match length and disconnect timeout unresolved | Feature 08 integration |
| Failure screens | Still to design | Docs require usable fallbacks | Feature 09 hardening and some earlier feature acceptance |

## Fixture-first implementation plan

After Feature 01 creates the workspace and canonical fixtures, implement frontend logic in this order:

1. App shell, design tokens, responsive frame, asset loading, and route/state scaffolding.
2. Join flow screens using sanitized fixtures, then wire to Feature 02 when ready.
3. Role intro and play layout shells for both roles using role-filtered snapshots.
4. Drawing component in isolation per Feature 03, then authorized relay after Feature 02.
5. Object viewer in isolation per Feature 04, then private role/phase access after Feature 02.
6. Hold-to-talk controls per Feature 05 after real media setup, not as fake audio.
7. Checking/result panels against Feature 07 fixtures, then real finalization in Feature 08.
8. Device and recovery hardening per Feature 09.

Keep each step independently reviewable. Do not wire fake backend/provider behavior in a way that looks production-complete.

## Frontend acceptance checks

For the UI implementation slice, record exact browser/device evidence for:

- Visual match to `artifact/screens/` at iPad 820 x 1180 and iPhone 390 x 844 frames.
- Touch targets meet the approved minimums: 72 px+ on iPad, 46 px+ on iPhone.
- No Drawer-before-Reveal fixture, response, DOM, preload, cache, or bundle contains object ID/name/rubric/asset URL/model bytes.
- Speaker view receives drawing updates but cannot edit.
- Drawer can draw with finger, undo, clear with confirmation, survive orientation changes, and submit the acknowledged revision.
- Hold-to-talk starts only while pressed and stops on release/cancel/loss/phase exit.
- Result screen handles both scored and neutral/unscored outcomes without negative child judgment.
- Asset/WebGL/AI/media failures have child-safe fallback screens and do not strand Play again.

## Copy and tone rules

- Use child-friendly English with minimal reading.
- Drawy gives encouragement and one guiding question. Drawy should never look sad or pressure the child.
- Do not show raw provider/database errors, transcripts, exact adult metrics, or model confidence to children.
- Do not describe the app as a diagnosis, therapy replacement, or validated educational assessment.

## Open inputs needed from design/product owner

Before real integration, confirm:

1. What is the exact play timer behavior when time runs out?
2. What is the disconnect timeout for Play again waiting?
3. What should children see when teammate disconnects, 3D fails, microphone fails, or AI feedback times out?

Resolved copy:

- Advanced unavailable: "Advanced pictures are coming soon!"
- Neutral/unscored result: "Drawy had trouble checking this one, but you still finished the round together!" and "Let's look at the picture and try another one."
