"""AI feedback for a finished round (demo step D2, docs/features/07-feedback.md).

One DeepSeek call per round with the drawing (rendered here from the stored strokes), the picture's
checklist, and the round's transcripts. The model only reports what it sees and writes short lines;
the server validates the reply and decides the stars. Any failure means the neutral result.
"""

import base64
import json
import logging
import os
from collections.abc import Iterable, Mapping
from io import BytesIO
from typing import Any

from openai import OpenAI, OpenAIError
from PIL import Image, ImageDraw
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger("heary_drawy.feedback")

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
# deepseek-flash accepts images and JSON output (api-docs.deepseek.com, checked 2026-10-11).
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-flash")
TIMEOUT_SECONDS = 20

# The shared drawing space used by every device (apps/web/src/app/ui/drawing.ts).
DRAWING_WIDTH = 760
DRAWING_HEIGHT = 680
LINE_MAX = 90  # Characters; keeps each line inside Drawy's bubble on the iPhone.


class FeatureCheck(BaseModel):
    feature: str
    described: bool
    drawn: bool


class AiReply(BaseModel):
    features: list[FeatureCheck]
    speaker_lines: list[str] = Field(min_length=1, max_length=2)
    drawer_lines: list[str] = Field(min_length=1, max_length=2)


def render_png(strokes: Iterable[Mapping[str, Any]]) -> bytes:
    """The drawing exactly as the server stored it, on a white 760 x 680 canvas."""
    image = Image.new("RGB", (DRAWING_WIDTH, DRAWING_HEIGHT), "white")
    pen = ImageDraw.Draw(image)
    for stroke in strokes:
        width = max(1, round(float(stroke.get("width", 14))))
        points = [(p["x"] * DRAWING_WIDTH, p["y"] * DRAWING_HEIGHT) for p in stroke.get("points", [])]
        if len(points) > 1:
            pen.line(points, fill=stroke["color"], width=width, joint="curve")
        for x, y in points[:1] + points[-1:]:
            pen.ellipse((x - width / 2, y - width / 2, x + width / 2, y + width / 2), fill=stroke["color"])
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def stars_for(checks: list[FeatureCheck], features: tuple[str, ...]) -> int:
    """3 if most features were both described and drawn, 2 if some, otherwise 1. Never 0."""
    both = {check.feature for check in checks if check.described and check.drawn} & set(features)
    if features and len(both) * 2 > len(features):
        return 3
    return 2 if both else 1


PROMPT = """You help with a cooperative game for children aged 5 and up.
One child (the Speaker) saw a secret picture and described it without saying its name.
The other child (the Drawer) listened and drew it. Look at the attached drawing.

Secret picture: {name}
Checklist of visual features: {features}

What the children said, in order:
{transcript}

Reply in json only, exactly in this shape:
{{"features": [{{"feature": "<checklist item>", "described": true, "drawn": false}}],
  "speaker_lines": ["<one warm line for the Speaker>", "<optional gentle question>"],
  "drawer_lines": ["<one warm line for the Drawer>", "<optional gentle question>"]}}

Rules:
- One entry in "features" for every checklist item, using the checklist wording.
- "described": the Speaker's words clearly gave this feature. "drawn": the drawing shows it.
- Lines are for young children: warm, simple words, at most 12 words each.
- Praise something specific that went well. A question may point at one missing feature without giving the answer.
- Never judge drawing skill or neatness, never compare the two children, never mention the picture's name.
- Never comment on how a child's voice or speech sounds (no clarity, loudness, or pronunciation); talk about what they said.
"""


def ask_deepseek(name: str, features: tuple[str, ...], transcript: list[tuple[str, str]], png: bytes) -> dict[str, Any] | None:
    """Return {"stars", "speaker_lines", "drawer_lines"}, or None for the neutral result."""
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key or not features:
        return None
    spoken = "\n".join(f"{role.capitalize()}: {text}" for role, text in transcript) or "(nobody said anything)"
    prompt = PROMPT.format(name=name, features=", ".join(features), transcript=spoken)
    image_url = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
    try:
        client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL, timeout=TIMEOUT_SECONDS, max_retries=0)
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": image_url}}],
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=800,
        )
        reply = AiReply.model_validate(json.loads(response.choices[0].message.content or ""))
    except (ValidationError, ValueError) as exc:
        logger.info("feedback reply rejected: %s", type(exc).__name__)
        return None
    except OpenAIError as exc:  # Network, auth, rate limit, timeout: the round still continues.
        logger.info("feedback call failed: %s", type(exc).__name__)
        return None
    speaker_lines = [line.strip()[:LINE_MAX] for line in reply.speaker_lines if line.strip()]
    drawer_lines = [line.strip()[:LINE_MAX] for line in reply.drawer_lines if line.strip()]
    if not speaker_lines or not drawer_lines:
        return None
    return {"stars": stars_for(reply.features, features), "speaker_lines": speaker_lines, "drawer_lines": drawer_lines}
