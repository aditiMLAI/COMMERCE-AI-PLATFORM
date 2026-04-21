"""Tests for the video product extraction endpoint.

Covers the happy path, input validation, error propagation for specific
failure modes, and edge cases such as invalid model names, no-audio
videos, and missing product fields from Claude.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from apps.api.core.config import Settings, get_settings
from apps.api.core.exceptions import ProductExtractionError, TranscriptionError
from apps.api.domain.product import ExtractedProduct
from apps.api.main import app


def _test_settings(**overrides) -> Settings:
    """Build a Settings instance with test defaults, overridable per-test."""
    defaults = {
        "anthropic_api_key": "test-key",
        "whisper_model": "base",
        "max_upload_bytes": 100_000_000,
        "claude_model": "claude-sonnet-4-20250514",
        "claude_max_tokens": 4096,
    }
    defaults.update(overrides)
    return Settings(**defaults)


def _make_client(**settings_overrides) -> TestClient:
    """Create a TestClient with optional settings overrides."""
    app.dependency_overrides[get_settings] = lambda: _test_settings(**settings_overrides)
    return TestClient(app)


def _cleanup():
    app.dependency_overrides.clear()


DUMMY_VIDEO = b"\x00\x00\x00\x1cftypisom" + b"\x00" * 100


# ---------- Happy path ----------


@patch(
    "apps.api.services.video_extraction.extract_products",
    return_value=[
        ExtractedProduct(
            product_name="Silk Saree",
            description="Handwoven silk saree with zari border",
            price=4500.0,
            currency="INR",
            category="Clothing",
            availability="in_stock",
        ),
    ],
)
@patch(
    "apps.api.services.video_extraction.transcribe_audio",
    return_value="Check out this beautiful silk saree priced at 4500 rupees",
)
def test_extract_products_success(mock_transcribe, mock_extract):
    client = _make_client()
    try:
        response = client.post(
            "/api/v1/videos/extract-products",
            files={"file": ("test.mp4", DUMMY_VIDEO, "video/mp4")},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert "transcript" not in body["data"]
        assert len(body["data"]["products"]) == 1
        assert body["data"]["products"][0]["product_name"] == "Silk Saree"
        assert body["data"]["products"][0]["price"] == 4500.0

        mock_transcribe.assert_called_once()
        mock_extract.assert_called_once()
    finally:
        _cleanup()


@patch(
    "apps.api.services.video_extraction.transcribe_audio",
    return_value="",
)
def test_extract_products_empty_transcript(mock_transcribe):
    client = _make_client()
    try:
        response = client.post(
            "/api/v1/videos/extract-products",
            files={"file": ("test.mp4", DUMMY_VIDEO, "video/mp4")},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["products"] == []
    finally:
        _cleanup()


# ---------- Input validation ----------


def test_extract_products_unsupported_content_type():
    client = _make_client()
    try:
        response = client.post(
            "/api/v1/videos/extract-products",
            files={"file": ("test.txt", b"not a video", "text/plain")},
        )
        assert response.status_code == 415
    finally:
        _cleanup()


def test_extract_products_missing_api_key():
    client = _make_client(anthropic_api_key="")
    try:
        response = client.post(
            "/api/v1/videos/extract-products",
            files={"file": ("test.mp4", DUMMY_VIDEO, "video/mp4")},
        )
        assert response.status_code == 503
        assert "API key" in response.json()["detail"]
    finally:
        _cleanup()


# ---------- Transcription error propagation ----------


@patch(
    "apps.api.services.video_extraction.transcribe_audio",
    side_effect=TranscriptionError("Failed to decode audio (is ffmpeg installed?): ffmpeg not found"),
)
def test_transcription_ffmpeg_failure(mock_transcribe):
    """ffmpeg-related errors propagate as 422 with a descriptive message."""
    client = _make_client()
    try:
        response = client.post(
            "/api/v1/videos/extract-products",
            files={"file": ("test.mp4", DUMMY_VIDEO, "video/mp4")},
        )
        assert response.status_code == 422
        assert "ffmpeg" in response.json()["detail"]
    finally:
        _cleanup()


@patch(
    "apps.api.services.video_extraction.transcribe_audio",
    side_effect=TranscriptionError(
        "Invalid Whisper model name: 'nonexistent'. "
        "Valid options: base, large, medium, small, tiny"
    ),
)
def test_transcription_invalid_model_name(mock_transcribe):
    """An invalid Whisper model name results in a 422 with the valid options."""
    client = _make_client(whisper_model="nonexistent")
    try:
        response = client.post(
            "/api/v1/videos/extract-products",
            files={"file": ("test.mp4", DUMMY_VIDEO, "video/mp4")},
        )
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert "Invalid Whisper model name" in detail
        assert "nonexistent" in detail
    finally:
        _cleanup()


@patch(
    "apps.api.services.video_extraction.transcribe_audio",
    side_effect=TranscriptionError("Transcription failed: No audio stream found"),
)
def test_transcription_no_audio_stream(mock_transcribe):
    """A video without an audio stream results in a 422."""
    client = _make_client()
    try:
        response = client.post(
            "/api/v1/videos/extract-products",
            files={"file": ("silent.mp4", DUMMY_VIDEO, "video/mp4")},
        )
        assert response.status_code == 422
        assert "audio" in response.json()["detail"].lower()
    finally:
        _cleanup()


# ---------- Product extraction error propagation ----------


@patch(
    "apps.api.services.video_extraction.extract_products",
    side_effect=ProductExtractionError("Claude API request failed: 401 Unauthorized"),
)
@patch(
    "apps.api.services.video_extraction.transcribe_audio",
    return_value="some transcript",
)
def test_extraction_claude_api_error(mock_transcribe, mock_extract):
    """Claude API failures propagate as 422."""
    client = _make_client()
    try:
        response = client.post(
            "/api/v1/videos/extract-products",
            files={"file": ("test.mp4", DUMMY_VIDEO, "video/mp4")},
        )
        assert response.status_code == 422
        assert "Claude API" in response.json()["detail"]
    finally:
        _cleanup()


@patch(
    "apps.api.services.video_extraction.extract_products",
    side_effect=ProductExtractionError("Claude returned invalid JSON: Expecting value"),
)
@patch(
    "apps.api.services.video_extraction.transcribe_audio",
    return_value="some transcript",
)
def test_extraction_invalid_json_from_claude(mock_transcribe, mock_extract):
    """Unparseable Claude output propagates as 422."""
    client = _make_client()
    try:
        response = client.post(
            "/api/v1/videos/extract-products",
            files={"file": ("test.mp4", DUMMY_VIDEO, "video/mp4")},
        )
        assert response.status_code == 422
        assert "invalid JSON" in response.json()["detail"]
    finally:
        _cleanup()


# ---------- Nullable product fields ----------


@patch(
    "apps.api.services.video_extraction.extract_products",
    return_value=[
        ExtractedProduct(
            product_name=None,
            description=None,
            price=None,
            currency=None,
            category=None,
            availability=None,
        ),
    ],
)
@patch(
    "apps.api.services.video_extraction.transcribe_audio",
    return_value="some vague audio about a product",
)
def test_extract_products_with_all_null_fields(mock_transcribe, mock_extract):
    """Products with all-null fields do not crash the system."""
    client = _make_client()
    try:
        response = client.post(
            "/api/v1/videos/extract-products",
            files={"file": ("test.mp4", DUMMY_VIDEO, "video/mp4")},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        product = body["data"]["products"][0]
        assert product["product_name"] is None
        assert product["category"] is None
        assert product["availability"] is None
    finally:
        _cleanup()


@patch(
    "apps.api.services.video_extraction.extract_products",
    return_value=[
        ExtractedProduct(product_name="Widget"),
        ExtractedProduct(
            product_name=None,
            description="unknown item with no name",
        ),
    ],
)
@patch(
    "apps.api.services.video_extraction.transcribe_audio",
    return_value="mentions a widget and another thing",
)
def test_extract_products_partial_fields(mock_transcribe, mock_extract):
    """A mix of complete and sparse products is handled gracefully."""
    client = _make_client()
    try:
        response = client.post(
            "/api/v1/videos/extract-products",
            files={"file": ("test.mp4", DUMMY_VIDEO, "video/mp4")},
        )
        assert response.status_code == 200
        products = response.json()["data"]["products"]
        assert len(products) == 2
        assert products[0]["product_name"] == "Widget"
        assert products[1]["product_name"] is None
        assert products[1]["description"] == "unknown item with no name"
    finally:
        _cleanup()


# ---------- Response structure ----------


@patch(
    "apps.api.services.video_extraction.extract_products",
    return_value=[ExtractedProduct(product_name="Test")],
)
@patch(
    "apps.api.services.video_extraction.transcribe_audio",
    return_value="test transcript that should not appear in response",
)
def test_response_excludes_transcript(mock_transcribe, mock_extract):
    """The raw transcript must NOT appear in the JSON response."""
    client = _make_client()
    try:
        response = client.post(
            "/api/v1/videos/extract-products",
            files={"file": ("test.mp4", DUMMY_VIDEO, "video/mp4")},
        )
        assert response.status_code == 200
        body = response.json()
        assert "transcript" not in body["data"]
        assert "transcript" not in str(body["data"])
    finally:
        _cleanup()
