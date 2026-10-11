# Heary Drawy

A cooperative communication-practice game for children aged 5+: one teammate describes a private 3D object while the other draws it. They talk live using hold-to-talk buttons, and the Speaker sees the drawing develop. Each round ends with role-specific feedback and shared 3D exploration.

**Current state: a minimal playable round runs locally - grown-up passcode join, pairing, random roles, a secret 2D picture only the Speaker sees, live drawing relay, peer-to-peer hold-to-talk voice, local Whisper transcription of each held clip, DeepSeek feedback with 1-3 team stars at reveal (neutral result without a key), and 3 rounds with role swap. `npm run demo` serves it over HTTPS on the LAN. Not yet checked on a real iPad/iPhone. No hosted deployment or 3D objects.** The current goal is a two-device iPad + iPhone demo on one Wi-Fi network, with adults only; see the [implementation plan](docs/implementation-plan.md).

## Start here

- [Product and confirmed gameplay](docs/product.md)
- [Architecture and proposed stack](docs/architecture.md)
- [API and WebSocket contracts](docs/api.md)
- [Implementation plan (demo-first)](docs/implementation-plan.md)
- [Documentation index](docs/README.md)
- [Domain glossary](CONTEXT.md)

## Run the two-device demo

For one iPad and one iPhone on the same Wi-Fi as the laptop. Adults only.

1. **Once per machine:** `npm install`. For AI feedback, put `DEEPSEEK_API_KEY=<your key>` in a file named `.env` next to `package.json` (git ignores it; see `.env.example`). Without a key every round shows the friendly neutral result.
2. **Start:** `npm run demo`. It prints the address to open (`https://<laptop IP>:5173`) and the Room passcode. The first round's first clip also downloads the Whisper speech model (about 250 MB, once). Ctrl+C stops everything.
3. **Windows with WSL only:** the devices reach Windows, not WSL. The demo prints two lines to paste into PowerShell opened with "Run as administrator". Paste them again if WSL's address changes (for example after a restart).
4. **On each device:** open the printed address in Safari. The certificate is self-signed, so tap **Show Details**, then **visit this website**, and confirm. A grown-up enters the passcode, then the child picks a character (name optional), taps **Turn on mic**, and the grown-up taps **Allow**.
5. **Play:** both tap **Let's play!** The Speaker sees the picture and holds **Hold to talk** to describe it without saying its name; the Drawer draws and can hold to ask questions. The Drawer taps **Done**; Drawy checks for a few seconds, then both see the picture, the drawing, their own feedback, and the team stars. **Play again** (both tap it) swaps roles; a match is 3 rounds. **Done** leaves.

Known limits: both devices must be on the same Wi-Fi (no TURN relay); if a device drops, restart the round; clips are transcribed on the laptop and only text, the drawing, and the picture's checklist go to DeepSeek; the local database lives in `~/.cache/heary-drawy/local-db` (delete it to start fresh); no round timer.

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

For development on one machine, run `npm run dev:api:local -- --room-hours 4` (a local Postgres, migrations, and a Room passcode) and `npm run dev:web`, then open `http://localhost:5173/join` in two browser windows (one private) and enter the passcode in each. For real devices use `npm run demo` above. Do not use it with children. Other fixture routes remain `/mic`, `/mode`, `/team`, `/play/speaker`, `/play/drawer` (each opens with its role intro), `/checking`, `/result`, `/grownups`, and `/grownups/parents` (sample data only). Screens reproduce the approved designs in `artifact/` with a fluid layout that runs from the iPhone design on phones to the iPad design on tablets.

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
