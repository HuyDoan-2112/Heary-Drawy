# Heary Drawy contributor and agent guide

## Read first

1. `README.md` for actual implementation status.
2. `CONTEXT.md` for vocabulary.
3. `docs/product.md` for confirmed behavior and unresolved decisions.
4. `docs/architecture.md` and `docs/api.md` for responsibility and interface boundaries.
5. `docs/implementation-plan.md` and the relevant `docs/features/NN-*.md` brief for the requested task.

These current docs override superseded mechanics in `docs/research/` and the historical technical HTML explainer. Research is evidence/background, not a backlog or current specification. Technology recommendations are not proof of implementation or provider eligibility.

## Scope discipline

- The current goal is the two-device demo in `docs/implementation-plan.md`. Do not build deferred features for it. Do not invent working commands or claim providers/devices were tested.
- A request to organize docs or revise a diagram is not permission to implement the app.
- When implementation is requested, work on the named feature or agreed vertical slice. Do not automatically continue into the next feature, deploy, commit, or push.
- Read that feature's dependencies and acceptance checks before editing. Resolve a blocking product question explicitly; do not quietly replace it with a new rule.
- Keep changes small and independently reviewable. At handoff report changed files, tests actually run, unmet checks, and the next dependency.

## Parallel work

- One owner coordinates shared API/schema changes, migrations, dependencies/lockfiles, and app entry-point wiring. Other lanes propose changes rather than racing to edit them.
- Freeze the relevant contract before parallel work; use clearly labeled fixtures for unavailable integrations. Fixtures do not establish real integration success.
- Do not overwrite another contributor's work. Inspect the worktree before and after the task.
- Never spawn a large agent swarm without explaining the tradeoffs and obtaining explicit approval.

## Non-negotiable behavior

- Web-first, English, touch-first, iPad and iPhone; roles swap, so both devices support drawing and speaking.
- Nickname joining, no child email/Google/password requirement; a nickname is not authentication. Use a scoped guest session behind the UI.
- Speaker keeps the private 3D reference and sees a read-only live canvas. Drawer alone edits and cannot receive secret object data/assets before Reveal.
- Both children hold to talk during collaboration; no always-open mic, video, or device-screen sharing. AI is outside partner audio delivery.
- Separate end-of-round Speaker and Drawer feedback; shared team result, no artistic grading or competitive child rankings.
- Discovery Reward every round even when AI or scoring is unavailable. Continue must have a usable fallback.
- Private room pairing only. Grown-up controls require separate authorization, not a special nickname.

## Engineering standards

- Server-authoritative authorization and transitions. Enforce nickname uniqueness and final-result idempotency transactionally.
- Preserve separate participant/round/hold identities for overlapping speech and late events.
- Never include secret catalogs, provider keys, service credentials, raw child speech, or host credentials in client bundles or logs.
- Treat model input as untrusted data; validate outputs. Never let a model directly execute commands or freely grade/criticize a child.
- Prefer simple, maintainable modules within the proposed runtime. Do not add queues, frameworks, microservices, or policy layers without a demonstrated need.
- Reproduce bugs through the closest available end-user E2E path first. Add regression tests, and fix visible UI/lint/test issues you encounter.
- Do not hide failing tests or mark device acceptance complete based on mocks. Keep status in the feature brief and implementation plan consistent.
- Use only adults/synthetic data until `docs/privacy-and-safety.md` gates are satisfied.
- Do not manually edit generated files or CHANGELOG files. Regenerate artifacts/types from their source.
- Use plain hyphens, not em dashes. Do not add agent co-authors to commits.

## Documentation updates

Update the owning specification with behavior/contract changes and link to it elsewhere instead of repeating its rules. `CONTEXT.md` is a glossary, not a technical spec. If implemented behavior differs from the draft, document the resolved contract and tests in the same change.
