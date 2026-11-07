"""Streamlit entry point for the website traffic analytics dashboard."""
import streamlit as st

import config
from src.dashboard.data import load_dashboard_data
from src.dashboard.views import (show_bounce_analysis, show_correlations,
                                 show_dimension_analysis, show_kpis, show_traffic_trends)


def main() -> None:
    """Configure the page, load data and render dashboard sections."""
    st.set_page_config(page_title=config.DASHBOARD_PAGE_TITLE,
                       page_icon=config.DASHBOARD_PAGE_ICON, layout="wide")
    st.title(f"{config.DASHBOARD_PAGE_ICON} Website Traffic & User Behavior Analysis")
    st.markdown("### Business Intelligence Dashboard")
    st.write("Explore website traffic, user behavior, engagement, bounce rate, conversions and revenue.")
    try:
        frame = load_dashboard_data()
    except (FileNotFoundError, ValueError) as exc:
        st.error(str(exc))
        st.stop()
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


if __name__ == "__main__":
    main()
