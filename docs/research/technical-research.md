# Heary Drawy: technical research

> Historical research snapshot, not the current implementation spec. Gameplay and stack proposals below may be superseded. Read [current product](../product.md), [architecture](../architecture.md), and the [implementation plan](../implementation-plan.md) before building.

Research checked: 2026-10-10  
Status: web-first, live push-to-talk demo confirmed for iPad and iPhone; provider, framework, backend, and scoring remain proposed  
Related reports: [Market research](market-research.md), [iPad and iPhone platform research](ios-platform-research.md)  
Visual companion: [Historical technical explainer](../../.lavish/technical-research.html)

## Executive finding

The proposed game uses live push-to-talk audio over WebRTC, synchronized round state, a drawing surface, and AI-assisted feature extraction. This replaces the earlier record-upload-play delivery proposal. The hard problems are protecting child data, preserving the hidden-information game, and giving fair feedback when speech recognition or vision is uncertain.

**The demo is web-first, served over HTTPS in Safari on iPad and iPhone.** Home Screen installation is optional; native iOS packaging and App Store distribution are deferred. Framework, backend, and scoring choices are not yet decided. At the initial audit, the repository contained only its README; research documents have since been added, but this report describes a candidate system, not existing application behavior. No real AI calls or end-to-end gameplay were tested during this research.

## 1. Required experience

### Confirmed demo scope

The initial demo uses two controlled player devices and one pair. The available demo devices are one iPad and one iPhone; exact models and OS versions are not yet known. The user has selected a website for the demo. See the iOS platform report for Safari requirements and future native options. Custom application-level rate limiting is deferred for this demo, not a prerequisite for the first playable loop. This is not permission to deploy an unrestricted public service: before broader or public access, revisit join abuse and resource-exhaustion controls. Supabase and AI providers may still impose their own limits; deferring our rate limiter does not disable theirs.

Keep role authorization, private media, the hidden-object boundary, and server-side turn limits even in the demo.


- Children aged 5+ play in English, with minimal reading required.
- Two teammates share feedback and a score.
- Initial roles are random; the roles swap after every round.
- The Describer sees a hidden object and describes it without naming it.
- Voice is live push-to-talk: hold the microphone button and the partner hears speech immediately; release ends the speaking turn. No always-open or unrestricted voice call.
- Feature icons and a prewritten hint can prompt at most 1-2 extra description turns; AI coaching follows each completed turn without delaying partner audio.
- The Drawer hears the Describer live, may ask one live voice question, and receives a live voice answer.
- The Drawer draws and presses Done.
- Results show 1-3 stars, the reference object beside the drawing, a feature checklist, and one gentle tip.
- After every round's drawing submission and grading, reveal an interactive 3D version of the secret object as a playful reward. Children can explore it before choosing Continue and swapping roles.
- Exact figures belong only in an authenticated grown-ups area.
- Children join private rooms using a three-shape code; pairing happens only inside that room.
- An odd player receives a bot partner that supports both roles.
- No public matchmaking, free chat, webcam, or video.

The product is communication practice, not a diagnostic tool or a replacement for a speech therapist.

## 2. Release gate: children's data and provider eligibility

### Verified policy and regulatory facts

OpenAI's current under-18 guidance states:

> You should not use OpenAI services to process any personal data of children under 13 or the applicable age of digital consent without first implementing zero data retention in our API.

Source: [OpenAI under-18 guidance](https://developers.openai.com/api/docs/guides/safety-checks/under-18-api-guidance).

OpenAI's data-control documentation says Zero Data Retention (ZDR) requires approval and has endpoint-specific eligibility and limitations. API data not being used for training by default is not the same as zero retention. Setting a request's `store` flag to false is not equivalent to organization-level ZDR.

Source: [OpenAI data controls](https://developers.openai.com/api/docs/guides/your-data).

The US COPPA definition includes an audio file containing a child's voice as personal information. An anonymous avatar does not remove that fact.

Source: [16 CFR § 312.2, definitions](https://www.law.cornell.edu/cfr/text/16/312.2).

### Recommendation

Use adult volunteers and synthetic examples for the hackathon prototype. Before actual child use:

1. Identify applicable jurisdictions and consent requirements with qualified guidance.
2. Verify the chosen providers' eligibility for this exact age group and data flow.
3. Obtain and configure required retention controls, including approved ZDR where applicable.
4. Define notices, consent or applicable school authorization, access, retention, and deletion.
5. Test deletion in application storage, logs, backups, and provider-side systems according to their documented behavior.
6. Provide age-appropriate AI disclosure and an adult reporting/escalation route.

Private rooms and adult facilitation help with supervision but do not, by themselves, establish legal compliance. This is technical risk identification, not legal advice.

## 3. How the system would work

### Two separate paths

**What the teammate hears:**

`Microphone -> authorized WebRTC audio connection -> partner hears speech as it happens`

Keep the pair's connection ready where practical, but transmit speech only during an authorized push-to-talk turn. Connection readiness is not permission to transmit continuously.

**What the AI assists with:**

`Authorized turn audio -> streaming transcription or disclosed temporary turn buffer -> completed-turn transcript -> checklist evidence -> bounded coaching`

`Drawing export -> visual checklist evidence -> deterministic feedback rules`

The teammate hears the original live voice, not synthesized transcript audio. AI latency or transcription errors must not delay or alter that voice path. Permanent voice recordings and replay are not required by the live delivery design; any temporary buffering or optional retention must be disclosed and covered by the privacy policy.

Live audio reaches the partner before AI checks it. AI cannot pre-screen naming violations or inappropriate speech before delivery. Provide adult supervision, mute/report controls, and a calm pause path rather than claiming preventive moderation.

### Candidate stack

| Layer | Candidate | Purpose | Decision status |
| --- | --- | --- | --- |
| Interface | Responsive web UI; React + TypeScript, optionally Next.js | Role-specific, touch-first Safari screens on iPad and iPhone | Web platform confirmed; framework proposed |
| Drawing | Browser canvas with stroke history and Pointer Events | Finger drawing, undo, clear, image export | Proposed implementation |
| Live voice | WebRTC; direct peer connection or a service such as LiveKit | Immediate original voice during permitted turns | Live push-to-talk confirmed; media provider undecided |
| Data | Supabase Postgres | Rooms, pairings, rounds, authorized state | Proposed |
| Media storage | Supabase private Storage | Drawing exports and only explicitly permitted retained audio | Proposed; permanent voice storage not required |
| Updates | Supabase Realtime | Notify devices of authorized state changes | Proposed |
| Rules | Server-authoritative commands and state | Validate turns and prevent cheating/races | Recommended invariant |
| AI | Live or buffered-turn transcription, structured text extraction, vision | Completed-turn feature evidence and drawing checks | Capabilities documented; target accuracy unvalidated |
| Feedback | Deterministic rules and curated messages | Stable stars, checklist, gentle tips | Policy undecided |

Use one mechanism for game-state updates. WebRTC media transport is a separate responsibility: Supabase Realtime or Socket.IO notifications are not substitutes for the voice path. WebRTC also needs signaling and ICE connectivity, including TURN relay support when direct connectivity fails. Do not add duplicate game-state mechanisms without a concrete need. AI model names should be selected after checking current access, privacy eligibility, latency, cost, and representative accuracy.

## 4. Round flow and synchronization

### Proposed logical states

`roles -> live description + partner listening -> turn-end coaching / extra live description -> optional live question -> live answer -> finish drawing -> analysis -> results -> 3D reveal / exploration -> swapped roles`

Recommended interaction, not yet validated: let the Drawer sketch while listening instead of waiting for a recording. Keep Done gated until the required speaking/question states have completed. The Describer must not see the partner's drawing before the reveal unless a later design explicitly changes the barrier rule.

The 3D exploration stage happens after every round's feedback, before Continue and the role swap. Per-round timing is confirmed; the exact viewer and controls remain proposed.

The question branch is optional; the Drawer can proceed without asking. The Describer’s additional turns and the single question must be bounded on the server, not just disabled in the interface.

### Server responsibilities

- Randomize pairs only among admitted players in one room.
- Randomize the first round's roles and swap them on subsequent rounds.
- Authorize every command against session identity, room, pair, role, and state.
- Issue the secret object only to the Describer.
- Authorize media-room access and speaking permissions, enforce turn duration, and revoke transmission when a turn ends. A disabled UI button alone is not a security boundary.
- Enforce the maximum extra descriptions and one question.
- Prevent duplicate Done actions and duplicate score updates.
- Ignore stale AI results from an earlier round or revision.
- Save authoritative state so reconnecting clients can reload it.
- Pause or offer adult assistance when a partner disconnects.

Each mutating command should carry a round identifier and expected state/version; duplicate requests should be handled idempotently. Realtime notifications are an update mechanism, not the sole source of truth.

## 5. Browser audio: feasible, but device testing is essential

### Documented capabilities and constraints

- `getUserMedia` requests microphone permission and requires a secure context, normally HTTPS.
- WebRTC supports real-time audio transport. Signaling exchanges connection information; STUN/TURN help establish connectivity or relay media. Do not assume that a shared Wi-Fi network guarantees a direct connection.
- Browser autoplay policies can require a deliberate tap to unlock incoming audio.
- Safari backgrounding, screen lock, phone calls, Bluetooth changes, and network loss need actual device testing.
- Browser `SpeechRecognition` is not a guaranteed cross-browser or privacy-neutral fallback.

Sources: [WebRTC API](https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API), [WebRTC peer connections and signaling](https://webrtc.org/getting-started/peer-connections), [microphone access](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia), [autoplay](https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Autoplay).

### Implementation recommendations

- Request audio only, never camera access.
- Show connection readiness and an unmistakable speaking indicator; transmit only during an authorized turn.
- Mute transmission reliably on release, pointer cancellation, focus loss, backgrounding, role change, disconnect, or maximum turn duration.
- Distinguish microphone permission/capture, track publication, and actual transmission. A connection staying ready or a browser microphone indicator does not mean the teammate should receive speech.
- Provide an accessible toggle-to-talk alternative if holding is difficult, still bounded by the same turn rules.
- Stop microphone tracks and disconnect media when leaving the room or when capture is no longer necessary.
- Keep any AI buffering separate from teammate delivery. If temporary recording is chosen, check Safari formats and disclose it; it is not a prerequisite for hearing each other live.
- Test echo and feedback on nearby devices, consider headphones, and request supported echo-cancellation constraints without treating them as a guarantee.
- Pause after connection loss; do not pretend the partner heard missing speech. Restore authorization before resuming.

The goal is conversational interaction, not guaranteed zero latency. No latency target, maximum turn duration, or media provider is approved or measured.

## 6. AI feature analysis: evidence, not a verdict

### Curated object records

Each object should have a reference image, allowed feature IDs, acceptable paraphrases, forbidden naming terms, and prewritten hints. Separate the spoken rubric from the visual rubric.

Example:

| Feature | Useful in speech? | Checkable in drawing? | Notes |
| --- | --- | --- | --- |
| Red | Yes | Usually | Accept rough coloring; avoid requiring full fills |
| Round | Yes | Usually | Allow imperfect shapes |
| Stem on top | Yes | Usually | Accept phrases such as "a little stick on top" |
| You can eat it | Yes | Not directly | Useful clue, not a required visual feature |
| Small | Yes, in context | Only with a reference | Absolute canvas size is not real-world size |

The pictured reference must actually contain the checklist features. Do not require a leaf on an object image that has none.

### Speech pipeline

1. Transcribe the permitted spoken turn, using a live stream or disclosed temporary buffer, without supplying the hidden object as a recognition hint. Wait for a final turn transcript before selecting a coach hint; partial transcripts can change.
2. Extract feature evidence from the transcript using a fixed schema and allowed IDs.
3. Require a transcript quotation for each positive speech match.
4. Respect negation: "not red" is not evidence for red.
5. Accept developmentally appropriate paraphrases, rather than literal-word matching only.
6. Treat transcript content as untrusted data, not instructions to the model.
7. Validate the response and select any hint from prewritten content.

Use three statuses: **mentioned**, **not detected**, and **uncertain**. "Not detected" is not proof that the child did not say it.

Do not turn a model-generated confidence number into a calibrated probability. Schema-valid output can still be factually wrong.

Sources for transcription capability: [OpenAI realtime transcription](https://developers.openai.com/api/docs/guides/realtime-transcription) and [file transcription](https://developers.openai.com/api/docs/guides/speech-to-text) if temporary turn buffering is chosen. Provider eligibility and retention controls must be checked for the actual endpoint.

### Drawing pipeline

Export the canvas and ask a vision-capable model to check only the permitted visual features. Do not ask it to grade beauty, handwriting, realism, or resemblance to a polished reference image.

Use **visible**, **not detected**, and **uncertain**. Rough drawings, ambiguous colors, and simple spatial relationships require forgiving examples and testing. A prompt saying "ignore artistic quality" cannot guarantee independence from drawing ability.

OpenAI documents accuracy and spatial-reasoning limitations: [vision guide](https://developers.openai.com/api/docs/guides/images-vision).

### What the results do not prove

A red drawing does not prove the child heard "red"; they may have guessed from prior knowledge. A missed stem does not prove poor listening; drawing skill or AI recognition may be responsible. Report observed evidence, not a causal diagnosis of communication ability.

## 7. Feedback and scoring

### Preserve the child-facing experience

- 1-3 stars and one shared team result.
- Reference object next to the child's drawing.
- A clear, icon-led feature recap with spoken labels available.
- One prewritten, gentle tip.
- An interactive 3D object reveal after every round's feedback, separate from the scoring evidence.
- No visible exact percentages or public ranking.

The earlier suggested 50/40/10 weights and thresholds were arbitrary. They are not approved or validated educational measures.

### Recommended policy constraints

- Do not award points merely because the question button was used.
- Do not automatically penalize suspected object naming; show a gentle reminder and handle uncertain transcription.
- Do not lower the score because an AI service failed or a response was uncertain.
- Do not label a child as a poor speaker, listener, or artist.
- Do not generate unrestricted criticism or medical conclusions.
- Let adults inspect the underlying evidence, subject to consent and minimization rules.

### Adult figures

Start with transparent counts, for example "2 of 3 selected visual clues detected." If percentages are shown, label the denominator and uncertainty. These are game metrics, not validated communication-ability scores or probabilities.

The exact aggregation, star policy, and uncertain-result presentation remain open decisions. Store finalized feedback with its rubric/version so retries do not silently change a result.

## 8. Private rooms, authentication, and hidden information

### A shape code is a join aid, not a password

If repetition is allowed, six available shapes yield `6^3 = 216` codes; eight yield `8^3 = 512`. This space is small enough to guess. The numbers are illustrations; the shape alphabet is undecided.

For the controlled iPad-and-iPhone demo, keep the three-shape interaction, known participants, per-device session identity, and server-enforced room, pair, role, and turn access. Do not require a custom rate limiter for this slice.

Before classroom-scale or public deployment, revisit:

- Active-code uniqueness and room expiry.
- Rate-limited joining and resource-abuse controls.
- Adult approval or another controlled admission mechanism.
- Room locking after admission.

These are future deployment considerations, not all requirements for the controlled two-device demo.

### Protect the secret structurally

Do not deliver the secret object to both clients and hide it with CSS. Store secret data separately from shared round state, and send it only to the authorized Describer. Likewise, feature coaching must not reveal the answer to the Drawer before results.

Role-specific API responses, database policies, realtime subscriptions, and media access all need the same authorization boundary. An adult-only view is not protected merely by hiding its navigation link.

### Supabase considerations

Anonymous sign-in can avoid child email/password entry, but the anonymous user still has a session identity. Supabase's anonymous API key is not a substitute for a per-player authenticated session.

The documentation notes an IP-based anonymous-sign-in limit of 30 requests per hour, configurable in the dashboard. A class behind one shared network needs load testing and abuse controls that do not lock out legitimate participants.

Sources: [anonymous sign-ins](https://supabase.com/docs/guides/auth/auth-anonymous), [row-level security](https://supabase.com/docs/guides/database/postgres/row-level-security).

Drawings and any explicitly permitted retained recordings should be in private buckets. Live media sessions need pair-scoped authorization and speaking permissions as well; a classroom room code must not put every child in one audible voice channel. Use authorized downloads or short-lived signed URLs. A signed URL is a bearer link during its lifetime; do not publish it in logs or shared feeds. Server/service credentials must never reach the browser.

Source: [private storage](https://supabase.com/docs/guides/storage/buckets/fundamentals).

## 9. Bot partner: preserve the same game rules

### When the bot describes

The bot may know the hidden object. Use curated, prerecorded or carefully generated descriptions and bounded answers. The child hears audio and draws. Keep naming restrictions and age-appropriate content.

### When the bot draws

The bot must receive only the child's descriptions and clarification answer, not the secret object ID, reference image, or feature checklist. Otherwise it can draw the answer without understanding the child.

A simple symbolic renderer or text-to-drawing pipeline is a candidate, not a tested capability. Its limits must not become unfair penalties for the child. A canned drawing can be used only as a clearly labeled demonstration stub.

### Role swaps

The bot must support both roles because the child changes roles every round. A bot that only describes does not fulfill the complete requirement.

## 10. Failure behavior and operational safety

| Failure | Recommended behavior |
| --- | --- |
| Microphone denied | Explain how an adult can enable it; do not leave the child waiting |
| Silent or unintelligible turn | Offer a calm retry, not a negative score |
| Live connection interrupted | Pause, mute transmission, reconnect, and allow a repeat; do not claim missing speech was heard |
| AI timeout or invalid output | Preserve authorized round state and permitted evidence; show a neutral retry or unscored result |
| Low-confidence feature evidence | Mark uncertainty rather than inventing a failure |
| Partner disconnects | Pause and restore the current round after reconnect |
| Duplicate Done / stale AI result | Apply one authorized transition; reject obsolete results |
| Guessed room code | In the demo, use controlled access and known participants; broader deployment needs admission and abuse controls |
| Inappropriate voice or drawing content | Provide adult intervention and reporting; bounded voice is not inherently safe |

Minimize collection, use ephemeral avatar names, and define retention before gathering data. Avoid raw audio, transcripts, and signed media links in application logs. Do not retain everything merely because an adult dashboard could display it later.

## 11. Prototype validation plan

### Direct first slice

1. Two devices, one room, one pair, one curated object.
2. Random roles and a secret visible only to the Describer.
3. Hold-to-talk sends original live audio immediately; release ends transmission. Verify this in both directions, before and after role swapping.
4. Feature extraction includes evidence and uncertainty.
5. Bounded coaching and additional descriptions work.
6. One voice question and one answer work.
7. Drawing submission, feature feedback, and gentle results work.
8. After every round's feedback, a 3D object is revealed only at the authorized post-grading stage; rotation and zoom work on both the demo iPad and iPhone.
9. Roles swap for the next round.

### Then test the requirements that make it a classroom game

- Three participants: one real pair and one bot partner, both bot roles exercised.
- Concurrent joining and pairing, including a shared-network classroom scenario.
- Refresh/reconnect at each significant state.
- Duplicate submissions, delayed AI responses, expired media URLs, and denied permissions.
- An unauthorized third participant trying to access the secret, another pair's recording, or the adult dashboard.
- Safari on both devices, touch cancellation, incoming-audio unlock, screen lock, backgrounding, speaker/headphone routing, echo, and room noise.
- Real network connectivity and TURN fallback; measure end-to-end voice delay instead of promising instant delivery.

### AI evaluation

Use adult recordings and synthetic examples first. Include negation, paraphrases, silence, background noise, ambiguous sketches, missing parts, and rough-but-valid drawings. Compare detection with human-reviewed labels and record failure patterns. No accuracy or latency target has yet been agreed or measured.

Real-child testing requires the release gate in Section 2, representative consented data, and adult/educator oversight.

## 12. Open decisions and recommendation

Still undecided:

- AI provider, exact models, and approved privacy configuration.
- Web framework, HTTPS hosting, backend, and optional Home Screen support; native packaging is deferred.
- WebRTC media/signaling provider, TURN deployment, AI streaming versus temporary buffering, turn limits, and voice-latency targets.
- Exact iPad / iPhone models and OS versions; a Mac is not required for the web demo.
- Shape alphabet and broader-deployment admission mechanism; custom rate limiting is deferred for the controlled two-device demo.
- Feature rubric, star thresholds, and uncertain-result treatment.
- 3D asset set, viewer, appearance, and controls; timing is confirmed after every round.
- Object set and progression.
- Bot drawing strategy.
- Adult access, permitted analytics, consent, retention, and deletion.

**Recommendation:** validate the two-device communication loop before building a broad dashboard or extra infrastructure. Preserve clarification, role swaps, and the hidden-information boundary. Resolve child-data eligibility before actual child recordings. Use the stack above as a candidate, not a commitment.

## 13. Interactive 3D reveal: a playful discovery reward

### A name for the idea

Call this an **interactive 3D object reveal** or a **discovery reward**. After every round, once the Drawer finishes and feedback is ready, children can explore a toy-like 3D version of the hidden object before choosing Continue and swapping roles. It is a celebration and exploration moment, not another assessment.

### Proposed interaction

- Drag to rotate the object.
- Use accessible buttons for zoom and reset; support touch gestures if tablets are added later.
- Keep the reference image, drawing, stars, and gentle tip available alongside it.
- Offer a clear Next / Continue control; exploration is optional and must not block role swapping.
- Make the reward available regardless of star count. Do not withhold it because the AI is uncertain or unavailable; a neutral result may still lead to the reveal.
- Avoid forced timers, flashing effects, or unnecessary automatic motion.

Per-round 3D exploration is confirmed by the user. The exact controls, appearance, and viewer remain proposed, not decided or implemented.

### Candidate implementation

Use curated GLB/glTF models associated with object IDs. A small set of manually prepared models is preferable to generating a new 3D object during each turn: it reduces latency, unpredictability, and asset-review risk.

The official [model-viewer project](https://modelviewer.dev/) is a candidate for a simple embeddable 3D viewer with camera controls. Three.js / React Three Fiber becomes a candidate if the design needs custom game effects or complex interaction. No viewer has been selected or tested for this product.

Keep model assets local to the deployment where practical. Do not enable AR or request camera access; the project's no-webcam/no-video requirement remains intact.

### Hidden-information and accessibility safeguards

Authorize the reveal after grading. Do not send the model ID, identifiable model URL, or reference object to the Drawer before the reveal stage. The pretty 3D model must not become a new visual standard used to judge the child's drawing.

Provide a static image fallback when WebGL or asset loading fails, keyboard-operable rotation/zoom/reset, an accessible label, and reduced-motion behavior. Validate asset licenses and ensure that the model's visible features match the object card.

The bot Drawer must never receive the secret 3D asset as an input to its drawing process.

## 14. iPad and iPhone application direction

The intended experience is touch-first and tablet-friendly. Both available devices must support both roles because roles swap each round. The iPhone cannot be permanently assigned to description without changing the game rules.

The detailed [iOS platform report](ios-platform-research.md) compares:

- Safari / Home Screen web app: no Mac or paid Apple membership needed for the demo.
- Capacitor: web interface in a signed native app, with local Xcode or cloud-build considerations.
- React Native + Expo Go: native preview on the available devices, without building our own signed binary.
- Our own native development/release build: provisioning, signing, and distribution requirements apply.

**Confirmed decision:** build the demo as a responsive website, served over HTTPS and tested in Safari on the available iPad and iPhone. Home Screen installation can be added if useful, but is not a demo requirement. Expo and Capacitor are future options, not current implementation tracks. No Mac, Apple signing, TestFlight, or App Store review is required for this web demo.

Apple's Kids Category and third-party AI data-sharing rules add distribution constraints beyond provider retention requirements. Do not assume ZDR alone permits sending children's voice to an external service in a Kids Category app.

## Sources and verification limits

Checked on 2026-10-10. Provider policies and capabilities can change; recheck before implementation and deployment.

- [OpenAI under-18 guidance](https://developers.openai.com/api/docs/guides/safety-checks/under-18-api-guidance).
- [OpenAI data controls and ZDR](https://developers.openai.com/api/docs/guides/your-data).
- [COPPA personal-information definitions, 16 CFR § 312.2](https://www.law.cornell.edu/cfr/text/16/312.2).
- [MDN microphone access](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia).
- [MDN WebRTC API](https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API).
- [WebRTC peer connections and signaling](https://webrtc.org/getting-started/peer-connections).
- [LiveKit track publishing](https://docs.livekit.io/home/client/tracks/publish/), a candidate transport service, not a selected provider.
- [OpenAI realtime transcription](https://developers.openai.com/api/docs/guides/realtime-transcription).
- [MDN MediaRecorder](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder).
- [MDN autoplay policies](https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Autoplay).
- [MDN SpeechRecognition](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition).
- [OpenAI recorded-file transcription](https://developers.openai.com/api/docs/guides/speech-to-text).
- [OpenAI image/vision capabilities and limitations](https://developers.openai.com/api/docs/guides/images-vision).
- [Supabase anonymous sign-ins](https://supabase.com/docs/guides/auth/auth-anonymous).
- [Supabase row-level security](https://supabase.com/docs/guides/database/postgres/row-level-security).
- [Supabase private storage](https://supabase.com/docs/guides/storage/buckets/fundamentals).
- [model-viewer official project and examples](https://modelviewer.dev/), a candidate for the post-grading 3D viewer.

This research verifies documentation and identifies design constraints. It does not verify model accuracy, legal compliance, production scalability, educational effectiveness, or working gameplay.
