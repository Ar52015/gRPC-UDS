# gRPC-UDS

[![CI](https://github.com/Ar52015/gRPC-UDS/actions/workflows/ci.yml/badge.svg)](https://github.com/Ar52015/gRPC-UDS/actions/workflows/ci.yml)

Containerized client-server pipeline that streams raw 1080p RGB frames at 30 FPS between isolated Docker containers. All IPC goes through gRPC over a Unix Domain Socket via a shared Docker volume — no TCP.

## Architecture

```
Client Container (Sender)         Server Container (Receiver)
  Generate 1080p RGB arrays  ──►  Reconstruct via np.frombuffer()
  Drift-corrected 30 FPS         Measure latency per frame
         │                                │
         └── Unix Domain Socket ──────────┘
             Shared Docker Volume @ /ipc/grpc.sock
```

- **Client** — generates random `(1080, 1920, 3)` uint8 frames, serializes to protobuf, streams via client-side streaming RPC with drift-corrected rate limiting.
- **Server** — receives frames over UDS, reconstructs NumPy arrays via `np.frombuffer`, logs shape and per-frame latency, detects dropped frames.
- **Transport** — gRPC over Unix Domain Socket (`unix:///ipc/grpc.sock`). No TCP ports mapped. Message size limit raised to 8 MB (a single 1080p RGB frame is ~6 MB).
- **Orchestration** — Docker Compose with a shared named volume at `/ipc`.

## Prerequisites

- Python 3.14
- [uv](https://docs.astral.sh/uv/) (package manager)
- Docker + Docker Compose
- [docker-buildx](https://docs.docker.com/build/buildx/) (for BuildKit support)

## Quick Start

### Docker (recommended)

```bash
make build    # build container images
make up       # start both containers in detached mode
make logs     # tail logs from both containers
make down     # tear down the stack
```

### Local (without Docker)

```bash
make setup    # install dependencies + pre-commit hooks
make proto    # generate protobuf stubs

# Terminal 1
uv run python server.py

# Terminal 2
uv run python client.py
```

## Configuration

All settings are loaded via Pydantic `BaseSettings` from environment variables or `.env`:

| Variable | Default | Description |
|---|---|---|
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `GRPC_SOCKET_PATH` | `/ipc/grpc.sock` | UDS socket path |
| `MAX_MESSAGE_SIZE` | `8388608` | Max gRPC message size (bytes) |
| `TARGET_FPS` | `30` | Target frames per second |
| `MAX_CHANNEL_CONNECT_RETRIES` | `5` | Client retry attempts with exponential backoff |

For local testing, override `GRPC_SOCKET_PATH` in `.env`:

```
GRPC_SOCKET_PATH=/tmp/grpc.sock
```

## Makefile Targets

| Target | Description |
|---|---|
| `make setup` | Install deps and pre-commit hooks |
| `make sync` | Sync dependencies |
| `make proto` | Regenerate protobuf stubs |
| `make lint` | Run ruff linter |
| `make format` | Run ruff formatter |
| `make type-check` | Run mypy |
| `make verify` | Run all checks (lint, format, type-check, pre-commit) |
| `make build` | Build Docker images |
| `make up` | Build and start containers |
| `make down` | Tear down containers |
| `make logs` | Tail container logs |
| `make clean` | Nuke all containers, images, volumes, and caches |

## Project Structure

```
├── client.py              # Async gRPC frame sender
├── server.py              # Async gRPC frame receiver
├── config.py              # Pydantic settings from .env
├── app/utils/logger.py    # Color-coded logger factory
├── proto/schema.proto     # Protobuf service definition
├── proto_compile.sh       # Protobuf code generation script
├── generated/             # Generated protobuf stubs (gitignored)
├── Dockerfile             # Multi-stage build (builder + runner)
├── compose.yaml           # Docker Compose topology
├── Makefile               # Project automation
└── SCHEDULE.md            # Implementation roadmap
```

## CI

GitHub Actions runs on every push and PR to `main`:

1. **Lint & Type Check** — `ruff check`, `ruff format --check`, `hadolint`, `mypy`
2. **Build Images** — `docker compose build`
3. **Integration Smoke Test** — spins up both containers, verifies frames are received, tears down
