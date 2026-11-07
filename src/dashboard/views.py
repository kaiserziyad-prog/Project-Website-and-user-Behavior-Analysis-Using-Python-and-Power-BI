"""Streamlit presentation functions; calculations live in ``src.analysis``/``dashboard.data``."""
import pandas as pd
import streamlit as st

import config
from src import analysis
from src.dashboard.charts import render_bar_chart, render_correlation_heatmap, render_line_chart
from src.dashboard.data import calculate_dashboard_metrics, grouped_analysis

_CARDS_PER_ROW = 4


def show_kpis(frame: pd.DataFrame) -> None:
    """Display overall website performance metrics."""
    metrics = calculate_dashboard_metrics(frame)
    st.subheader("📌 Key Performance Indicators")
    cards = [
        ("Total Sessions", f"{metrics['sessions']:,}"),
        ("Unique Users", f"{metrics['users']:,}"),
        ("Total Page Views", f"{metrics['page_views']:,}"),
        ("Total Revenue", f"{config.CURRENCY_SYMBOL}{metrics['revenue']:,.2f}"),
        ("Pages / Session", f"{metrics['pages_per_session']:.2f}"),
        ("Avg Session Duration", f"{metrics['average_duration']:.2f} sec"),
        ("Bounce Rate", f"{metrics['bounce_rate']:.2f}%"),
        ("Conversion Rate", f"{metrics['conversion_rate']:.2f}%"),
    ]
    rows = [st.columns(_CARDS_PER_ROW) for _ in range(-(-len(cards) // _CARDS_PER_ROW))]
    for index, (label, value) in enumerate(cards):
        rows[index // _CARDS_PER_ROW][index % _CARDS_PER_ROW].metric(label, value)


def show_traffic_trends(frame: pd.DataFrame) -> None:
    """Display daily and hourly traffic trends."""
    st.subheader("📈 Daily Website Traffic")
    daily = analysis.summarize_trend(frame, "daily")
    st.pyplot(render_line_chart(daily, config.COL_DATE, "Sessions", "Daily Sessions", "Sessions"))
    st.subheader("⏰ Sessions by Hour")
    hourly = grouped_analysis(frame, config.COL_HOUR).sort_values(config.COL_HOUR)
    st.pyplot(render_line_chart(hourly, config.COL_HOUR, "Sessions", "Sessions by Hour", "Sessions"))
    if not hourly.empty:
        peak = hourly.loc[hourly["Sessions"].idxmax()]
        best = hourly.loc[hourly["Conversion_Rate"].idxmax()]
        left, right = st.columns(2)
        left.info(f"Peak traffic hour: {int(peak[config.COL_HOUR])}:00 ({int(peak['Sessions'])} sessions)")
        right.success(f"Best conversion hour: {int(best[config.COL_HOUR])}:00 ({best['Conversion_Rate']:.2f}%)")


def show_dimension_analysis(frame: pd.DataFrame, dimension: str, title: str) -> None:
    """Display grouped charts and a detailed performance table."""
    st.subheader(title)
    summary = grouped_analysis(frame, dimension)
    first, second = st.columns(2)
    with first:
        st.pyplot(render_bar_chart(summary, dimension, "Sessions", f"Sessions by {dimension}", "Sessions"))
    with second:
        st.pyplot(render_bar_chart(summary, dimension, "Conversion_Rate",
                                   f"Conversion Rate by {dimension}", "Conversion Rate (%)"))
    st.dataframe(summary.round(config.DECIMAL_PLACES))


def show_bounce_analysis(frame: pd.DataFrame) -> None:
    """Display bounce-rate comparison by acquisition source."""
    st.subheader("🔴 Bounce Rate Analysis")
    summary = grouped_analysis(frame, config.COL_SOURCE)
    st.pyplot(render_bar_chart(summary, config.COL_SOURCE, "Bounce_Rate",
                               "Bounce Rate by Source", "Bounce Rate (%)"))


def show_correlations(frame: pd.DataFrame) -> None:
    """Display correlations between numerical website behaviour measures."""
    st.subheader("🔥 Correlation Analysis")
    st.pyplot(render_correlation_heatmap(analysis.compute_correlations(frame)))
    st.caption("Correlation shows association between variables and does not prove causation.")
