"""API request/response models aligned with contracts/openapi.yaml."""

from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AnswerStatus(str, Enum):
    ok = "ok"
    not_found = "not_found"
    error = "error"


class SourcePublic(BaseModel):
    """CSV source metadata exposed to clients (no dataframe)."""

    id: UUID
    filename: str
    columns: list[str]
    row_count: int = Field(ge=0)
    preview_rows: list[dict[str, Any]] = Field(
        description="First few rows for UI preview",
    )


class Session(BaseModel):
    """Session summary including active sources."""

    id: UUID
    sources: list[SourcePublic]


class AskRequest(BaseModel):
    """Natural-language question against the session's active sources."""

    question: str = Field(min_length=1)


class AskResponse(BaseModel):
    """Agent answer payload."""

    text: str
    status: AnswerStatus
    source_filenames: list[str] | None = None


class Error(BaseModel):
    """Standard error body."""

    detail: str


class SourcesList(BaseModel):
    """Wrapper used by list/upload source endpoints in OpenAPI."""

    sources: list[SourcePublic]


class HealthResponse(BaseModel):
    """Liveness payload for GET /api/v1/health."""

    status: str = "ok"
