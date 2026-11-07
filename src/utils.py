"""Shared helpers: logging and filesystem utilities."""
import logging
from pathlib import Path

import config


def setup_logging(level: str = config.LOG_LEVEL) -> None:
    """Configure root logger with a consistent format."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def ensure_dir(path: Path) -> Path:
    """Create a directory (and parents) if missing and return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path
