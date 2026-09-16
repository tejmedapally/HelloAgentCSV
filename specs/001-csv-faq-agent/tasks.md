# Tasks: Hello Agent CSV FAQ

**Input**: Design documents from `/specs/001-csv-faq-agent/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Optional — not explicitly requested in the feature specification; omit TDD tasks. Validate via `quickstart.md` in Polish.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/app/`, `frontend/`, `datasets/` per plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create monorepo directories `backend/app/api/`, `backend/app/models/`, `backend/app/services/`, `backend/tests/`, `frontend/`, and `datasets/` at repository root
- [x] T002 Move sample CSVs from `Datasets/` into `datasets/` (`ecommerce_faqs.csv`, `credit_card_terms.csv`, `hospital_policy.csv`, `saas_docs.csv`) and leave a short note in `Datasets/README.md` pointing to `datasets/` (or remove empty `Datasets/` if unused)
- [x] T003 [P] Initialize backend Python project with FastAPI, Uvicorn, Pandas, LangChain, langchain-experimental, langchain-anthropic, python-multipart in `backend/pyproject.toml` (or `backend/requirements.txt`)
- [x] T004 [P] Initialize frontend Python project with Streamlit and httpx in `frontend/pyproject.toml` (or `frontend/requirements.txt`)
- [x] T005 [P] Add root `.gitignore` entries for `.venv/`, `__pycache__/`, `.env`, `.streamlit/secrets.toml`, and Docker override files; add `backend/.env.example` and `frontend/.env.example` without real secrets
- [x] T006 [P] Add root `README.md` describing Hello Agent layout (`backend/`, `frontend/`, `datasets/`) and pointer to `specs/001-csv-faq-agent/quickstart.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T007 Implement settings loader for `ANTHROPIC_API_KEY`, model name, temperature, preview row count, and max upload size in `backend/app/config.py`
- [x] T008 [P] Implement in-memory session store (create/get/delete session, attach sources) in `backend/app/services/session_store.py` per `specs/001-csv-faq-agent/data-model.md`
- [x] T009 [P] Define Pydantic schemas for Session, SourcePublic, AskRequest, AskResponse, and Error in `backend/app/models/schemas.py` aligned with `specs/001-csv-faq-agent/contracts/openapi.yaml`
- [x] T010 Create FastAPI app entry with CORS, router include, and `GET /api/v1/health` in `backend/app/main.py` and `backend/app/api/routes.py`
- [x] T011 Implement session create/get handlers (`POST /api/v1/session`, `GET /api/v1/session`) with `X-Session-Id` support in `backend/app/api/routes.py`
- [x] T012 Add frontend HTTP client skeleton (session create/get, base URL from `BACKEND_URL`) in `frontend/api_client.py`
- [x] T013 Add minimal Streamlit shell that creates/stores a session id and shows connection/health status in `frontend/app.py`

**Checkpoint**: Foundation ready — health works; session can be created; FE can reach BE; user story implementation can begin

---

## Phase 3: User Story 1 - Ask a question after uploading CSVs (Priority: P1) 🎯 MVP

**Goal**: With at least one CSV available in the session, user can ask a natural-language question and get a clear English data-only answer or an explicit not-found/error message.

**Independent Test**: Load sample CSV(s) into a session, ask a question present in the data (grounded answer) and one absent (not-found); confirm no invented world-knowledge answers when data is missing.

### Implementation for User Story 1

- [x] T014 [P] [US1] Implement CSV parse-to-DataFrame helper and preview extraction in `backend/app/services/csv_service.py`
- [x] T015 [P] [US1] Implement Claude + LangChain pandas dataframe agent with data-only system prompt and low temperature in `backend/app/services/agent_service.py`
- [x] T016 [US1] Wire minimal upload path `POST /api/v1/sources` (multipart) into session store using `csv_service` in `backend/app/api/routes.py` (enough for MVP ask flow)
- [x] T017 [US1] Implement `POST /api/v1/ask` to refuse empty sessions, invoke `agent_service`, and return `AskResponse` (`ok` | `not_found` | `error`) in `backend/app/api/routes.py`
- [x] T018 [US1] Extend `frontend/api_client.py` with `upload_sources` and `ask` methods matching the OpenAPI contract
- [x] T019 [US1] Add Streamlit controls in `frontend/app.py` to upload at least one CSV, enter a question, submit ask, and display answer text

**Checkpoint**: User Story 1 is fully functional and testable independently (upload → ask → grounded or not-found answer)

---

## Phase 4: User Story 2 - Upload and preview CSV files (Priority: P2)

**Goal**: Users can upload one or many CSVs, see previews and active source list, clear sources, and get clear errors for invalid files.

**Independent Test**: Upload one CSV and multiple CSVs with previews; attempt invalid non-CSV and confirm error without crashing; clear sources and confirm ask refuses until new uploads.

### Implementation for User Story 2

- [ ] T020 [P] [US2] Harden CSV validation (empty rows, size limit, non-CSV) with clear error messages in `backend/app/services/csv_service.py`
- [ ] T021 [US2] Complete sources API: `GET /api/v1/sources`, `DELETE /api/v1/sources`, multi-file upload behavior, and public preview payloads in `backend/app/api/routes.py`
- [ ] T022 [US2] Extend `frontend/api_client.py` with `list_sources` and `clear_sources`
- [ ] T023 [US2] Update `frontend/app.py` to show per-file previews, active source filenames, multi-file upload, clear-all action, and upload error display

**Checkpoint**: User Stories 1 and 2 both work; multi-upload + preview + clear are solid

---

## Phase 5: User Story 3 - First-time usable simple interface (Priority: P3)

**Goal**: First-time users understand upload → ask → answer without a manual; answers are easy to copy.

**Independent Test**: New user completes the flow using only on-screen labels; answer text is selectable/copyable in one straightforward action.

### Implementation for User Story 3

- [ ] T024 [P] [US3] Add concise on-screen instructions and clear section headings (Upload, Ask, Answer) in `frontend/app.py`
- [ ] T025 [P] [US3] Tune Streamlit layout/theme defaults for a clean simple UI in `frontend/.streamlit/config.toml`
- [ ] T026 [US3] Make answer area copy-friendly (full text visible, code/text block or equivalent) and show answer `status` subtly in `frontend/app.py`
- [ ] T027 [US3] Disable or guard Ask when no sources are active with an inline prompt to upload first in `frontend/app.py`

**Checkpoint**: All three user stories independently functional; UI is self-explanatory

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Containers, AWS delivery, docs, and end-to-end validation

- [ ] T028 [P] Add backend container build in `backend/Dockerfile` (non-root where practical; `ANTHROPIC_API_KEY` only via runtime env)
- [ ] T029 [P] Add frontend container build in `frontend/Dockerfile` with `BACKEND_URL` runtime env
- [ ] T030 Add `docker-compose.yml` at repo root wiring backend + frontend and documenting required env vars
- [ ] T031 [P] Document ECR push steps for both images in `docs/aws-deploy.md`
- [ ] T032 Document AWS App Runner deploy for backend and frontend (frontend `BACKEND_URL` → backend HTTPS URL; secrets on backend only) in `docs/aws-deploy.md`
- [ ] T033 Align root `README.md` and `specs/001-csv-faq-agent/quickstart.md` with final ports, compose commands, and env var names
- [ ] T034 Run quickstart validation scenarios A–G from `specs/001-csv-faq-agent/quickstart.md` locally (Compose or dual-terminal) and fix any gaps
- [ ] T035 Archive or clearly mark legacy stub `Hello_Agent_CSV_FAQ_Agent_(Stub_File).ipynb` as non-runtime so the supported path is `frontend/` + `backend/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — **BLOCKS** all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational — MVP
- **User Story 2 (Phase 4)**: Depends on Foundational; builds on US1 upload/ask surface
- **User Story 3 (Phase 5)**: Depends on Foundational; polish assumes ask UI from US1 and sources UI from US2
- **Polish (Phase 6)**: Depends on desired user stories (recommend all three before AWS publish)

### User Story Dependencies

- **User Story 1 (P1)**: After Foundational; includes minimal upload so ask is demoable alone
- **User Story 2 (P2)**: After Foundational; extends upload/preview/clear; should remain testable without US3 polish
- **User Story 3 (P3)**: After Foundational; primarily frontend UX; best after US1+US2 UI pieces exist

### Within Each User Story

- Services before route wiring
- Backend before frontend client/UI for the same capability
- Story complete before next priority when working solo

### Parallel Opportunities

- Phase 1: T003, T004, T005, T006 in parallel after T001
- Phase 2: T008 and T009 in parallel after T007; T012 can start once T010–T011 shapes are clear
- Phase 3: T014 and T015 in parallel; then T016→T017; then T018→T019
- Phase 4: T020 parallel with early client work only after API shape known; prefer T020→T021→T022→T023
- Phase 5: T024 and T025 in parallel; then T026, T027
- Phase 6: T028 and T029 in parallel; T031 can draft while images build

---

## Parallel Example: User Story 1

```text
# After Foundational checkpoint, in parallel:
Task: "T014 Implement CSV parse-to-DataFrame helper in backend/app/services/csv_service.py"
Task: "T015 Implement Claude + LangChain agent in backend/app/services/agent_service.py"

# Then sequentially:
Task: "T016 Wire POST /api/v1/sources in backend/app/api/routes.py"
Task: "T017 Implement POST /api/v1/ask in backend/app/api/routes.py"
Task: "T018 Extend frontend/api_client.py with upload_sources and ask"
Task: "T019 Add Streamlit upload/ask/answer UI in frontend/app.py"
```

---

## Parallel Example: User Story 3

```text
Task: "T024 Add on-screen instructions in frontend/app.py"
Task: "T025 Tune Streamlit defaults in frontend/.streamlit/config.toml"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: upload sample CSV → ask in-data and not-found questions
5. Demo locally before upload polish / AWS

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. US1 → MVP Q&A demo
3. US2 → multi-file preview and validation
4. US3 → first-time UX polish
5. Polish → Compose + ECR + App Runner

### Parallel Team Strategy

1. Team completes Setup + Foundational together
2. Then: Developer A on US1 backend agent/ask; Developer B on early Streamlit client shell; merge before US2
3. US2/US3 and Docker/AWS as follow-on

---

## Notes

- [P] tasks = different files, no incomplete-task dependencies
- [USn] label maps task to spec user story
- No OpenAI dependencies; Claude via `ANTHROPIC_API_KEY` on backend only
- Commit after each task or logical group
- Stop at checkpoints to validate independently
- Suggested MVP scope: **Phases 1–3 (through T019)**
