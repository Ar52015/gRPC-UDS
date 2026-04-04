import asyncio
import os
import signal
import time
from collections.abc import AsyncIterator
from typing import override

import grpc.aio
import numpy as np

from app.utils.logger import setup_logger
from config import Settings
from generated import schema_pb2, schema_pb2_grpc

logger = setup_logger(__name__)
settings = Settings()


class FrameServicer(schema_pb2_grpc.StreamServiceServicer):
    """ """

    @override
    async def StreamFrames(
        self,
        request_iterator: AsyncIterator[schema_pb2.StreamFramesRequest],
        context: grpc.aio.ServicerContext[
            schema_pb2.StreamFramesRequest,
            schema_pb2.StreamFramesResponse,
        ],
    ) -> schema_pb2.StreamFramesResponse:
        frames_received: int = 0
        total_latency: float = 0.0
        last_frame_number: int = -1

        async for req in request_iterator:
            latency_ms = (time.time() - req.timestamp) * 1000

            if last_frame_number >= 0 and req.frame_number != last_frame_number + 1:
                dropped = req.frame_number - last_frame_number - 1
                logger.warning(
                    "Dropped %d frame(s) between #%d and #%d",
                    dropped,
                    last_frame_number,
                    req.frame_number,
                )

            frame = np.frombuffer(req.frame_data, dtype=np.uint8).reshape(
                (req.height, req.width, req.channels)
            )

            frames_received += 1
            total_latency += latency_ms
            last_frame_number = req.frame_number

            logger.info(
                "Recieved Frame #%d: %s | Latency: %.2fms",
                req.frame_number,
                frame.shape,
                latency_ms,
            )

        avg_latency = total_latency / frames_received if frames_received > 0 else 0.0

        logger.info(
            "Stream complete: %d frames, avg_latency %.2fms",
            frames_received,
            avg_latency,
        )

        return schema_pb2.StreamFramesResponse(
            frames_received=frames_received,
            frames_dropped=max(0, last_frame_number - frames_received + 1)
            if last_frame_number >= 0
            else 0,
            avg_latency_ms=avg_latency,
        )


async def serve() -> None:
    socket_path = settings.GRPC_SOCKET_PATH

    try:
        os.unlink(socket_path)
    except FileNotFoundError:
        pass

    server = grpc.aio.server(
        options=[
            ("grpc.max_receive_message_length", settings.MAX_MESSAGE_SIZE),
        ]
    )

    schema_pb2_grpc.add_StreamServiceServicer_to_server(FrameServicer(), server)

    listen_addr = f"unix://{socket_path}"
    _ = server.add_insecure_port(listen_addr)

    await server.start()
    logger.info("Server listening on %s", listen_addr)

    shutdown_event = asyncio.Event()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, shutdown_event.set)

    _ = await shutdown_event.wait()

    logger.info("Shutting down server...")
    await server.stop(grace=5)

    try:
        os.unlink(socket_path)
    except FileNotFoundError:
        pass

    logger.info("Server Stopped")


if __name__ == "__main__":
    asyncio.run(serve())
