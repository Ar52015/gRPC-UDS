"""Async gRPC client that streams 1080p RGB frames over UDS."""

import asyncio
import time
from collections import deque
from collections.abc import AsyncIterator

import grpc.aio
import numpy as np

from app.utils.logger import setup_logger
from config import Settings
from generated import schema_pb2, schema_pb2_grpc

logger = setup_logger(__name__)
settings = Settings()


async def frame_generator(
    frame_count: int,
) -> AsyncIterator[schema_pb2.StreamFramesRequest]:
    """Yield random 1080p RGB frames at a drift-corrected rate.

    Uses an anchor-based timing loop to sustain TARGET_FPS. Sleeps
    until the target send time before generating each frame. Logs
    a rolling FPS average every TARGET_FPS frames.

    Args:
        frame_count: Number of frames to generate.

    Yields:
        StreamFramesRequest containing raw frame bytes and metadata.
    """
    rng = np.random.default_rng()
    interval = 1 / settings.TARGET_FPS
    timestamps: deque[float] = deque(maxlen=settings.TARGET_FPS)
    anchor = time.perf_counter()

    for frame_number in range(frame_count):
        target = anchor + frame_number * interval
        sleep_duration = target - time.perf_counter()
        if sleep_duration > 0:
            await asyncio.sleep(sleep_duration)

        frame = rng.integers(0, 256, size=(1080, 1920, 3), dtype=np.uint8)
        frame_bytes = frame.tobytes()

        timestamps.append(time.perf_counter())
        if len(timestamps) == settings.TARGET_FPS:
            fps = (len(timestamps) - 1) / (timestamps[-1] - timestamps[0])
            logger.info("Rolling FPS: %.1f", fps)

        yield schema_pb2.StreamFramesRequest(
            frame_data=frame_bytes,
            height=1080,
            width=1920,
            channels=3,
            frame_number=frame_number,
            timestamp=time.time(),
        )


async def send() -> None:
    """Connect to the gRPC server over UDS and stream frames.

    Opens an async gRPC channel with exponential backoff retry,
    streams generated frames, and logs the server's summary response.

    Raises:
        RuntimeError: If all connection retries are exhausted.
    """
    client = grpc.aio.insecure_channel(
        target=f"unix://{settings.GRPC_SOCKET_PATH}",
        options=[
            ("grpc.max_send_message_length", settings.MAX_MESSAGE_SIZE),
        ],
    )

    backoff = 2.0
    for _ in range(settings.MAX_CHANNEL_CONNECT_RETRIES):
        try:
            await asyncio.wait_for(client.channel_ready(), timeout=backoff)
            break
        except TimeoutError:
            logger.warning("Connection to channel failed, retrying ...")
            backoff *= 2
            await asyncio.sleep(backoff)
    else:
        raise RuntimeError("Couldn't connect channel")

    stub = schema_pb2_grpc.StreamServiceStub(client)
    response = await stub.StreamFrames(frame_generator(30))

    logger.info(
        "Server received %d frames | Latency: %.2f",
        response.frames_received,
        response.avg_latency_ms,
    )


if __name__ == "__main__":
    asyncio.run(send())
