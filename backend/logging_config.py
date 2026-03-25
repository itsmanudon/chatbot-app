"""
logging_config.py
-----------------
Centralized logging configuration for the Personal AI Memory System backend.

Sets up a structured logger with:
- Console handler with a consistent format
- Log level controlled by the LOG_LEVEL environment variable (default: INFO)
- Named loggers per module for easy filtering

Usage
-----
Import ``get_logger`` in any module::

    from logging_config import get_logger
    logger = get_logger(__name__)

    logger.info("Something happened")
    logger.warning("Something unexpected: %s", detail)
    logger.error("Something failed", exc_info=True)
"""

import logging
import os
import sys

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

_fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_date_fmt = "%Y-%m-%dT%H:%M:%S"

logging.basicConfig(
    level=LOG_LEVEL,
    format=_fmt,
    datefmt=_date_fmt,
    stream=sys.stdout,
    force=True,
)

# Quieten noisy third-party loggers
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger configured by this module."""
    return logging.getLogger(name)
