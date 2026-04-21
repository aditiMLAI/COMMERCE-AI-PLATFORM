"""Whisper-based audio transcription client.

Wraps the openai-whisper library to transcribe audio from video files.
Models are cached in memory after first load to avoid repeated I/O on
subsequent requests.
"""

import logging

import whisper

from apps.api.core.exceptions import TranscriptionError

logger = logging.getLogger(__name__)

VALID_MODELS = {"tiny", "base", "small", "medium", "large"}

_model_cache: dict[str, whisper.Whisper] = {}


def get_whisper_model(model_name: str = "base") -> whisper.Whisper:
    """Load a Whisper model by name, returning a cached instance if available.

    Raises TranscriptionError for unrecognised model names.
    """
    if model_name not in VALID_MODELS:
        raise TranscriptionError(
            f"Invalid Whisper model name: '{model_name}'. "
            f"Valid options: {', '.join(sorted(VALID_MODELS))}"
        )
    if model_name not in _model_cache:
        logger.info("Loading Whisper model: %s", model_name)
        try:
            _model_cache[model_name] = whisper.load_model(model_name)
        except Exception as exc:
            raise TranscriptionError(
                f"Failed to load Whisper model '{model_name}': {exc}"
            ) from exc
    return _model_cache[model_name]


def transcribe_audio(file_path: str, model_name: str = "base") -> str:
    """Transcribe audio from a video or audio file at the given path.

    Raises TranscriptionError if the model is invalid, the file has no
    audio stream, or ffmpeg fails to decode the media.
    """
    model = get_whisper_model(model_name)
    try:
        result = model.transcribe(file_path)
    except RuntimeError as exc:
        msg = str(exc).lower()
        if "no such file" in msg or "ffmpeg" in msg:
            raise TranscriptionError(
                f"Failed to decode audio (is ffmpeg installed?): {exc}"
            ) from exc
        raise TranscriptionError(f"Transcription failed: {exc}") from exc
    except Exception as exc:
        raise TranscriptionError(f"Transcription failed: {exc}") from exc

    text = result.get("text", "").strip()
    if not text:
        logger.warning("Whisper returned empty transcript for %s", file_path)
    return text
