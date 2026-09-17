# Hello Agent frontend — Streamlit UI
# Build:  docker build -t hello-agent-frontend .
# Run:    docker run --rm -p 8501:8501 -e BACKEND_URL=http://host.docker.internal:8000 hello-agent-frontend
# Compose: BACKEND_URL=http://backend:8000
# Never put ANTHROPIC_API_KEY in this image — backend only.

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8501 \
    BACKEND_URL=http://localhost:8000 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser

# Frontend is not an installable package (tool.uv.package = false); install deps explicitly.
COPY pyproject.toml README.md ./
RUN pip install --upgrade pip \
    && pip install "streamlit>=1.40.0" "httpx>=0.27.0"

COPY app.py api_client.py ./
COPY .streamlit ./.streamlit

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8501

# BACKEND_URL is overridable at runtime (Compose service name or ECS Express Mode HTTPS URL).
CMD ["sh", "-c", "exec streamlit run app.py --server.address=0.0.0.0 --server.port=${PORT}"]
