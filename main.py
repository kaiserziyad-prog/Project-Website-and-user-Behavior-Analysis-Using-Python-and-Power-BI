"""Entry point: load -> clean -> analyse -> visualise -> report insights.

Usage:
    python main.py
"""
import logging
import sys

import config
from src import analysis, preprocessing, visualization
from src.data_loader import DataLoadError, load_raw_data, save_dataframe, save_text
from src.utils import setup_logging

logger = logging.getLogger("cronus")


def run_pipeline() -> None:
    """Execute the complete analysis pipeline."""
    raw = load_raw_data()
    clean = preprocessing.clean_data(raw)
    save_dataframe(clean, config.PROCESSED_DATA_PATH)

    tables = analysis.build_analysis_tables(clean)
    for name, table in tables.items():
        save_dataframe(table, config.TABLES_DIR / f"{name}.csv")

    visualization.create_all_charts(tables, analysis.compute_correlations(clean))

    insights = analysis.generate_insights(tables)
    save_text(insights, config.INSIGHTS_PATH)
    for line in insights:
        logger.info(line)


def main() -> int:
    """Run the pipeline and return a process exit code."""
    setup_logging()
    try:
        run_pipeline()
    except DataLoadError as exc:
        logger.error("Pipeline aborted: %s", exc)
        return 1
    except Exception:  # noqa: BLE001 - last-resort handler for the CLI
        logger.exception("Unexpected failure")
        return 2
    logger.info("Pipeline finished successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
