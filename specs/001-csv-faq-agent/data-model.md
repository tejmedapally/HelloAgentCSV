# Data Model: Hello Agent CSV FAQ

**Feature**: `001-csv-faq-agent`  
**Date**: 2026-09-16

In-memory only (no persistent database). Entities map to backend session state.

## Session

| Field | Type | Rules |
|-------|------|--------|
| `id` | string (UUID) | Required; created on first contact; sent via cookie or `X-Session-Id` |
| `created_at` | datetime | Set on create |
| `sources` | list of Source | Active answer sources for this session |
| `updated_at` | datetime | Bumped on upload/clear/ask |

**Lifecycle**: Created when client starts or first API call without ID → used for
uploads and asks → destroyed on process restart or explicit clear/delete.
Multi-instance production note: multiple ECS Express Mode / Fargate tasks would not share
memory; Week 0 assumes single backend instance or sticky sessions. Document in
deploy notes; scale-out would need shared store (out of scope unless amended).

## Source (Uploaded CSV source)

| Field | Type | Rules |
|-------|------|--------|
| `id` | string (UUID) | Required |
| `filename` | string | Original upload name; shown in UI |
| `columns` | list of string | Header names after parse |
| `row_count` | int | ≥ 0 |
| `preview_rows` | list of object | First N rows (e.g. 5) as column→value maps for UI |
| `dataframe` | runtime only | Pandas DataFrame; not serialized to client |

**Validation**:
- Content-Type / extension must be CSV (or parseable as CSV).
- Must parse with header row; empty file or zero data rows → reject or mark
  unusable with clear error (no agent use).
- Max size soft limit (e.g. 5–10 MB) for warm-up; reject with clear message.

**Relationships**: Many Sources belong to one Session. Ask uses all Sources in
the session’s active set.

## Question

| Field | Type | Rules |
|-------|------|--------|
| `text` | string | Required; non-empty after trim |
| `session_id` | string | Must reference existing session |

Not stored long-term unless logging is added later (out of scope).

## Answer

| Field | Type | Rules |
|-------|------|--------|
| `text` | string | Clear English; copy-ready |
| `status` | enum | `ok` \| `not_found` \| `error` |
| `source_filenames` | list of string | Optional hint of which files were in the active set |

**Rules**:
- `ok`: grounded in uploaded table content (text or simple aggregate).
- `not_found`: model/service concludes data insufficient; fixed-style message.
- `error`: validation failure, no sources, or LLM/API failure — never invent
  business facts.

## Active source set

Derived: all `Source` records on the current `Session`. Clearing uploads empties
the set; subsequent asks must fail closed (prompt to upload) until new sources
exist.

## Sample dataset files (disk, not session)

Reference CSVs under `datasets/` for demos/tests (not auto-loaded into a session
unless the UI offers a “load sample” helper). Files:

- `ecommerce_faqs.csv`
- `credit_card_terms.csv`
- `hospital_policy.csv`
- `saas_docs.csv`

## State transitions

```text
[No session] --start--> [Empty session]
[Empty session] --upload valid CSV--> [Session with sources]
[Session with sources] --upload more--> [Session with sources]
[Session with sources] --clear--> [Empty session]
[Empty session] --ask--> Error: upload required
[Session with sources] --ask--> Answer (ok | not_found | error)
```
