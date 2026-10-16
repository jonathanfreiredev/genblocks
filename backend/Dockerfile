# syntax=docker/dockerfile:1

FROM python:3.14-slim AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install dependencies first so this layer is cached unless the lockfile changes.
COPY pyproject.toml uv.lock ./

# --- development image (all deps; used by docker-compose.override.yml) ---
FROM base AS dev
RUN uv sync --frozen
COPY . .
CMD ["fastapi", "dev", "--host", "0.0.0.0", "--port", "8000"]

# --- production build (runtime deps only) ---
FROM base AS build
RUN uv sync --frozen --no-dev
COPY . .

FROM python:3.14-slim AS runtime

WORKDIR /app

RUN useradd --create-home --uid 1000 appuser

COPY --from=build --chown=appuser:appuser /app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
