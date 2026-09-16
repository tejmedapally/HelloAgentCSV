# Hello Agent — backend

FastAPI service for session-scoped CSV upload and Claude-backed Q&A.

## Setup

```powershell
cd backend
uv sync --system-certs
```

(Omit `--system-certs` if your network does not need it.)

## Run (after later tasks wire the app)

```powershell
$env:ANTHROPIC_API_KEY = "your-key"
uv run uvicorn app.main:app --reload --port 8000
```
