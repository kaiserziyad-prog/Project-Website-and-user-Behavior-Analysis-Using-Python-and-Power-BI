"""Streamlit views for the schema-free dashboard (any uploaded table)."""
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

import config
from src.dashboard import generic
from src.dashboard.charts import (render_bar_chart, render_correlation_heatmap, render_histogram,
                                  render_horizontal_bars, render_line_chart, render_scatter)

_CARDS_PER_ROW = 4
_MAX_KPI_CARDS = 8
_SCATTER_SAMPLE = 5000


def _show(fig: plt.Figure) -> None:
    """Render a figure and free its memory."""
    st.pyplot(fig)
    plt.close(fig)


def _fmt(value: float) -> str:
    if pd.isna(value):
        return "–"
    return f"{value:,.0f}" if abs(value) >= 1000 else f"{value:,.2f}"


def _cards(items) -> None:
    for start in range(0, len(items), _CARDS_PER_ROW):
        row = st.columns(_CARDS_PER_ROW)
        for slot, (label, value, *help_text) in zip(row, items[start:start + _CARDS_PER_ROW]):
            slot.metric(label, value, help=help_text[0] if help_text else None)


def show_generic_dashboard(profile: generic.Profile) -> None:
    """Render a statistics dashboard built only from the columns present in ``profile``."""
    frame = profile.frame
    st.subheader("📌 Dataset at a glance")
    missing_pct = frame.isna().to_numpy().mean() * 100 if frame.size else 0.0
    _cards([
        ("Rows", f"{len(frame):,}"), ("Columns", f"{frame.shape[1]:,}"),
        ("Numeric columns", f"{len(profile.numeric)}"), ("Category columns", f"{len(profile.categorical)}"),
        ("Date columns", f"{len(profile.datetime)}"), ("Missing cells", f"{missing_pct:.2f}%"),
        ("Duplicate rows", f"{profile.duplicate_rows:,}"),
        ("Empty columns removed", f"{len(profile.dropped_empty_columns)}"),
    ])
    tabs = st.tabs(["📋 Overview", "🔢 Numeric", "🏷️ Categories", "📈 Trends", "🔗 Relationships", "🗂️ Data"])
    with tabs[0]:
        _overview(profile)
    with tabs[1]:
        _numeric(profile)
    with tabs[2]:
        _categories(profile)
    with tabs[3]:
        _trends(profile)
    with tabs[4]:
        _relationships(profile)
    with tabs[5]:
        _data(profile)


def _overview(profile: generic.Profile) -> None:
    st.markdown("#### Quick insights")
    for note in generic.quick_insights(profile):
        st.markdown(f"- {note}")
    st.markdown("#### Columns")
    st.dataframe(generic.column_overview(profile), hide_index=True, width="stretch")
    missing = generic.missing_summary(profile.frame)
    if missing.empty:
        st.success("No missing values.")
    else:
        st.markdown("#### Missing values")
        _show(render_horizontal_bars(missing["Column"], missing["Missing %"], "Missing values by column", "Missing (%)"))
    if profile.dropped_empty_columns:
        st.caption("Removed because they were completely empty: " + ", ".join(profile.dropped_empty_columns))


def _numeric(profile: generic.Profile) -> None:
    if not profile.numeric:
        st.info("No numeric columns were found in this file.")
        return
    stat = st.radio("Headline statistic", ["Mean", "Median", "Sum", "Max"], horizontal=True, key="gen_stat")
    summary = generic.numeric_summary(profile.frame, profile.numeric).set_index("Column")
    cards = [(column, _fmt(summary.loc[column, stat]),
              f"Median {_fmt(summary.loc[column, 'Median'])} · Min {_fmt(summary.loc[column, 'Min'])} · "
              f"Max {_fmt(summary.loc[column, 'Max'])}") for column in profile.numeric[:_MAX_KPI_CARDS]]
    _cards(cards)
    if len(profile.numeric) > _MAX_KPI_CARDS:
        st.caption(f"Showing {_MAX_KPI_CARDS} of {len(profile.numeric)} numeric columns; all are in the table below.")
    st.markdown("#### Summary statistics")
    st.dataframe(summary.reset_index().round(config.DECIMAL_PLACES), hide_index=True, width="stretch")

    st.markdown("#### Distributions")
    options = profile.varying_numeric
    if not options:
        st.info("All numeric columns hold a single constant value, so there is no distribution to plot.")
        return
    chosen = st.multiselect("Columns to plot", options, default=options[:6], key="gen_hist")
    for start in range(0, len(chosen), 2):
        for slot, column in zip(st.columns(2), chosen[start:start + 2]):
            with slot:
                _show(render_histogram(profile.frame[column], f"Distribution of {column}"))


def _categories(profile: generic.Profile) -> None:
    options = profile.group_columns
    if not options:
        st.info("No category-style columns were found (columns with a manageable number of repeated values).")
        return
    category = st.selectbox("Group by", options, key="gen_cat")
    counts = generic.category_counts(profile.frame[category])
    left, right = st.columns(2)
    with left:
        _show(render_horizontal_bars(counts.iloc[:, 0], counts["Count"], f"Rows by {category}", "Rows"))
    with right:
        st.dataframe(counts, hide_index=True, width="stretch")
    metrics = [c for c in profile.numeric if c != category]
    if not metrics:
        return
    st.markdown(f"#### Numeric metric by {category}")
    first, second = st.columns(2)
    metric = first.selectbox("Metric", metrics, key="gen_cat_metric")
    agg = second.selectbox("Aggregation", ["mean", "sum", "median", "max", "min"], key="gen_cat_agg")
    result = generic.numeric_by_category(profile.frame, category, metric, agg)
    _show(render_bar_chart(result, category, result.columns[1], f"{agg.title()} of {metric} by {category}",
                           f"{agg} of {metric}"))
    st.dataframe(result.round(config.DECIMAL_PLACES), hide_index=True, width="stretch")


def _trends(profile: generic.Profile) -> None:
    if not profile.datetime:
        st.info("No date/time column was detected, so trends over time are not available for this file.")
        return
    first, second, third, fourth = st.columns(4)
    date_col = first.selectbox("Date column", profile.datetime, key="gen_date")
    metric = second.selectbox("Metric", ["Row count"] + profile.numeric, key="gen_trend_metric")
    agg = third.selectbox("Aggregation", ["sum", "mean", "median", "max", "min"], key="gen_trend_agg",
                          disabled=metric == "Row count")
    frequencies = list(generic.FREQUENCIES)
    default = frequencies.index(generic.auto_frequency(profile.frame[date_col]))
    frequency = fourth.selectbox("Group by", frequencies, index=default, key="gen_trend_freq")
    series = generic.time_series(profile.frame, date_col, None if metric == "Row count" else metric, agg, frequency)
    if series.empty:
        st.info("The selected date column has no valid dates.")
        return
    label = "Rows" if metric == "Row count" else f"{agg.title()} of {metric}"
    _show(render_line_chart(series, date_col, "Value", f"{label} per {frequency.lower()}", label))
    dates = profile.frame[date_col].dropna()
    st.caption(f"Date range: {dates.min():%d %b %Y} to {dates.max():%d %b %Y}")


def _relationships(profile: generic.Profile) -> None:
    usable = profile.varying_numeric
    if len(usable) < 2:
        st.info("At least two numeric columns with varying values are needed to show relationships.")
        return
    corr = generic.correlation_matrix(profile.frame, usable)
    _show(render_correlation_heatmap(corr, annot=len(corr) <= 12))
    st.caption("Correlation shows association between variables and does not prove causation."
               + (f" Showing the first {generic.MAX_HEATMAP_COLUMNS} numeric columns."
                  if len(usable) > generic.MAX_HEATMAP_COLUMNS else ""))
    st.markdown("#### Strongest relationships")
    st.dataframe(generic.top_correlations(corr), hide_index=True, width="stretch")
    st.markdown("#### Compare two columns")
    left, right = st.columns(2)
    x = left.selectbox("X axis", usable, key="gen_x")
    y = right.selectbox("Y axis", usable, index=min(1, len(usable) - 1), key="gen_y")
    if x == y:
        st.info("Choose two different columns to compare.")
        return
    data = profile.frame[[x, y]].dropna()
    if len(data) > _SCATTER_SAMPLE:
        data = data.sample(_SCATTER_SAMPLE, random_state=0)
        st.caption(f"Plotting a random sample of {_SCATTER_SAMPLE:,} points.")
    _show(render_scatter(data, x, y))


def _data(profile: generic.Profile) -> None:
    st.caption(f"Showing the first {min(len(profile.frame), 1000):,} of {len(profile.frame):,} rows.")
    st.dataframe(profile.frame.head(1000), width="stretch")
    st.download_button("⬇️ Download tidied data (CSV)", profile.frame.to_csv(index=False).encode(config.CSV_ENCODING),
                       file_name="tidied_data.csv", mime="text/csv")
