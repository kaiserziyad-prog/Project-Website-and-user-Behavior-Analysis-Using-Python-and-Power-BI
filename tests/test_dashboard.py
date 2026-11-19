"""Tests for dashboard data loading and calculations."""
import pandas as pd
import pytest

import config
from src.dashboard.data import (build_template_csv, calculate_dashboard_metrics, grouped_analysis,
                                 load_dashboard_data, load_uploaded_data)


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
    assert metrics["engaged_session_rate"] == 50
    assert metrics["revenue_per_conversion"] == 50


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


def _csv_bytes(frame):
    import io
    return io.BytesIO(frame.to_csv(index=False).encode("utf-8"))


def test_load_uploaded_data_fills_optional_columns_and_cleans():
    frame = sample_frame()
    frame = pd.concat([frame, frame.iloc[[0]]])          # exact duplicate row
    cleaned, summary = load_uploaded_data(_csv_bytes(frame))
    assert summary == {"rows_uploaded": 3, "rows_used": 2, "rows_removed": 1}
    assert (cleaned[config.COL_COUNTRY] == config.DASHBOARD_UNKNOWN_LABEL).all()


def test_load_uploaded_data_missing_required_columns():
    with pytest.raises(ValueError, match="missing required columns"):
        load_uploaded_data(_csv_bytes(sample_frame().drop(columns=[config.COL_REVENUE])))


def test_load_uploaded_data_no_valid_rows():
    bad = sample_frame()
    bad[config.COL_HOUR] = 99
    with pytest.raises(ValueError, match="No valid rows"):
        load_uploaded_data(_csv_bytes(bad))


def test_load_uploaded_data_empty_file():
    import io
    with pytest.raises(ValueError, match="Could not read"):
        load_uploaded_data(io.BytesIO(b""))


def test_template_csv_round_trips():
    import io
    template = build_template_csv(load_dashboard_data())
    cleaned, _ = load_uploaded_data(io.BytesIO(template))
    assert len(cleaned) == config.DASHBOARD_TEMPLATE_ROWS


@pytest.mark.parametrize("name", list(config.SAMPLE_DATASETS))
def test_every_sample_datasheet_loads_and_computes_metrics(name):
    from src.dashboard.data import load_sample_dataset
    frame = load_sample_dataset(name)
    assert len(frame) > 1000
    assert calculate_dashboard_metrics(frame)["sessions"] == len(frame)


def test_sample_names_include_default_and_three_stores():
    assert list(config.SAMPLE_DATASETS) == [config.SAMPLE_DEFAULT_NAME, "Amazon", "Flipkart", "Myntra"]
