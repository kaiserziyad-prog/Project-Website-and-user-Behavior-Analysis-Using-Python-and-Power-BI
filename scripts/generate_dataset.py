"""Generate a reproducible sample website-traffic dataset (CLI wrapper)."""
import argparse
import logging
from pathlib import Path

import config
from src.data_generator import generate_website_traffic_data
from src.data_loader import save_dataframe
from src.utils import setup_logging

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=int, default=config.DEFAULT_GENERATED_RECORDS,
                        help="Number of sessions to generate")
    parser.add_argument("--seed", type=int, default=config.DEFAULT_RANDOM_SEED,
                        help="Random seed for reproducibility")
    parser.add_argument("--output", type=Path, default=config.RAW_DATA_PATH, help="CSV output path")
    return parser.parse_args()


def main() -> int:
    """Generate the sample dataset at the requested location."""
    setup_logging()
    args = parse_args()
    if args.records <= 0:
        logger.error("--records must be greater than zero")
        return 2
    dataset = generate_website_traffic_data(num_records=args.records, random_seed=args.seed)
    save_dataframe(dataset, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
