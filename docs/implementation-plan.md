# Implementation plan

Status: **all features not started**. This organizes future work; it does not authorize starting the app, provisioning services, or running parallel agents automatically.

## Build order and dependencies

| ID | Deliverable | Integration dependencies | Status |
| --- | --- | --- | --- |
| [01](features/01-foundation.md) | Workspace, runnable shells, canonical contracts, fixtures, test commands | None | Implemented |
| [02](features/02-rooms-and-rounds.md) | Guest sessions, Room admission/pairing, authoritative phases | 01 | Implemented for demo - passcode admission, 3-round matches; see brief |
| [03](features/03-drawing.md) | Finger canvas and read-only live relay | 01; 02 for authorized relay | Not started |
| [04](features/04-object-viewer.md) | Private object/reference access and 3D viewer | 01; 02 for role/phase gates | Not started |
| [05](features/05-live-voice.md) | Two-device independent hold-to-talk | 01 + 02; real devices/provider account | Not started |
| [06](features/06-transcription.md) | Separate attributed live transcription | 05; approved demo AI access | Not started |
| [07](features/07-feedback.md) | Speech/image evidence and separate role feedback | 03 + 06; rubric decision for stars | Not started |
| [08](features/08-round-integration.md) | Complete human Round, Reveal, reward, role swap | 02-07; match length and disconnect timeout decisions | Not started |
| [09](features/09-demo-hardening.md) | Recovery, Safari/device acceptance, controlled deployment | 08; host/retention/deployment decisions | Not started |
| [10](features/10-bot-partner.md) | Odd-player partner supporting both roles | Accepted real-pair demo through 09 | Not started / later |

**Sequential path:** 01 -> 02 -> 03 -> 04 -> 05 -> 06 -> 07 -> 08 -> 09. Feature 10 follows later.

Do not wait until integration to test the riskiest path: after 02, prove real two-device voice in 05 before investing heavily in AI or polished full-round UI. Known device/network/SDK problems should change the next task, not remain hidden behind mock success.

## Parallel lanes

After 01 freezes relevant contracts:

- **Room/authority lane:** 02 owns sessions, admission, phases, role projections, and coordinated migrations.
- **Canvas lane:** isolated 03 UI/stroke model can proceed against sanitized fixtures while 02 is built. Authorized relay integrates only after 02 is available.
- **Object lane:** isolated 04 viewer/reference fallback can proceed with synthetic assets. Private delivery integrates after 02.
- **Media lane:** 05 integrates after 02. It may proceed alongside canvas/object work if nobody races to change shared socket schemas/app wiring.
- **Analysis lane:** 06 follows real media; 07's pure evidence/rule tests and panel rendering may use fixtures before its final real-service integration.
- **Integration lane:** 08 connects accepted modules. It is a deliberate owner, not several people rewriting the application shell concurrently.

Parallel isolated work is not permission to bypass a dependency or call an integration complete. Use the feature briefs' planned source areas. No CRDT, extra state bus, or multi-service architecture is needed just to work in parallel.

## Shared-file ownership

| Shared area | Coordination rule |
| --- | --- |
| `docs/api.md`, canonical schemas, exports/generated types | One contract owner; all consumers review breaking changes before merge |
| Database migrations/data constraints | One migration owner; other features propose additions and test affected flows |
| Package manifests/lockfiles and environment setup | Foundation/integration owner; avoid simultaneous dependency edits |
| Frontend bootstrap/routes and backend registration/startup | Integration owner; feature lanes expose modules rather than rewiring the whole app |
| Product/lifecycle rules | Update owning docs when user resolves a decision; do not invent lane-specific behavior |
| Feature status | Owner records evidence; plan summary must agree |

No named humans/agents are assigned yet. The current request creates a work structure, not a swarm.

## Milestones

1. **Runnable base:** 01; honest commands and typed fixtures exist.
2. **Authorized live conversation:** 02 + 05 on actual devices, without AI in the audio path.
3. **Visible collaboration:** 03 + 04 integrated; Speaker retains 3D and sees live canvas while Drawer stays secret-blind.
4. **End-to-end human round:** 06-08; two feedback panels, neutral failures, exploration, and swapped roles.
5. **Controlled demo ready:** 09 with recorded checks/known limitations, adults/synthetic data only unless child gates separately pass.
6. **Odd-player completeness:** 10 without secret shortcuts.

## How to start a task

Give the contributor the feature brief, `AGENTS.md`, and its referenced docs. Example:

> Implement feature 03 only. Use the agreed contracts and existing foundation. Work in the drawing areas and tests; coordinate contract/migration changes. Do not implement voice, object selection, AI, or full-round wiring. Report unmet dependencies.

If a dependency is absent, choose either its implementation first or explicitly authorize isolated fixture-backed work. Do not create fake backend/provider behavior and imply the feature is integrated.

## Definition of done

- Scope implemented without unrelated features.
- Contract/authorization/failure tests pass; required end-user/actual-device checks recorded.
- No leaked secrets, provider credentials, stale states, or falsely claimed test coverage.
- Relevant specs, real commands, feature status, and plan summary updated.
- Demonstration/review completed for the agreed slice; remaining release gates explicit.

All checkboxes in feature briefs start unchecked. Mark blocked/partial honestly, and do not move automatically to the next feature just because one task was approved.
