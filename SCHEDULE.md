# Phase 1: High-Performance IPC & Hardware Isolation

**The Validation Task**:
> To validate Phase 1, the developer must engineer a containerized client-server topology. Container A will run a Python process that generates randomized 1080p RGB image matrices. Container B will host a Python gRPC server. Both containers must be orchestrated via Docker Compose, sharing a mounted volume to facilitate a Unix Domain Socket connection. Container A must stream the raw binary image data to Container B over the UDS gRPC channel at a sustained rate of thirty requests per second. Container B must receive the payload, reconstruct the NumPy array, and print the tensor shape and execution latency. This project proves mastery of hardware isolation, binary contracts, and optimized IPC.

This schedule simulates a **systems engineering stress test**. You are building a zero-network, hardware-accelerated Inter-Process Communication (IPC) pipeline.
**Goal**: Prove absolute mastery over Docker volume mounting, binary serialization contracts, and asynchronous Python streaming.

---

## Day 0: Tooling & Foundations
**Focus**: Pre-commit Hooks, Logging, Project Config, Dependencies
**Load**: Level 2

- **Tasks**:
    - [x] Install and configure `uv` as the project package manager.
    - [x] Initialize `uv` project with Python 3.14 (`uv init`, `pyproject.toml`, `.python-version`, `uv.lock`).
    - [x] Configure pre-commit hooks (`.pre-commit-config.yaml`):
        - `trailing-whitespace`, `end-of-file-fixer`, `check-yaml`, `check-toml`
        - `hadolint-docker` for Dockerfile linting
        - Local hooks: `ruff check --fix`, `ruff format`, `mypy .` (all via `uv run`)
    - [x] Configure ruff rules: `E`, `F`, `I` (isort), `UP` (pyupgrade), `NPY` (NumPy).
    - [x] Configure strict mypy type checking (`[tool.mypy]` in `pyproject.toml` with `strict = true`).
    - [x] Build `config.py` — Pydantic `BaseSettings` loading `LOG_LEVEL` from `.env`.
    - [x] Build `app/utils/logger.py` — color-coded logger factory using `colorlog`:
        - DEBUG (blue), INFO (green), WARNING (yellow), ERROR (red), CRITICAL (bold_red)
        - Format: `%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s`
    - [x] Add `__init__.py` files to `app/` and `app/utils/` so modules are importable from any working directory (required for Docker).
    - [x] Resolve `.env` tracking — either remove `.env` from `.gitignore` (safe for this project) or stop tracking it with `git rm --cached .env`.
    - [x] Install core dependencies: `grpcio`, `grpcio-tools`, `pydantic-settings`, `colorlog`.

---

## Day 1: The Binary Contract
**Focus**: Protobuf Design & Code Generation
**Load**: Level 3

- **Objectives**:
    1. Define a strict binary contract for a 1080p RGB matrix payload using client-side streaming.
    2. Set up repeatable proto compilation and integrate generated files into the project cleanly.

- **Tasks**:
    - [x] Write `schema.proto` defining a client-side streaming RPC service:
        - `FrameRequest` message: `bytes frame_data`, `uint32 width`, `uint32 height`, `uint32 channels`, `uint64 frame_number`, `double timestamp`
        - `StreamSummary` response: `uint64 frames_received`, `double avg_latency_ms`
        - `rpc StreamFrames(stream FrameRequest) returns (StreamSummary)`
        - Note: `frame_number` is a monotonically increasing sequence ID used for drop detection.
        - Note: `timestamp` uses `time.time()` (wall clock), not `perf_counter()`, since sender and receiver are separate processes in separate containers. Docker containers share the host clock so wall-clock deltas are valid.
    - [ ] Write a `proto_compile.sh` script to invoke `uv run python -m grpc_tools.protoc` for repeatable codegen.
    - [ ] Compile the `.proto` file into Python `_pb2.py` and `_pb2_grpc.py` stubs.
    - [ ] Add generated `_pb2.py` / `_pb2_grpc.py` patterns to `.gitignore` (they are build artifacts, regenerated from the `.proto` source via `proto_compile.sh`).
    - [ ] Exclude generated `_pb2.py` / `_pb2_grpc.py` files from ruff and mypy (update `pyproject.toml` excludes).
    - [ ] Ensure `__init__.py` files exist in any package directories so generated stubs and app modules are importable.
    - [ ] Verify the generated stubs import cleanly: `uv run python -c "import schema_pb2; import schema_pb2_grpc"`.
    - [ ] Add `numpy` as a project dependency (`uv add numpy`) — needed for local testing in Day 3 before Docker is involved.

- **Acceptance Criteria**:
    - The compiled protobuf files exist and can be imported without `ModuleNotFoundError`.
    - Running `proto_compile.sh` regenerates the stubs idempotently.
    - Generated `_pb2` files are gitignored and do not trigger pre-commit hook failures.

- **Resources**:
    - [gRPC Python Quickstart & Compilation](https://grpc.io/docs/languages/python/quickstart/)
    - [Protocol Buffers Language Guide (proto3)](https://protobuf.dev/programming-guides/proto3/)

---

## Day 2: The Topology
**Focus**: Dockerfiles, Docker Compose, Shared Volumes, UDS Plumbing
**Load**: Level 4

- **Objectives**:
    1. Containerize both services with proper Dockerfiles.
    2. Engineer the Docker Compose topology to completely isolate the network while sharing a physical file structure.
    3. Verify the UDS volume mount works between containers.

- **Tasks**:
    - [ ] Write `.dockerignore` to exclude `.venv/`, `.git/`, `.mypy_cache/`, `.ruff_cache/`, `__pycache__/`, etc. from build context.
    - [ ] Write `Dockerfile.sender` for the client container (Python 3.14, `uv sync`, copies app code, runs `proto_compile.sh` during build).
    - [ ] Write `Dockerfile.receiver` for the server container (Python 3.14, `uv sync`, copies app code, runs `proto_compile.sh` during build).
    - [ ] Write `docker-compose.yml` defining `sender` and `receiver` services:
        - No port mappings whatsoever — all IPC goes through the UDS.
        - Shared host volume: `./shared_socket:/ipc` mounted in both containers.
    - [ ] The client's retry logic (Day 3) handles the startup race — no `depends_on` health check needed for the socket itself.
    - [ ] Add config entries for gRPC settings: `GRPC_SOCKET_PATH`, `MAX_MESSAGE_SIZE`, `TARGET_FPS` to `config.py` / `.env`.
    - [ ] **Blocker**: Do not map any standard TCP network ports (`50051`). No `network_mode: host`.

- **Acceptance Criteria**:
    - Running `docker compose up -d` successfully spins up both containers.
    - Creating a dummy file in Container A's `/ipc` folder makes it instantly visible in Container B's `/ipc` folder.
    - `docker compose down` cleanly tears down both containers.
    - Hadolint pre-commit hook passes on both Dockerfiles.
    - Docker build completes in reasonable time (`.dockerignore` excludes bloat).

- **Resources**:
    - [Docker Compose Volumes Documentation](https://docs.docker.com/compose/compose-file/05-services/#volumes)
    - [Dockerfile Best Practices](https://docs.docker.com/build/building/best-practices/)

---

## Day 3: The Server & The Client
**Focus**: gRPC AsyncIO, NumPy Serialization, Message Size Limits
**Load**: Level 5

- **Objectives**:
    1. Build the async gRPC server that ingests frames over UDS and reconstructs NumPy arrays.
    2. Build the async gRPC client that generates and streams 1080p frames.
    3. Handle the gRPC 4MB default message size limit (a single 1080p RGB frame is ~6MB).

- **Tasks**:

    **Server (`receiver`)**
    - [ ] Check for and remove a stale socket file (`os.unlink()`) before binding — prevents `Address already in use` on restart after a crash.
    - [ ] Bind a `grpc.aio` server to `unix:///ipc/grpc.sock`.
    - [ ] Increase `max_receive_message_length` to at least 8MB (default 4MB is too small for a ~6MB frame).
    - [ ] Implement `StreamFrames` RPC handler: receive each `FrameRequest`, reconstruct the matrix via `np.frombuffer(frame_data, dtype=np.uint8).reshape((height, width, channels))`.
    - [ ] Compute end-to-end latency: `time.time() - request.timestamp` (wall clock, shared host clock between containers).
    - [ ] Track `frame_number` to detect dropped frames — log a warning if a gap is detected.
    - [ ] Log each frame using the project logger: `Received Frame #42: (1080, 1920, 3) | Latency: 4.2ms`.
    - [ ] On stream completion, return `StreamSummary` with total frames received and average latency.
    - [ ] Handle `SIGTERM`/`SIGINT` for graceful shutdown (cleanup socket file on exit).

    **Client (`sender`)**
    - [ ] Connect a `grpc.aio` channel to `unix:///ipc/grpc.sock`.
    - [ ] Increase `max_send_message_length` to at least 8MB.
    - [ ] Implement a frame generator: produce `(1080, 1920, 3)` `np.uint8` random matrices.
    - [ ] Embed `time.time()` timestamp and monotonically increasing `frame_number` in each `FrameRequest`.
    - [ ] Add retry logic with exponential backoff for initial connection (server socket may not exist yet on startup).

- **Acceptance Criteria**:
    - Server starts, cleans up any stale socket, and binds to the UDS socket successfully.
    - Client connects, sends a single test frame, server receives and reconstructs it correctly.
    - No gRPC message size errors (the ~6MB frames go through cleanly).
    - Server logs: `Received Frame #1: (1080, 1920, 3) | Latency: Xms` using the `colorlog` logger.
    - Server detects and warns on frame number gaps.

- **Resources**:
    - [gRPC AsyncIO Python API](https://grpc.github.io/grpc/python/grpc_asyncio.html)
    - [gRPC Message Size Configuration](https://grpc.io/docs/guides/message-size-limits/)
    - [NumPy `frombuffer` Documentation](https://numpy.org/doc/stable/reference/generated/numpy.frombuffer.html)

---

## Day 4: 30 FPS & Integration
**Focus**: Rate Control, End-to-End Validation, Telemetry
**Load**: Level 5 (The Performance Hurdle)

- **Objectives**:
    1. Implement drift-corrected rate limiting on the client to sustain exactly 30 FPS.
    2. Run the full pipeline in Docker and validate all acceptance criteria.

- **Tasks**:

    **Rate Control**
    - [ ] Implement drift-corrected rate limiting in the client (not naive `sleep(1/30)` — account for frame generation and send time).
    - [ ] Log actual FPS on the client side every N frames (e.g., rolling average over last 30 frames).

    **Integration**
    - [ ] Run `docker compose up` — both containers running, frames streaming over UDS at 30 FPS.
    - [ ] Confirm no TCP connections are used (`ss -tlnp` inside containers shows nothing).
    - [ ] Verify graceful shutdown: `docker compose down` cleanly stops both containers and removes the socket file.
    - [ ] Soak test: monitor for frame drops (via `frame_number` gaps), buffer overflows, or memory leaks over a sustained 60-second run.

- **Acceptance Criteria**:
    - The gRPC channel connects over the UDS file without using localhost or TCP.
    - The Client sustains a transmission rate of 30 FPS without crashing due to buffer overflow or gRPC message size errors.
    - The Server terminal logs output formatted as: `Received Frame #N: (1080, 1920, 3) | Latency: 4.2ms`.
    - Graceful shutdown: `docker compose down` cleanly stops both containers and removes the socket file.
    - No `frame_number` gaps detected by the server over a 60-second soak test.

- **Resources**:
    - [Python `time.perf_counter` Profiling](https://docs.python.org/3/library/time.html#time.perf_counter)
    - [Python Signal Handling for Graceful Shutdown](https://docs.python.org/3/library/signal.html)

---

## Day 5: DevOps & Delivery
**Focus**: CI/CD, Image Publishing, Deployment Automation
**Load**: Level 4

- **Objectives**:
    1. Automate testing and linting in CI.
    2. Build and publish container images to a registry.
    3. Make the stack deployable with a single command on any Docker host.

- **Tasks**:

    **CI Pipeline (GitHub Actions)**
    - [ ] Create `.github/workflows/ci.yml`:
        - Trigger on push and PR to `main`.
        - Job 1 — **Lint & Type Check**: `uv sync`, `ruff check`, `ruff format --check`, `mypy .`.
        - Job 2 — **Build Images**: `docker compose build` — this runs `proto_compile.sh` inside the Dockerfile, confirming both proto compilation and image build succeed.
        - Job 3 — **Integration Smoke Test**: `docker compose up -d`, wait for logs, verify server output contains `Received Frame`, `docker compose down`.
    - [ ] Add CI status badge to `README.md`.

    **Container Registry**
    - [ ] Create `.github/workflows/publish.yml`:
        - Trigger on tags matching `v*` (e.g., `v0.1.0`).
        - Build multi-platform images (`linux/amd64`, `linux/arm64`) using `docker buildx`.
        - Push to GitHub Container Registry (`ghcr.io`).
        - Tag images as `latest` + the git tag version.

    **Deployment**
    - [ ] Write a `Makefile` with common targets:
        - `make proto` — regenerate protobuf stubs locally.
        - `make build` — build Docker images.
        - `make up` — start the stack (`docker compose up -d`).
        - `make down` — tear down the stack.
        - `make logs` — tail logs from both containers.
        - `make clean` — remove images, volumes, and the socket file.
    - [ ] Add a `deploy.sh` script (or `make deploy`) that pulls published images from `ghcr.io` and runs the stack — no local build required.
    - [ ] Document deployment steps in `README.md`: prerequisites, quick start, and configuration via `.env`.

- **Acceptance Criteria**:
    - Pushing to `main` triggers CI; all jobs pass green.
    - Tagging a release builds and pushes images to `ghcr.io/<owner>/grpc-uds-sender` and `ghcr.io/<owner>/grpc-uds-receiver`.
    - A fresh machine with Docker can run `make deploy` (or `deploy.sh`) and have the full stack streaming frames within 60 seconds.
    - `make up && make logs` shows frames streaming; `make down` tears everything down cleanly.

- **Resources**:
    - [GitHub Actions Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
    - [Publishing Docker Images to GHCR](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
    - [Docker Buildx Multi-Platform Builds](https://docs.docker.com/build/building/multi-platform/)
