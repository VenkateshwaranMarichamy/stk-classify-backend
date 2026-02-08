"""Logging configuration and logger factory."""

import logging
import sys
from typing import Optional

from app.core.config import settings


def get_logger(
    name: str,
    level: Optional[str] = None,
) -> logging.Logger:
    """
    Return a configured logger for the given module name.

    Args:
        name: Logger name (typically __name__).
        level: Override log level (e.g. DEBUG, INFO). Uses settings.log_level if None.

    Returns:
        Configured Logger instance.
    """
    log_level = (level or settings.log_level).upper()
    level_value = getattr(logging, log_level, logging.INFO)

    logger = logging.getLogger(name)
    logger.setLevel(level_value)

    # Avoid adding handlers again if already configured (e.g. when get_logger is called multiple times)
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level_value)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# Default app logger
logger = get_logger("app")
