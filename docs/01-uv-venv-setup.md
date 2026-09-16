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

## Step 4: Create the virtual environment

```powershell
uv venv
```

Optional — pin a Python version:

```powershell
uv venv --python 3.12
```

This creates a `.venv` folder in the project.

## Step 5: Activate the venv (PowerShell)

```powershell
.\.venv\Scripts\Activate.ps1
```

If you get an execution-policy error:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then activate again. Your prompt should show something like `(Week_0)`.

## Step 6: Confirm the venv is active

```powershell
python -c "import sys; print(sys.executable)"
```

The path should include `.venv\Scripts\python.exe`.

## Step 7: Install packages later (when needed)

With the venv active:

```powershell
uv pip install <package-name>
```

Example (app dependencies — only when you start implementing):

```powershell
uv pip install fastapi uvicorn pandas langchain langchain-experimental langchain-anthropic python-multipart streamlit httpx
```

Or use project files when they exist:

```powershell
cd backend
uv sync
```

## Deactivate (when done)

```powershell
deactivate
```

## Notes

- `.venv` should **not** be committed to Git (keep it in `.gitignore`).
- If `uv` fails to reach PyPI with `invalid peer certificate: UnknownIssuer`, retry with:

```powershell
uv pip install --system-certs <package>
# or for tools:
uv tool install --system-certs <tool-name>
```

You can also set for the session:

```powershell
$env:UV_SYSTEM_CERTS = "1"
```
