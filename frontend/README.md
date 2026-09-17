# Hello Agent — frontend

Streamlit UI that talks to the FastAPI backend over HTTP.

## Setup

```powershell
cd frontend
copy .env.example .env
# Default: BACKEND_URL=http://localhost:8000
uv sync --system-certs
```

(Omit `--system-certs` if your network does not need it.)

## Run

Start the **backend** first (see `../backend/README.md`), then:

```powershell
uv run --system-certs streamlit run app.py
```

UI: http://localhost:8501  

Never put `ANTHROPIC_API_KEY` in the frontend — only `BACKEND_URL`.
