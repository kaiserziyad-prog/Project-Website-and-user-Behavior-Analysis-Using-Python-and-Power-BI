"""Streamlit entry point for the website traffic analytics dashboard.

Starts with the bundled default dataset. Users can instead upload any CSV, TSV, Excel
or JSON file: files in the website-traffic format get the full traffic dashboard, and
every other file gets an automatic statistics dashboard built from its own columns.
"""
from typing import Any, Dict, Optional, Tuple

import pandas as pd
import streamlit as st

import config
from src.dashboard import generic
from src.dashboard.data import (build_template_csv, load_dashboard_data, load_sample_dataset,
                                load_traffic_if_matching)
from src.dashboard.generic_views import show_generic_dashboard
from src.dashboard.views import (show_bounce_analysis, show_correlations,
                                 show_dimension_analysis, show_kpis, show_traffic_trends)



@st.cache_data(show_spinner=False)
def _cached_default() -> pd.DataFrame:
    return load_dashboard_data()


@st.cache_data(show_spinner="Loading sample datasheet...")
def _cached_sample(name: str) -> pd.DataFrame:
    return load_sample_dataset(name)


@st.cache_data(show_spinner="Reading your file...")
def _cached_upload(content: bytes, name: str) -> Dict[str, Any]:
    """Parse an upload into either a cleaned traffic frame or a generic profile."""
    raw = generic.read_table(content, name)
    traffic = load_traffic_if_matching(raw)
    if traffic is not None:
        return {"kind": "traffic", "frame": traffic[0], "summary": traffic[1]}
    profile = generic.prepare_table(raw)
    if profile.frame.empty or profile.frame.shape[1] == 0:
        raise ValueError("No usable data was found in this file (it has no data rows or only empty columns).")
    return {"kind": "generic", "profile": profile}


def choose_dataset() -> Tuple[str, Any, str]:
    """Render the sidebar and return ``(kind, data, label)``.

    ``kind`` is ``"traffic"`` (data is a cleaned DataFrame) or ``"generic"`` (data is a
    ``generic.Profile``). Falls back to the default dataset when no valid upload exists.
    """
    default = _cached_default()
    fallback = ("traffic", default, f"{config.SAMPLE_DEFAULT_NAME} sample datasheet")
    with st.sidebar:
        st.header("📂 Data source")
        choice = st.radio("Choose dataset", [config.DASHBOARD_SOURCE_DEFAULT, config.DASHBOARD_SOURCE_UPLOAD],
                          label_visibility="collapsed")
        if choice == config.DASHBOARD_SOURCE_DEFAULT:
            sample = st.selectbox("Sample datasheet", list(config.SAMPLE_DATASETS))
            try:
                frame = _cached_sample(sample)
            except (FileNotFoundError, ValueError) as exc:
                st.error(str(exc))
                return fallback
            st.download_button("⬇️ Download sample CSV", build_template_csv(frame),
                               file_name=f"{sample.split()[0].lower()}_sample.csv", mime="text/csv")
            return "traffic", frame, f"{sample} sample datasheet"

        uploaded = st.file_uploader("Upload a data file", type=generic.SUPPORTED_EXTENSIONS)
        if uploaded is None:
            st.info("No file uploaded yet - showing the default sample datasheet.")
            return fallback
        try:
            result = _cached_upload(uploaded.getvalue(), uploaded.name)
        except ValueError as exc:
            st.error(str(exc))
            st.warning("Showing the default sample datasheet instead.")
            return fallback

        if result["kind"] == "traffic":
            summary = result["summary"]
            st.success(f"Website-traffic format detected: {summary['rows_used']:,} rows loaded.")
            if summary["rows_removed"]:
                st.caption(f"{summary['rows_removed']:,} invalid or duplicate rows were removed.")
            return "traffic", result["frame"], f"uploaded file ({uploaded.name})"
        profile = result["profile"]
        st.success(f"Loaded {len(profile.frame):,} rows × {profile.frame.shape[1]} columns.")
        return "generic", profile, f"uploaded file ({uploaded.name})"


def render_traffic_dashboard(frame: pd.DataFrame, label: str) -> None:
    """The website-traffic dashboard (default data or traffic-format uploads)."""
    filtered = frame.copy()
    with st.sidebar:
        st.header("🔎 Dashboard filters")
        min_date = filtered[config.COL_DATE].min().date()
        max_date = filtered[config.COL_DATE].max().date()
        date_range = st.date_input("Date range", value=(min_date, max_date),
                                   min_value=min_date, max_value=max_date)
        sources = sorted(filtered[config.COL_SOURCE].dropna().astype(str).unique())
        selected_sources = st.multiselect("Traffic sources", sources, default=sources)
        devices = sorted(filtered[config.COL_DEVICE].dropna().astype(str).unique())
        selected_devices = st.multiselect("Devices", devices, default=devices)

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = date_range
        filtered = filtered[
            filtered[config.COL_DATE].dt.date.between(start, end)
        ]
    if selected_sources:
        filtered = filtered[filtered[config.COL_SOURCE].isin(selected_sources)]
    if selected_devices:
        filtered = filtered[filtered[config.COL_DEVICE].isin(selected_devices)]

    if filtered.empty:
        st.warning("No sessions match the selected filters.")
        return

    frame = filtered
    dates = frame[config.COL_DATE]
    st.caption(f"Showing: **{label}** · {len(frame):,} sessions · "
               f"{dates.min():%d %b %Y} to {dates.max():%d %b %Y}")
    sections = (
        lambda: show_kpis(frame),
        lambda: show_traffic_trends(frame),
        lambda: show_dimension_analysis(frame, config.COL_SOURCE, "🌐 Traffic Source Analysis"),
        lambda: show_dimension_analysis(frame, config.COL_DEVICE, "💻 Device Analysis"),
        lambda: show_bounce_analysis(frame),
        lambda: show_correlations(frame),
    )
    for index, render in enumerate(sections):
        if index:
            st.divider()
        render()


def main() -> None:
    """Configure the page, load data and render the matching dashboard."""
    st.set_page_config(page_title=config.DASHBOARD_PAGE_TITLE,
                       page_icon=config.DASHBOARD_PAGE_ICON, layout="wide")
    st.title(f"{config.DASHBOARD_PAGE_ICON} Website Traffic & User Behavior Analysis")
    st.markdown("### Business Intelligence Dashboard")
    try:
        kind, data, label = choose_dataset()
    except (FileNotFoundError, ValueError) as exc:
        st.error(str(exc))
        st.stop()
    if kind == "traffic":
        st.write("Explore website traffic, user behavior, engagement, bounce rate, conversions and revenue.")
        render_traffic_dashboard(data, label)
    else:
        st.write(f"Automatic statistics for **{label}**.")
        show_generic_dashboard(data)


if __name__ == "__main__":
    main()
