# Documentation map

Status: demo-first. A minimal playable round runs locally; the goal is a two-device iPad + iPhone demo. See [implementation-plan.md](implementation-plan.md).

## Sources of truth

| Question | Read | Owns |
| --- | --- | --- |
| What are we building? | [product.md](product.md) | Confirmed gameplay, scope, unresolved product decisions |
| What do words mean? | [CONTEXT.md](../CONTEXT.md) | Domain glossary only |
| Which component does what? | [architecture.md](architecture.md) | Stack recommendations, module boundaries, deployment shape |
| What crosses client/server boundaries? | [api.md](api.md) | Draft endpoints, messages, projections, errors |
| What is stored and constrained? | [data-model.md](data-model.md) | Persistent records, uniqueness, idempotency, retention ownership |
| How does a round progress? | [round-lifecycle.md](round-lifecycle.md) | Transitions, permissions, timers, recovery |
| What should we build next? | [implementation-plan.md](implementation-plan.md) | Ordered features, dependencies, shared-file ownership, status |
| What proves it works? | [testing.md](testing.md) | Automated, E2E, and actual-device acceptance |
| How do approved screens become frontend logic? | [frontend-ui-implementation-spec.md](frontend-ui-implementation-spec.md) | UI screen behavior, fixture-first wiring, design-to-contract gaps |
| Can real children use it? | [privacy-and-safety.md](privacy-and-safety.md) | Provider eligibility, consent, data and media release gates |

## Feature briefs

Each brief defines a bounded deliverable. 01 and 02 (plus a minimal round slice) are implemented; 03-10 are **deferred** future work. The current work is demo steps D1-D4 in the implementation plan.

1. [Foundation and contracts](features/01-foundation.md)
2. [Guest rooms, pairing, and round authority](features/02-rooms-and-rounds.md)
3. [Drawing and live canvas](features/03-drawing.md)
4. [Secret picture (3D later)](features/04-object-viewer.md)
5. [Hold-to-talk voice](features/05-live-voice.md)
6. [Transcription](features/06-transcription.md)
7. [AI feedback and shared result](features/07-feedback.md)
8. [Round integration, reveal, and role swap](features/08-round-integration.md)
9. [Demo setup](features/09-demo-hardening.md)
10. [Bot partner (later)](features/10-bot-partner.md)

Read a brief together with its referenced contracts. Feature files describe execution scope and acceptance, not independent copies of the product rules.

## Working in parallel

[implementation-plan.md](implementation-plan.md) identifies safe lanes and shared-file ownership. Agreement on an API draft does not mean its backend is implemented. Clearly labeled fixtures can unblock isolated frontend work; the integrated feature still needs end-to-end acceptance.

## Research and visual artifacts

Earlier reports are preserved under [research/](research/README.md). They contain older gameplay/stack proposals and should not override current specs.

- [Current architecture diagram](../.archify/architecture-heary-drawy-20261010-114417/heary-drawy.html)
- [Historical technical explainer](../.lavish/technical-research.html)

## Status and change rules

- **Confirmed product behavior**: explicitly agreed user-facing requirements in `product.md`.
- **Proposed technical baseline**: recommendations in architecture/contracts, to verify while implementing.
- **Implemented**: code exists and the brief records concrete checks; documentation alone never qualifies.
- **Release-ready**: all applicable E2E/device/privacy gates pass with recorded evidence.

Update the document that owns a rule; link to it from other docs. Keep API, lifecycle, data constraints, and acceptance tests aligned. Mark unresolved matters explicitly, and do not silently adopt assumptions from historical research.
