"""Custom exception types for the Commerce AI Platform.

Provides domain-specific exceptions that allow the route layer to map
failures to appropriate HTTP status codes instead of generic 500 errors.
"""


class TranscriptionError(Exception):
    """Raised when audio transcription fails.

    Covers scenarios such as invalid Whisper model names, videos without
    an audio stream, corrupt media files, or missing ffmpeg dependency.
    """


class ProductExtractionError(Exception):
    """Raised when structured product extraction from a transcript fails.

    Covers scenarios such as Claude API errors, unparseable LLM output,
    or Pydantic validation failures on the extracted data.
    """
