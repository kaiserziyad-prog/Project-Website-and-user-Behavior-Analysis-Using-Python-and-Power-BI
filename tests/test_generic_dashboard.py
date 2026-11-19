"""Tests for the schema-free (any uploaded file) dashboard logic."""
import json

import numpy as np
import pandas as pd
import pytest

import config
from src.dashboard import generic
from src.dashboard.data import load_traffic_if_matching, load_dashboard_data


def _profile(frame):
    return generic.prepare_table(frame)


def test_column_roles_are_detected_without_any_fixed_schema():
    n = 100
    frame = pd.DataFrame({
        "when": pd.date_range("2024-01-01", periods=n).astype(str),
        "Sales ($)": [f"${x:,.2f}" for x in np.linspace(10, 5000, n)],
        "Region": ["A", "B", "C", "D"] * 25,
        "note": [f"free text {i}" for i in range(n)],
        "ID": range(n),
        "blank": np.nan,
    })
    p = _profile(frame)
    assert p.datetime == ["when"]
    assert p.numeric == ["Sales ($)"] and p.frame["Sales ($)"].max() == 5000
    assert p.categorical == ["Region"]
    assert "ID" in p.identifier and "note" in p.identifier
    assert p.dropped_empty_columns == ["blank"]


def test_read_table_handles_formats_and_delimiters(tmp_path):
    assert generic.read_table(b"a;b\n1;2\n3;4\n", "x.csv").shape == (2, 2)          # semicolon sniffed
    assert generic.read_table(b"a\tb\n1\t2\n", "x.tsv").shape == (1, 2)
    assert generic.read_table("a,b\nCaf\xe9,1\n".encode("latin-1"), "x.csv").shape == (1, 2)  # non-UTF8
    records = json.dumps([{"u": "x", "v": 1}, {"u": "y", "v": 2}]).encode()
    assert list(generic.read_table(records, "x.json").columns) == ["u", "v"]
    path = tmp_path / "book.xlsx"
    pd.DataFrame({"d": pd.date_range("2024-01-01", periods=3), "v": [1, 2, 3]}).to_excel(path, index=False)
    assert generic.read_table(path.read_bytes(), "book.xlsx").shape == (3, 2)


def test_empty_file_gives_friendly_error():
    with pytest.raises(ValueError, match="empty"):
        generic.read_table(b"   \n", "x.csv")


@pytest.mark.parametrize("frame", [
    pd.DataFrame({"a": [1]}),                                  # single cell
    pd.DataFrame({"a": [1, 2, 3, 4, 5]}),                      # one numeric column
    pd.DataFrame({"name": ["a", "b", "c"], "city": ["x", "y", "x"]}),   # no numerics
    pd.DataFrame({"a": [], "b": []}),                          # header only
    pd.DataFrame({"k": [5] * 30, "v": range(30)}),             # constant column
])
def test_statistics_never_crash_on_unusual_shapes(frame):
    p = _profile(frame)
    generic.column_overview(p)
    generic.missing_summary(p.frame)
    generic.quick_insights(p)
    if p.numeric:
        generic.numeric_summary(p.frame, p.numeric)
    generic.correlation_matrix(p.frame, p.numeric)
    generic.top_correlations(generic.correlation_matrix(p.frame, p.numeric))


def test_time_series_and_category_helpers():
    frame = pd.DataFrame({"d": pd.date_range("2024-01-01", periods=60), "v": range(60),
                          "c": ["a", "b", "a"] * 20})
    p = _profile(frame)
    daily = generic.time_series(p.frame, "d", "v", "sum", "Day")
    assert len(daily) == 60 and daily["Value"].sum() == sum(range(60))
    assert generic.time_series(p.frame, "d", None, "sum", "Month")["Value"].sum() == 60
    by_cat = generic.numeric_by_category(p.frame, "c", "v", "sum")
    assert by_cat.iloc[:, 1].sum() == sum(range(60))
    counts = generic.category_counts(p.frame["c"])
    assert counts["Count"].sum() == 60


def test_user_style_file_with_different_columns_is_not_forced_into_traffic_schema():
    frame = pd.DataFrame({"Page Views": [5, 4, 3], "Traffic Source": ["Organic", "Social", "Organic"],
                          "Bounce Rate": [0.2, 0.4, 0.3]})
    assert load_traffic_if_matching(frame) is None
    assert _profile(frame).numeric == ["Page Views", "Bounce Rate"]


def test_traffic_format_with_spaced_headers_is_still_recognised():
    sample = load_dashboard_data().head(50)
    spaced = sample.rename(columns=lambda c: c.replace("_", " ").lower())
    result = load_traffic_if_matching(spaced)
    assert result is not None and len(result[0]) == 50
    assert config.COL_SOURCE in result[0].columns
