# Hello Agent — frontend

Streamlit UI that talks to the FastAPI backend over HTTP.

## Setup

```powershell
cd frontend
uv sync --system-certs
```

(Omit `--system-certs` if your network does not need it.)

## Run (after later tasks add `app.py`)

```powershell
$env:BACKEND_URL = "http://localhost:8000"
uv run streamlit run app.py
```
