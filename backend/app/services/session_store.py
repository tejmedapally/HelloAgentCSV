"""In-memory session store for uploaded CSV sources.

Process-local only: state is lost on restart and is not shared across
multiple backend instances (see data-model.md).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any
from uuid import uuid4

import pandas as pd


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class SourceRecord:
    """One uploaded CSV attached to a session (runtime + preview metadata)."""

    id: str
    filename: str
    columns: list[str]
    row_count: int
    preview_rows: list[dict[str, Any]]
    dataframe: pd.DataFrame


@dataclass
class SessionRecord:
    """Session holding the active CSV source set."""

    id: str
    created_at: datetime
    updated_at: datetime
    sources: list[SourceRecord] = field(default_factory=list)


class SessionNotFoundError(KeyError):
    """Raised when a session id is unknown."""


class SessionStore:
    """Thread-safe in-memory store for sessions and their sources."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionRecord] = {}
        self._lock = Lock()

    def create_session(self) -> SessionRecord:
        """Create and store a new empty session."""
        now = _utc_now()
        session = SessionRecord(
            id=str(uuid4()),
            created_at=now,
            updated_at=now,
            sources=[],
        )
        with self._lock:
            self._sessions[session.id] = session
        return session

    def get_session(self, session_id: str) -> SessionRecord:
        """Return an existing session or raise SessionNotFoundError."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise SessionNotFoundError(session_id)
            return session

    def delete_session(self, session_id: str) -> None:
        """Remove a session and all attached sources."""
        with self._lock:
            if session_id not in self._sessions:
                raise SessionNotFoundError(session_id)
            del self._sessions[session_id]

    def attach_sources(
        self,
        session_id: str,
        sources: list[SourceRecord],
    ) -> SessionRecord:
        """Append one or more sources to the session's active set."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise SessionNotFoundError(session_id)
            session.sources.extend(sources)
            session.updated_at = _utc_now()
            return session

    def clear_sources(self, session_id: str) -> SessionRecord:
        """Remove all sources from a session (keep the session itself)."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise SessionNotFoundError(session_id)
            session.sources.clear()
            session.updated_at = _utc_now()
            return session

    def list_sources(self, session_id: str) -> list[SourceRecord]:
        """Return a copy of the session's source list."""
        session = self.get_session(session_id)
        return list(session.sources)


# Process-wide store used by API routes (single instance for Week 0).
session_store = SessionStore()
