# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python project implementing containerized client-server architecture for streaming 1080p RGB images at 30 FPS using gRPC over Unix Domain Sockets (UDS) via shared Docker volumes. No TCP — all IPC goes through a shared socket at `/ipc/grpc.sock`.

## Development Setup

- **Python 3.14** managed via `uv`
- **Package manager:** `uv` (not pip)
- Install dependencies: `uv sync`
- Add a dependency: `uv add <package>`
- Add a dev dependency: `uv add --dev <package>`

## Commands

- **Lint:** `uv run ruff check --fix`
- **Format:** `uv run ruff format`
- **Type check:** `uv run mypy .`
- **Run pre-commit hooks:** `pre-commit run --all-files`

## Pre-commit Hooks

Commits are gated by pre-commit hooks that run: trailing-whitespace fix, end-of-file fix, YAML/TOML validation, hadolint (Dockerfile linting), ruff check+format, and mypy. All must pass before a commit succeeds.

## Architecture

```
Client Container (Sender)         Server Container (Receiver)
  Generate 1080p RGB arrays  ──►  Reconstruct via np.frombuffer()
  Serialize & send via gRPC       Measure latency per frame
         │                                │
         └── Unix Domain Socket ──────────┘
             Shared Docker Volume @ /ipc/grpc.sock
```

- **Config:** `config.py` — Pydantic `BaseSettings` loading from `.env`
- **Logger:** `app/utils/logger.py` — color-coded logger factory, reads `LOG_LEVEL` from config
- **Proto/gRPC:** Not yet implemented (see `SCHEDULE.md` for Phase 1 tasks)

## Interaction Rules

- Do NOT provide, suggest, or write any code unless the user explicitly asks for it. Discuss, explain, and plan — but no code until requested.

## Code Style

- Ruff rules: `E`, `F`, `I` (isort), `UP` (pyupgrade), `NPY` (NumPy)
- Target Python version for ruff: 3.14
- Strict mypy type checking
