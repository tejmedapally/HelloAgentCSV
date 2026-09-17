# 2. Spec Kit (specify-cli) Setup and Commands

Step-by-step for this project using **Cursor** (`cursor-agent` integration) on **Windows PowerShell**.

## Prerequisites

- `uv` installed (see `01-uv-venv-setup.md`)
- Project root: `C:\Projects\IK\Week_0`
- Cursor IDE (for Spec Kit skills in Agent chat)
- Python 3.11+ recommended

---

## Part A — Install Spec Kit CLI

Spec Kit is a **global tool**, not something you install only inside the project venv.

### Install

```powershell
uv tool install --system-certs specify-cli
```

If SSL is fine without the flag:

```powershell
uv tool install specify-cli
```

### Verify

```powershell
specify --help
```

If `specify` is not found, open a **new** PowerShell window and try again.

---

## Part B — Initialize Spec Kit in this repo

From the project root (folder already has files, so use `--here --force`):

```powershell
cd C:\Projects\IK\Week_0
specify init --here --force --integration cursor-agent --script ps
```

| Flag | Meaning |
|------|---------|
| `--here` | Use current directory |
| `--force` | Allow non-empty folder |
| `--integration cursor-agent` | Cursor Agent skills (not Copilot, not Claude Code CLI) |
| `--script ps` | PowerShell helper scripts |

### Verify init

```powershell
Get-ChildItem .specify
Get-ChildItem .cursor\skills
```

You should see Spec Kit skills such as `speckit-constitution`, `speckit-specify`, `speckit-plan`, `speckit-tasks`, `speckit-implement`.

Optional check:

```powershell
Get-Content .specify\init-options.json
```

Confirm `"integration": "cursor-agent"` (or equivalent).

---

## Part C — Spec Kit workflow (in Cursor Agent chat)

Open the project root in Cursor. In **Agent** chat, run skills with `/` (names use hyphens).

### Order we used for Hello Agent

1. **Constitution** — project rules  

```text
/speckit-constitution
```

(Attach or mention constraints: backend/frontend, Claude API, two Docker images, AWS, data-only answers.)

2. **Specify** — what to build (product)  

```text
/speckit-specify
```

Attach `@docs/requirements.pdf` (or your requirements doc).

3. **Plan** — how to build (stack, layout, Docker, AWS)  

```text
/speckit-plan
```

Include tech choices (FastAPI + Streamlit, Claude, ECR/ECS Express Mode, etc.).

4. **Tasks** — ordered checklist  

```text
/speckit-tasks
```

Usually no extra arguments needed if plan/spec already exist.

5. **Implement** — prefer **one task at a time** (see Part D below)

### Optional quality gates

```text
/speckit-clarify
/speckit-checklist
/speckit-analyze
/speckit-converge
```

---

## Part D — Run each task one by one, review, then commit

Do **not** ask the agent to implement all of `tasks.md` at once. Work **one task ID**
per turn, review the diff, then commit before starting the next task.

Task list for this feature: `specs/001-csv-faq-agent/tasks.md`  
Do tasks in order: **T001 → T002 → T003 → …**  
User stories 1–3 are implemented through **T027**. Remaining work is Phase 6 polish (Docker/AWS/docs validation: T028+).

### Step 1: Ask the agent for only one task

In Cursor Agent chat, paste (change the ID each time):

```text
Implement ONLY task T001 from specs/001-csv-faq-agent/tasks.md.
Do not start T002 or any other task.
Follow plan.md and constitution.
When done, show which files changed and how to verify.
```

Or with Spec Kit:

```text
/speckit-implement
Only T001. Stop when T001 is done. Do not continue to other tasks.
```

### Step 2: Review what changed

In PowerShell from the project root:

```powershell
cd C:\Projects\IK\Week_0
git status
git diff
```

If files are already staged:

```powershell
git diff --staged
```

Check in Cursor’s Source Control / file diffs that only this task’s work appears.

### Step 3: Mark the task done in `tasks.md`

In `specs/001-csv-faq-agent/tasks.md`, change:

```text
- [ ] T001 ...
```

to:

```text
- [x] T001 ...
```

### Step 4: Stage and commit that task

Stage the files this task touched (prefer paths over `git add -A` when you can):

```powershell
git add path\to\changed\files
git add specs/001-csv-faq-agent/tasks.md
git status
git commit -m "T001: short description of what this task did"
```

Examples:

```powershell
git commit -m "T001: create monorepo directories"
git commit -m "T007: add backend config loader"
```

### Step 5: Push to GitHub (once remote is set up)

See `03-git-github-setup.md`. After the remote exists:

```powershell
git push
```

### Step 6: Next task

Repeat Steps 1–5 with **T002**, then **T003**, and so on.

Example next prompt:

```text
T001 looks good. Implement ONLY task T002 from specs/001-csv-faq-agent/tasks.md.
Do not start T003. Show files changed and how to verify.
```

### Loop summary

```text
Ask for T00N only → review git status/diff → mark [x] in tasks.md
→ git add → git commit -m "T00N: ..." → git push → next ID
```

### Tips

- One task ID per Agent message keeps reviews small and safe.
- If the agent touches files beyond the task, ask it to revert extras or only commit the intended paths.
- Do not skip Phase 2 (Foundational) before user-story tasks.
- After Foundational (T013) or MVP (T019), run a quick manual check before continuing (see `specs/001-csv-faq-agent/quickstart.md` when the app exists).

---

## Part E — Where artifacts live

| Path | Purpose |
|------|---------|
| `.specify/memory/constitution.md` | Project governance |
| `specs/001-csv-faq-agent/spec.md` | Feature specification |
| `specs/001-csv-faq-agent/plan.md` | Implementation plan |
| `specs/001-csv-faq-agent/tasks.md` | Task checklist |
| `.cursor/skills/` | Spec Kit skills for Cursor |
| `.specify/feature.json` | Active feature directory |

---

## Cursor vs Claude Code vs Copilot

| You want | Use |
|----------|-----|
| Spec Kit inside **Cursor** (this project) | `--integration cursor-agent` |
| Spec Kit with **Claude Code CLI** | `--integration claude` |
| Spec Kit with **GitHub Copilot** | `--integration copilot` |

Claude **API** for the Hello Agent app (`ANTHROPIC_API_KEY`) is separate from Spec Kit’s `--integration` flag.

---

## Useful reference links

- Spec Kit: https://github.com/github/spec-kit  
- Quick start: https://github.github.io/spec-kit/quickstart.html  
