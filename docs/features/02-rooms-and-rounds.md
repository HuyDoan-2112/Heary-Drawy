# 02 - Guest rooms, pairing, and round authority

Status: **partial - local SQLite authority and join adapter; not deployable**
Dependencies: [01](01-foundation.md)
References: [product](../product.md), [API](../api.md), [data model](../data-model.md), [lifecycle](../round-lifecycle.md)

## Deliverable

Two admitted guest sessions in a private Room receive a persisted Pair, initial random roles, and correct role-filtered round state.

## Scope and ownership

Own backend sessions/game modules, Room UI, their tests, and coordinated schema migrations.

- Nickname/avatar join with transactional normalized-name uniqueness; private session token and resume/expiry behavior.
- Room admission, Pair isolation, persisted roles/round assignment, lifecycle transition guards, current-state reconnect.
- Authenticated socket bootstrap and explicit per-role projections. Never serialize the private Round record directly.
- Define session/room reservation behavior and cleanup with the reviewed retention policy.
- Protect host operations separately. Controlled demo Rooms may be provisioned server-side; host API/UI remains disabled until host authorization is chosen.

Role intro and Play again handlers may be tested with explicit provisional fixtures. Match length and disconnect timeout decisions are required before final interaction is accepted. Keep this visible rather than hardcoding them as product rules.

## Out of scope

Canvas rendering, real voice, 3D rendering, AI, bot implementation, and unrestricted public Room creation.

## Acceptance

- [ ] Concurrent `Sam`/`sam` joins yield one admitted name and one friendly conflict.
- [ ] Same name without the session token cannot take over; valid session refresh resumes roles.
- [ ] Pair creation/random assignment persists across reconnect/restart.
- [ ] Wrong-role/Room/Pair requests, guessed IDs, and expired sessions reveal no secrets.
- [ ] Drawer projections exclude object/rubric/asset metadata before Reveal.
- [ ] A nickname such as `Teacher` cannot access host actions/metrics.
- [ ] Duplicate/stale commands cannot reroll roles or repeat transitions.

## Handoff

Provide canonical auth/state adapters to the canvas, object, and media lanes; record unresolved host/timing choices. Coordinate migration and contract changes through the shared owner.

Evidence (local Python 3.13, FastAPI TestClient, SQLite temporary files):

- `services/api/tests/test_rooms_and_rounds.py`: concurrent normalized nickname conflict, session resume, two-player pair/role persistence across new app instances, wrong-room denial, Drawer secret omission, blocked host route, socket authentication/origin rejection, refresh after pairing, expiry checks, and two-person role-intro transition with idempotent/stale command rejection.
- `apps/web/src/app/App.test.tsx`: Room join, friendly conflict, session storage and explicit teammate/role refresh. The other screens remain isolated fixture previews; no real gameplay navigation is implied. `services/api/app/local_demo.py` and `npm run dev:api:fixture` provision a known-code Room **only on localhost for adult/synthetic manual checks**; the default app creates no Room.
- Local live HTTP smoke check: two independent guest joins, waiting state, paired role-filtered state. `npm run test` and `npm run build:web` pass locally. Browser E2E attempted but Chromium could not start because `libnspr4.so` is missing; no device/UI visual check is claimed.
- **Unmet:** Postgres migrations and transaction integration (no Postgres tooling/instance available), approved host provisioning and retention/reservation policy, true connection presence and live state push, object assignment/access, Play again and subsequent lifecycle transitions, production-grade frontend flow and real two-device acceptance. Match length and disconnect timeout remain unresolved. Do not deploy or use with children.
