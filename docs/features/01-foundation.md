# 01 - Foundation and contracts

Status: **implemented for the foundation slice**
Dependencies: none
References: [architecture](../architecture.md), [API](../api.md), [testing](../testing.md)

## Deliverable

A reproducible frontend/backend workspace with honest run/test commands and one agreed typed contract boundary. No playable round or provider integration yet.

## Scope and ownership

- Create the planned React/TypeScript/Vite and FastAPI source areas, minimal web shell, and liveness endpoint.
- Pin actual supported dependency versions; choose/document package managers and environment setup. Add secret-safe example configuration, never real credentials.
- Establish canonical HTTP/socket schemas and sanitized fixtures for Speaker, Drawer, Reveal, drawing updates, and command errors.
- Export types through a standard schema generator; generated output is not hand-edited.
- Add only the testing/lint/typecheck tools actually used, and document verified commands in README.

Own workspace/configuration, contracts/exports, initial app wiring, and base tests. These shared areas need a single coordinator when parallel work begins.

## Out of scope

Real rooms, media, AI, cloud provisioning, public secret assets, polished round screens, and the entire backlog. Fixture data is not implemented provider behavior.

## Acceptance

- [x] Fresh setup starts the web shell and backend health check using documented commands.
- [x] Lint/typecheck/test smoke checks run and pass.
- [x] Generated frontend types match canonical schemas.
- [x] Speaker/Drawer fixtures validate; Drawer-before-Reveal fixtures contain no object identity/assets/rubric.
- [x] No secrets or complete object catalog are bundled/logged.
- [x] Repository status and commands reflect what exists, not future expectations.

## Handoff

List exact commands, dependency/runtime versions, fixture locations, contract change process, and remaining external prerequisites. Unblock isolated canvas/object lanes; do not start them automatically.

Evidence:

- Dependency/runtime versions: Node.js `v24.21.0`, npm `11.19.0`, uv `0.13.0`, Python `3.13.16` from `services/api/pyproject.toml`.
- Commands verified: `npm run generate:contracts`, `npm run check:contracts`, `npm run typecheck:web`, `npm run lint:web`, `npm run test:web`, `npm run test:api`, `npm run test`, `npm run build:web`.
- Runtime checks verified: FastAPI health endpoint returned `{ "status": "ok" }`; Vite web shell served the Heary Drawy page locally.
- Fixture locations: `contracts/fixtures/*.json`.
- Contract source of truth: `services/api/app/contracts/schemas.py`; generated outputs are `contracts/schema.json` and `apps/web/src/generated/contracts.ts`.
- Remaining external prerequisites: real room authority, persistence, media provider, object storage/assets, AI/provider access, deployment, and real-device validation are still unimplemented.
