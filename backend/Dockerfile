# Hello Agent backend — FastAPI + Claude dataframe agent
# Build:  docker build -t hello-agent-backend .
# Run:    docker run --rm -p 8000:8000 -e ANTHROPIC_API_KEY=... hello-agent-backend
# Never bake ANTHROPIC_API_KEY into the image; inject it only at runtime.

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser

# Dependency metadata first for better layer caching
COPY pyproject.toml README.md ./
COPY app ./app

RUN pip install --upgrade pip \
    && pip install . \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Bind 0.0.0.0 for containers; PORT overridable (e.g. App Runner).
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
