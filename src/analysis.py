"""Business logic: KPIs, grouped summaries and insight extraction.

Functions take and return DataFrames only (no printing, plotting or file I/O).
"""
from typing import Dict, List

import pandas as pd

import config as cfg

_ROUND = cfg.DECIMAL_PLACES


def _safe_divide(numerator: float, denominator: float) -> float:
    """Divide, returning 0.0 instead of raising/inf when the denominator is zero."""
    return float(numerator) / float(denominator) if denominator else 0.0


def compute_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """Compute headline KPIs for the whole dataset as a KPI/Value table."""
    sessions = df[cfg.COL_SESSION].nunique()
    page_views = df[cfg.COL_PAGE_VIEWS].sum()
    conversions = df[cfg.COL_CONVERSIONS].sum()
    revenue = df[cfg.COL_REVENUE].sum()
    rows = {
        "Total Sessions": sessions,
        "Unique Users": df[cfg.COL_USER].nunique(),
        "Total Page Views": page_views,
        "Pages per Session": _safe_divide(page_views, sessions),
        "Average Session Duration": df[cfg.COL_DURATION].mean(),
        "Bounce Rate": df[cfg.COL_BOUNCE].mean() * 100,
        "Total Conversions": conversions,
        "Conversion Rate": _safe_divide(conversions, sessions) * 100,
        "Total Revenue": revenue,
        "Revenue per Session": _safe_divide(revenue, sessions),
    }
    return pd.DataFrame({"KPI": list(rows), "Value": [round(v, _ROUND) for v in rows.values()]})


def summarize_by(df: pd.DataFrame, dimension: str) -> pd.DataFrame:
    """Aggregate traffic, engagement and conversion metrics by one dimension.

    Args:
        df: cleaned dataset.
        dimension: column to group by (e.g. Source, Device, Hour).
    """
    summary = df.groupby(dimension).agg(
        Sessions=(cfg.COL_SESSION, "nunique"),
        Users=(cfg.COL_USER, "nunique"),
        Page_Views=(cfg.COL_PAGE_VIEWS, "sum"),
        Average_Duration=(cfg.COL_DURATION, "mean"),
        Bounce_Rate=(cfg.COL_BOUNCE, "mean"),
        Conversions=(cfg.COL_CONVERSIONS, "sum"),
        Revenue=(cfg.COL_REVENUE, "sum"),
    ).reset_index()
    summary["Pages_per_Session"] = summary["Page_Views"] / summary["Sessions"]
    summary["Conversion_Rate"] = summary["Conversions"] / summary["Sessions"] * 100
    summary["Bounce_Rate"] = summary["Bounce_Rate"] * 100
    cols = ["Average_Duration", "Bounce_Rate", "Pages_per_Session", "Conversion_Rate", "Revenue"]
    summary[cols] = summary[cols].round(_ROUND)
    return summary


def summarize_trend(df: pd.DataFrame, period: str) -> pd.DataFrame:
    """Aggregate sessions, users, page views, conversions and revenue over time.

    Args:
        period: "daily" or "monthly".
    """
    if period == "daily":
        key = df[cfg.COL_DATE]
        label = cfg.COL_DATE
    elif period == "monthly":
        key = df[cfg.COL_DATE].dt.to_period("M").astype(str)
        label = "Month"
    else:
        raise ValueError(f"period must be 'daily' or 'monthly', got {period!r}")
    return df.groupby(key.rename(label)).agg(
        Sessions=(cfg.COL_SESSION, "nunique"),
        Users=(cfg.COL_USER, "nunique"),
        Page_Views=(cfg.COL_PAGE_VIEWS, "sum"),
        Conversions=(cfg.COL_CONVERSIONS, "sum"),
        Revenue=(cfg.COL_REVENUE, "sum"),
    ).reset_index()


def compute_engagement_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Overall engagement metrics as a Metric/Value table."""
    sessions = df[cfg.COL_SESSION].nunique()
    metrics = {
        "Total Page Views": df[cfg.COL_PAGE_VIEWS].sum(),
        "Average Page Views per Session": _safe_divide(df[cfg.COL_PAGE_VIEWS].sum(), sessions),
        "Average Session Duration": df[cfg.COL_DURATION].mean(),
        "Bounce Rate": df[cfg.COL_BOUNCE].mean() * 100,
    }
    return pd.DataFrame({"Metric": list(metrics), "Value": [round(v, _ROUND) for v in metrics.values()]})


def compute_correlations(df: pd.DataFrame) -> pd.DataFrame:
    """Correlation matrix of the numeric behaviour columns."""
    return df[cfg.CORRELATION_COLUMNS].corr()


def build_analysis_tables(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Run every analysis and return the results keyed by output table name."""
    by_source = summarize_by(df, cfg.COL_SOURCE)
    by_device = summarize_by(df, cfg.COL_DEVICE)
    return {
        "kpi_summary": compute_kpis(df),
        "source_analysis": by_source,
        "device_analysis": by_device,
        "hour_analysis": summarize_by(df, cfg.COL_HOUR),
        "daily_analysis": summarize_trend(df, "daily"),
        "monthly_analysis": summarize_trend(df, "monthly"),
        "engagement_summary": compute_engagement_summary(df),
        "bounce_by_source": by_source[[cfg.COL_SOURCE, "Sessions", "Bounce_Rate"]],
        "bounce_by_device": by_device[[cfg.COL_DEVICE, "Sessions", "Bounce_Rate"]],
        "conversion_by_source": by_source[[cfg.COL_SOURCE, "Sessions", "Conversions", "Revenue", "Conversion_Rate"]],
        "conversion_by_device": by_device[[cfg.COL_DEVICE, "Sessions", "Conversions", "Revenue", "Conversion_Rate"]],
    }


def _top(table: pd.DataFrame, column: str) -> pd.Series:
    """Return the row of ``table`` with the largest value in ``column``."""
    return table.loc[table[column].idxmax()]


def generate_insights(tables: Dict[str, pd.DataFrame]) -> List[str]:
    """Turn analysis tables into human-readable business insight lines."""
    src, dev = tables["source_analysis"], tables["device_analysis"]
    hour, day = tables["hour_analysis"], tables["daily_analysis"]
    top_src, top_conv = _top(src, "Sessions"), _top(src, "Conversion_Rate")
    top_dev, top_eng = _top(dev, "Sessions"), _top(dev, "Pages_per_Session")
    peak, best = _top(hour, "Sessions"), _top(hour, "Conversion_Rate")
    top_day = _top(day, "Sessions")
    return [
        f"1. Highest traffic source: {top_src[cfg.COL_SOURCE]} ({int(top_src['Sessions'])} sessions)",
        f"2. Highest conversion-rate source: {top_conv[cfg.COL_SOURCE]} ({top_conv['Conversion_Rate']}%)",
        f"3. Highest traffic device: {top_dev[cfg.COL_DEVICE]} ({int(top_dev['Sessions'])} sessions)",
        f"4. Most pages per session: {top_eng[cfg.COL_DEVICE]} ({top_eng['Pages_per_Session']})",
        f"5. Peak traffic hour: {int(peak[cfg.COL_HOUR])}:00 ({int(peak['Sessions'])} sessions)",
        f"6. Highest conversion-rate hour: {int(best[cfg.COL_HOUR])}:00 ({best['Conversion_Rate']}%)",
        f"7. Highest traffic day: {top_day[cfg.COL_DATE]:%Y-%m-%d} ({int(top_day['Sessions'])} sessions)",
        "Note: correlation shows association and does not prove causation.",
    ]
