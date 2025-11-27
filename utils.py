"""
Utility functions for logging and general operations.

Centralized utilities for configuration, logging, and common operations.
"""

import logging
from typing import Any


def configure_logging(level: int = logging.INFO) -> None:
    """
    Configure application-wide logging.

    Args:
        level: Logging level (default: INFO)
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def safe_get(dictionary: dict, key: str, default: Any = None) -> Any:
    """
    Safely get value from dictionary with default.

    Args:
        dictionary: Dictionary to query
        key: Key to look up
        default: Default value if key not found

    Returns:
        Value or default
    """
    return dictionary.get(key, default)
