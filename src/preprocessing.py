"""Data cleaning and validation. Contains no I/O and no analysis logic."""
import logging

import numpy as np
import pandas as pd

import config

logger = logging.getLogger(__name__)


def convert_types(df: pd.DataFrame) -> pd.DataFrame:
    """Parse dates, coerce numeric columns and strip whitespace in text columns."""
    df = df.copy()
    df[config.COL_DATE] = pd.to_datetime(df[config.COL_DATE], errors="coerce")
    for col in config.NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in config.TEXT_COLUMNS:
        df[col] = df[col].astype("string").str.strip()
    for col in config.IDENTIFIER_COLUMNS:
        df[col] = df[col].astype("string").str.strip()
    return df


def find_invalid_rows(df: pd.DataFrame) -> pd.Series:
    """Return a boolean mask of rows that violate the validation rules."""
    low, high = config.HOUR_RANGE
    invalid = ~df[config.COL_HOUR].between(low, high)
    for col in config.NON_NEGATIVE_COLUMNS:
        invalid |= df[col] < 0
    for col in config.NUMERIC_COLUMNS:
        invalid |= ~np.isfinite(df[col])
    for col in config.BINARY_COLUMNS:
        invalid |= ~df[col].isin([0, 1])
    for col in config.TEXT_COLUMNS + config.IDENTIFIER_COLUMNS:
        if col in df.columns:
            invalid |= df[col].isna() | df[col].str.strip().eq("")
    return invalid


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Run the full cleaning pipeline and return a cleaned DataFrame.

    Steps: type conversion, drop rows with missing/invalid values, drop duplicate
    rows and duplicate session IDs. Every removal is logged.
    """
    df = convert_types(df)
    start = len(df)

    df = df.dropna(subset=config.NUMERIC_COLUMNS + [config.COL_DATE] +
                   config.TEXT_COLUMNS + config.IDENTIFIER_COLUMNS)
    invalid = find_invalid_rows(df)
    logger.info("Invalid rows removed: %d", int(invalid.sum()))
    df = df[~invalid]

    df = df.drop_duplicates()
    dup_sessions = int(df[config.COL_SESSION].duplicated().sum())
    if dup_sessions:
        logger.warning("Dropping %d duplicate %s values", dup_sessions, config.COL_SESSION)
        df = df.drop_duplicates(subset=config.COL_SESSION)

    logger.info("Cleaning complete: %d -> %d rows", start, len(df))
    return df.reset_index(drop=True)
