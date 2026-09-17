# Quickstart: Hello Agent CSV FAQ

**Feature**: `001-csv-faq-agent`  
**Date**: 2026-09-17

Validation guide for the FE/BE split. Commands assume repo root
`C:\Projects\IK\Week_0` (or your clone root).

## Ports and env vars (source of truth)

| Item | Value |
|------|--------|
| Backend port | **8000** |
| Frontend / Streamlit port | **8501** |
| Health | `GET http://localhost:8000/api/v1/health` → `{"status":"ok"}` |
| `ANTHROPIC_API_KEY` | Backend only (`backend/.env`, root `.env` for Compose, or ECS secret/env) |
| `BACKEND_URL` (local dual-terminal) | `http://localhost:8000` in `frontend/.env` |
| `BACKEND_URL` (Compose) | `http://backend:8000` (set in `docker-compose.yml`) |
| `BACKEND_URL` (AWS) | Backend Express Mode HTTPS URL (no trailing slash) |

## Prerequisites

- Python 3.12+ and `uv` (or pip) for local non-Docker runs
- Docker Desktop (for Compose / image builds)
- `ANTHROPIC_API_KEY` available to the **backend** only
- Sample CSVs under `datasets/`
- Optional: AWS CLI for ECR + ECS Express Mode ([`docs/aws-deploy.md`](../../docs/aws-deploy.md))

See also: [data-model.md](./data-model.md), [contracts/openapi.yaml](./contracts/openapi.yaml).

## 1. Local backend + frontend (dev)

Create env files once (if missing):

```powershell
cd C:\Projects\IK\Week_0
copy backend\.env.example backend\.env
copy frontend\.env.example frontend\.env
# Edit backend\.env → ANTHROPIC_API_KEY=...
# Confirm frontend\.env → BACKEND_URL=http://localhost:8000
```

```powershell
# Terminal A — backend (port 8000)
cd backend
uv sync --system-certs
uv run --system-certs uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal B — frontend (port 8501)
cd frontend
uv sync --system-certs
uv run --system-certs streamlit run app.py --server.port 8501
```

**Expected**:

- UI: http://localhost:8501
- Health: `GET http://localhost:8000/api/v1/health` → `{"status":"ok"}`
- API docs: http://localhost:8000/docs

More setup detail: [`docs/01-uv-venv-setup.md`](../../docs/01-uv-venv-setup.md).

## 2. Local Compose (parity with two images)

From repo root:

```powershell
cd C:\Projects\IK\Week_0
$env:ANTHROPIC_API_KEY = "sk-ant-your-key"   # or put ANTHROPIC_API_KEY=... in a root .env
docker compose up --build
```

Compose publishes:

| Service | Host URL | Notes |
|---------|----------|--------|
| frontend | http://localhost:8501 | `BACKEND_URL=http://backend:8000` inside the Compose network |
| backend | http://localhost:8000 | Health at `/api/v1/health` |

**Expected**: Both containers healthy; UI can upload and ask through the backend service name.

## 3. End-to-end product checks

Use files from `datasets/` (ecommerce, credit card, hospital, SaaS).

| # | Steps | Expected |
|---|--------|----------|
| A | Open UI with no uploads; try to ask | Ask disabled / clear prompt to upload; no invented policy answer |
| B | Upload `ecommerce_faqs.csv`; confirm preview rows | Filename listed; preview shows first rows |
| C | Ask a question answered in that CSV | `status` ok; answer grounded in file (plain text, copyable) |
| D | Ask something absent from all uploads | Clear not-found wording (`not_found`) |
| E | Upload a second domain CSV; ask a domain-specific question | Answer from relevant data only |
| F | Upload a non-CSV / corrupt file | Error; not added as answer source |
| G | Copy answer text from UI | Single straightforward copy for paste |

Map to spec success criteria SC-001–SC-006 qualitatively for warm-up.

## 4. API smoke (optional)

```powershell
curl.exe -s http://localhost:8000/api/v1/health
# Expect: {"status":"ok"}
```

Create session / upload / ask via Swagger at http://localhost:8000/docs or HTTP client.
Compare shapes to [contracts/openapi.yaml](./contracts/openapi.yaml).

## 5. AWS (ECR + ECS Express Mode)

Full steps: [`docs/aws-deploy.md`](../../docs/aws-deploy.md).

Summary:

1. Build and push `hello-agent-backend` / `hello-agent-frontend` to ECR (ports **8000** / **8501** in the images).
2. Deploy **backend** Express Mode first (`ANTHROPIC_API_KEY`, health `/api/v1/health`).
3. Deploy **frontend** with `BACKEND_URL` = backend HTTPS Application URL (health `/`).
4. Or one-shot: `.\scripts\deploy-aws.ps1` (see Part F9 in aws-deploy).
5. Open frontend URL; repeat checks A–E against the deployed stack.

**Expected**: FE reaches BE over HTTPS; answers still data-only; key never present in frontend env.

## Out of scope for this quickstart

- Full pytest suite listing (see `tasks.md` / implement)
- Load/perf testing
- Multi-instance sticky-session proof
