# Quickstart: Hello Agent CSV FAQ

**Feature**: `001-csv-faq-agent`  
**Date**: 2026-09-16

Validation guide for the planned FE/BE split. Commands assume repo root
`C:\Projects\IK\Week_0` (or clone root) after implementation exists.

## Prerequisites

- Python 3.12+ and `uv` (or pip) for local non-Docker runs
- Docker Desktop (for Compose / image builds)
- `ANTHROPIC_API_KEY` in the environment (backend only)
- Sample CSVs under `datasets/` (migrated from `Datasets/`)
- Optional: AWS CLI configured for ECR push + ECS Express Mode deploy

See also: [data-model.md](./data-model.md), [contracts/openapi.yaml](./contracts/openapi.yaml).

## 1. Local backend + frontend (dev)

Create env files once (if missing):

```powershell
cd C:\Projects\IK\Week_0
copy backend\.env.example backend\.env
copy frontend\.env.example frontend\.env
# Edit backend\.env → set ANTHROPIC_API_KEY
```

```powershell
# Terminal A — backend
cd backend
uv sync --system-certs
uv run --system-certs uvicorn app.main:app --reload --port 8000

# Terminal B — frontend
cd frontend
uv sync --system-certs
uv run --system-certs streamlit run app.py
```

**Expected**: Browser opens Streamlit UI; health `GET http://localhost:8000/api/v1/health` returns `{"status":"ok"}`.

**Also useful**: interactive API docs at http://localhost:8000/docs  

More setup detail: [`docs/01-uv-venv-setup.md`](../../docs/01-uv-venv-setup.md).

## 2. Local Compose (parity with two images)

```powershell
$env:ANTHROPIC_API_KEY = "your-key"
docker compose up --build
```

**Expected**: Backend and frontend containers healthy; UI reachable on published frontend port; UI can upload and ask via backend service name/URL.

## 3. End-to-end product checks

Use files from `datasets/` (ecommerce, credit card, hospital, SaaS).

| # | Steps | Expected |
|---|--------|----------|
| A | Open UI with no uploads; submit a question | Clear prompt to upload; no invented policy answer |
| B | Upload `ecommerce_faqs.csv`; confirm preview rows | Filename listed; preview shows first rows |
| C | Ask a question answered in that CSV | `status` conceptually ok; answer grounded in file |
| D | Ask something absent from all uploads | Clear not-found wording |
| E | Upload a second domain CSV; ask a domain-specific question | Answer from relevant data only |
| F | Upload a non-CSV / corrupt file | Error; not added as answer source |
| G | Copy answer text from UI | Single straightforward copy for paste |

Map to spec success criteria SC-001–SC-006 qualitatively for warm-up.

## 4. API smoke (optional)

```powershell
# Create session, upload, ask — adjust to implemented client/headers
curl http://localhost:8000/api/v1/health
```

Compare responses to [contracts/openapi.yaml](./contracts/openapi.yaml).

## 5. AWS (after images build)

High-level validation (details filled during implement tasks):

1. `docker build` backend and frontend images.
2. Push both to ECR.
3. Create/update two **ECS Express Mode** services; set backend `ANTHROPIC_API_KEY`; set frontend `BACKEND_URL` to backend HTTPS URL.
4. Open frontend URL; repeat checks A–E against deployed stack.

**Expected**: FE reaches BE over HTTPS; answers still data-only; key never present in frontend env.

## Out of scope for this quickstart

- Full pytest suite listing (see `tasks.md` / implement)
- Load/perf testing
- Multi-instance sticky-session proof
