"""
Logging configuration for SehatSaathi-AI.

Provides structured, consistent logging across the entire application
with both console and rotating file handlers.
"""

import logging
import logging.handlers
import os
from typing import Optional


LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Third-party loggers that are too noisy at DEBUG/INFO
_SUPPRESS_LOGGERS = [
    "uvicorn.access",
    "httpx",
    "httpcore",
    "multipart",
]


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = "logs/app.log",
) -> None:
    """
    Configure application-wide logging.

    Sets up a console handler (always) and an optional rotating file
    handler. Should be called once at application startup before any
    other module emits log messages.

    Args:
        log_level: Minimum severity level to capture (DEBUG, INFO, WARNING, ERROR).
        log_file:  Path to the rotating log file. Pass ``None`` to disable
                   file logging.
    """
    # Ensure the log directory exists before attaching the file handler
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove any handlers that may have been attached by imported libraries
    root_logger.handlers.clear()

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # Console handler — always present
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Rotating file handler — 10 MB per file, keep 5 backups
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Quieten noisy third-party libraries
    for logger_name in _SUPPRESS_LOGGERS:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger.

    Convenience wrapper so modules don't need to import ``logging``
    directly just to call ``logging.getLogger``.

    Args:
        name: Typically ``__name__`` of the calling module.

    Returns:
        A :class:`logging.Logger` instance.
    """
    return logging.getLogger(name)
