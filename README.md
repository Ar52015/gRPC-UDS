# gRPC-UDS

This project is a containerized client-server architecture that streams raw 1080p RGB image matrices at 30fps between isolated Python processes. By routing gRPC communication over a Unix Domain Socket (UDS) via a shared Docker volume, it bypasses the TCP/IP stack to achieve highly optimized, low-latency inter-process communication.

## Architecture

* **Client (Container A):** Python process generating randomized 1080p RGB tensors ($1920 \times 1080 \times 3$).
* **Server (Container B):** Python gRPC server receiving the binary payload, reconstructing the NumPy array, and logging tensor shape and execution latency.
* **Orchestration:** Docker Compose.
* **Transport Layer:** gRPC over Unix Domain Sockets (IPC) facilitated by a shared Docker volume.
