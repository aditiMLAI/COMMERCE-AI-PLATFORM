"""Application settings loaded from environment variables and .env file.

Uses pydantic-settings to provide typed, validated configuration with
sensible defaults for the Whisper transcription and Claude extraction
pipeline.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration for the Commerce AI Platform."""

    anthropic_api_key: str = ""
    whisper_model: str = "base"
    max_upload_bytes: int = 100_000_000  # 100 MB
    claude_model: str = "claude-sonnet-4-20250514"
    claude_max_tokens: int = 4096

    model_config = {"env_file": ".env", "extra": "ignore"}


def get_settings() -> Settings:
    """Factory for dependency-injected settings; override in tests."""
    return Settings()
