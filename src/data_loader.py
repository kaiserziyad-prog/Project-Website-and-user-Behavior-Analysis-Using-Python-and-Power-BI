"""Data input/output: reading the raw dataset and saving tables."""
import logging
from pathlib import Path
from typing import Iterable

import pandas as pd

import config
from src.utils import ensure_dir

logger = logging.getLogger(__name__)


class DataLoadError(Exception):
    """Raised when the dataset cannot be loaded or is malformed."""


def load_raw_data(path: Path = config.RAW_DATA_PATH) -> pd.DataFrame:
    """Load the raw website-traffic CSV and verify the expected schema.

    Raises:
        DataLoadError: if the file is missing, empty, unreadable or lacks required columns.
    """
    try:
        df = pd.read_csv(path)
    except FileNotFoundError as exc:
        raise DataLoadError(f"Dataset not found: {path}") from exc
    except (pd.errors.EmptyDataError, pd.errors.ParserError) as exc:
        raise DataLoadError(f"Dataset could not be parsed: {path} ({exc})") from exc

    missing = set(config.REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise DataLoadError(f"Dataset is missing columns: {sorted(missing)}")

    logger.info("Loaded %d rows x %d columns from %s", *df.shape, path)
    return df


def save_dataframe(df: pd.DataFrame, path: Path) -> Path:
    """Save a DataFrame to CSV, creating parent folders as needed."""
    ensure_dir(path.parent)
    df.to_csv(path, index=False, encoding=config.CSV_ENCODING)
    logger.info("Saved %s (%d rows)", path.name, len(df))
    return path


def save_text(lines: Iterable[str], path: Path) -> Path:
    """Write lines of text to a file, creating parent folders as needed."""
    ensure_dir(path.parent)
    path.write_text("\n".join(lines), encoding=config.CSV_ENCODING)
    logger.info("Saved %s", path.name)
    return path
