# Heary Drawy

A cooperative communication-practice game for children aged 5+: one teammate describes a private 3D object while the other draws it. They talk live using hold-to-talk buttons, and the Speaker sees the drawing develop. Each round ends with role-specific feedback and shared 3D exploration.

**Current state: Feature 01 foundation is implemented. A minimal React/Vite fixture UI covers UI-01 through UI-09 screens, alongside a FastAPI health endpoint, canonical contract schemas, generated frontend types, and sanitized fixtures. No playable room, drawing relay, voice, object delivery, AI feedback, deployment, provisioned infrastructure, or real-device validation exists yet.** The initial demo is an HTTPS website for one iPad and one iPhone, tested with adults/synthetic data first.

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
- Python `3.13.16`, provisioned by uv from `services/api/pyproject.toml`

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

Open `http://localhost:5173/join` to start the fixture flow. Implemented fixture routes are `/join`, `/mic`, `/mode`, `/team`, `/intro`, `/play/speaker`, and `/play/drawer`.

Run the API shell:

```bash
npm run dev:api
# then open http://127.0.0.1:8000/health
```

Run checks:

```bash
npm run check:contracts
npm run typecheck:web
npm run lint:web
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
