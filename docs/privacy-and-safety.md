# Privacy, safety, and release gates

Status: design requirements and unresolved eligibility checks, not a compliance certification or legal advice.

## Demo versus actual-child use

The controlled demo uses adults and synthetic examples. A product intended for children aged 5+ cannot treat nicknames, private Rooms, school facilitation, or provider training opt-outs as sufficient child-data protection.

Before actual child participation, resolve applicable jurisdiction, notices/consent or valid school authorization, provider age/endpoint eligibility, data retention/deletion, and reporting with qualified guidance.

OpenAI's under-18 guidance states that processing under-13 personal data requires implementing Zero Data Retention. ZDR requires approval and has endpoint-specific limitations; `store: false` and "not used for training" are not equivalent. Verify the exact transcription/image/text endpoints and current safety/model recommendations before child use.

COPPA's personal-information definition includes an audio file containing a child's voice. Nicknames, drawings, transcripts, identifiers, and evidence can also be personal data depending on their context. An anonymous guest token does not remove these obligations.

## Data flow inventory

| Processor / location | Proposed data |
| --- | --- |
| Player browser | Nickname/session credential, local stroke draft, permitted object assets, partner playback |
| LiveKit Cloud | Pair-scoped participant identity/metadata and live microphone transport |
| FastAPI deployment | Guest authorization, role state, ephemeral audio frames, attributed transcripts, bounded jobs |
| Supabase Postgres/Storage | Sessions/state, drawings/reference/GLB assets, approved transcript/evidence/result retention |
| OpenAI eligible endpoints | Permitted audio for STT; final text and drawing image for feature extraction |
| Hosting/logging/backups | Must be explicitly configured not to collect raw voice, credentials, prompts, or signed asset URLs |

No permanent raw audio recording/replay is in the baseline. In-memory queues and streaming providers still process voice and require disclosure/control. Define transcript, local draft, result, session, object-cache, backup, and deletion policies before deploying the demo; values are not decided yet.

## Authorization and information barriers

- Nickname identifies the player in the UI; private server-issued possession credentials authenticate the session.
- Keep host authorization separate. Do not expose host actions before the mechanism is chosen; a special nickname or shared shape code is not a host credential.
- Authorize every game/media/asset request against Room membership, Pair, role, and phase. Limit both tokens and published track sources.
- Never send secret data to Drawer before Reveal, including model/rubric IDs, asset keys, metadata, or future-round preloads.
- Signed URLs are bearer capabilities: keep them short-lived, private, and out of logs. Previously downloaded authorized bytes cannot be retrospectively revoked.
- Pair isolation must hold for voice and live strokes, not only UI visibility.
- Bot Drawer input must remain secret-free even if the same model/provider also performs privileged feature analysis.

## Live-media safety limitation

Both use hold-to-talk during collaboration. Speech reaches the teammate before analysis, so AI cannot prevent object naming or inappropriate speech from being heard. Provide a clear adult-supported pause/end path; no claim of preventive moderation.

Revocation and cancellation must be effective on the provider, not merely reflected by a button. A backend crash can leave an existing cloud publication grant active. Cooperative heartbeat-based client cutoff is a controlled-demo limitation, not a malicious-client guarantee. Broader child deployment needs demonstrated server-independent cutoff or a reviewed watchdog/relay strategy.

No always-open microphone, free-text chat, public matchmaking, camera/video, device-screen sharing, or AR.

## Model behavior and fairness

- Models return bounded feature evidence, not arbitrary stars, diagnoses, or unrestricted criticism.
- Treat transcripts/images as untrusted data and validate schema, feature IDs, quotes, negation, and finite bounds.
- Separate participants and speech/drawing rubrics. Do not credit Speaker for words spoken only by Drawer or penalize Drawer for an uncommunicated feature.
- Prefer uncertain/incomplete evidence to a fabricated negative judgment. Do not present a model confidence number as a calibrated probability.
- Use curated child-facing copy; no raw model text is shown/spoken to children.
- Because Speaker sees and helps correct the drawing, feedback concerns supported collaboration, not independent ability measurement.

## Release checklist

- [ ] Actual-child consent/authorization and notices reviewed.
- [ ] All processors/subprocessors and applicable age restrictions verified.
- [ ] Required ZDR/endpoint eligibility approved and configured where applicable.
- [ ] Current model safety recommendations and actual task evaluations reviewed.
- [ ] Retention/deletion policy includes browser drafts, logs, backups, and providers.
- [ ] Role/Pair/media boundaries tested, including backend failure/cutoff.
- [ ] Separate host control/reporting access reviewed and tested.
- [ ] Real-device acceptance in [testing.md](testing.md) complete.
- [ ] Broader/public-access abuse and resource controls revisited; deferred custom rate limits are not a production exemption.

Primary policy sources checked during research on 2026-10-10; recheck at implementation/release:

- [OpenAI under-18 guidance](https://developers.openai.com/api/docs/guides/safety-checks/under-18-api-guidance).
- [OpenAI data controls](https://developers.openai.com/api/docs/guides/your-data).
- [16 CFR 312.2](https://www.law.cornell.edu/cfr/text/16/312.2).

Native/App Store requirements are deferred, not waived; consult [historical platform research](research/ios-platform-research.md) before revisiting packaging.
