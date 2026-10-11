"""Local speech-to-text for hold-to-talk clips (demo step D2, docs/features/06-transcription.md).

Whisper runs on this machine, so audio never leaves it. The model is loaded once: the demo loads it
at startup so the first round's speech is not lost to the download.
"""

import os
import threading

WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "small.en")

_model = None
_lock = threading.Lock()


def _load():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        _model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    return _model


def load_model() -> None:
    """Download (first time only) and load the model now instead of during the first round."""
    with _lock:
        _load()


def transcribe_file(path: str) -> str:
    """Text of one clip (iOS sends audio/mp4, Chrome audio/webm; PyAV decodes both)."""
    with _lock:  # One clip at a time: the demo has two players and a laptop CPU.
        segments, _info = _load().transcribe(path, language="en", beam_size=1, vad_filter=True)
        return " ".join(segment.text.strip() for segment in segments).strip()
