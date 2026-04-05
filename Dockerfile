# syntax=docker/dockerfile:1
# Stage 0 -> builder
FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim as builder

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_NO_DEV=1
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --locked --no-install-project

COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

RUN bash /app/proto_compile.sh

# Stage 1 -> runner
FROM python:3.14-slim-trixie

RUN groupadd --system --gid 999 nonroot \
    && useradd --system --gid 999 --uid 999 --create-home nonroot

COPY --from=builder --chown=nonroot:nonroot /app /app

RUN mkdir -p /ipc && chown nonroot:nonroot /ipc

ENV PATH="/app/.venv/bin:$PATH"

USER nonroot

WORKDIR /app

# TO BE OVERRIDEN BY DOCKER COMPOSE
CMD ["python", "main.py"]
