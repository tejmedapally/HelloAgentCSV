"""HTTP client for the Hello Agent FastAPI backend."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx

SESSION_HEADER = "X-Session-Id"
DEFAULT_BACKEND_URL = "http://localhost:8000"


def _load_dotenv(path: Path) -> None:
    """Load simple KEY=VALUE lines from a .env file if present."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_dotenv(Path(__file__).resolve().parent / ".env")


class BackendClient:
    """Thin httpx wrapper for session create/get and health checks."""

    def __init__(self, base_url: str | None = None, timeout: float = 30.0) -> None:
        self.base_url = (
            base_url or os.getenv("BACKEND_URL", DEFAULT_BACKEND_URL)
        ).rstrip("/")
        self.session_id: str | None = None
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> BackendClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def health(self) -> dict[str, Any]:
        """GET /api/v1/health."""
        response = self._client.get("/api/v1/health")
        response.raise_for_status()
        return response.json()

    def create_session(self) -> dict[str, Any]:
        """POST /api/v1/session and remember the session id."""
        response = self._client.post("/api/v1/session")
        response.raise_for_status()
        data = response.json()
        self.session_id = str(data["id"])
        header_id = response.headers.get(SESSION_HEADER)
        if header_id:
            self.session_id = header_id
        return data

    def get_session(self, session_id: str | None = None) -> dict[str, Any]:
        """GET /api/v1/session with X-Session-Id."""
        sid = session_id or self.session_id
        if not sid:
            raise ValueError("session_id is required (create a session first)")
        response = self._client.get(
            "/api/v1/session",
            headers={SESSION_HEADER: sid},
        )
        response.raise_for_status()
        return response.json()
