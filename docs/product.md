# Product specification

Status: current agreed behavior, with open decisions listed separately. This replaces earlier describe-then-draw rules in the research reports. No gameplay has been implemented or tested.

## Purpose and demo scope

Heary Drawy is a cooperative communication-practice game for children aged 5+, not a diagnostic tool or a replacement for a speech therapist. The interface is English, touch-first, with large controls, icons, and minimal reading.

The initial demo is a responsive HTTPS website on one iPad and one iPhone. Both devices must support both roles. Use adults/synthetic examples until the [child-use gates](privacy-and-safety.md) are satisfied. Native iOS packaging, App Store distribution, and Home Screen installation are not prerequisites.

## Joining and teammates

- Teammates are matched only from admitted guests within an adult-managed private Room. There is no child-facing shape-code or invite-link join flow. How a device is admitted and receives its scoped guest session still needs a product decision.
- Show Normal mode as the active demo mode. Advanced mode may be visible with "Advanced pictures are coming soon!", but it must not change object selection or gameplay until a reviewed contract exists.
- No child email, Google/Gmail sign-in, password, or permanent account is required.
- Nicknames are unique within the Room, ignoring case and surrounding whitespace. A private guest session prevents name-based takeover and supports reconnect.
- Pair participants only within their admitted Room. No public matchmaking.
- Choose initial roles randomly and swap after every Round.
- An odd participant eventually gets a Bot Partner supporting both roles. Build the real human Pair first; bot support is a later feature, not silently dropped.

## Round experience

### 1. Role intro and live collaboration

Each Round starts with a short role intro, then moves directly into live collaboration. There is no separate private preparation period for the demo. The Speaker can inspect the secret 3D object during collaboration; the Drawer does not receive object data before Reveal.

- The Speaker keeps the object visible throughout drawing and can rotate/inspect it again to answer questions.
- The Speaker also sees the evolving drawing, read-only.
- The Drawer edits the canvas while listening and asking clarification questions.
- Both independently hold a button to talk; release stops transmission. No always-open microphone or strict alternating floor. Overlapping speech is possible and must remain separately attributable.
- Clarifications are conversational. The old one-question/one-answer and extra-description caps no longer apply.
- The Speaker describes without naming the object. AI cannot prevent a naming violation before live speech reaches the partner.
- Share drawing data, not either child's entire device screen.

### 3. Submission and role-specific feedback

Drawer chooses Done. Freeze a confirmed drawing revision, end microphone grants, finalize permitted audio/transcripts, and analyze the round.

- Speaker feedback: useful keywords/features communicated, clarity/clarification evidence, and one gentle curated suggestion.
- Drawer feedback: communicated visual features represented in the drawing, and one gentle curated suggestion. Do not penalize unspoken details, uncertain analysis, or artistic quality.
- Keep one shared team result, normally 1-3 stars when a reviewed scoring rubric is available. Exact thresholds are unresolved. Provider failure must not fabricate a poor score; neutral/unscored feedback is acceptable with friendly copy such as "Drawy had trouble checking this one, but you still finished the round together!" and "Let's look at the picture and try another one."
- The game observes supported collaboration because the Speaker guides the drawing; do not present feedback as an independent assessment of either child's ability.
- Exact figures/detailed metrics are restricted to a separately authorized grown-ups area. Separate feedback does not imply competitive individual scores.

### 4. Reveal, exploration, and next round

Show the reference beside the drawing, role-specific feature recaps, and gentle tips. Both may now explore the 3D object. Offer this Discovery Reward every round, regardless of stars or AI availability.

Play again advances to the next Round and swaps roles after both children acknowledge they are ready. If one child is ready first, show friendly waiting copy such as "Waiting for Kiwi to be ready..." and "Mango wants to play again!". Do not wait forever when a teammate disconnects; provide a grown-up/help fallback. Failed 3D loading must have an image fallback and must not strand the children.

## Information and safety boundaries

- Before Reveal, Drawer receives no secret object ID, name, rubric, image/model URL, model bytes, or identifying asset metadata. Do not preload or bundle the complete secret catalog.
- Speaker can see the canvas, but cannot edit it. Other Room participants cannot subscribe to the Pair's drawing or voice.
- Bot Drawer receives permitted spoken dialogue and no secret/checklist/reference/history from a prior Speaker role.
- No free-text chat, public matchmaking, webcam, video, screen sharing, or AR/camera requirement.
- Grown-up access requires separate authorization; a guest nickname never confers grown-up privileges.
- Keep authorization and bounded microphone holds even when custom application rate limiting is deferred for the controlled demo.

## Decisions still needed

| Decision | Blocks |
| --- | --- |
| Actual device models and OS versions | Credible Safari/device acceptance |
| Separate host-access mechanism | Adult room creation/controls and detailed metrics |
| Star rubric and evidence handling thresholds | Scored rather than neutral feedback |
| Match length and disconnect timeout for Play again waiting | Final role-swap interaction |
| Session/draft/transcript/result retention policy | Deployed demo cleanup and actual-child use |
| Provider access, model eligibility, asset licensing | Real AI/media/3D integration |

Discuss a decision when it blocks the chosen feature; do not require resolving the entire table before isolated work. API/state docs may suggest a baseline, but unresolved product rules must remain explicitly provisional.
