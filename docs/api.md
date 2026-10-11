# HTTP and WebSocket contract draft

Status: proposed v1 integration contract with Feature 01 canonical schemas/fixtures implemented. Later changes require coordinating the contract owner. Only `GET /health` is live; the gameplay endpoints and socket messages are not implemented.

Related: [product](product.md), [lifecycle](round-lifecycle.md), [data model](data-model.md), [architecture](architecture.md).

## Conventions and authentication

- HTTPS base path: `/api/v1`. JSON identifiers are opaque strings; times are UTC ISO-8601.
- Role values: `speaker` and `drawer`. Round phases: `role_intro`, `collaborating`, `finalizing`, `feedback`, `exploring`, `finished`, matching the lifecycle document.
- Guest authentication: `Authorization: Bearer <guest_session_token>` for protected HTTP calls. Tokens bind to one Player/Room; names are not credentials.
- Host operations require a separate host credential. The host-access mechanism must be reviewed before exposing them; never interpret a nickname as host authority.
- Socket endpoint: `/api/v1/rooms/{room_id}/socket` over WSS. Browser authenticates in its first message, not a long-lived token in a URL. Validate Origin; send no game state before successful authentication; enforce an authentication timeout.
- Media credentials are separate scoped LiveKit tokens issued by the backend. Guest/host credentials and provider API keys do not become media metadata.
- Bound message/image sizes, point counts, simultaneous holds/jobs, and timeouts. Values are to be pinned/tested during the owning feature; deferring custom rate limiting does not mean unbounded inputs.

## Proposed HTTP endpoints

| Method / path | Caller | Purpose |
| --- | --- | --- |
| `GET /health` | Deployment/test | Minimal liveness; no secrets/config dump |
| `POST /rooms` | Host only | Create controlled private Room; disabled until host authorization is chosen |
| `POST /rooms/join` | Joining device | Resolve shape code, validate nickname/avatar, create guest session under admission policy |
| `GET /rooms/{room_id}/state` | Admitted guest / authorized host | Role-filtered current state; host detail requires explicit separate projection |
| `POST /pairs/{pair_id}/media-session` | Current Pair member | Issue subscribe-only microphone-capable room session, not an always-open publishing grant |
| `GET /rounds/{round_id}/object-access` | Authorized role/phase | Private reference/GLB access; denied to Drawer before Reveal |
| `POST /rounds/{round_id}/drawing-submission` | Current Drawer | Freeze acknowledged revision and create/validate its bounded PNG; idempotent |
| `POST /rooms/{room_id}/close` | Host only | Close Room, revoke sessions/media, schedule policy-compliant cleanup |

Media-session issuance must use a provider grant that initially disallows publication; microphone publication is enabled only for a live authorized hold. Exact LiveKit grant fields must be verified against the pinned SDK.

Controlled demo Rooms may be provisioned server-side before a host UI exists. Do not expose unauthenticated host routes as a shortcut.

### Join example

```json
{
  "shape_code": ["circle", "triangle", "square"],
  "nickname": "BlueFox",
  "avatar_id": "fox"
}
```

On success, `201` returns `room_id`, `player_id`, `guest_session_token`, `expires_at`, and `admission_status`. Shape vocabulary and avatar catalog are allowlisted fixtures/catalogs, not arbitrary paths. Room admission determines whether the new guest can see a Pair; possessing a shape code is not host authorization.

Concurrent normalized-name conflicts return `409` with code `nickname_taken` and friendly text. A reconnect uses the existing token; joining with the same name without it cannot resume the other player's session.

### Submission example

```json
{
  "command_id": "unique-submission-id",
  "expected_round_version": 4,
  "drawing_revision": 37
}
```

Respond `202` when a single submission has been accepted and finalization is pending. Freeze the current server-acknowledged revision transactionally. The drawing feature chooses and documents authoritative server rendering versus verified client export. Do not accept an arbitrary PNG detached from revision 37. A replay returns the original submission outcome; a different payload under the same command ID is a conflict.

## Socket envelopes

First message:

```json
{
  "protocol_version": 1,
  "type": "session.authenticate",
  "payload": {"guest_session_token": "private-possession-credential"}
}
```

Typical command after authentication:

```json
{
  "protocol_version": 1,
  "type": "drawing.op",
  "command_id": "unique-command-id",
  "round_id": "round-id",
  "payload": {
    "expected_revision": 12,
    "operation": {
      "kind": "stroke.append",
      "stroke_id": "existing-stroke-id",
      "points": [{"x": 0.4, "y": 0.6}]
    }
  }
}
```

Server responses carry `protocol_version`, `type`, an event identity, and `payload`; command acknowledgements/errors also carry `command_id`. State messages identify Room/Pair/Round and their relevant version/revision. Event IDs help diagnose duplicates; they are not a promise of event-log replay. Reconnect requests a current snapshot.

### Client command families

| Type | Permission / payload responsibility |
| --- | --- |
| `state.request` | Authenticated member; request current permitted projection and drawing snapshot |
| `round.intro.seen` | Current participant; role intro completed or skipped under the reviewed timing policy |
| `voice.hold.start` | Participant in collaboration; unique `hold_id`, connection epoch, round identity |
| `voice.hold.end` | Owner of hold; same `hold_id`/epoch; idempotent even before a grant arrives |
| `drawing.op` | Current Drawer only; expected drawing revision, bounded stroke start/append/end or undo/clear operation |
| `round.explore` | Participant acknowledging feedback presentation |
| `round.play_again` | Participant's Play again intent; both-ready acknowledgement with phase version guard |
| `session.heartbeat` | Authenticated connection; authority/connection health, never automatic mic renewal |

A microphone hold does not need exclusive access to a global round version or speaking floor. Track each participant's active hold separately. Phase/epoch checks invalidate old-round requests; end/cancel must work when a grant acknowledgement is delayed.

### Server event families

| Type | Meaning |
| --- | --- |
| `session.authenticated` | Session/membership accepted; includes new connection epoch |
| `command.ack` / `command.error` | Identified operation accepted/rejected; not a substitute for current state |
| `state.snapshot` | Full permitted projection after authentication, resync, or a transition |
| `voice.hold.granted` | Provider confirmed permission for that still-active hold; client must still be holding |
| `voice.hold.ended` | Hold ended/canceled; provider failure may additionally pause the round |
| `drawing.updated` | Authorized revision/operations to Drawer and read-only Speaker |
| `drawing.snapshot` | Current retained drawing and revision for reconnect/resync |
| `round.feedback` | Finalized role panels/shared result; no private adult metrics |
| `round.paused` / `round.resumed` | Explicit recovery state; resume never reopens microphones |
| `room.closed` | Stop operations/media and clear session/drafts under policy |

No child-facing transcript stream or free-text chat is required. AI status/evidence is internal until approved feedback is ready.

## Role-filtered snapshots

Common fields: membership, teammate avatars/nicknames, role, permitted phase/version, connection status, relevant drawing revision, and feature availability. Construct each role projection explicitly.

- Speaker in role intro/collaboration may receive the current object's authorized access plus read-only drawing state.
- Drawer in role intro/collaboration receives its editable drawing state but **no object identity, rubric, label, URL, or asset bytes**. Omit secret fields entirely; do not send them and hide them with CSS.
- Before feedback, results/model evidence are not exposed as a substitute secret checklist.
- At Reveal, both may receive object/reference/model access, separate child-safe role recaps/tips, and the shared team result. Stars may be absent with explicit neutral/unscored status when analysis/rubric is unavailable.
- Host projection is separately authorized; guest snapshots never contain exact adult metrics or credentials.
- Neither role may obtain another Pair's state/media/assets using guessed IDs.

## Errors and recovery

HTTP errors use `{ "error": { "code": "...", "message": "...", "retryable": false } }`. Socket command errors carry the same shape plus the originating command ID. Child-facing copy is curated and minimal; raw provider/database errors never reach them.

Expected codes include `nickname_taken`, `session_invalid`, `room_unavailable`, `not_admitted`, `not_authorized`, `wrong_phase`, `stale_round`, `drawing_revision_conflict`, `hold_canceled`, `payload_invalid`, and `provider_unavailable`. Use 401 for invalid session, 403 or consistently masked 404 for denied resources, 409 for state/idempotency conflicts, 422 for invalid bounded input, and 503 for temporary dependencies. Choose the masking policy consistently when implementing.

- Same command identity + same payload replays its outcome. Same identity + changed payload is rejected.
- Stale drawing revisions trigger snapshot resync; never silently drop a child's work and analyze an older image.
- Lost authority/connection stops local transmit/playback and invalidates pending presses; server reconciles/revokes permissions.
- Late grants, old-round strokes, and late model results cannot revive canceled work or overwrite a finalized round.
- Log opaque IDs and bounded error codes, never tokens, nicknames, transcripts, model prompts, or signed URLs.

## Contract ownership

Feature 01 establishes canonical Pydantic HTTP/socket schemas, exportable JSON/OpenAPI schema, client types, and sanitized fixtures. Generated files are not edited manually. This Markdown document describes the reviewed interface; it is not a second hand-written implementation of every type.

One owner coordinates interface changes and updates affected fixtures, docs, and tests. Parallel lanes consume the agreed types; they do not invent incompatible endpoints or message names independently.
