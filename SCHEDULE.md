# Phase 1: High-Performance IPC & Hardware Isolation (Days 1-2)

**The Validation Task**:
> To validate Phase 1, the developer must engineer a containerized client-server topology. Container A will run a Python process that generates randomized 1080p RGB image matrices. Container B will host a Python gRPC server. Both containers must be orchestrated via Docker Compose, sharing a mounted volume to facilitate a Unix Domain Socket connection. Container A must stream the raw binary image data to Container B over the UDS gRPC channel at a sustained rate of thirty requests per second. Container B must receive the payload, reconstruct the NumPy array, and print the tensor shape and execution latency. This project proves mastery of hardware isolation, binary contracts, and optimized IPC.

This schedule simulates a **systems engineering stress test**. You are building a zero-network, hardware-accelerated Inter-Process Communication (IPC) pipeline.
**Goal**: Prove absolute mastery over Docker volume mounting, binary serialization contracts, and asynchronous Python streaming.

---

## Day 1: The Contract & The Topology
**Focus**: Protobuf Design, Orchestration, Unix Domain Sockets
**Load**: Level 4

- **Objectives**:
    1. Define a strict binary contract for a 1080p RGB matrix payload.
    2. Engineer the Docker Compose topology to completely isolate the network while sharing a physical file structure.

- **Tasks**:
    - [ ] Write `schema.proto` defining an RPC service that accepts a stream of raw bytes.
    - [ ] Compile the `.proto` file into Python `_pb2.py` and `_pb2_grpc.py` stubs.
    - [ ] Write `docker-compose.yml` defining `sender` and `receiver` services.
    - [ ] Configure a shared host volume mapping `./shared_socket` to `/ipc` in both containers.
    - [ ] **Blocker**: Do not map any standard TCP network ports (`50051`).

- **Acceptance Criteria**:
    - Running `docker compose up -d` successfully spins up both containers.
    - Creating a dummy file in Container A's `/ipc` folder makes it instantly visible in Container B's `/ipc` folder.
    - The compiled protobuf files exist and can be imported without `ModuleNotFoundError`.

- **Resources**:
    - [gRPC Python Quickstart & Compilation](https://grpc.io/docs/languages/python/quickstart/)
    - [Docker Compose Volumes Documentation](https://docs.docker.com/compose/compose-file/05-services/#volumes)
    - [Protocol Buffers Language Guide (proto3)](https://protobuf.dev/programming-guides/proto3/)

---

## Day 2: The Zero-Network Data Hose
**Focus**: NumPy Serialization, Asyncio, Telemetry
**Load**: Level 5 (The Performance Hurdle)

- **Objectives**:
    1. Construct a client process that generates simulated high-resolution camera data.
    2. Construct an asynchronous server process to ingest, reconstruct, and profile the byte stream.

- **Tasks**:
    - [ ] Build the **Server** (`receiver`): Bind a `grpc.aio` server to `unix:///ipc/grpc.sock`.
    - [ ] Build the **Client** (`sender`): Connect a gRPC channel to the same socket file.
    - [ ] Implement the Client loop: Generate a `(1080, 1920, 3)` `np.uint8` matrix, flatten to bytes, and transmit at exactly 30 Requests Per Second (RPS).
    - [ ] Implement the Server ingestion: Receive the payload, use `np.frombuffer()` to reconstruct the matrix shape.
    - [ ] Instrument the Server using `time.perf_counter()` to measure end-to-end execution latency.

- **Acceptance Criteria**:
    - The gRPC channel successfully connects over the UDS file without using localhost or TCP.
    - The Client sustains a transmission rate of 30 FPS without crashing due to buffer overflow.
    - The Server terminal logs output formatted as: `Received Matrix: (1080, 1920, 3) | Latency: 4.2ms`.

- **Resources**:
    - [gRPC AsyncIO Python API](https://grpc.github.io/grpc/python/grpc_asyncio.html)
    - [NumPy `frombuffer` Documentation](https://numpy.org/doc/stable/reference/generated/numpy.frombuffer.html)
    - [Python `time.perf_counter` Profiling](https://docs.python.org/3/library/time.html#time.perf_counter)
