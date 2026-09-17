# Grounded FAQ — frontend

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

## Docker

```powershell
cd frontend
docker build -t hello-agent-frontend .

# Backend on the host (Docker Desktop):
docker run --rm -p 8501:8501 -e BACKEND_URL=http://host.docker.internal:8000 hello-agent-frontend

# Backend as another container on Compose network (later T030):
# -e BACKEND_URL=http://backend:8000
```

`BACKEND_URL` is a **runtime** env var — do not bake production URLs or secrets into the image.
