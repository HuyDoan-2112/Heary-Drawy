# 06 - Transcription

Status: **planned for the demo (step D2); not started**
Dependencies: [05](05-live-voice.md)

## Demo version

Speech becomes text so the AI can judge what the Speaker said in [07](07-feedback.md). No live streaming and no external speech service: audio never leaves the laptop.

- **Capture:** while a player holds the talk button, the browser also records the same mic stream with `MediaRecorder` (iOS Safari produces `audio/mp4`). On release it uploads the clip with the round ID to a new endpoint, e.g. `POST /api/v1/rounds/{round_id}/clips`. Partner audio still goes peer-to-peer and is never delayed by this.
- **Authorize:** only a player in that round, only during collaboration; clips over ~60 s or ~2 MB are rejected.
- **Transcribe:** the API runs open-source Whisper locally (`faster-whisper`, an English model such as `small.en`, loaded once at startup) in a background thread. It decodes the clip itself, so no system ffmpeg is needed.
- **Store:** one row per clip - round, player, role, start time, text, and status (`pending`, `done`, `failed`). Delete the audio as soon as it is transcribed; keep only the text.
- Both players can hold at once; each clip is attributed to its own player, so overlap is fine.

## Demo checks

- [ ] A held phrase on the iPad and on the iPhone each produces correct text attributed to the right player and role.
- [ ] Partner audio is unaffected while clips upload and transcribe.
- [ ] A failed or empty clip is marked `failed` and does not block the round.
- [ ] No audio files remain on disk after transcription.

## Later (deferred)

Live streaming transcription from server-side subscription to each voice track, word-level timing, and retention rules for real-child use ([privacy-and-safety.md](../privacy-and-safety.md)).
