# 07 - Separate role feedback and shared result

Status: **not started**  
Dependencies: [03](03-drawing.md) + [06](06-transcription.md) for integration; fixture-backed pure rules/UI can start after 01  
References: [product](../product.md), [data model](../data-model.md), [testing](../testing.md), [privacy](../privacy-and-safety.md)

## Deliverable

A finalized Round receives separate Speaker and Drawer recaps/tips and one shared team result, grounded in evidence rather than artistic grading.

## Scope and ownership

Own backend analysis/feedback modules, frontend feedback panels, fixture evaluation, and tests. Coordinate result/job migrations and result schemas with their owners.

- GPT-5.4 Mini snapshot text analysis for Speaker features with relevant quotes, attribution, paraphrase, and negation handling.
- Separate submitted-image analysis for visual features; validate schemas/feature IDs and uncertainty.
- Derive Drawer feedback from communicated visual features, not every private object detail or nondrawable function clue.
- Curated child-facing copy only. No model-generated unrestricted criticism or direct model star assignment.
- Versioned deterministic shared-star rules after user reviews the rubric; neutral/unscored path until then and on incomplete evidence.
- Durable Postgres jobs with bounded claims/retries/deadlines; atomically persist one Result and feedback transition.

## Parallel boundary

Pure rule tests and panel layouts can use explicit sanitized evidence fixtures. Do not label them real transcription/vision success. Real integration needs the frozen drawing and final attributed transcripts.

## Acceptance

- [ ] Speaker positives are supported by their own relevant evidence, not only Drawer keywords or negated/injected text.
- [ ] Drawer is not penalized for unspoken, nonvisual, uncertain, or artistically rough details.
- [ ] Each role gets its own gentle recap/tip; both stay a team, not ranked against each other.
- [ ] Malformed/unknown model fields are rejected or marked uncertain; no model commands execute.
- [ ] Retry/stale-job/provider-failure tests produce one immutable Result and a neutral fallback.
- [ ] Approved rubric version/model configuration is recorded; exact adult metrics remain separately protected.
- [ ] Adult/synthetic rough-drawing/speech evaluation includes uncertain/ambiguous examples.

Evidence: none yet.
