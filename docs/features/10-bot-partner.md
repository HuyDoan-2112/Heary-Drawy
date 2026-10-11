# 10 - Odd-player Bot Partner

Status: **not started / later**  
Dependencies: accepted real-pair demo through [09](09-demo-hardening.md)  
References: [product](../product.md), [architecture](../architecture.md), [privacy](../privacy-and-safety.md)

## Deliverable

An odd admitted participant can complete Rounds with a Bot Partner acting as either Speaker or Drawer, then swap roles normally.

## Scope and ownership

Own backend bots module, curated bot assets, renderer/plan schemas, and secret-isolation tests. Coordinate pairing/media/drawing adapters and lifecycle contracts.

- Bot Speaker uses curated prerecorded descriptions/answers for the initial object pack, under authorized media phases. It can retain the reference and observe the child's drawing, like a human Speaker.
- Bot Drawer receives a fresh, secret-free context with permitted spoken dialogue only. Extract a bounded primitive drawing plan with GPT-5.4 Mini; render deterministically.
- Bot Drawer may know its own strokes, but not object IDs/rubric/reference/model URLs or prior Speaker-role context.
- Keep privileged feedback analysis separate from bot drawing inputs.
- Use only supported shapes/colors/parts/relative positions; restrict the initial pack to what the actual renderer supports. No hidden-answer canned image or model-code execution.
- Bound bot behavior/latency and provide neutral fallback; do not penalize the child for bot limitations.

## Out of scope

General-purpose conversational agents, unrestricted generated speech, perfect artistic drawings, extra image-generation infrastructure, or automatic replacement of a disconnected human mid-round.

## Acceptance

- [ ] Odd-player pairing works privately without changing existing human Pairs.
- [ ] Both bot roles complete rounds, reveal/explore, and swap normally.
- [ ] Secret-free input traces/tests prove Bot Drawer never sees the answer/rubric/assets/history.
- [ ] Bot drawings derive from permitted clues, including incomplete/incorrect clues, not hidden answers.
- [ ] Invalid/malicious drawing plans are bounded and rejected; no commands/code execute.
- [ ] Clarification/failure copy and limitations are honest, gentle, and tested.

Evidence: none yet.
