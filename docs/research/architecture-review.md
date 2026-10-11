# Heary Drawy architecture review

> Historical independent review, before nickname sessions and live-collaboration changes. It did not verify live documentation/devices. Read the [current architecture](../architecture.md) and [product](../product.md) instead of treating this review as the build plan.

## Verdict

The candidate stack is appropriate, provided it is simplified to **one authoritative game server, one state-update channel, and one microphone capture path**. The largest unresolved risks are enforceable push-to-talk permissions, Safari lifecycle behavior, transcription boundaries, and hidden-information leakage. These are prototype gates, not solved capabilities.

This review uses the supplied technical and iOS reports. No application, device behavior, provider guarantees, or current documentation was independently verified.

## 1. Recommended architecture

| Responsibility | Recommendation |
|---|---|
| Client | React + TypeScript + Vite, served over HTTPS |
| Drawing | Canvas + Pointer Events, with a retained stroke model |
| Game authority | One long-running Node/Fastify service |
| State notifications | Authenticated server WebSocket with role-filtered snapshots |
| Durable state | Supabase Postgres |
| Identity and drawing storage | Supabase Auth and private Storage |
| Human voice | LiveKit Cloud, one media room per pair |
| Transcription | Server-side media subscriber in the same backend deployment, streaming authorized turn PCM to STT |
| Analysis | Fixed-schema text/vision extraction, validated server-side |
| Feedback | Versioned deterministic rules and curated tips |
| Reveal | Curated GLB assets through model-viewer, no AR |

**Prefer the static SPA plus long-running Node service over Next.js all-in-one.** This game does not need server-rendered pages or SEO. Persistent media subscriptions, turn timers, and transcription streams require a long-lived runtime regardless. Next.js is viable on a persistent Node deployment, but adds little here; serverless request handlers should not own these responsibilities.

Use Supabase for persistence, identity, and storage, not as a second game authority. Do not add Supabase Realtime alongside the game WebSocket. Postgres-backed pending analysis jobs, processed by the same service, are sufficient initially. No Redis, Kubernetes, event sourcing, or agent framework is justified.

**Gate the Node media subscriber early:** decoding subscribed WebRTC audio into the STT provider’s required PCM format is not automatically established by choosing Node. Validate the supported server SDK/runtime, resampling, and shutdown behavior before committing. If a separate media worker is concretely required, add only that worker.

## 2. Exact audio routes and speaking control

### Human route

`One browser microphone track -> authorized LiveKit publication -> pair partner playback`

### AI route

`Same publication -> backend subscriber -> turn-scoped PCM -> streaming STT -> finalized transcript -> feature extraction -> curated coaching`

There is no second browser recorder, browser STT session, or AI proxy in the teammate’s audio path. AI failure must not interrupt voice delivery. The subscriber receives only authorized audio; raw voice is not permanently stored.

Clients receive scoped media tokens, never provider API secrets or Supabase service credentials. Pair participants may subscribe only within their pair. Human publication is microphone-only; server authorization must also reject video, screen sharing, and unauthorized tracks.

### Push-to-talk protocol

1. A press requests a turn using a round ID, expected version, and unique request ID.
2. The server grants a turn ID, speaker identity, media-session epoch, and bounded speaking lease.
3. The client transmits only after that grant and after local readiness checks.
4. Release immediately stops local transmission, then submits an idempotent end command.
5. The server revokes publishing, closes the audio segment, and advances state.

A release occurring before the grant must cancel the request: a delayed grant must never reopen the microphone. Handle pointer cancellation, lost capture, backgrounding, disconnect, and role changes identically.

**Permission revocation is a critical feasibility test.** Token expiration and a disabled button do not prove an existing publication stops. Verify provider-side revocation, track removal, reconnect behavior, and stale-token rejection. Disconnect the participant if necessary to fail closed. If bounded server-side cutoff cannot be demonstrated, this design does not meet the requirement.

Client release provides prompt muting; server leases provide an independent maximum bound. Neither eliminates packets already in flight. Measure and define the acceptable tail rather than promise instantaneous silence.

## 3. Authoritative turns, finalization, and recovery

Persist round phase, role assignments, version, turn counters, active turn, drawing submission, analysis status, and finalized feedback. Store secrets separately.

- Validate every command against identity, classroom, pair, round, role, and version.
- Serialize mutations with database transactions and row locking.
- Enforce the extra-description limit and single question/answer branch server-side.
- Make submission and scoring idempotent through unique constraints.
- Require both players’ Continue acknowledgements before swapping roles.
- On reconnect, send a fresh authorized snapshot, not an assumed replay of missed notifications.

Separate **audio ended** from **transcript finalized**. On release, finish the STT segment and await its documented finalization with a deadline. Coaching uses the finalized transcript, never unstable partials. Mark truncated, timed-out, or interrupted turns incomplete; offer a bounded retry or neutral fallback.

Tag asynchronous work with round, turn, input revision, and analysis attempt. Reject obsolete results. Finalization writes evidence, rubric/model versions, stars, and tip atomically; retries cannot award stars twice or silently revise completed feedback.

After backend restart, pause active turns and revoke stale media authorization before resuming commands. Never automatically reopen speaking. Pending analysis can restart from permitted durable inputs; unavailable ephemeral audio means an interrupted turn, not an invented transcript.

Persist draft strokes in local session storage with round ownership, clear them at room exit, and document retention. This supports refresh recovery without continuously uploading the drawing.

## 4. Hidden information and bot isolation

Role-specific responses must exclude secret IDs, labels, feature checklists, reference images, coaching, and model URLs from the Drawer. Avoid broad database subscriptions and inspect error messages, logs, and frontend payloads.

**“Local GLB assets” must not mean public secret assets.** Keep assets in deployment-controlled private storage or authenticated server routes. Do not bundle the object catalog, preload identifiable models, or let a service worker cache future secrets. Authorize each reference/model request by role and reveal state. A signed URL is a temporary bearer capability.

The Describer’s coaching remains private before reveal. Protect the Drawer’s drawing from the Describer until results.

For the eventual bot Drawer, create a separate input contract containing only the permitted descriptions and clarification answer. Exclude object IDs, rubrics, references, media metadata, and secret-bearing tools. Reset bot context each round, especially after it previously played Describer. A symbolic drawing renderer is plausible but **unvalidated**. Do not secretly select a canned answer or penalize the child for renderer limitations.

## 5. Mobile drawing and reveal

Canvas is sufficient. Retain normalized strokes independently of bitmap size; redraw after orientation/layout changes and device-pixel-ratio scaling. Use pointer capture, scoped `touch-action`, undo, and explicit export dimensions/background. Test simultaneous listening and drawing on the iPhone, not just the iPad.

model-viewer is sufficient for rotation, zoom, and reset. Three.js is unnecessary without custom scene interactions. Validate accessible controls, modest asset sizes, memory/context loss, and cleanup between rounds. Mount the viewer only after reveal authorization.

A static reference fallback must preserve Continue. The 3D reward remains available after neutral AI fallback and never becomes a drawing-quality standard.

## 6. Reliability, scoring, and child-data gates

Use three-state evidence and quoted transcript support. Fixed schemas constrain format, not truth. Validate negation and unsupported claims; never treat model confidence as calibrated or results as clinical evidence.

For the demo, label stars as a provisional team-game policy. Use a completion floor plus bounded evidence bonuses; unknown evidence must not reduce stars. Service failure produces clearly neutral feedback rather than fabricated success. Freeze the policy and rubric version.

Adults/synthetic data are mandatory until jurisdiction, consent, provider eligibility, retention, deletion, and operational access gates are resolved across **all** processors, including media transport and logs. Avoid content logging and unnecessary analytics. Private classrooms do not establish compliance or prevent harmful live speech; include adult pause/mute controls.

Keep the demo controlled despite deferred custom rate limiting: restricted admission, expiry, bounded turn lengths, upload sizes, and provider spending limits.

## 7. Top five failures to prototype first

1. **Microphone remains audible after release:** delayed grant, lost release, backgrounding, stale token, or malicious publication. Verify local cutoff and independent server revocation on both devices.
2. **Secret reaches the wrong role:** inspect payloads, asset requests, subscriptions, caches, role swaps, and bot inputs with an unauthorized third session.
3. **Live speech is missing or unusable:** Safari autoplay, permission denial, interruptions, echo, network change, and TURN fallback. Pause and repeat rather than imply delivery.
4. **State and scoring diverge:** duplicate Done, simultaneous commands, refresh, backend restart, and late AI completion. Assert one durable result and no stale transition.
5. **Turn evidence or mobile output fails:** clipped final words, uncertain transcription, ambiguous sketches, orientation loss, and WebGL failure. Verify neutral feedback, preserved drawing, and reveal/Continue fallback end to end.
