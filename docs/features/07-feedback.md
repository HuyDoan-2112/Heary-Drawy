# 07 - AI feedback and shared result

Status: **built for the demo (step D2); real DeepSeek reply not yet checked**

Built as described below in `services/api/app/game/feedback.py`: Done moves the round to `finalizing` (the Checking screen), `check_round` in `main.py` waits for clips, renders the PNG, makes one `deepseek-flash` call (image + JSON output, confirmed on api-docs.deepseek.com 2026-10-11) and publishes once. `DEEPSEEK_API_KEY` comes from the git-ignored `.env` via `npm run demo`. A round left in checking by a restart is finished at startup.
Dependencies: [03](03-drawing.md), [04](04-object-viewer.md), [06](06-transcription.md)

## Demo version

At Done, DeepSeek looks at what the Speaker said and what the Drawer drew, and both players get their own gentle feedback plus one shared 1-3 star team result.

- **Checklist:** each catalog picture gets 3-5 visual features in `services/api/app/game/objects.py`, e.g. Apple: red, round body, stem on top, leaf.
- **Flow:** Done moves the round to `checking` (the existing Checking screen). A background task waits up to ~15 s for that round's pending transcriptions, then makes one DeepSeek call. The result is saved once and pushed to both players, who move on to Reveal.
- **Drawing image:** the server renders the stored strokes to a PNG (Pillow), so the analyzed image is exactly what the server accepted.
- **DeepSeek call:** DeepSeek's OpenAI-compatible Chat Completions API via the `openai` Python SDK with DeepSeek's base URL, one request with the PNG, the picture's name and checklist, and the round's transcripts labeled Speaker/Drawer. The model must accept image input: third-party reports (September 2026) say `deepseek-flash` (V4.1 Flash) does and the Pro model does not - confirm the model ID and image limits in DeepSeek's official docs before building. Keep the model ID in one config value. Use JSON output mode and validate the reply with a Pydantic model on the server, since the schema is not enforced by the API. The reply gives, for each checklist feature, whether the Speaker described it and whether the drawing shows it, plus 1-2 short lines for each role. Lines are told to be warm, simple, for ages 5+, never about drawing skill, and never comparing the two players.
- **Stars:** computed by the server, not chosen by the model: 3 stars if most features were both described and drawn, 2 if some, otherwise 1. Never 0.
- **Fallback:** no `DEEPSEEK_API_KEY`, a timeout (~20 s), an API error, or output that fails validation all give the existing neutral result. Reveal and Play again always work.
- **Privacy:** only the drawing PNG, the picture name/checklist, and transcript text go to DeepSeek - no audio, names, or device info. Adults only.

## Demo checks

- [ ] A round where the Speaker clearly describes the picture gets matching Speaker and Drawer feedback and 2-3 stars on both devices.
- [ ] A round with no talking still gets kind feedback and at least 1 star.
- [ ] With the API key removed, the round shows the neutral result and continues normally.
- [ ] Feedback text fits the Reveal screen on the iPhone without clipping.

## Later (deferred)

A curated tip library instead of model-written lines, a reviewed long-term star rubric, an evaluation set of adult/synthetic rounds, and the protected grown-ups detail view.
