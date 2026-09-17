# Research: Hello Agent CSV FAQ

**Feature**: `001-csv-faq-agent`  
**Date**: 2026-09-16

## 1. LLM provider

**Decision**: Anthropic Claude API via `langchain-anthropic` (`ChatAnthropic`),
not OpenAI.

**Rationale**: Project constitution v1.1.0 and available API access; course PDF
OpenAI default is overridden deliberately.

**Alternatives considered**:
- OpenAI `gpt-4o-mini` — matches PDF literally; rejected (no OpenAI requirement).
- Calling Anthropic SDK without LangChain — simpler deps but loses dataframe
  agent helpers from the course pattern; rejected for warm-up learning alignment.

## 2. Agent pattern

**Decision**: LangChain **pandas dataframe agent**
(`create_pandas_dataframe_agent` from `langchain_experimental`) over one or more
in-memory DataFrames, with a strict **data-only system prompt** and **low
temperature** (e.g. `0`).

**Rationale**: Matches course learning goals; supports multi-CSV by passing a
list of frames; keeps out vector DB / RAG.

**Alternatives considered**:
- Manual retrieval (keyword filter + LLM summarize) — more code, less “agent”
  learning value for Week 0.
- Vector embeddings over rows — violates constitution simplicity / no vector DB.

## 3. Frontend vs backend split

**Decision**: **Streamlit frontend** + **FastAPI backend**. Streamlit handles
upload widgets, previews, question box, and displays answers. Backend owns
session storage, CSV validation/parsing, and agent invocation.

**Rationale**: Constitution requires FE/BE + HTTP contract and two images;
Streamlit remains the simple UI from the course brief without putting secrets or
agent logic only in the browser.

**Alternatives considered**:
- Single Streamlit process (PDF default) — fails dual-image / separated
  architecture constitution gates.
- React/Vue SPA + FastAPI — heavier than needed for Week 0.
- Streamlit calling Claude directly — bypasses backend image and shared API
  contract; rejected.

## 4. Session and storage

**Decision**: **In-memory session store** on the backend keyed by a session ID
(cookie or `X-Session-Id` header). Store filenames, previews, and DataFrames for
the life of the process/session. No PostgreSQL/SQLite/MongoDB.

**Rationale**: Spec assumes session-scoped uploads; constitution forbids
unnecessary external DB.

**Alternatives considered**: Redis — ops overhead for warm-up. Disk temp files
only — possible later; in-memory is enough for sample CSVs.

## 5. Local run and containers

**Decision**: `docker-compose.yml` runs `backend` and `frontend` services.
Frontend env `BACKEND_URL=http://backend:8000` (Compose network) or
`http://localhost:8000` for host-run Streamlit.

**Rationale**: Mirrors production split; constitution asks for Compose or
equivalent locally.

**Alternatives considered**: Manual two-terminal `uvicorn` + `streamlit` only —
still supported in quickstart for fast iteration, but Compose is the canonical
parity path.

## 6. AWS publish and deploy

**Decision** (updated 2026-09 — App Runner closed to new customers):
1. Build two images; tag and push to **Amazon ECR** (two repositories).
2. Deploy each image with **Amazon ECS Express Mode** (backend + frontend).
3. Configure frontend `BACKEND_URL` to the backend public HTTPS URL.
4. Inject `ANTHROPIC_API_KEY` into the **backend** service only (runtime
   secrets/env — never on the frontend or in the image).

**Rationale**: AWS recommends ECS Express Mode as the App Runner successor:
one-call-style deploy of a container (Fargate + load balancer + networking)
while staying on the ECS path. Still satisfies “two images on AWS that work
together.” See [App Runner availability change](https://docs.aws.amazon.com/apprunner/latest/dg/apprunner-availability-change.html).

**Alternatives considered**:
- AWS App Runner — deferred/unavailable for new accounts after 2026-04-30.
- Full ECS Fargate + ALB hand-rolled — more control, more moving parts.
- EC2 Docker Compose — works but less managed deploy.

## 7. Sample datasets path

**Decision**: Canonical folder `datasets/` at repo root; migrate files from
existing `Datasets/` during implementation.

**Rationale**: Constitution naming; lowercase path is friendlier in Linux
containers.

**Alternatives considered**: Keep `Datasets/` only — fine functionally; renamed
for consistency.

## 8. API shape

**Decision**: Small REST API under `/api/v1`: create/get session, upload
sources (multipart), list sources with previews, clear sources, ask question.
See `contracts/openapi.yaml`.

**Rationale**: Explicit FE↔BE contract; enough for Streamlit client without
GraphQL or websockets.

**Alternatives considered**: WebSockets for streaming tokens — nicer UX, extra
complexity; defer. Sync request/response is enough for Week 0.

## 9. CORS and security baseline

**Decision**: Backend enables CORS for the frontend origin(s). No user auth in
v1 (per spec). Rate limiting / API keys between FE and BE optional later; for
AWS, prefer private networking or at least not exposing Anthropic key to the
frontend (key only on backend).

**Rationale**: Spec out-of-scopes login; constitution requires secrets not in
frontend/git/images.
