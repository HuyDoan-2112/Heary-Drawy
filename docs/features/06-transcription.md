# 06 - Attributed streaming transcription

Status: **not started**  
Dependencies: [05](05-live-voice.md); eligible adult-demo AI access  
References: [architecture](../architecture.md), [API](../api.md), [data model](../data-model.md), [privacy](../privacy-and-safety.md)

## Deliverable

Authorized hold audio becomes final/incomplete text attributed to the correct participant, role, Round, and hold, without changing or delaying partner audio.

## Scope and ownership

Own backend transcription module and the media-subscriber adapter/tests; coordinate media lifecycle/startup changes with 05.

- Subscribe in the Python RTC runtime to the same authorized tracks; separate streams/sessions by participant, not mixed pair audio.
- Produce documented 24 kHz mono PCM with bounded queues, per-hold authorization windows, and tested tail draining.
- Use `gpt-live-transcribe`, English hints, manual hold boundaries/commit, and documented `turn_detection: null`. Recheck exact provider contract and model access first.
- Track provider item ID with participant/role/Round/hold/epoch; final events may arrive out of order.
- Bound finalization and retries. Missing tails/events/restart buffers yield incomplete evidence, not invented success.
- Apply approved ephemeral-buffer/transcript retention and secret-safe logging.

## Out of scope

Another browser microphone recorder, permanent audio/replay, showing live transcripts to children, mid-round AI coaching, feature scoring, or actual-child use before eligibility gates.

## Acceptance

- [ ] Actual permitted audio produces final text without blocking partner playback.
- [ ] Both concurrent speakers stay separately attributed, including after role swaps.
- [ ] Late/out-of-order provider events map correctly and cannot attach to a new Round/hold.
- [ ] Final words are preserved under the tested release/tail policy.
- [ ] Overflow, missing final events, provider disconnect, and backend restart yield bounded incomplete states.
- [ ] Hidden answer/checklist is not seeded into STT hints.
- [ ] No raw audio/transcript/credentials leak into logs or unauthorized projections.

## Handoff

Provide immutable final/incomplete transcript records to 07, with timing/model metadata and explicit evidence limitations. Model alias/snapshot availability and child-data eligibility remain separate checks.

Evidence: none yet.
