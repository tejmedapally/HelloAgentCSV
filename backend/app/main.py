"""FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

app = FastAPI(
    title="Hello Agent CSV FAQ API",
    version="1.0.0",
    description="Session-scoped CSV upload, preview, and data-only Q&A.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root() -> dict[str, str]:
    """Friendly landing note for browsers that hit the host root."""
    return {
        "message": "Hello Agent API is at /api/v1",
        "health": "/api/v1/health",
        "docs": "/docs",
    }


@app.get("/json/version")
def json_version_probe() -> dict[str, str]:
    """Quiet probes that expect a browser debug endpoint (e.g. DevTools)."""
    return {
        "message": "Not a browser debug endpoint. Hello Agent API is at /api/v1",
        "health": "/api/v1/health",
        "docs": "/docs",
    }

