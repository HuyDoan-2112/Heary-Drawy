# 08 - Human round integration, Reveal, and role swap

Status: **not started**  
Dependencies: integrated [02](02-rooms-and-rounds.md)-[07](07-feedback.md)  
References: [product](../product.md), [lifecycle](../round-lifecycle.md), [API](../api.md), [testing](../testing.md)

## Deliverable

One complete human Round works across the two devices, followed by exploration and another Round with swapped roles.

## Scope and ownership

Own frontend app/round wiring, backend transition integration, and full-round E2E tests. Feature modules remain owned by their lanes; coordinate fixes rather than rewriting them.

- Implement short role intro with no separate private preparation period; review/resolve match length and Play again disconnect timeout before acceptance.
- Wire Speaker's persistent private 3D reference plus read-only live canvas; Drawer edit view remains secret-blind.
- Enable both hold-to-talk controls during collaboration, including clarification and overlapping speech.
- Freeze acknowledged drawing, stop grants, finalize transcripts, show separate feedback and shared result.
- Reveal object/reference beside drawing; offer 3D Discovery Reward and usable fallback regardless of AI status.
- Advance under reviewed acknowledgement/disconnect policy, swap roles, and deliver new projections without secret preloads.

## Out of scope

New social features, real-child pilot, bot shortcuts, cosmetic redesign of accepted modules, and optional native packaging.

## Acceptance

- [ ] Two adults complete a real HTTPS/device round and then play swapped roles.
- [ ] Speaker keeps object access while correcting/clarifying; live canvas stays read-only for them.
- [ ] Drawer never receives secret data before Reveal; third-session requests fail.
- [ ] Drawing/mic multitouch works; lost connection/canceled grants/late strokes do not corrupt submission.
- [ ] Both role panels show evidence-based gentle feedback; incomplete AI still allows exploration and Play again.
- [ ] Play again and retries advance once; late prior-Round events cannot affect the new Round.
- [ ] Actual flow matches reviewed role intro, Play again, timing, and fallback rules in current docs.

## Handoff

Record a complete walkthrough, real services/device versions, remaining recovery/privacy gates, and any fixture-only portions. Passing a mocked browser flow is not this feature's real-device completion.

Evidence: none yet.
