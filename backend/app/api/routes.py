"""API routes for Hello Agent backend."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Response, status

from app.models.schemas import (
    Error,
    HealthResponse,
    Session,
    SourcePublic,
)
from app.services.session_store import (
    SessionNotFoundError,
    SessionRecord,
    SourceRecord,
    session_store,
)

router = APIRouter(prefix="/api/v1")

SESSION_HEADER = "X-Session-Id"


def _source_to_public(source: SourceRecord) -> SourcePublic:
    return SourcePublic(
        id=UUID(source.id),
        filename=source.filename,
        columns=source.columns,
        row_count=source.row_count,
        preview_rows=source.preview_rows,
    )


def _session_to_schema(session: SessionRecord) -> Session:
    return Session(
        id=UUID(session.id),
        sources=[_source_to_public(s) for s in session.sources],
    )


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness check for local and deployed backends."""
    return HealthResponse(status="ok")


@router.post(
    "/session",
    response_model=Session,
    status_code=status.HTTP_201_CREATED,
)
def create_session(response: Response) -> Session:
    """Create a new empty session and return its id."""
    session = session_store.create_session()
    response.headers[SESSION_HEADER] = session.id
    response.set_cookie(
        key="session_id",
        value=session.id,
        httponly=True,
        samesite="lax",
    )
    return _session_to_schema(session)


@router.get(
    "/session",
    response_model=Session,
    responses={404: {"model": Error}},
)
def get_session(
    x_session_id: str | None = Header(default=None, alias=SESSION_HEADER),
) -> Session:
    """Return session summary for the given X-Session-Id header."""
    if not x_session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Session-Id header is required",
        )
    try:
        session = session_store.get_session(x_session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        ) from exc
    return _session_to_schema(session)
