# Implementation Plan: Hello Agent CSV FAQ

**Branch**: `001-csv-faq-agent` | **Date**: 2026-09-16 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-csv-faq-agent/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Build **Hello Agent**, a session-based CSV FAQ tool: users upload one or more
CSVs, preview them, ask natural-language questions, and get clear English
answers grounded only in those tables (or an explicit not-found message).

**Technical approach**: Monorepo with a **FastAPI** backend (Pandas + LangChain
dataframe agent + **Anthropic Claude**) and a **Streamlit** frontend that talks
to the backend over HTTP. Two Docker images, local Compose, publish to **ECR**,
run with **Amazon ECS Express Mode** so the frontend can call the backend URL.
Sample CSVs
live under `datasets/` (from existing `Datasets/`). No vector DB, no SQL DB,
no OpenAI.

## Technical Context

**Language/Version**: Python 3.12+ (venv via `uv`; 3.13 acceptable if deps allow)

**Primary Dependencies**:
- Backend: FastAPI, Uvicorn, Pandas, LangChain, `langchain-experimental`,
  `langchain-anthropic`, python-multipart
- Frontend: Streamlit, `httpx` (or `requests`) to call backend
- Ops: Docker, Docker Compose, AWS CLI (ECR + ECS Express Mode)

**Storage**: In-memory session store on the backend (uploaded dataframes +
metadata). No external database. Sample/reference CSVs on disk under `datasets/`.

**Testing**: `pytest` for backend unit/API tests; manual Streamlit E2E per
`quickstart.md`; optional contract checks against OpenAPI.

**Target Platform**: Linux containers locally and on AWS; developers on Windows
with Docker Desktop / Compose.

**Project Type**: Web application (separated frontend + backend services)

**Performance Goals**: Interactive support use on sample-scale CSVs; ask→answer
typically within ~15–30s under normal API latency (warm-up, not SLA-hardened).

**Constraints**:
- Data-only answers; low model temperature; no world-knowledge invention
- No vector DB / complex RAG / MySQL/MongoDB
- Secrets via env (`ANTHROPIC_API_KEY`, backend URL); never in images or git
- Exactly two runtime images (backend, frontend)
- OpenAI MUST NOT be required

**Scale/Scope**: Single internal warm-up app; one main screen; multi-CSV session
Q&A; dual-image AWS deploy path documented and runnable.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | How plan satisfies |
|-----------|--------|--------------------|
| I. Spec-Driven Development | PASS | Work traces to `spec.md` + this plan; tasks/implement follow |
| II. Clean Separated Architecture | PASS | `backend/`, `frontend/`, `datasets/`; HTTP API contract in `contracts/` |
| III. Data-Only Answers | PASS | System prompt + low temperature + not-found path in agent service |
| IV. Containerized Dual-Image Delivery | PASS | Two Dockerfiles, Compose, ECR push, ECS Express Mode deploy of both |
| V. Simplicity and Predictability | PASS | No vector/SQL DB; Streamlit UI; in-memory sessions; ECS Express Mode over hand-rolled ECS/ALB |

**Post-Phase 1 re-check**: PASS — data model is session-scoped only; contracts are
a small REST surface; quickstart validates FE→BE→Claude without extra services.

## Project Structure

### Documentation (this feature)

```text
specs/001-csv-faq-agent/
├── plan.md              # This file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/           # Phase 1
│   └── openapi.yaml
└── tasks.md             # Phase 2 (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
backend/
├── Dockerfile
├── pyproject.toml          # or requirements.txt
├── app/
│   ├── main.py             # FastAPI entry
│   ├── api/
│   │   └── routes.py       # upload, list sources, ask
│   ├── models/
│   │   └── schemas.py      # request/response models
│   ├── services/
│   │   ├── session_store.py
│   │   ├── csv_service.py
│   │   └── agent_service.py  # LangChain + Claude, data-only prompt
│   └── config.py
└── tests/
    ├── test_csv_service.py
    ├── test_api.py
    └── test_agent_prompt.py

frontend/
├── Dockerfile
├── pyproject.toml          # or requirements.txt
├── app.py                  # Streamlit UI
├── api_client.py           # HTTP client to backend
└── .streamlit/
    └── config.toml         # optional UI defaults

datasets/
├── ecommerce_faqs.csv
├── credit_card_terms.csv
├── hospital_policy.csv
└── saas_docs.csv

docker-compose.yml          # local: backend + frontend
docs/
└── requirements.pdf
.specify/
specs/
```

**Structure Decision**: Web application monorepo (`backend/` + `frontend/` +
`datasets/`) per constitution. Streamlit is the **frontend service** only; all
CSV parsing and Claude/LangChain agent logic run in the **backend**. Existing
`Datasets/` contents move/rename into `datasets/` during implementation.
Repository-root notebook stub is not the runtime entrypoint; keep or archive
out of the main path during implement.

## Complexity Tracking

> No constitution violations requiring justification.
