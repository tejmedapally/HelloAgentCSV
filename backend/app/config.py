"""Application settings loaded from environment variables / `.env`."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Backend configuration for Hello Agent.

    Values are read from environment variables and optional `backend/.env`.
    Never commit real secrets — use `.env.example` as the template.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: str = Field(
        default="",
        description="Anthropic Claude API key (required at ask-time)",
    )
    backend_api_key: str = Field(
        default="",
        description=(
            "Shared secret for X-API-Key. When non-empty, all API routes except "
            "health require this header (frontend must send the same value)."
        ),
    )
    anthropic_model: str = Field(
        default="claude-haiku-4-5-20251001",
        description="Claude model id for the dataframe agent",
    )
    llm_temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Model temperature; keep near 0 for data-only answers",
    )
    preview_row_count: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Number of CSV rows returned in upload previews",
    )
    max_upload_size_mb: float = Field(
        default=10.0,
        gt=0.0,
        description="Maximum upload size per CSV file in megabytes",
    )

    @property
    def max_upload_size_bytes(self) -> int:
        return int(self.max_upload_size_mb * 1024 * 1024)


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
