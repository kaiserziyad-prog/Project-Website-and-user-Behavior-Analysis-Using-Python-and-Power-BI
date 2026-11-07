"""Unit tests for preprocessing and analysis."""
import pandas as pd
import pytest

import config
from src import analysis, preprocessing


@pytest.fixture
def raw_df() -> pd.DataFrame:
    """Tiny dataset containing one duplicate row and one invalid hour."""
    rows = [
        ("2026-01-01", 10, "S1", "U1", "Google", "organic", "Mobile", "Chrome", "IN", 3, 60, 0, 1, 20.0),
        ("2026-01-01", 11, "S2", "U2", "Direct", "none", "Desktop", "Safari", "IN", 1, 5, 1, 0, 0.0),
        ("2026-01-02", 12, "S3", "U1", "Google", "organic", "Mobile", "Chrome", "IN", 2, 30, 0, 0, 0.0),
        ("2026-01-02", 12, "S3", "U1", "Google", "organic", "Mobile", "Chrome", "IN", 2, 30, 0, 0, 0.0),
        ("2026-01-02", 99, "S4", "U3", "Google", "organic", "Mobile", "Chrome", "IN", 2, 30, 0, 0, 0.0),
    ]
    return pd.DataFrame(rows, columns=config.REQUIRED_COLUMNS)


def test_clean_data_removes_duplicates_and_invalid(raw_df):
    clean = preprocessing.clean_data(raw_df)
    assert len(clean) == 3
    assert clean[config.COL_HOUR].between(0, 23).all()


def test_kpis(raw_df):
    kpis = analysis.compute_kpis(preprocessing.clean_data(raw_df)).set_index("KPI")["Value"]
    assert kpis["Total Sessions"] == 3
    assert kpis["Conversion Rate"] == pytest.approx(33.33)
    assert kpis["Total Revenue"] == 20.0


def test_summarize_by_source(raw_df):
    table = analysis.summarize_by(preprocessing.clean_data(raw_df), config.COL_SOURCE)
    google = table[table[config.COL_SOURCE] == "Google"].iloc[0]
    assert google["Sessions"] == 2
    assert google["Bounce_Rate"] == 0


def test_invalid_period_raises(raw_df):
    with pytest.raises(ValueError):
        analysis.summarize_trend(preprocessing.clean_data(raw_df), "weekly")
