# syntax=docker/dockerfile:1

# ---- build -----------------------------------------------------------------
FROM python:3.12.11-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /build
RUN pip install --no-cache-dir uv==0.11.30

# Dependencies resolve in their own layer so application edits do not reinstall them.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app ./app
RUN uv sync --frozen --no-dev

# ---- runtime ---------------------------------------------------------------
FROM python:3.12.11-slim AS runtime

ARG GIT_SHA=unknown
LABEL org.opencontainers.image.source="https://github.com/devsecops-playground-org/arteamis-backend" \
      org.opencontainers.image.revision="${GIT_SHA}"

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# The service never needs to write to its own filesystem, and never runs as root.
RUN groupadd --system --gid 1001 app \
    && useradd --system --uid 1001 --gid app --no-create-home app

WORKDIR /srv
COPY --from=builder --chown=app:app /opt/venv /opt/venv
COPY --chown=app:app app ./app

USER app
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4).status == 200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
