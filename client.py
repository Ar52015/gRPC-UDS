import asyncio
import time
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
    """ """
    rng = np.random.default_rng()

    for frame_number in range(frame_count):
        frame = rng.integers(0, 256, size=(1080, 1920, 3), dtype=np.uint8)
        frame_bytes = frame.tobytes()

        yield schema_pb2.StreamFramesRequest(
            frame_data=frame_bytes,
            height=1080,
            width=1920,
            channels=3,
            frame_number=frame_number,
            timestamp=time.time(),
        )


async def send() -> None:
    """ """
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
