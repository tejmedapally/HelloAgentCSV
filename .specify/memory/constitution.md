<!--
Sync Impact Report
- Version change: 1.0.0 → 1.1.0
- Modified principles: none (titles unchanged)
- Added sections: none
- Removed sections: none
- Amended: Delivery and Security Constraints — LLM provider OpenAI → Anthropic Claude API;
  secrets wording updated accordingly
- Follow-up TODOs: none
-->

# Hello Agent (CSV FAQ Agent) Constitution

## Core Principles

### I. Spec-Driven Development
All product and delivery work MUST follow Spec Kit artifacts before implementation:
constitution → specify → plan → tasks → implement. Code and infrastructure MUST
trace to an approved specification and plan. Ad-hoc features, folder layouts, or
deploy paths that contradict those artifacts MUST NOT ship until the constitution
or feature spec is amended.

**Rationale**: Keeps a warm-up project coherent when scope grows (UI, agent,
Docker, AWS) and prevents untraceable changes.

### II. Clean Separated Architecture
The repository MUST use a clear monorepo layout with distinct concerns, at minimum:
- `backend/` — API and agent/CSV reasoning logic
- `frontend/` — user-facing web UI
- `datasets/` (or equivalent) — sample/reference CSV data used for demos and tests

Frontend and backend MUST communicate through an explicit HTTP API contract.
Shared types/contracts SHOULD live in one agreed place (documented in the plan).
Application logic MUST NOT be dumped at the repository root except for thin
entrypoints, docs, and tooling config.

**Rationale**: Supports two deployable images, independent iteration, and a
maintainable path from mini-project to production-shaped delivery.

### III. Data-Only Answers (NON-NEGOTIABLE)
The agent MUST answer only from uploaded or provided CSV table content. It MUST
NOT invent facts from general world knowledge. When the data does not contain a
sufficient answer, the system MUST reply clearly that the information was not
found in the uploaded files. Model temperature MUST stay low (near-deterministic)
so behavior remains predictable and safe for support-style copy/paste use.

**Rationale**: Core business rule from the Week 0 brief; incorrect invented
policy/FAQ answers are worse than an explicit miss.

### IV. Containerized Dual-Image Delivery
The project MUST produce exactly two primary runtime Docker images: one for the
backend and one for the frontend. Images MUST be buildable from the repo,
publishable to AWS (for example ECR), and deployable so the frontend can reach
the backend in the target environment. Local development SHOULD provide a
compose or equivalent path that mirrors that split. Secrets and environment
config MUST be injected at runtime, never baked into images.

**Rationale**: Matches the stated delivery goal and forces production-shaped
boundaries early without requiring a microservices sprawl.

### V. Simplicity and Predictability
This is a Week 0 warm-up: prefer the simplest design that meets the brief.
MUST NOT introduce a vector database, complex RAG pipeline, or external
document/SQL database unless the constitution is amended. Code MUST remain easy
to read and change. The UI MUST be simple enough that a first-time support user
can upload CSVs, ask a question, and read an answer without long instructions.

**Rationale**: Learning goals prioritize end-to-end agent-on-tables flow over
infrastructure novelty.

## Delivery and Security Constraints

- **Product intent**: Internal tool "Hello Agent" for support agents, PMs, and
  ops to upload CSV FAQ/policy files and ask natural-language questions.
- **Required capabilities**: multi-CSV upload with preview; natural-language
  question input; answers grounded in CSV rows (text lookup or simple numeric
  aggregation when appropriate); clear English answers suitable to share.
- **Stack baseline (course brief adapted for available API access; refine in
  plan if split architecture requires adapters)**: Python; Pandas for CSV/data
  frames; LangChain dataframe agent pattern; Anthropic Claude chat model via
  the Claude API (for example a current Haiku or Sonnet model suitable for
  low-latency Q&A); simple web UI (Streamlit is the brief default and MAY be
  the frontend or a UI service). OpenAI MUST NOT be required for this project.
- **Secrets**: Anthropic (Claude) and AWS credentials MUST NOT be committed to
  git. Use environment variables or a secret store (for example
  `ANTHROPIC_API_KEY`). Example/dummy env files MUST NOT contain real keys.
- **AWS**: Publishing and running the two images on AWS is in scope for delivery
  planning; concrete service choice (ECS, App Runner, etc.) belongs in the
  technical plan, not as ad-hoc one-off scripts that bypass Spec Kit.

## Development Workflow

1. Amend this constitution when governance principles change; bump the version.
2. Capture or update product behavior with `/speckit-specify` (and clarify as
   needed) using `docs/requirements.pdf` and stakeholder input.
3. Capture architecture, stack choices, repo layout, Docker, and AWS with
   `/speckit-plan`.
4. Generate ordered work with `/speckit-tasks`; implement with
   `/speckit-implement`; verify with `/speckit-converge` / analyze / checklist
   as appropriate.
5. Reviews MUST check: data-only behavior, layout separation, two-image
   delivery path, and no secrets in the repo.

## Governance

This constitution supersedes informal practice for this repository. Amendments
MUST update `.specify/memory/constitution.md`, bump **Version** using semantic
versioning (MAJOR: incompatible principle removal/redefinition; MINOR: new or
materially expanded principle/section; PATCH: clarifications only), set
**Last Amended** to the amendment date, and note impact for open specs/plans.
Compliance is reviewed at plan, task, and implement gates: unjustified
violations MUST block merge or be explicitly waived in the plan with rationale.
Runtime feature detail lives in Spec Kit feature specs and plans under
`.specify/` / `specs/`; this file is governance only.

**Version**: 1.1.0 | **Ratified**: 2026-09-16 | **Last Amended**: 2026-09-16
