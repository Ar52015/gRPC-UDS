"""Color-coded logger factory using colorlog."""

import logging
import sys

import colorlog

from config import Settings

settings = Settings()


def setup_logger(name: str = "app") -> logging.Logger:
    """Configure and return a color-coded console logger.

    Args:
        name: Name of the logger instance.

    Returns:
        Configured logger with color-coded output to stdout.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(settings.LOG_LEVEL)

    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = colorlog.ColoredFormatter(
        fmt=(
            "%(log_color)s%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s"
        ),
        log_colors={
            "DEBUG": "blue",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    logger.propagate = False

    return logger
