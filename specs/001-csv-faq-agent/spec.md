# Feature Specification: Hello Agent CSV FAQ

**Feature Branch**: `001-csv-faq-agent`

**Created**: 2026-09-16

**Status**: Draft

**Input**: User description: "Build Hello Agent per docs/requirements.pdf — a CSV FAQ web tool where users upload one or more CSV files, ask natural-language questions, and receive answers grounded only in that tabular data (not general knowledge), with a simple UI for support-style use."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ask a question after uploading CSVs (Priority: P1)

A customer support agent opens Hello Agent, uploads one or more CSV files that contain FAQs, policies, or product documentation, confirms the files look right via a short preview, types a natural-language question (for example about returns, warranties, visiting hours, or plan limits), and receives a clear English answer they can copy into email or chat. The answer is based on the uploaded tables only.

**Why this priority**: This is the core business value — replace manual searching in CSV rows with a fast, consistent answer.

**Independent Test**: With sample business CSVs uploaded, ask a question whose answer appears in the data and verify a clear, data-grounded reply is shown; ask a question with no matching data and verify an explicit not-found message.

**Acceptance Scenarios**:

1. **Given** the agent has uploaded at least one valid CSV, **When** they submit a question whose answer exists in the uploaded data, **Then** the system shows a clear English answer derived from that data (text excerpt or simple numeric summary as appropriate).
2. **Given** the agent has uploaded at least one valid CSV, **When** they submit a question that cannot be answered from the uploaded data, **Then** the system states clearly that the information was not found in the uploaded files (or equivalent wording).
3. **Given** the agent has uploaded multiple CSVs covering different domains, **When** they ask a question relevant to only one domain, **Then** the system answers from the relevant uploaded content without inventing facts from outside the files.

---

### User Story 2 - Upload and preview CSV files (Priority: P2)

A support agent, product manager, or operations staff member uploads one or many CSV files from their machine. For each file, the app shows a small preview (for example the first few rows) so they can confirm they uploaded the right export before asking questions.

**Why this priority**: Upload and preview are required before trustworthy Q&A; without them the agent cannot use current policy/FAQ exports.

**Independent Test**: Upload one CSV and multiple CSVs; confirm each appears with a short preview; reject or clearly error on clearly invalid non-CSV content without crashing the session.

**Acceptance Scenarios**:

1. **Given** the user is on the Hello Agent screen, **When** they upload one CSV file, **Then** the system accepts it and shows a small preview of that file.
2. **Given** the user already has one file uploaded, **When** they upload additional CSV files, **Then** each file is accepted and previewed so they can see all active sources.
3. **Given** the user selects a file that is not a usable CSV, **When** upload is attempted, **Then** the system shows a clear error and does not treat the file as a valid data source for answers.

---

### User Story 3 - First-time usable simple interface (Priority: P3)

A first-time user who has not read a long manual can tell what to do next: add files, ask a question, and read the answer. The layout is simple and clean; answers are presented in a way that is easy to copy for customer communication.

**Why this priority**: The brief requires an obvious UI so the tool is usable under time pressure (phone/chat support).

**Independent Test**: A new user completes upload → question → answer without external instructions; answer text is selectable/copyable.

**Acceptance Scenarios**:

1. **Given** a first-time user opens the app, **When** they view the main screen, **Then** the primary actions (upload files, enter question, get answer) are obvious without lengthy instructions.
2. **Given** an answer has been generated, **When** the user views it, **Then** they can easily copy the answer text for use in email or chat.

---

### Edge Cases

- User asks a question before any CSV is uploaded — system MUST prompt them to upload files first and MUST NOT invent an answer.
- Uploaded CSV is empty or has headers but no data rows — system MUST explain that there is no usable data and MUST NOT fabricate content.
- Question is ambiguous across multiple uploaded files — system SHOULD prefer the most relevant rows or state uncertainty while still not using outside knowledge.
- Very large CSV relative to a warm-up demo — system SHOULD remain usable for the provided sample-scale files; oversized files MAY be rejected or warned with a clear message.
- Model or language service unavailable — system MUST show a clear failure message rather than a partial invented answer.
- User replaces or clears uploads mid-session — subsequent answers MUST use only the currently active uploaded set.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Users MUST be able to upload one or many CSV files from their local machine in a single session.
- **FR-002**: For each successfully uploaded CSV, the system MUST show a small preview (for example the first few rows).
- **FR-003**: Users MUST be able to enter a natural-language question in a text input and submit it for an answer.
- **FR-004**: The system MUST generate answers using only content from the currently uploaded CSV data (row text and, when appropriate, simple calculations such as totals or averages over that data).
- **FR-005**: The system MUST NOT answer from general world knowledge or invent policies, FAQs, or figures that are not supported by the uploaded files.
- **FR-006**: When the uploaded data does not contain a sufficient answer, the system MUST reply with a clear not-found message (for example that the information could not be found in the uploaded files).
- **FR-007**: Answers MUST be returned in clear English suitable to copy into customer email or chat.
- **FR-008**: The user interface MUST be simple and self-explanatory for a first-time internal user (upload, ask, read answer).
- **FR-009**: If the user submits a question with no valid uploaded CSV data, the system MUST refuse to answer from outside knowledge and MUST instruct the user to upload files.
- **FR-010**: Answer behavior MUST be predictable and conservative (no creative or speculative replies); the experience MUST feel safe for support use on small business CSV exports.
- **FR-011**: The product MUST support the sample business domains represented by the course datasets (ecommerce FAQs, credit card terms, hospital policy, SaaS documentation) when those files are uploaded by the user.
- **FR-012**: Users MUST be able to see which files are currently active as answer sources for the session.

### Key Entities

- **Uploaded CSV source**: A user-provided tabular file in the current session; identified by name; contains columns and rows of business text or numbers; has a short preview for confirmation.
- **Question**: Natural-language text submitted by the user against the active uploaded sources.
- **Answer**: System response in clear English, either grounded in one or more relevant rows / simple aggregates from the active sources, or an explicit not-found / error message.
- **Active source set**: The collection of successfully uploaded CSVs that answers may use until the user changes uploads.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A typical support user can upload sample CSV files, ask a question present in the data, and see a usable answer in under 3 minutes on first use without a manual.
- **SC-002**: For a fixed set of at least 8 representative questions whose answers appear in the sample CSVs, at least 7 of 8 answers are judged by a reviewer as correctly grounded in the file content (not invented).
- **SC-003**: For at least 3 questions that have no supporting rows in the uploaded files, 100% of responses clearly indicate the information was not found (no fabricated policy/FAQ content).
- **SC-004**: On the provided sample-scale CSV files, users perceive the ask → answer flow as responsive for interactive support use (no multi-minute waits under normal conditions).
- **SC-005**: In a first-use walkthrough, at least 9 of 10 testers correctly identify how to upload files and submit a question without being given written instructions beyond the on-screen UI.
- **SC-006**: Generated answers are copy-ready: testers can copy the full answer text in one straightforward action for pasting into email or chat.

## Assumptions

- This is a Week 0 warm-up internal tool; login, roles, and multi-tenant isolation are out of scope for this feature version unless later specified.
- Uploaded files and Q&A context are session-scoped (not a long-term document management system); persistence across days is out of scope.
- Sample CSVs supplied with the course (ecommerce FAQs, credit card terms, hospital policy, SaaS docs) are the primary validation datasets; users may also upload their own similarly structured CSVs.
- No vector search catalog, complex retrieval product, or external business database is required for this feature; tabular file content in the session is sufficient.
- A configured language-model service credential will be available at runtime (provider choice is governed by the project constitution and detailed in planning, not in this product spec).
- Exact UI toolkit and service topology (single surface vs separated UI and processing service) are planning concerns; this specification defines user-visible behavior only.
- Numeric questions are limited to straightforward aggregates over the uploaded tables (for example totals or averages), not advanced analytics or forecasting.
- Mobile-native apps are out of scope; a standard web browser experience is sufficient.
