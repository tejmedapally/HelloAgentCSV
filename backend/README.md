# Hello Agent — backend

FastAPI service for session-scoped CSV upload and Claude-backed Q&A.

## Setup

```powershell
cd backend
copy .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=...
uv sync --system-certs
```

(Omit `--system-certs` if your network does not need it.)

## Run

```powershell
uv run --system-certs uvicorn app.main:app --reload --port 8000
```

| URL | Purpose |
|-----|---------|
| http://127.0.0.1:8000/api/v1/health | Health |
| http://127.0.0.1:8000/docs | Swagger (Try it out) |
| http://127.0.0.1:8000/redoc | ReDoc |

Sessions are stored in memory — restarting the server clears them; create a new session and re-upload CSVs.

## Docker

```powershell
cd backend
docker build -t hello-agent-backend .
docker run --rm -p 8000:8000 -e ANTHROPIC_API_KEY=your-key hello-agent-backend
```

Do not pass secrets via `docker build --build-arg`; use runtime `-e` / Compose / ECS Express Mode env only.
