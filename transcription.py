from pathlib import Path
from shutil import which

import whisper


def check_ffmpeg() -> None:
    if not which("ffmpeg"):
        raise RuntimeError(
            "ffmpeg is not installed or not available in PATH. Install it first, e.g. on macOS: brew install ffmpeg"
        )


def transcribe_audio(audio_path: Path, model_name: str) -> str:
    model = whisper.load_model(model_name)
    result = model.transcribe(str(audio_path))
    text = (result or {}).get("text", "").strip()
    if not text:
        raise RuntimeError("Local Whisper transcription returned no text.")
    return text
