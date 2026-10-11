# 02 - Guest rooms, pairing, and round authority

Status: **implemented for the demo - grown-up passcode admission; not yet checked on real devices**
Dependencies: [01](01-foundation.md)
References: [product](../product.md), [API](../api.md), [data model](../data-model.md), [lifecycle](../round-lifecycle.md)

## Deliverable

Two admitted guest sessions in a private Room receive a persisted Pair, initial random roles, and correct role-filtered round state.

## Scope and ownership

Own backend sessions/game modules, Room UI, their tests, and coordinated schema migrations.

- Internal admission seam for already-authorized nickname/avatar guests with transactional normalized-name uniqueness; scoped session token and resume/expiry behavior. There is no child-facing Room join code or link. The authorized admission/bootstrap method remains a blocking decision.
- Match waiting admitted guests only within their server-private Room; persist Pair isolation, roles/round assignment, lifecycle transition guards, current-state reconnect.
- Authenticated socket bootstrap and explicit per-role projections. Never serialize the private Round record directly.
- Define session/room reservation behavior and cleanup with the reviewed retention policy.
- Protect host operations separately. Controlled demo Rooms may be provisioned server-side; host API/UI remains disabled until host authorization is chosen.

Role intro and Play again handlers may be tested with explicit provisional fixtures. Match length and disconnect timeout decisions are required before final interaction is accepted. Keep this visible rather than hardcoding them as product rules.

## Out of scope

Canvas rendering, real voice, 3D rendering, AI, bot implementation, and unrestricted public Room creation.

## Acceptance

- [x] Concurrent internal admissions for `Sam`/`sam` yield one admitted name and one conflict (local Postgres integration). Child-facing conflict handling awaits the admission decision.
- [x] Same name without the session token cannot take over; valid session refresh resumes roles (local integration, pre-admitted browser contexts).
- [x] Pair creation/random assignment persists across reconnect/restart (local Postgres integration).
- [ ] Wrong-role/Room/Pair requests, guessed IDs, and expired sessions reveal no secrets. Existing state and command routes are checked; object/media authorization routes are owned by later features and are not implemented.
- [x] Drawer projections exclude object/rubric/asset metadata before Reveal (current role-intro projection; object assignment awaits Feature 04).
- [x] Guest nicknames never grant host actions/metrics (host routes remain disabled).
- [x] Duplicate/stale commands cannot reroll roles or repeat transitions (current intro and Play again commands, local Postgres).

## Decisions (2026-10-11)

- **Admission:** `npm run db:provision-room` prints a Room passcode once (only its hash is stored). A grown-up enters it on each device (`POST /api/v1/device-enrollments`), which unlocks that device; the child then picks a free character and an optional name (`POST /api/v1/rooms/{room_id}/guests`). Characters and names are unique among a Room's admitted players. Re-joining on a device releases its previous player.
- **Match length:** 3 rounds. Play again is refused after round 3; Done (`POST /api/v1/session/leave`) ends the session and tells the teammate.
- **Play again disconnect timeout:** 60 s then a grown-up help screen - decided but **not built yet** (demo scope).
- **Retention:** sessions and device unlocks last 24 h; `npm run db:close-room` closes a Room early; `npm run db:cleanup` deletes Rooms 7 days after they close or expire.
- **Demo round slice (Features 03-08, minimal):** the server picks a secret picture per round (speaker-only until reveal), relays live strokes, Done reveals the picture with the neutral result (no AI scoring), and hold-to-talk uses peer-to-peer WebRTC with socket signaling (no TURN). Timer, transcription, AI feedback, and limits are out of scope for now.

## Handoff

Provide canonical auth/state adapters to the canvas, object, and media lanes; record unresolved host/timing choices. Coordinate migration and contract changes through the shared owner.

Evidence (local Python 3.12, real Postgres 16.2 via `pgserver`, FastAPI TestClient):

- `supabase/migrations/20261010000000_rooms_and_rounds.sql` defines server-private RLS-protected tables, constraints and indexes. `services/api/app/db.py` applies SQL locally in order under an advisory lock. `services/api/tests/conftest.py` clones a migrated Postgres database per test; the concurrent admission/command tests fail without their database locks.
- `services/api/tests/test_rooms_and_rounds.py` covers internal room-scoped matching, concurrent normalized nickname conflicts, pair/role persistence, hashed/expired sessions, cross-Room denial, Drawer projection, host denial, socket authentication/origin, presence/transition pushes, and idempotent intro/Play again role swaps. The child-facing join route is absent. The later-feature exploration phase is injected only by a labeled fixture; no feedback or object service exists.
- `apps/web/src/features/rooms/` reconnects already-provisioned guest sessions and sends versioned intro/Play again commands. The character screen is a fixture until an authorized admission flow is designed. `npm run dev:api:local` starts a local Postgres API without admitting guests; `db:provision-room` creates only a server-private Room.
- Local headless Chromium checked two isolated pre-admitted sessions at 390px/820px: no join route or shape-code UI, waiting, matching, assigned roles, both intro acknowledgements, collaboration, session refresh, no horizontal overflow or browser errors. Sessions were inserted through the internal test seam before opening each page; this **does not** validate a usable guest admission flow, real iPhone/iPad devices, or hosted Supabase.
- **Unmet:** decide how already-authorized guest sessions are provisioned and delivered to both devices without shape codes, invite links, or public matchmaking. Also unresolved: host authorization, retention/reservation/cleanup, match length and Play again disconnect timeout/help path, real-device acceptance, hosted Supabase migration/permissions, and multi-instance socket fanout. Subsequent phase triggers and object/media authorization belong to Features 03-08. Do not deploy or use with children.
