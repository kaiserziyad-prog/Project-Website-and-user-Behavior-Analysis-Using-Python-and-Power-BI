"""Dashboard data access. Calculations are delegated to ``src.analysis``."""
from pathlib import Path
from typing import Dict

import pandas as pd

import config
from src import analysis


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
            "average_duration", "bounce_rate", "conversion_rate")
    if frame.empty:
        return {key: 0.0 for key in keys}
    kpis = analysis.compute_kpis(frame).set_index("KPI")["Value"]
    return {
        "sessions": int(kpis["Total Sessions"]),
        "users": int(kpis["Unique Users"]),
        "page_views": int(kpis["Total Page Views"]),
        "revenue": float(kpis["Total Revenue"]),
        "pages_per_session": float(kpis["Pages per Session"]),
        "average_duration": float(kpis["Average Session Duration"]),
        "bounce_rate": float(kpis["Bounce Rate"]),
        "conversion_rate": float(kpis["Conversion Rate"]),
    }


def grouped_analysis(frame: pd.DataFrame, dimension: str) -> pd.DataFrame:
    """Aggregate key measures by ``dimension`` (validated against the frame's columns)."""
    if dimension not in frame.columns:
        raise ValueError(f"Unknown grouping column: {dimension}")
    return analysis.summarize_by(frame, dimension)
