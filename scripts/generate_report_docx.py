"""Create a DOCX report from the current dataset and generated charts."""
import argparse
import logging
from pathlib import Path
from typing import Dict, List

import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

import config
from src.analysis import build_analysis_tables, generate_insights
from src.data_loader import DataLoadError, load_raw_data
from src.preprocessing import clean_data
from src.utils import ensure_dir, setup_logging

logger = logging.getLogger(__name__)


def load_report_data() -> pd.DataFrame:
    """Return the cleaned dataset used for the report.

    Raises:
        DataLoadError: if neither the raw nor the processed dataset exists.
        ValueError: if the dataset is empty.
    """
    if config.RAW_DATA_PATH.is_file():
        clean = clean_data(load_raw_data())
    elif config.PROCESSED_DATA_PATH.is_file():
        clean = pd.read_csv(config.PROCESSED_DATA_PATH, parse_dates=[config.COL_DATE])
    else:
        raise DataLoadError("No raw or processed dataset found. Run `python main.py` first.")
    if clean.empty:
        raise ValueError("Cannot create a report from an empty dataset.")
    return clean


def _add_metric_table(document: Document, frame: pd.DataFrame, columns: List[str]) -> None:
    """Append a formatted table containing selected columns."""
    table = document.add_table(rows=1, cols=len(columns))
    table.style = config.REPORT_TABLE_STYLE
    for cell, heading in zip(table.rows[0].cells, columns):
        cell.text = str(heading).replace("_", " ")
    for _, row in frame[columns].iterrows():
        cells = table.add_row().cells
        for cell, value in zip(cells, row):
            cell.text = f"{value:,.{config.DECIMAL_PLACES}f}" if isinstance(value, float) else str(value)


def _add_chart(document: Document, filename: str) -> None:
    """Add a generated chart (captioned from config) when it exists; skip absent charts."""
    image_path = config.FIGURES_DIR / filename
    if not image_path.is_file():
        logger.warning("Chart not found, skipped: %s", image_path.name)
        return
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.add_run().add_picture(str(image_path), width=Inches(config.REPORT_IMAGE_WIDTH_INCHES))
    caption = document.add_paragraph(config.REPORT_CAPTIONS.get(filename, filename))
    caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if caption.runs:
        caption.runs[0].italic = True
        caption.runs[0].font.size = Pt(config.REPORT_CAPTION_SIZE_PT)


def _setup_document() -> Document:
    """Create a document with configured margins and base font."""
    document = Document()
    section = document.sections[0]
    section.top_margin = section.bottom_margin = Inches(config.REPORT_MARGIN_INCHES)
    normal = document.styles["Normal"]
    normal.font.name = config.REPORT_FONT_NAME
    normal.font.size = Pt(config.REPORT_FONT_SIZE_PT)
    return document


def _add_title_block(document: Document, clean: pd.DataFrame) -> None:
    """Add the title, subtitle and analysis-period line."""
    document.add_heading(config.REPORT_TITLE, 0).alignment = WD_ALIGN_PARAGRAPH.CENTER
    document.add_paragraph(config.REPORT_SUBTITLE).alignment = WD_ALIGN_PARAGRAPH.CENTER
    start = clean[config.COL_DATE].min().strftime(config.REPORT_DATE_FORMAT)
    end = clean[config.COL_DATE].max().strftime(config.REPORT_DATE_FORMAT)
    meta = document.add_paragraph(f"Analysis period: {start} – {end} | Records: {len(clean):,}")
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER


def _add_executive_summary(document: Document, kpis: Dict[str, float]) -> None:
    """Add the executive summary and KPI table sections."""
    document.add_heading("1. Executive Summary", level=1)
    document.add_paragraph(
        f"The dataset contains {int(kpis['Total Sessions']):,} sessions from "
        f"{int(kpis['Unique Users']):,} unique users, generating "
        f"{int(kpis['Total Page Views']):,} page views and revenue of "
        f"{float(kpis['Total Revenue']):,.2f}. The overall conversion rate is "
        f"{float(kpis['Conversion Rate']):.2f}% and the bounce rate is "
        f"{float(kpis['Bounce Rate']):.2f}%. All figures are calculated from the current dataset."
    )


def _add_segment_section(document: Document, heading: str, table: pd.DataFrame,
                         dimension: str, chart: str) -> None:
    """Add a segment (source/device) section: heading, table and chart."""
    document.add_heading(heading, level=1)
    _add_metric_table(document, table, [dimension] + config.REPORT_SEGMENT_COLUMNS)
    _add_chart(document, chart)


def _add_time_section(document: Document, tables: Dict[str, pd.DataFrame]) -> None:
    """Add busiest hour/month statements and the time-trend charts."""
    document.add_heading("5. Time-based Traffic Patterns", level=1)
    hourly = tables["hour_analysis"].sort_values("Sessions", ascending=False)
    monthly = tables["monthly_analysis"].sort_values("Sessions", ascending=False)
    if not hourly.empty:
        peak = hourly.iloc[0]
        document.add_paragraph(
            f"The busiest hour is {int(peak[config.COL_HOUR])}:00 with {int(peak['Sessions']):,} sessions.")
    if not monthly.empty:
        peak_month = monthly.iloc[0]
        document.add_paragraph(
            f"The busiest month is {peak_month['Month']} with {int(peak_month['Sessions']):,} sessions.")
    _add_chart(document, config.FIG_DAILY_SESSIONS)
    _add_chart(document, config.FIG_SESSIONS_BY_HOUR)


def create_report(output_path: Path = config.REPORT_PATH) -> Path:
    """Build a data-driven report from the current dataset and chart outputs."""
    clean = load_report_data()
    tables = build_analysis_tables(clean)
    kpis = tables["kpi_summary"].set_index("KPI")["Value"].to_dict()
    by_sessions = lambda name: tables[name].sort_values("Sessions", ascending=False)  # noqa: E731

    document = _setup_document()
    _add_title_block(document, clean)
    _add_executive_summary(document, kpis)
    document.add_heading("2. Key Performance Indicators", level=1)
    _add_metric_table(document, tables["kpi_summary"], ["KPI", "Value"])
    _add_segment_section(document, "3. Acquisition Source Analysis", by_sessions("source_analysis"),
                         config.COL_SOURCE, config.FIG_TRAFFIC_BY_SOURCE)
    _add_segment_section(document, "4. Device Analysis", by_sessions("device_analysis"),
                         config.COL_DEVICE, config.FIG_TRAFFIC_BY_DEVICE)
    _add_time_section(document, tables)

    document.add_heading("6. Business Insights", level=1)
    for insight in generate_insights(tables):
        document.add_paragraph(insight, style="List Bullet")

    document.add_heading("7. Recommendations", level=1)
    document.add_paragraph(config.REPORT_RECOMMENDATION_TEXT)
    for chart in (config.FIG_BOUNCE_BY_SOURCE, config.FIG_CONVERSION_BY_SOURCE,
                  config.FIG_CORRELATION_HEATMAP):
        _add_chart(document, chart)

    output_path = Path(output_path)
    ensure_dir(output_path.parent)
    document.save(output_path)
    logger.info("Report saved to %s", output_path)
    return output_path


def main() -> int:
    """CLI entry point for report generation."""
    setup_logging()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=config.REPORT_PATH, help="DOCX output path")
    args = parser.parse_args()
    try:
        create_report(args.output)
    except (DataLoadError, ValueError) as exc:
        logger.error("Report not created: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
