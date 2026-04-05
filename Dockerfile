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

# Stage 1 -> runner (minimal image, no build tools)
FROM python:3.14-slim-trixie

# Create a non-root user for running the application
RUN groupadd --system --gid 999 nonroot \
    && useradd --system --gid 999 --uid 999 --create-home nonroot

# Copy built application from builder stage
COPY --from=builder --chown=nonroot:nonroot /app /app

# Create the UDS mount point writable by nonroot
RUN mkdir -p /ipc && chown nonroot:nonroot /ipc

ENV PATH="/app/.venv/bin:$PATH"

USER nonroot

WORKDIR /app

# Overridden by docker compose (server.py / client.py)
CMD ["python", "main.py"]
