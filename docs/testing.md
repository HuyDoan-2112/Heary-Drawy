# Testing and acceptance

Status: test strategy only. No game tests, real-device media connection, AI benchmark, or educational outcome test has run. Earlier passing checks apply to HTML explainers/diagrams, not gameplay.

## Layered checks

1. **Contracts:** schema validation, generated-client compatibility, sanitized role fixtures, negative secret-field checks.
2. **Domain/integration:** database constraints, authorization, lifecycle transitions, stroke revisions, hold cancellation, durable analysis/result idempotency. Exercise real database transactions where concurrency matters.
3. **Browser E2E:** two isolated authenticated sessions, joins, role views, canvas relay, submission, feedback, Reveal, Play again. Clearly distinguish simulated media/model fixtures from real services.
4. **Actual devices:** HTTPS Safari on the user's iPad and iPhone, both role directions, actual microphone/playback/WebRTC/3D behavior. Desktop device emulation is not this gate.
5. **Provider/fixture evaluation:** adult/synthetic speech and rough drawings, paraphrases, negation, interruptions, overlap, missing/incomplete evidence, and provider failures.

Suggested tools are pytest for backend tests, Vitest/React Testing Library for focused UI behavior, and Playwright for browser E2E. Install and document only the tools used by feature 01. There are no working commands to run yet; do not fabricate them.

## Critical scenarios

### Identity and permission

- Concurrent `Sam`/`sam` joins admit only one normalized name; conflict copy is friendly.
- Another browser using the same name cannot take over a Player. Valid session refresh/reconnect resumes it.
- Guessed Room/Pair/Round IDs and invalid/expired/revoked tokens yield no private data/media.
- Drawer cannot request secret assets or find object identifiers in sockets, responses, metadata, caches, bundle, or preloads before Reveal.
- Speaker sees but cannot edit the partner canvas. Third Room member cannot subscribe to Pair content.
- A nickname such as `Teacher` gives no adult access.

### Canvas and object

- Finger drawing, palette, undo/clear, orientation change, and bounded PNG export work on both devices.
- Incremental updates arrive in the Speaker view; duplicate/out-of-order operations resync safely.
- Simultaneous drawing and hold-to-talk touch interactions do not create stray strokes or stuck microphones.
- Submission freezes the acknowledged revision; late operations cannot alter the analyzed drawing.
- Speaker retains 3D access during questions; Drawer gains it only at Reveal.
- Asset/WebGL failure shows an image fallback and usable Play again path.

### Live voice and transcription

- Mic permission and remote-playback unlock are explicit. Partner hears original live speech while held, before AI completes anything.
- Release-before-grant, pointer cancellation, lost socket, backgrounding, role change, and room closure all stop/cancel transmission.
- Both participants may hold concurrently without forced alternating turns; attribution remains separate.
- Reconnect/restart never reopens a mic or replays queued presses automatically.
- Provider revocation failure pauses rather than pretending the grant is gone; verify effective track unpublication and token behavior.
- Test echo, first/last word preservation, poor network, cross-network/TURN behavior where possible, and controlled backend restart.
- Manual commit/final events map to correct participant/Round/hold IDs even when out of order. Overflow/missing final events produce incomplete evidence, not silently truncated success.

### Feedback and progress

- Keyword positives require relevant Speaker evidence, not just a Drawer question, negated phrase, or injected instruction.
- Drawing checks include only communicated visual features; function clues are not mandatory visual requirements.
- No artistic-quality judgment, competitive role scores, or uncalibrated confidence claims.
- Duplicate job retries publish one result. Late results for an old revision/Round are ignored.
- Provider timeout yields neutral/unscored feedback and the full Discovery Reward.
- Play again applies both-ready acknowledgement, swaps roles once, and does not wait forever for a disconnected teammate. Next-round secrets remain private.

## Evidence and completion

Each feature brief records actual checks, date/environment, failures, and remaining gates. A feature with isolated tests but unmet provider/device checks is not fully complete; label it partial or blocked instead of claiming success.

Record actual hardware/OS, network scenario, dependency/model versions, microphone/role direction, and observable failures. Measure latency on the real path before setting a promised target; none has been established yet.

Use the [implementation plan](implementation-plan.md) as the status summary. A docs link checker or HTML browser test validates documentation, not app functionality. Child participation and learning impact remain separate from technical acceptance.
