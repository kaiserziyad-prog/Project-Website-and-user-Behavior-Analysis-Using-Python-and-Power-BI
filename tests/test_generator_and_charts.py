"""Tests for the synthetic data generator, chart rendering and report helpers."""
import pandas as pd
import pytest

import config
from src import analysis, preprocessing, visualization
from src.data_generator import (bounce_probability, conversion_probability,
                                generate_website_traffic_data)


@pytest.fixture(scope="module")
def generated() -> pd.DataFrame:
    return generate_website_traffic_data(num_records=300, random_seed=1)


def test_generator_is_reproducible(generated):
    again = generate_website_traffic_data(num_records=300, random_seed=1)
    pd.testing.assert_frame_equal(generated, again)


def test_generator_schema_and_quality_issues(generated):
    assert list(generated.columns) == config.REQUIRED_COLUMNS
    assert len(generated) == 300 + config.GENERATOR_DUPLICATE_ROWS
    cleaned = preprocessing.clean_data(generated)
    assert len(cleaned) == 300
    assert not cleaned[config.COL_SOURCE].str.endswith(" ").any()


def test_probabilities_stay_in_range():
    low, high = config.BOUNCE_PROBABILITY_RANGE
    for device in config.GENERATOR_DEVICES:
        for source, _, _ in config.GENERATOR_SOURCES:
            assert low <= bounce_probability(device, source) <= high
            assert 0 < conversion_probability(device, source, 8) < 1


def test_kpis_handle_empty_frame(generated):
    empty = preprocessing.clean_data(generated).iloc[0:0]
    kpis = analysis.compute_kpis(empty).set_index("KPI")["Value"]
    assert kpis["Total Sessions"] == 0
    assert kpis["Conversion Rate"] == 0


def test_create_all_charts_writes_every_file(generated, tmp_path):
    clean = preprocessing.clean_data(generated)
    tables = analysis.build_analysis_tables(clean)
    paths = visualization.create_all_charts(tables, analysis.compute_correlations(clean), tmp_path)
    assert len(paths) == len(config.CHART_SPECS) + 1
    assert all(path.is_file() for path in paths)


def test_render_chart_rejects_unknown_kind(tmp_path):
    spec = {"kind": "pie", "table": "t", "filename": "x.png"}
    with pytest.raises(ValueError, match="Unsupported chart kind"):
        visualization.render_chart(spec, {"t": pd.DataFrame()}, tmp_path)
