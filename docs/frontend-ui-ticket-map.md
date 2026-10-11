# Frontend UI ticket map

Status: planning aid. UI-01 through UI-09 and UI-13 through UI-15 are implemented as fixture-backed screens that reproduce the approved `artifact/` designs. Layouts are fluid: sizes interpolate from the iPhone design (390 px wide) to the iPad design (820 px wide), and screens without an iPhone design are adapted from the iPad one. Checked in headless Chromium at 375 x 667, 390 x 844, 430 x 932, 820 x 1180, 1180 x 820, and 1280 x 800, not on real devices. This breaks [`frontend-ui-implementation-spec.md`](frontend-ui-implementation-spec.md) into independently reviewable implementation tickets. It does not authorize building ahead of the feature dependencies in [`implementation-plan.md`](implementation-plan.md).

## Purpose

Use this map to keep the approved visual UI work aligned with the feature sequence. Frontend screens may start fixture-first only after Feature 01 provides the workspace, canonical contracts, generated types, and sanitized fixtures.

Do not treat the frontend UI spec as one large ticket. Each ticket below has explicit dependencies and must report evidence for only the slice it implements.

## Dependency summary

| Ticket | Slice | Required before starting | Integrates later with |
| --- | --- | --- | --- |
| UI-01 | Frontend shell and design tokens | Feature 01 workspace | Implemented as fixture-backed shell |
| UI-02 | Typed UI fixtures and role-filtered state | Feature 01 contracts/fixtures | Implemented as safe fixture state |
| UI-03 | Pick character | UI-01, UI-02 | Implemented as fixture-backed screen |
| UI-04 | Turn on mic | UI-01 | Implemented as fixture-backed screen |
| UI-05 | Pick mode | UI-01, UI-02 | Implemented as fixture-backed screen |
| UI-06 | Meet teammate | UI-02 | Implemented as fixture-backed screen |
| UI-07 | Role intro | UI-02 | Implemented as a timed overlay that fades into each play screen |
| UI-08 | Speaker play shell | UI-02 | Implemented as fixture-backed shell |
| UI-09 | Drawer play shell | UI-02 | Implemented as fixture-backed shell |
| UI-10 | Drawing component integration | Feature 03 | Feature 08 round integration |
| UI-11 | Object viewer integration | Feature 04 | Feature 08 Reveal/reward |
| UI-12 | Hold-to-talk integration | Feature 05 | Feature 08 round integration |
| UI-13 | Checking/finalizing | Feature 07 fixtures or accepted fallback contract | Implemented as fixture-backed screen |
| UI-14 | Result and Discovery Reward | Features 04, 07 | Implemented as fixture-backed screen |
| UI-15 | Grown-ups gate placeholder | UI-01 | Implemented as the designed 3-second hold gate in front of a sample-data parent page; real access still blocked |
| UI-16 | Recovery and failure states | Relevant feature fallback contracts | Feature 09 hardening |
| UI-17 | Visual/device acceptance pass | Implemented screen slices | Feature 09 hardening |

## Tickets

### UI-01 - Frontend shell and design tokens

**Depends on:** Feature 01 foundation.

**Scope:**

- Create the React/TypeScript/Vite frontend shell once the workspace exists.
- Add route placeholders for the approved screens.
- Add responsive iPad/iPhone layout frame.
- Add design tokens for colors, spacing, typography, surface styles, and touch target sizes.
- Load approved Drawy and avatar assets safely.

**Acceptance:**

- App shell starts with documented commands.
- Placeholder routes render without claiming real gameplay is available.
- Reusable styles encode touch target minimums: 72 px+ on iPad and 46 px+ on iPhone.
- `.dc.html` design files are not used as production runtime code.

### UI-02 - Typed UI fixtures and role-filtered state

**Depends on:** Feature 01 contracts and fixtures.

**Scope:**

- Define UI state slices for session, room, round, object, drawing, voice, and feedback.
- Consume generated contract types instead of hand-written incompatible shapes.
- Add sanitized role-filtered fixtures for Speaker, Drawer before Reveal, Reveal, drawing updates, and command errors.
- Make fixture mode visibly distinguishable in development and review evidence.

**Acceptance:**

- Fixtures validate against canonical schemas.
- Drawer-before-Reveal fixtures omit object ID, name, rubric, URLs, model bytes, and identifying asset metadata.
- No complete secret catalog is bundled into the Drawer-before-Reveal path.
- Tests prove Drawer projections omit secret fields entirely instead of hiding them in CSS or unused properties.

### UI-03 - Pick character screen

**Depends on:** UI-01, UI-02.

**Future integration:** Feature 02 real join.

**Scope:**

- Implement the pick character screen.
- Show 10 approved avatars.
- Require avatar selection and nickname entry.
- Show unavailable avatars only when fixture/backend state explicitly says so.
- Add a Grown-ups button that opens only the gate/blocked UI.

**Acceptance:**

- Visual match is checked against `artifact/screens/01-pick-character.png`.
- Nickname copy does not imply authentication or account ownership.
- Duplicate nickname fixture displays friendly `nickname_taken` copy.
- Grown-ups entry does not grant host privileges.

### UI-04 - Turn on mic permission screen

**Depends on:** UI-01.

**Future integration:** Feature 05 live voice.

**Scope:**

- Implement the microphone permission screen.
- Request browser microphone permission only from a clear user action.
- Show denied, retry, and help states.
- Explain that permission does not publish audio by itself.

**Acceptance:**

- Visual match is checked against `artifact/screens/02-turn-on-mic.png`.
- No audio is published from this screen.
- Permission denial does not strand the user.
- Raw browser/provider errors are not shown to children.

### UI-05 - Pick mode screen

**Depends on:** UI-01, UI-02.

**Future integration:** Feature 02 room setup.

**Scope:**

- Implement the mode screen.
- Show Normal as selected.
- Show Advanced as visible but unavailable.
- Use the resolved copy: "Advanced pictures are coming soon!"

**Acceptance:**

- Visual match is checked against `artifact/screens/03-pick-mode.png`.
- Advanced cannot alter object selection or gameplay.
- No hidden production difficulty logic exists.

### UI-06 - Meet teammate screen

**Depends on:** UI-02.

**Future integration:** Feature 02 pairing.

**Scope:**

- Implement the teammate screen.
- Show teammate nickname/avatar from role-filtered state.
- Add a waiting state for pending pairing.
- Do not invent a Bot Partner.

**Acceptance:**

- Visual match is checked against `artifact/screens/04-meet-teammate.png`.
- Pending pairing has friendly waiting copy.
- Bot Partner is not shown unless Feature 10 explicitly provides it.

### UI-07 - Role intro screen

**Depends on:** UI-02.

**Future integration:** Feature 02 lifecycle.

**Scope:**

- Implement the role intro substate.
- Show role-specific intro copy.
- Support a short fixture/local transition for review.
- Prepare for `round.intro.seen` once the socket contract is wired.

**Acceptance:**

- Visual match is checked against `artifact/screens/05a-role-intro-ipad.png`.
- Speaker intro only receives object access when authorized.
- Drawer intro receives no object data.
- Timer/transition behavior is labeled fixture-local until the lifecycle policy is wired.

### UI-08 - Speaker play shell

**Depends on:** UI-02.

**Future integration:** Features 02, 03, 04, and 05.

**Scope:**

- Implement Speaker play screens for iPad and iPhone.
- Show role chip `You talk`, private object viewer slot, rotate/zoom/reset controls, read-only drawing frame, live indicator, hold-to-talk control shell, and speaking indicators.
- Keep the drawing frame read-only.

**Acceptance:**

- Visual match is checked against `artifact/screens/05b-speaker-ipad.png` and `artifact/screens/05d-speaker-iphone.png`.
- Speaker receives drawing updates in fixture mode.
- Speaker cannot edit the drawing.
- Hold-to-talk UI does not publish fake audio.

### UI-09 - Drawer play shell

**Depends on:** UI-02.

**Future integration:** Features 03 and 05.

**Scope:**

- Implement Drawer play screens for iPad and iPhone.
- Show role chip `You draw`, editable canvas slot, palette, undo, clear, Done, hold-to-talk shell, and remote speaker talking strip.
- Ensure the view does not read object/reference fields before Reveal.

**Acceptance:**

- Visual match is checked against `artifact/screens/05c-drawer-ipad.png` and `artifact/screens/05e-drawer-iphone.png`.
- Drawer view has no object ID, name, rubric, URL, or model bytes before Reveal.
- Clear confirmation exists where specified.
- Done uses the acknowledged drawing revision once Feature 03 is integrated.

### UI-10 - Drawing component integration

**Depends on:** Feature 03 drawing.

**Scope:**

- Implement touch drawing with normalized retained strokes.
- Add undo and clear.
- Make rendering DPR-aware.
- Support resize and orientation changes.
- Add read-only rendering mode for Speaker.

**Acceptance:**

- Drawer can draw with finger.
- Undo works.
- Clear requires confirmation.
- Speaker view is read-only.
- Submission references the last acknowledged revision, not an arbitrary PNG detached from server state.

### UI-11 - Object viewer integration

**Depends on:** Feature 04 object viewer.

**Scope:**

- Implement authorized object/reference viewer.
- Support rotate, zoom, and reset.
- Add image fallback for failed 3D/WebGL.
- Enforce role/phase-filtered access in UI consumption.

**Acceptance:**

- Speaker can inspect the object during collaboration.
- Drawer cannot receive or preload object data before Reveal.
- Both roles can access the object after Reveal.
- 3D failure falls back safely and does not strand the round.

### UI-12 - Hold-to-talk integration

**Depends on:** Feature 05 live voice.

**Scope:**

- Wire hold-to-talk controls to real media/session commands.
- Start only while pressed.
- Stop on release, pointer cancel, socket loss, phase exit, and room close.
- Show local and remote speaking indicators.

**Acceptance:**

- No always-open microphone exists.
- Holds are independently tracked per participant.
- A late grant after release does not publish.
- Reconnect never automatically reopens the microphone.

### UI-13 - Checking/finalizing screen

**Depends on:** Feature 07 fixtures or an accepted fallback contract.

**Future integration:** Feature 08 finalization.

**Scope:**

- Implement Drawy checking screen.
- Disable microphone and drawing edits.
- Support timeout and failure fallback state.
- Avoid poor scores on provider failure.

**Acceptance:**

- Visual match is checked against `artifact/screens/06-drawy-checking.png`.
- Finalizing state prevents edits and talk.
- AI/provider timeout shows child-safe fallback.
- Raw provider errors are not shown to children.

### UI-14 - Result and Discovery Reward screen

**Depends on:** Features 04 and 07.

**Future integration:** Feature 08 Play again and role swap.

**Scope:**

- Implement the result screen.
- Show shared team result, role-appropriate feedback, drawing versus reference after Reveal, sticker/reward, Play again, and Done.
- Support scored and neutral/unscored outcomes.
- Support both-ready Play again wait state.

**Acceptance:**

- Visual match is checked against `artifact/screens/07-result.png`.
- Discovery Reward is available every round.
- Neutral/unscored copy is supported.
- No individual competitive ranking or artistic grading appears.
- Play again waits for both children and shows friendly waiting copy.

### UI-15 - Grown-ups gate placeholder

**Depends on:** UI-01.

**Blocked for real access by:** separate host/grown-up authorization decision.

**Scope:**

- Implement visual gate only.
- Do not expose real room controls or metrics.
- Make unsupported/locked status clear.

**Acceptance:**

- Visual match is checked against `artifact/screens/08-parents-phone.png`.
- Child guest sessions cannot access host data.
- Nickname/avatar cannot grant grown-up access.
- Detailed metrics are not present in child projections.

### UI-16 - Recovery and failure states

**Depends on:** Relevant feature fallback contracts.

**Future integration:** Feature 09 hardening.

**Scope:**

- Add child-safe recovery UI for teammate disconnect, socket reconnect, mic failure, media provider unavailable, 3D/WebGL failure, AI feedback timeout, and stale drawing revision.
- Align unresolved timeouts and actions with product decisions when confirmed.

**Acceptance:**

- Children are never stranded with no action.
- Local audio stops on connection/media loss.
- Editing and talking state follows authoritative phase.
- Raw provider/database errors are not displayed.

### UI-17 - Visual/device acceptance pass

**Depends on:** Implemented screen slices.

**Future integration:** Feature 09 hardening.

**Scope:**

- Test approved screens against artifact screenshots.
- Capture evidence at iPad 820 x 1180 and iPhone 390 x 844 frames.
- Verify touch target sizes.
- Verify orientation and resize behavior.

**Acceptance:**

- Screenshot evidence is recorded.
- Major visual mismatches are fixed or documented.
- Touch target minimums pass.
- Known device/browser limitations are listed honestly.

## Cross-ticket guardrails

- Do not fake real rooms, voice publishing, drawing relay, object delivery, AI feedback, or device acceptance.
- Fixture-backed UI must be labeled and must not look production-complete when dependencies are absent.
- Drawer-before-Reveal paths must not receive, preload, bundle, cache, or hide secret object data.
- Speaker can view the drawing but cannot mutate it.
- Microphone permission is not publishing. Publishing is controlled by hold-to-talk only.
- Grown-up access requires separate authorization and cannot be granted by nickname, avatar, or child guest session.
- Update the owning spec when behavior or contracts change. Do not duplicate product rules in new places unless linking back to the source of truth.
