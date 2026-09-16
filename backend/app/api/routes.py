"""API routes for Hello Agent backend."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, File, Header, HTTPException, Response, UploadFile, status

from app.models.schemas import (
    AskRequest,
    AskResponse,
    AnswerStatus,
    Error,
    HealthResponse,
    Session,
    SourcePublic,
    SourcesList,
)
from app.services.agent_service import answer_from_sources
from app.services.csv_service import CsvParseError, parse_csv_bytes
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


def _require_session_id(x_session_id: str | None) -> str:
    if not x_session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Session-Id header is required",
        )
    return x_session_id


def _get_session_or_404(session_id: str) -> SessionRecord:
    try:
        return session_store.get_session(session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        ) from exc


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
    session_id = _require_session_id(x_session_id)
    session = _get_session_or_404(session_id)
    return _session_to_schema(session)


@router.post(
    "/sources",
    response_model=SourcesList,
    responses={400: {"model": Error}, 404: {"model": Error}},
)
async def upload_sources(
    response: Response,
    files: list[UploadFile] = File(...),
    x_session_id: str | None = Header(default=None, alias=SESSION_HEADER),
) -> SourcesList:
    """Upload one or more CSV files into the session's active source set.

    Valid files are attached even when some siblings fail. If every file
    fails validation, returns 400 and attaches nothing.
    """
    session_id = _require_session_id(x_session_id)
    _get_session_or_404(session_id)

    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one file is required",
        )

    parsed: list[SourceRecord] = []
    errors: list[str] = []
    for upload in files:
        filename = upload.filename or "upload.csv"
        content = await upload.read()
        try:
            parsed.append(parse_csv_bytes(content, filename))
        except CsvParseError as exc:
            errors.append(f"{filename}: {exc}")

    if not parsed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="; ".join(errors) if errors else "No valid CSV files in upload",
        )

    session = session_store.attach_sources(session_id, parsed)
    if errors:
        # Partial success: keep good files; surface sibling failures to the client.
        response.headers["X-Upload-Warnings"] = "; ".join(errors)
    return SourcesList(sources=[_source_to_public(s) for s in session.sources])


@router.get(
    "/sources",
    response_model=SourcesList,
    responses={400: {"model": Error}, 404: {"model": Error}},
)
def list_sources(
    x_session_id: str | None = Header(default=None, alias=SESSION_HEADER),
) -> SourcesList:
    """Return active CSV sources with public preview payloads."""
    session_id = _require_session_id(x_session_id)
    session = _get_session_or_404(session_id)
    return SourcesList(sources=[_source_to_public(s) for s in session.sources])


@router.delete(
    "/sources",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={400: {"model": Error}, 404: {"model": Error}},
)
def clear_sources(
    x_session_id: str | None = Header(default=None, alias=SESSION_HEADER),
) -> Response:
    """Clear all sources in the session (session itself is kept)."""
    session_id = _require_session_id(x_session_id)
    _get_session_or_404(session_id)
    session_store.clear_sources(session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/ask",
    response_model=AskResponse,
    responses={
        400: {"model": Error},
        404: {"model": Error},
        502: {"model": Error},
    },
)
def ask_question(
    body: AskRequest,
    x_session_id: str | None = Header(default=None, alias=SESSION_HEADER),
) -> AskResponse:
    """Ask a question against the session's uploaded CSV sources."""
    session_id = _require_session_id(x_session_id)
    session = _get_session_or_404(session_id)

    if not session.sources:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload one or more CSV files before asking a question.",
        )

    result = answer_from_sources(session.sources, body.question)
    if result.status == AnswerStatus.error and "ANTHROPIC_API_KEY" in result.text:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=result.text,
        )
    if result.status == AnswerStatus.error and result.text.startswith(
        "Could not generate an answer:"
    ):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=result.text,
        )
    return result
