"""Dashboard data access. Calculations are delegated to ``src.analysis``."""
import re
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd

import config
from src import analysis
from src.preprocessing import clean_data


def load_dashboard_data(path: Path = config.PROCESSED_DATA_PATH) -> pd.DataFrame:
    """Load and validate the processed dataset used by the dashboard.

    Raises:
        FileNotFoundError: if the processed dataset does not exist.
        ValueError: if the file is unreadable, lacks columns or has no rows.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Processed dataset not found: {path}. Run `python main.py` first.")
    try:
        frame = pd.read_csv(path, parse_dates=[config.COL_DATE])
    except (pd.errors.EmptyDataError, pd.errors.ParserError, ValueError) as exc:
        raise ValueError(f"Could not read dashboard dataset: {exc}") from exc
    missing = sorted(set(config.DASHBOARD_REQUIRED_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"Processed dataset is missing columns: {missing}")
    if frame.empty:
        raise ValueError("Processed dataset contains no rows.")
    return frame


def calculate_dashboard_metrics(frame: pd.DataFrame) -> Dict[str, float]:
    """Return headline KPIs for the dashboard (all zeros for an empty frame)."""
    keys = ("sessions", "users", "page_views", "revenue", "pages_per_session",
            "sessions_per_user", "average_duration", "bounce_rate", "engaged_session_rate",
            "conversion_rate", "revenue_per_conversion")
    if frame.empty:
        return {key: 0.0 for key in keys}
    kpis = analysis.compute_kpis(frame).set_index("KPI")["Value"]
    return {
        "sessions": int(kpis["Total Sessions"]),
        "users": int(kpis["Unique Users"]),
        "page_views": int(kpis["Total Page Views"]),
        "revenue": float(kpis["Total Revenue"]),
        "pages_per_session": float(kpis["Pages per Session"]),
        "sessions_per_user": float(kpis["Sessions per User"]),
        "average_duration": float(kpis["Average Session Duration"]),
        "bounce_rate": float(kpis["Bounce Rate"]),
        "engaged_session_rate": float(kpis["Engaged Session Rate"]),
        "conversion_rate": float(kpis["Conversion Rate"]),
        "revenue_per_conversion": float(kpis["Revenue per Conversion"]),
    }


def grouped_analysis(frame: pd.DataFrame, dimension: str) -> pd.DataFrame:
    """Aggregate key measures by ``dimension`` (validated against the frame's columns)."""
    if dimension not in frame.columns:
        raise ValueError(f"Unknown grouping column: {dimension}")
    return analysis.summarize_by(frame, dimension)


def match_traffic_schema(raw: pd.DataFrame) -> Optional[pd.DataFrame]:
    """Rename columns like ``Page Views`` -> ``Page_Views`` if every required traffic column is present.

    Returns the renamed frame, or ``None`` when the file does not follow the traffic format.
    """
    def key(name: str) -> str:
        return re.sub(r"[^a-z0-9]", "", str(name).lower())

    available = {}
    for column in raw.columns:
        available.setdefault(key(column), column)
    wanted = {col: available.get(key(col)) for col in config.DASHBOARD_REQUIRED_COLUMNS}
    if any(source is None for source in wanted.values()):
        return None
    renames = {source: target for target, source in wanted.items()}
    for col in config.DASHBOARD_OPTIONAL_COLUMNS:
        if available.get(key(col)) is not None:
            renames[available[key(col)]] = col
    return raw[list(renames)].rename(columns=renames)


def prepare_traffic_frame(raw: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """Validate and clean a frame that follows the traffic format (same rules as ``main.py``).

    Medium, Browser and Country are optional and filled with "Unknown" when absent.

    Raises:
        ValueError: if required columns are missing or no valid rows remain.
    """
    raw = raw.copy()
    raw.columns = [str(col).strip() for col in raw.columns]
    missing = sorted(set(config.DASHBOARD_REQUIRED_COLUMNS) - set(raw.columns))
    if missing:
        raise ValueError(f"Uploaded CSV is missing required columns: {missing}")
    for col in config.DASHBOARD_OPTIONAL_COLUMNS:
        if col not in raw.columns:
            raw[col] = config.DASHBOARD_UNKNOWN_LABEL
    cleaned = clean_data(raw)
    if cleaned.empty:
        raise ValueError("No valid rows remain after cleaning. Check dates, hours (0-23) and numeric values.")
    summary = {"rows_uploaded": len(raw), "rows_used": len(cleaned),
               "rows_removed": len(raw) - len(cleaned)}
    return cleaned, summary


def load_uploaded_data(source) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """Read a traffic-format CSV (path or file-like object) and clean it.

    Raises:
        ValueError: if the file is unreadable, lacks required columns or has no valid rows.
    """
    try:
        raw = pd.read_csv(source)
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        raise ValueError(f"Could not read the uploaded file as CSV: {exc}") from exc
    return prepare_traffic_frame(raw)


def load_traffic_if_matching(raw: pd.DataFrame) -> Optional[Tuple[pd.DataFrame, Dict[str, int]]]:
    """Return ``(cleaned_frame, summary)`` if ``raw`` follows the traffic format, else ``None``."""
    renamed = match_traffic_schema(raw)
    if renamed is None:
        return None
    try:
        return prepare_traffic_frame(renamed)
    except ValueError:
        return None


def build_template_csv(frame: pd.DataFrame, rows: int = config.DASHBOARD_TEMPLATE_ROWS) -> bytes:
    """Return a small example CSV (all expected columns) users can use as a template."""
    columns = [col for col in config.REQUIRED_COLUMNS if col in frame.columns]
    return frame[columns].head(rows).to_csv(index=False, date_format=config.DATE_FORMAT).encode(config.CSV_ENCODING)


def load_sample_dataset(name: str) -> pd.DataFrame:
    """Load one of the bundled sample datasheets (``config.SAMPLE_DATASETS``) as a cleaned frame.

    Raises:
        KeyError: if ``name`` is not a known sample.
        FileNotFoundError: if the sample's CSV file is missing.
        ValueError: if the file is not valid traffic data.
    """
    path = config.SAMPLE_DATASETS[name]
    if path == config.PROCESSED_DATA_PATH:
        return load_dashboard_data()
    if not path.exists():
        raise FileNotFoundError(f"Sample datasheet not found: {path}")
    return load_uploaded_data(path)[0]
