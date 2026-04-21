"""Video extraction route — HTTP endpoint for the product extraction pipeline.

Accepts a video file upload, validates it, and delegates to the extraction
service.  Maps domain-specific exceptions to appropriate HTTP status codes.
"""

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from apps.api.core.config import Settings, get_settings
from apps.api.core.exceptions import ProductExtractionError, TranscriptionError
from apps.api.domain.product import ExtractionResponse
from apps.api.services.video_extraction import extract_products_from_video

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/videos", tags=["videos"])

ALLOWED_CONTENT_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/x-msvideo",
    "video/webm",
    "video/x-matroska",
}


@router.post("/extract-products", response_model=ExtractionResponse)
async def extract_products_endpoint(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
) -> ExtractionResponse:
    """Accept a video upload and return structured product information.

    Validates content type, file size, and API key configuration before
    running the Whisper + Claude extraction pipeline.
    """
    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported media type: {file.content_type}. Expected a video file.",
        )

    if file.size and file.size > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_upload_bytes} bytes.",
        )

    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=503,
            detail="Anthropic API key is not configured.",
        )

    try:
        result = await extract_products_from_video(file, settings)
    except TranscriptionError as exc:
        logger.error("Transcription failed: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ProductExtractionError as exc:
        logger.error("Product extraction failed: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error during extraction")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ExtractionResponse(success=True, data=result)
