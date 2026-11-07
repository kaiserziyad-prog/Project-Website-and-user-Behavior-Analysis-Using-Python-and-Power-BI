"""Tests for dashboard data loading and calculations."""
import pandas as pd
import pytest

import config
from src.dashboard.data import calculate_dashboard_metrics, grouped_analysis, load_dashboard_data


def sample_frame():
    return pd.DataFrame({
        config.COL_DATE: pd.to_datetime(["2026-01-01", "2026-01-02"]),
        config.COL_SESSION: ["S1", "S2"], config.COL_USER: ["U1", "U2"],
        config.COL_PAGE_VIEWS: [2, 4], config.COL_DURATION: [20, 40],
        config.COL_BOUNCE: [0, 1], config.COL_CONVERSIONS: [1, 0],
        config.COL_REVENUE: [50.0, 0.0], config.COL_SOURCE: ["Google", "Direct"],
        config.COL_DEVICE: ["Mobile", "Desktop"], config.COL_HOUR: [9, 10],
    })


def test_dashboard_metrics():
    metrics = calculate_dashboard_metrics(sample_frame())
    assert metrics["sessions"] == 2
    assert metrics["page_views"] == 6
    assert metrics["conversion_rate"] == 50
    assert metrics["bounce_rate"] == 50


def test_grouped_analysis_rejects_unknown_dimension():
    with pytest.raises(ValueError, match="Unknown grouping column"):
        grouped_analysis(sample_frame(), "NotAColumn")


def test_load_dashboard_data_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_dashboard_data(tmp_path / "missing.csv")


def test_load_dashboard_data_empty_file(tmp_path):
    empty_file = tmp_path / "empty.csv"
    empty_file.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="Could not read"):
        load_dashboard_data(empty_file)
