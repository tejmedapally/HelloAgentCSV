"""Optional shared-secret gate for backend API routes."""

from __future__ import annotations

import hashlib
import hmac

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import get_settings

API_KEY_HEADER = "X-API-Key"

# Always public so ECS/ALB health checks keep working without custom headers.
_PUBLIC_PATHS = frozenset(
    {
        "/api/v1/health",
    }
)


def _keys_match(provided: str | None, expected: str) -> bool:
    if not provided:
        return False
    left = hashlib.sha256(provided.encode("utf-8")).digest()
    right = hashlib.sha256(expected.encode("utf-8")).digest()
    return hmac.compare_digest(left, right)


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """When ``BACKEND_API_KEY`` is set, require matching ``X-API-Key`` header."""

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if path in _PUBLIC_PATHS:
            return await call_next(request)

        expected = (get_settings().backend_api_key or "").strip()
        if not expected:
            # Local/dev convenience: unset key means open API.
            return await call_next(request)

        provided = request.headers.get(API_KEY_HEADER)
        if not _keys_match(provided, expected):
            return JSONResponse(
                status_code=401,
                content={
                    "detail": (
                        "Invalid or missing API key. "
                        f"Send header {API_KEY_HEADER} with the shared BACKEND_API_KEY."
                    )
                },
            )
        return await call_next(request)
