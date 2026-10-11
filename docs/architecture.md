# Architecture

Status: long-term technical baseline, mostly deferred. **The demo uses a smaller subset:** React/Vite web app, one FastAPI process with local Postgres, one WebSocket for game state and strokes, peer-to-peer WebRTC voice on one Wi-Fi network, 2D secret pictures, local Whisper transcription of uploaded hold clips, and one DeepSeek feedback call per round. LiveKit, OpenAI, 3D GLB assets, Supabase Storage, and hosting below are not used for the demo. See [implementation-plan.md](implementation-plan.md).

## Selected baseline

| Responsibility | Recommendation |
| --- | --- |
| Frontend | React + TypeScript + Vite; Tailwind CSS with custom touch-first child controls |
| Canvas | Canvas 2D + Pointer Events, retained normalized strokes, bounded PNG export |
| 3D | Bundled model-viewer library; authorized self-contained private GLB assets |
| Backend | Python FastAPI, one persistent deployment and one process for the demo |
| Voice | LiveKit Cloud WebRTC/TURN; one media room per Pair |
| Game/canvas channel | One authenticated FastAPI WebSocket; no Supabase Realtime or Socket.IO |
| Identity | Nickname + server-issued guest session; no Supabase Auth requirement |
| Persistence | Supabase Postgres, transactional mutations, SQL migrations |
| Files | Supabase private Storage; server-authorized access |
| Transcription | Server-side OpenAI `gpt-live-transcribe`, manually committed holds |
| Feature analysis | OpenAI `gpt-5.4-mini-2026-03-17`, separate text/image jobs and strict schemas |
| Feedback | Deterministic rules and curated tips; separate role panels, shared team result |
| Hosting | Static HTTPS frontend plus an always-running FastAPI container; Render or equivalent is a candidate, not provisioned |

Pin libraries and verify model/account availability during implementation. These demo model choices do not establish suitability or permission for actual-child data.

## Three paths

1. **Human media:** browser mic -> LiveKit -> partner playback. Both use hold-to-talk independently. AI never sits in this delivery path.
2. **Control and drawing:** browser -> HTTPS/authenticated WSS -> FastAPI -> role-filtered state/live strokes. Only Drawer can mutate the canvas; Speaker receives read-only updates.
3. **Observation:** each authorized LiveKit track -> Python RTC subscriber -> bounded 24 kHz mono PCM stream -> that participant's STT session -> finalized transcript. At round end, text and submitted PNG -> feature evidence -> deterministic feedback.

One microphone capture per device. Do not mix both tracks into one transcription stream. No recording/upload/play substitute for live partner audio and no screen-sharing track.

## Planned source layout

Create these areas only as the corresponding feature is implemented. They do not exist yet.

```text
apps/web/src/
  app/                  Routing, bootstrap, integration wiring
  features/
    rooms/              Nickname/lobby and guest-session UI
    round/              Role views and round coordination
    drawing/            Stroke model, canvas, read-only live preview
    objects/            Authorized 3D/reference viewer
    voice/              Hold-to-talk and remote playback
    feedback/           Separate role panels and shared result
  lib/                  Shared API/socket adapters and small utilities
  generated/            Generated contract types, never hand-edited
services/api/
  app/
    contracts/          Canonical typed HTTP/socket schemas
    sessions/           Guest sessions and host authorization
    game/               Pairing, roles, lifecycle, role-filtered projections
    drawing/            Revision validation and live relay
    assets/             Object catalog and private asset access
    media/              LiveKit permissions, RTC subscription, hold state
    transcription/      Attributed streams, commit/finalization
    analysis/           Feature jobs and model-output validation
    feedback/           Rubric rules, curated hints, result persistence
    bots/               Later secret-free partner implementation
  tests/                Backend tests and fixtures
contracts/              Exported schemas for client types/test fixtures
supabase/migrations/    SQL migrations; coordinated single writer
tests/e2e/              Browser/two-session integration tests
```

The named backend modules share one runtime, not microservices. Source layout is an ownership plan, not a reason to introduce an abstraction for every folder.

## Authority and persistence

FastAPI owns membership, roles, phases, permitted media, drawing revisions, asset access, and final results. Browser state is a projection. Validate each command, including when service credentials bypass database row policies.

Use Postgres transactions/constraints for identities, transitions, submission, and result idempotency. Active connections/buffers are disposable. Keep analysis jobs in Postgres with bounded in-process consumption; do not add Redis or an external queue before a demonstrated need.

One backend instance/process owns media for this demo. Do not use live reload or multiple Uvicorn workers as if process-local sessions coordinated themselves. Multi-instance routing/coordination is a future design decision.

See [API](api.md), [data model](data-model.md), and [lifecycle](round-lifecycle.md) for the actual responsibility contracts.

## Role-dependent assets

The Speaker may load the current object's reference and GLB during collaboration. Drawer may load them only at Reveal. Bundle the viewer, not secret assets/catalogs. Keep models licensed, modest in size, self-contained, and consistent with the curated rubric.

Signed asset access must follow a server role/phase check. Authorized Speaker downloads are not a promise that copied URLs/bytes can be revoked retrospectively. Do not leak identifiers through room metadata, reconnect snapshots, caches, logs, or future-round preloads.

## Failures that must be designed explicitly

- Release before a delayed permission grant must never start mic transmission.
- Remote permission changes and database mutations are not one atomic transaction. Record intent/state, acknowledge a grant only after provider confirmation, and compensate/revoke a grant if its hold was canceled meanwhile.
- Revoke on end/phase exit; expiry of a join token is not an active-media cutoff.
- A dead backend cannot execute its own revocation timer. Cooperative client heartbeat muting is sufficient only for the controlled demo, not a malicious-client enforcement guarantee. Broader child deployment needs a proven independent cutoff/watchdog/relay approach.
- Audio tail/final transcription events may be late or missing. Mark evidence incomplete instead of inventing text or blocking partner audio.
- Duplicate/late jobs cannot change the submitted drawing or award a second result.
- WebGL/AI failure yields usable fallback and Play again, not a negative child judgment.

## Tradeoffs and evidence

A static SPA is preferred over Next.js because SEO/SSR are not needed and media still requires a persistent server. Python keeps game authority and RTC subscription in one backend runtime.

The [independent review](research/architecture-review.md) favored this shape with Node/Fastify. Its review predates guest-name joining and the live-collaboration revisions. LiveKit's Node reference labels RTC developer preview while its registry has a 1.x release, so maturity evidence is inconsistent; that does not prove Node is unusable or Python is faster. Verify the selected Python integration on real devices.

Avoid native packaging, AR, video, Kubernetes, event sourcing, general agent frameworks, and speculative services in this slice.

## Primary references

Checked during research on 2026-10-10; recheck endpoint/version details when implementing:

- [Vite deployment](https://vite.dev/guide/static-deploy.html), [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/).
- [LiveKit permissions](https://docs.livekit.io/intro/basics/rooms-participants-tracks/participants/), [Python RTC](https://github.com/livekit/python-sdks/tree/main/livekit-rtc), [AudioStream](https://github.com/livekit/python-sdks/blob/main/livekit-rtc/livekit/rtc/audio_stream.py), [Node RTC reference](https://docs.livekit.io/reference/client-sdk-node/).
- [Realtime transcription](https://developers.openai.com/api/docs/guides/realtime-transcription), [transcription model](https://developers.openai.com/api/docs/models/gpt-live-transcribe), [GPT-5.4 Mini snapshots](https://developers.openai.com/api/docs/models/gpt-5.4-mini), [structured output](https://developers.openai.com/api/docs/guides/structured-outputs).
- [model-viewer](https://modelviewer.dev/), [Supabase private Storage](https://supabase.com/docs/guides/storage/buckets/fundamentals), [row policies](https://supabase.com/docs/guides/database/postgres/row-level-security).

The [current diagram](../.archify/architecture-heary-drawy-20261010-114417/heary-drawy.html) is a component overview, not evidence of implemented infrastructure. Provider/child-data gates live in [privacy-and-safety.md](privacy-and-safety.md).
