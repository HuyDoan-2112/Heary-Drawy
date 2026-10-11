# Heary Drawy

A cooperative communication-practice game for children aged 5+: one teammate describes a private 3D object while the other draws it. They talk live using hold-to-talk buttons, and the Speaker sees the drawing develop. Each round ends with role-specific feedback and shared 3D exploration.

**Current state: Feature 01 foundation and a local Feature 02 Postgres-backed guest-room slice are implemented. Already-admitted guests can be matched within a server-private Room, see live presence, acknowledge role intro, and receive server-pushed state. There is no child-facing Room join flow. Other screens are fixture previews; real gameplay is not integrated. No hosted deployment, drawing relay, voice, object delivery, AI feedback, or real-device validation exists yet.** The initial demo is an HTTPS website for one iPad and one iPhone, tested with adults/synthetic data first.

## Start here

- [Product and confirmed gameplay](docs/product.md)
- [Architecture and proposed stack](docs/architecture.md)
- [API and WebSocket contracts](docs/api.md)
- [Implementation plan and parallel work](docs/implementation-plan.md)
- [Documentation index](docs/README.md)
- [Domain glossary](CONTEXT.md)

## Repository layout

```text
README.md                     Project entry point and honest implementation status
AGENTS.md                     Shared coding-agent and contributor guidance
CLAUDE.md                     Claude entry point importing shared guidance
CONTEXT.md                    Product vocabulary
apps/web/                     React + TypeScript + Vite shell
services/api/                 FastAPI shell and canonical Pydantic contracts
contracts/                    Exported JSON Schema and sanitized fixtures
scripts/                      Contract generation checks
docs/
   README.md                  Documentation map and sources of truth
   product.md                 What the game must do
   architecture.md            How responsibilities are separated
   api.md                     Shared client/server contract draft
   data-model.md              Persistence, constraints, ownership
   round-lifecycle.md         States, transitions, and recovery
   testing.md                 Acceptance tests and real-device gates
   privacy-and-safety.md      Data and child-use release gates
   implementation-plan.md     Sequence, dependencies, parallel lanes
   features/                  One bounded implementation brief per feature
   research/                  Earlier research, not current build instructions
.lavish/                      Reviewable HTML explainers
.archify/                     Architecture diagram specifications and receipts
```

## Local setup and commands

Prerequisites used for Feature 01:

- Node.js `v24.21.0`
- npm `11.19.0`
- uv `0.13.0` for Python dependency management
- Python `3.12` for the local `pgserver` dev fixture, selected by `services/api/.python-version` (the API also supports Python 3.13 with an external Postgres instance)

Install JavaScript dependencies:

```bash
npm install
```

Generate contract artifacts after changing `services/api/app/contracts/schemas.py`:

```bash
npm run generate:contracts
```

Run the web fixture shell:

```bash
npm run dev:web
```

For a **local, adult/synthetic-only** demo, run `npm run dev:api:local -- --room-hours 4` in another terminal; it prints a Room passcode. Open the web app on two devices or tabs, enter the passcode on each (Grown-up setup), pick characters, and play. Voice needs HTTPS (or localhost) for microphone access and both devices on the same network. This starts a local Postgres server and applies SQL migrations. It does **not** admit guests or provide a child-facing join method. `http://localhost:5173/join` remains a character-selection fixture unless a guest session has already been securely provisioned; the admission/bootstrap contract is still unresolved. Do not expose the local server to a network or use it with children. Other fixture routes remain `/mic`, `/mode`, `/team`, `/play/speaker`, `/play/drawer` (each opens with its role intro), `/checking`, `/result`, `/grownups`, and `/grownups/parents` (sample data only). Screens reproduce the approved designs in `artifact/` with a fluid layout that runs from the iPhone design on phones to the iPad design on tablets.

For an existing Postgres instance, set `DATABASE_URL` in your shell, run `npm run db:migrate` for local/test databases (or use Supabase CLI for deployed migrations), run `npm run db:provision-room -- --ttl-hours 24` to create a server-private Room, then `npm run dev:api`. That operator command does **not** admit children or generate a Room join code/link. The default API provisions no Room. Set `ALLOWED_ORIGINS` to the comma-separated exact web origins before accepting WebSockets from other origins. Host HTTP/UI controls remain disabled pending a separate authorization decision.

Run checks:

```bash
npm run check:contracts
npm run typecheck:web
npm run lint:web
npm run lint:api
npm run test:web
npm run test:api
npm run test
```

Build the web shell:

```bash
npm run build:web
```

The contract source of truth is `services/api/app/contracts/schemas.py`. `contracts/schema.json` and `apps/web/src/generated/contracts.ts` are generated artifacts; regenerate them instead of hand-editing them.

## Work one feature at a time

Start with [01 - Foundation](docs/features/01-foundation.md). Each feature brief defines its scope, dependencies, owned areas, interfaces, and acceptance checks. Work may run in parallel where the plan explicitly permits it; integrating a feature is not permission to implement the entire backlog.

For example:

> Implement feature 03 using its brief and the shared contracts. Keep the work limited to the drawing component and its tests. Do not implement voice or AI.

Read [AGENTS.md](AGENTS.md) before changing the repository. No claims of educational effectiveness, child-data approval, or clinical validity are supported by the current work.
