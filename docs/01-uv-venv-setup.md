# 1. Install uv and Set Up a Python Virtual Environment

Step-by-step for **Windows PowerShell**. Run these yourself in a terminal.

## Prerequisites

- Windows PowerShell
- Project folder exists (this repo: `C:\Projects\IK\Week_0`)

---

## Step 1: Install uv

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Close and reopen the terminal (or open a new one) so `uv` is on your PATH.

## Step 2: Verify uv

```powershell
uv --version
```

You should see a version number. If not, restart the terminal and check that `%USERPROFILE%\.local\bin` is on PATH.

## Step 3: Go to the project root

```powershell
cd C:\Projects\IK\Week_0
```

## Step 4: Create the virtual environment (optional root venv)

A root `.venv` is optional. **Backend and frontend each have their own env** via `uv sync` in those folders (preferred for day-to-day work).

```powershell
uv venv
```

Optional — pin a Python version:

```powershell
uv venv --python 3.12
```

This creates a `.venv` folder in the project.

## Step 5: Activate the venv (PowerShell)

Only needed if you created a root `.venv` and want to use it directly:

```powershell
.\.venv\Scripts\Activate.ps1
```

If you get an execution-policy error:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then activate again. Your prompt should show something like `(Week_0)`.

With `uv run` / `uv sync` in `backend/` or `frontend/`, activation is usually unnecessary.

## Step 6: Confirm the venv is active

```powershell
python -c "import sys; print(sys.executable)"
```

The path should include `.venv\Scripts\python.exe`.

## Step 7: Install packages

### Preferred — sync each service from its `pyproject.toml`

```powershell
cd C:\Projects\IK\Week_0\backend
uv sync --system-certs

cd C:\Projects\IK\Week_0\frontend
uv sync --system-certs
```

Omit `--system-certs` if your network does not need it. You can also set for the session:

```powershell
$env:UV_SYSTEM_CERTS = "1"
```

### Ad-hoc install into the active env

```powershell
uv pip install --system-certs <package-name>
```

---

## Step 8: Create `.env` files

From the repo root:

```powershell
cd C:\Projects\IK\Week_0
copy backend\.env.example backend\.env
copy frontend\.env.example frontend\.env
```

Edit **`backend\.env`** and set your Anthropic key (backend only — never put this in the frontend):

```text
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

`frontend\.env` can keep the default:

```text
BACKEND_URL=http://localhost:8000
```

Do **not** commit real keys (`.env` is gitignored).

---

## Step 9: Run the backend and frontend

Use **two terminals**. Start the backend first.

### Terminal A — backend (FastAPI)

```powershell
cd C:\Projects\IK\Week_0\backend
uv sync --system-certs
uv run --system-certs uvicorn app.main:app --reload --port 8000
```

Alternative if the key is not in `.env`:

```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-your-key-here"
uv run --system-certs uvicorn app.main:app --reload --port 8000
```

**Useful URLs (backend running):**

| URL | Purpose |
|-----|---------|
| http://127.0.0.1:8000/ | Short “API is at /api/v1” message |
| http://127.0.0.1:8000/api/v1/health | Health check → `{"status":"ok"}` |
| http://127.0.0.1:8000/docs | Interactive Swagger UI (Try it out) |
| http://127.0.0.1:8000/redoc | Read-only API docs |

### Terminal B — frontend (Streamlit)

```powershell
cd C:\Projects\IK\Week_0\frontend
uv sync --system-certs
uv run --system-certs streamlit run app.py
```

Streamlit usually opens http://localhost:8501.

**Expected flow:** Upload a CSV from `datasets/` → Ask a question → copy the answer.

---

## Common issues

| Symptom | What to do |
|---------|------------|
| `UnknownIssuer` / SSL errors from `uv` | Use `--system-certs` or `$env:UV_SYSTEM_CERTS = "1"` |
| Ask fails: `ANTHROPIC_API_KEY is not set` | Put the key in `backend\.env`, then **restart** uvicorn |
| Ask fails: `Import tabulate failed` | From `backend/`: `uv sync --system-certs` (or `uv add tabulate --system-certs`), restart backend |
| `Session not found` | Sessions are in-memory; restarting the backend clears them. Create a new session and re-upload CSVs |
| `GET /` or `/json/version` in logs | Harmless probes; `/` is handled. Ignore leftover 404s for unknown paths |
| Frontend cannot reach backend | Confirm uvicorn is on port 8000 and `frontend\.env` has `BACKEND_URL=http://localhost:8000` |

---

## Deactivate (when using an activated root venv)

```powershell
deactivate
```

## Notes

- `.venv` should **not** be committed to Git (keep it in `.gitignore`).
- Prefer `uv sync` / `uv run` inside `backend/` and `frontend/` over a single shared root env for app work.
- Full product checks: [`specs/001-csv-faq-agent/quickstart.md`](../specs/001-csv-faq-agent/quickstart.md).
- Spec Kit workflow: [`02-speckit-setup.md`](02-speckit-setup.md).
- Git/GitHub: [`03-git-github-setup.md`](03-git-github-setup.md).
