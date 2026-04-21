"""Video extraction service — orchestrates transcription and product extraction.

Coordinates the full pipeline: saving the uploaded video to a temp file,
running Whisper transcription, sending the transcript to Claude for
structured extraction, and cleaning up the temp file.
"""

import json
import logging
import os
import tempfile

from fastapi import UploadFile

from apps.api.core.config import Settings
from apps.api.domain.product import ExtractionResult
from apps.api.infrastructure.claude_client import extract_products
from apps.api.infrastructure.whisper_client import transcribe_audio

logger = logging.getLogger(__name__)


async def extract_products_from_video(
    file: UploadFile,
    settings: Settings,
) -> ExtractionResult:
    """Run the full extraction pipeline on an uploaded video file.

    Saves the upload to a temp file, transcribes with Whisper, extracts
    products with Claude, and returns structured results.  The raw
    transcript is logged for traceability but excluded from the response.

    Raises:
        TranscriptionError: Whisper model or audio decoding failure.
        ProductExtractionError: Claude API or response parsing failure.
    """
    suffix = os.path.splitext(file.filename or "video.mp4")[1] or ".mp4"

    logger.info(
        "Extraction request received: filename=%s, content_type=%s, size=%s",
        file.filename,
        file.content_type,
        file.size,
    )

    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = tmp.name
            contents = await file.read()
            tmp.write(contents)

        logger.info("Transcribing video: %s (%d bytes)", file.filename, len(contents))
        transcript = transcribe_audio(tmp_path, model_name=settings.whisper_model)
        logger.info("Transcript length: %d chars", len(transcript))

        if not transcript:
            logger.info("Empty transcript — returning zero products")
            result = ExtractionResult(products=[])
            logger.info(
                "Extraction response: %s",
                json.dumps(result.model_dump(), default=str),
            )
            return result

        logger.info("Extracting products from transcript")
        products = extract_products(
            transcript=transcript,
            api_key=settings.anthropic_api_key,
            model=settings.claude_model,
            max_tokens=settings.claude_max_tokens,
        )
        logger.info("Extracted %d products", len(products))

        result = ExtractionResult(products=products)
        logger.info(
            "Extraction response: %s",
            json.dumps(result.model_dump(), default=str),
        )
        return result

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
