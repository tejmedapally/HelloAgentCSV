# Hello Agent — CSV FAQ Agent

Week 0 mini-project: upload CSV FAQ/policy files, ask natural-language questions,
and get answers grounded only in that table data (Claude API on the backend).

## Layout

```text
backend/     FastAPI API + Pandas/LangChain agent (Claude) — port 8000
frontend/    Streamlit UI (calls the backend over HTTP) — port 8501
datasets/    Sample CSVs for demos and tests
docs/        Requirements PDF and setup guides
specs/       Spec Kit feature specs, plan, and tasks
scripts/     Optional AWS one-shot deploy (`deploy-aws.ps1`)
.specify/    Spec Kit project config and constitution
```

## Environment variables

| Variable | Where | Example |
|----------|--------|---------|
| `ANTHROPIC_API_KEY` | **Backend only** | set in `backend/.env`, root `.env` (Compose), or ECS env/secret |
| `BACKEND_URL` | **Frontend only** | local: `http://localhost:8000` · Compose: `http://backend:8000` · AWS: backend HTTPS URL |
| `PORT` | optional | backend default `8000`, frontend/Streamlit default `8501` |

Never put `ANTHROPIC_API_KEY` on the frontend. Never commit real keys.

## Spec-driven development

This repo uses [Spec Kit](https://github.com/github/spec-kit) with Cursor
(`cursor-agent`). Feature work for this app lives under:

- Spec / plan / tasks: [`specs/001-csv-faq-agent/`](specs/001-csv-faq-agent/)
- **Run & validate**: [`specs/001-csv-faq-agent/quickstart.md`](specs/001-csv-faq-agent/quickstart.md)

Setup cheat sheets:

- [`docs/01-uv-venv-setup.md`](docs/01-uv-venv-setup.md)
- [`docs/02-speckit-setup.md`](docs/02-speckit-setup.md)
- [`docs/03-git-github-setup.md`](docs/03-git-github-setup.md)
- [`docs/aws-deploy.md`](docs/aws-deploy.md) (ECR + ECS Express Mode; one-shot: `scripts/deploy-aws.ps1`)

## Docker Compose (both services)

```powershell
# From repo root — set ANTHROPIC_API_KEY in the environment or a root .env file
$env:ANTHROPIC_API_KEY = "sk-ant-your-key"
docker compose up --build
```

Compose wires frontend `BACKEND_URL=http://backend:8000` automatically.

| Service | URL |
|---------|-----|
| UI (Streamlit) | http://localhost:8501 |
| API health | http://localhost:8000/api/v1/health |
| API docs | http://localhost:8000/docs |

## Quick local setup (two terminals)

```powershell
# Env files (once)
copy backend\.env.example backend\.env   # set ANTHROPIC_API_KEY=
copy frontend\.env.example frontend\.env # BACKEND_URL=http://localhost:8000

# Backend (terminal A) — port 8000
cd backend
uv sync --system-certs
uv run --system-certs uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Frontend (terminal B) — port 8501
cd frontend
uv sync --system-certs
uv run --system-certs streamlit run app.py --server.port 8501
```

- UI: http://localhost:8501  
- Health: http://localhost:8000/api/v1/health  

Step-by-step uv / run / troubleshooting: **[docs/01-uv-venv-setup.md](docs/01-uv-venv-setup.md)**.  
Full acceptance checks: **[quickstart.md](specs/001-csv-faq-agent/quickstart.md)**.

## Secrets

Never commit real API keys. Use `.env` files (gitignored). Templates:

- `backend/.env.example`
- `frontend/.env.example`
