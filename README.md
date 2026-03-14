# gRPC-UDS
This project is a containerized client-server architecture that streams raw 1080p RGB image matrices at 30fps between isolated Python processes. By routing gRPC communication over a Unix Domain Socket (UDS) via a shared Docker volume, it bypasses the TCP/IP stack to achieve highly optimized, low-latency inter-process communication.
