# Hello Agent — CSV FAQ Agent

Week 0 mini-project: upload CSV FAQ/policy files, ask natural-language questions,
and get answers grounded only in that table data (Claude API on the backend).

## Layout

```text
backend/     FastAPI API + Pandas/LangChain agent (Claude)
frontend/    Streamlit UI (calls the backend over HTTP)
datasets/    Sample CSVs for demos and tests
docs/        Requirements PDF and setup guides
specs/       Spec Kit feature specs, plan, and tasks
.specify/    Spec Kit project config and constitution
```

## Spec-driven development

This repo uses [Spec Kit](https://github.com/github/spec-kit) with Cursor
(`cursor-agent`). Feature work for this app lives under:

- Spec / plan / tasks: [`specs/001-csv-faq-agent/`](specs/001-csv-faq-agent/)
- **Run & validate**: [`specs/001-csv-faq-agent/quickstart.md`](specs/001-csv-faq-agent/quickstart.md)

Setup cheat sheets:

- [`docs/01-uv-venv-setup.md`](docs/01-uv-venv-setup.md)
- [`docs/02-speckit-setup.md`](docs/02-speckit-setup.md)
- [`docs/03-git-github-setup.md`](docs/03-git-github-setup.md)

## Quick local setup (after implementation tasks)

```powershell
# Backend
cd backend
copy .env.example .env   # then set ANTHROPIC_API_KEY
uv sync --system-certs

# Frontend (another terminal)
cd frontend
copy .env.example .env   # BACKEND_URL=http://localhost:8000
uv sync --system-certs
```

Full run steps and acceptance checks: **[quickstart.md](specs/001-csv-faq-agent/quickstart.md)**.

## Secrets

Never commit real API keys. Use `.env` files (gitignored). Templates:

- `backend/.env.example`
- `frontend/.env.example`
