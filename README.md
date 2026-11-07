# Cronus – Website Traffic & User Behavior Analysis

A modular Python analytics application that validates and cleans website-session data, calculates KPIs and segment summaries, generates charts and business insights, and provides an optional Streamlit dashboard and DOCX report.

## Project structure

```text
cronus-project-refactored/
├── main.py                       # Pipeline entry point
├── app.py                        # Thin Streamlit entry point
├── config.py                     # Central paths, schema and settings
├── data/
│   ├── raw/                       # Source CSV
│   └── processed/                 # Cleaned CSV
├── src/
│   ├── data_loader.py             # CSV input/output and schema validation
│   ├── preprocessing.py           # Type conversion and data-quality rules
│   ├── analysis.py                # Reusable analysis/business logic
│   ├── visualization.py           # Static chart generation (driven by config.CHART_SPECS)
│   ├── data_generator.py          # Config-driven synthetic data generation
│   ├── utils.py                   # Logging and filesystem helpers
│   └── dashboard/                 # Dashboard data, charts and presentation
├── scripts/
│   ├── generate_dataset.py        # Optional synthetic dataset generator
│   └── generate_report_docx.py   # Data-driven DOCX report generator
├── tests/                         # Automated tests (pytest)
├── outputs/tables/                # Analysis CSV files
├── outputs/figures/               # Generated charts
├── outputs/business_insights.txt
├── requirements.txt               # Runtime dependencies
├── requirements-dev.txt           # Runtime + test dependencies
├── pytest.ini
└── README.md
```

## Setup

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
```

Activate the environment:

- Windows PowerShell: `.venv\\Scripts\\Activate.ps1`
- macOS/Linux: `source .venv/bin/activate`

Install dependencies:

```bash
python -m pip install -r requirements.txt
# for running the tests as well:
python -m pip install -r requirements-dev.txt
```

## Run the application

1. Place the source file at `data/raw/website_traffic.csv` (or update `RAW_DATA_PATH` in `config.py`).
2. Run the complete cleaning and analysis pipeline:

```bash
python main.py
```

3. Launch the dashboard:

```bash
python -m streamlit run app.py
```

4. Generate a DOCX report from the current dataset and generated charts:

```bash
python -m scripts.generate_report_docx
```

## Optional: generate sample data

This replaces the configured raw CSV, so back up any original data first.

```bash
python -m scripts.generate_dataset
python -m scripts.generate_dataset --records 8000 --seed 7 --output data/raw/sample.csv
```

## Tests

```bash
python -m pytest -q
```

## Configuration

Edit `config.py` to change input/output paths, column names, validation rules, plot and chart definitions, dashboard and report text, currency symbol, or every synthetic-data parameter (sources, weights, bounce/conversion model, seeds). Paths are resolved relative to the project directory; no developer-specific absolute paths are required.

## Data-quality rules

Rows with unparseable dates/numbers, hours outside 0–23, negative page views/session duration/revenue, non-binary bounce/conversion values, exact duplicate rows, or duplicate session IDs are removed. Cleaning counts are logged. The raw input file is never modified by the analysis pipeline.

## Notes

- The dashboard is a presentation layer; data loading and calculations live in `src/dashboard/`.
- Report KPIs and segment tables are recalculated from the current dataset rather than embedded as fixed values.
- Generated outputs are reproducible from the source dataset and project configuration.
- `outputs/` and `data/processed/` are committed as reference deliverables; running `python main.py` regenerates them.
- No notebooks are used anywhere; all code is plain `.py` modules.
