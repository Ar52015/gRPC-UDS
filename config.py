from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Logging

    LOG_LEVEL: str = "INFO"

    # gRPC Settings

    GRPC_SOCKET_PATH: str = "/ipc/grpc.sock"
    MAX_MESSAGE_SIZE: int = 8388608
    TARGET_FPS: int = 30
    MAX_CHANNEL_CONNECT_RETRIES: int = 5
