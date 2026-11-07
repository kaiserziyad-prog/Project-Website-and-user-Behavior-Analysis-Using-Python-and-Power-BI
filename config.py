"""Central configuration: paths, schema, thresholds, generator, chart and report settings.

Every tunable value used by the application lives here so that behaviour can be
changed without editing business logic.
"""
from pathlib import Path

# --- Paths -----------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
RAW_DATA_PATH = BASE_DIR / "data" / "raw" / "website_traffic.csv"
PROCESSED_DATA_PATH = BASE_DIR / "data" / "processed" / "website_traffic_cleaned.csv"
TABLES_DIR = BASE_DIR / "outputs" / "tables"
FIGURES_DIR = BASE_DIR / "outputs" / "figures"
INSIGHTS_PATH = BASE_DIR / "outputs" / "business_insights.txt"
REPORT_PATH = BASE_DIR / "outputs" / "Website_Traffic_User_Behavior_Report.docx"

# --- Column names ----------------------------------------------------------
COL_DATE = "Date"
COL_HOUR = "Hour"
COL_SESSION = "Session_ID"
COL_USER = "User_ID"
COL_SOURCE = "Source"
COL_MEDIUM = "Medium"
COL_DEVICE = "Device"
COL_BROWSER = "Browser"
COL_COUNTRY = "Country"
COL_PAGE_VIEWS = "Page_Views"
COL_DURATION = "Session_Duration"
COL_BOUNCE = "Bounce"
COL_CONVERSIONS = "Conversions"
COL_REVENUE = "Revenue"

REQUIRED_COLUMNS = [
    COL_DATE, COL_HOUR, COL_SESSION, COL_USER, COL_SOURCE, COL_MEDIUM, COL_DEVICE,
    COL_BROWSER, COL_COUNTRY, COL_PAGE_VIEWS, COL_DURATION, COL_BOUNCE,
    COL_CONVERSIONS, COL_REVENUE,
]
NUMERIC_COLUMNS = [
    COL_HOUR, COL_PAGE_VIEWS, COL_DURATION, COL_BOUNCE, COL_CONVERSIONS, COL_REVENUE,
]
TEXT_COLUMNS = [COL_SOURCE, COL_MEDIUM, COL_DEVICE, COL_BROWSER, COL_COUNTRY]
CORRELATION_COLUMNS = NUMERIC_COLUMNS
DASHBOARD_REQUIRED_COLUMNS = [
    COL_DATE, COL_SESSION, COL_USER, COL_PAGE_VIEWS, COL_DURATION, COL_BOUNCE,
    COL_CONVERSIONS, COL_REVENUE, COL_SOURCE, COL_DEVICE, COL_HOUR,
]

# --- Validation rules ------------------------------------------------------
HOUR_RANGE = (0, 23)
BINARY_COLUMNS = [COL_BOUNCE, COL_CONVERSIONS]
NON_NEGATIVE_COLUMNS = [COL_PAGE_VIEWS, COL_DURATION, COL_REVENUE]

# --- Output formatting -----------------------------------------------------
DECIMAL_PLACES = 2
CSV_ENCODING = "utf-8"
DATE_FORMAT = "%Y-%m-%d"
CURRENCY_SYMBOL = "₹"
LOG_LEVEL = "INFO"

# --- Plot settings ---------------------------------------------------------
FIGURE_DPI = 300
FIGURE_SIZE_WIDE = (12, 6)
FIGURE_SIZE_MEDIUM = (10, 6)
FIGURE_SIZE_SMALL = (8, 6)
HEATMAP_SIZE = (10, 7)
HEATMAP_CMAP = "coolwarm"
HEATMAP_TITLE = "Correlation Heatmap"
LABEL_ROTATION = 45

# Chart file names (shared by the chart generator and the DOCX report).
FIG_DAILY_SESSIONS = "daily_sessions.png"
FIG_TRAFFIC_BY_SOURCE = "traffic_by_source.png"
FIG_TRAFFIC_BY_DEVICE = "traffic_by_device.png"
FIG_SESSIONS_BY_HOUR = "sessions_by_hour.png"
FIG_BOUNCE_BY_SOURCE = "bounce_rate_by_source.png"
FIG_PAGES_BY_DEVICE = "pages_per_session_by_device.png"
FIG_CONVERSION_BY_SOURCE = "conversion_rate_by_source.png"
FIG_CORRELATION_HEATMAP = "correlation_heatmap.png"

# Declarative chart definitions rendered by src.visualization.create_all_charts.
CHART_SPECS = [
    {"kind": "line", "table": "daily_analysis", "x": COL_DATE, "y": "Sessions",
     "title": "Daily Sessions", "filename": FIG_DAILY_SESSIONS},
    {"kind": "bar", "table": "source_analysis", "x": COL_SOURCE, "y": "Sessions",
     "title": "Traffic by Source", "ylabel": "Sessions",
     "filename": FIG_TRAFFIC_BY_SOURCE, "rotate_labels": True},
    {"kind": "bar", "table": "device_analysis", "x": COL_DEVICE, "y": "Sessions",
     "title": "Traffic by Device", "ylabel": "Sessions",
     "filename": FIG_TRAFFIC_BY_DEVICE, "size": FIGURE_SIZE_SMALL},
    {"kind": "line", "table": "hour_analysis", "x": COL_HOUR, "y": "Sessions",
     "title": "Sessions by Hour", "filename": FIG_SESSIONS_BY_HOUR, "integer_ticks": True},
    {"kind": "bar", "table": "bounce_by_source", "x": COL_SOURCE, "y": "Bounce_Rate",
     "title": "Bounce Rate by Source", "ylabel": "Bounce Rate (%)",
     "filename": FIG_BOUNCE_BY_SOURCE, "rotate_labels": True},
    {"kind": "bar", "table": "device_analysis", "x": COL_DEVICE, "y": "Pages_per_Session",
     "title": "Pages per Session by Device", "ylabel": "Pages per Session",
     "filename": FIG_PAGES_BY_DEVICE, "size": FIGURE_SIZE_SMALL},
    {"kind": "bar", "table": "conversion_by_source", "x": COL_SOURCE, "y": "Conversion_Rate",
     "title": "Conversion Rate by Source", "ylabel": "Conversion Rate (%)",
     "filename": FIG_CONVERSION_BY_SOURCE, "rotate_labels": True},
]

# --- Dashboard settings ----------------------------------------------------
DASHBOARD_PAGE_TITLE = "Website Traffic Analysis"
DASHBOARD_PAGE_ICON = "📊"
DASHBOARD_FIGSIZE_BAR = (8, 5)
DASHBOARD_FIGSIZE_LINE = (12, 5)

# --- Report settings -------------------------------------------------------
REPORT_TITLE = "Website Traffic & User Behavior Analysis"
REPORT_SUBTITLE = "Data-driven business intelligence report"
REPORT_FONT_NAME = "Calibri"
REPORT_FONT_SIZE_PT = 10
REPORT_MARGIN_INCHES = 0.7
REPORT_IMAGE_WIDTH_INCHES = 5.8
REPORT_CAPTION_SIZE_PT = 9
REPORT_TABLE_STYLE = "Light Shading Accent 1"
REPORT_DATE_FORMAT = "%d %b %Y"
REPORT_RECOMMENDATION_TEXT = (
    "Prioritize acquisition channels with strong conversion performance, investigate "
    "high-bounce segments, and review device-specific user journeys. Validate any "
    "proposed campaign changes with controlled experiments before reallocating "
    "significant budget."
)
REPORT_CAPTIONS = {
    FIG_TRAFFIC_BY_SOURCE: "Sessions by acquisition source",
    FIG_TRAFFIC_BY_DEVICE: "Sessions by device",
    FIG_DAILY_SESSIONS: "Daily session trend",
    FIG_SESSIONS_BY_HOUR: "Sessions by hour",
    FIG_BOUNCE_BY_SOURCE: "Bounce rate by acquisition source",
    FIG_CONVERSION_BY_SOURCE: "Conversion rate by acquisition source",
    FIG_CORRELATION_HEATMAP: "Correlation matrix; association does not imply causation",
}
REPORT_SEGMENT_COLUMNS = ["Sessions", "Bounce_Rate", "Conversion_Rate", "Revenue"]

# --- Synthetic data generator ----------------------------------------------
DEFAULT_GENERATED_RECORDS = 6000
DEFAULT_RANDOM_SEED = 42
GENERATOR_START_DATE = "2026-01-01"
GENERATOR_END_DATE = "2026-03-31"
GENERATOR_NUM_USERS = 3800          # distinct users (repeat visits are simulated)
GENERATOR_USER_PREFIX = "USER_"
GENERATOR_USER_ID_START = 1000
GENERATOR_SESSION_PREFIX = "SESS_"
GENERATOR_SESSION_ID_START = 10000

# (source, medium, traffic share)
GENERATOR_SOURCES = [
    ("Google", "organic", 0.32),
    ("Direct", "none", 0.22),
    ("Social Media", "social", 0.18),
    ("Paid Search", "cpc", 0.12),
    ("Email", "email", 0.08),
    ("Referral", "referral", 0.05),
    ("Display", "cpm", 0.03),
]
GENERATOR_DEVICES = ["Mobile", "Desktop", "Tablet"]
GENERATOR_DEVICE_WEIGHTS = [0.52, 0.40, 0.08]
GENERATOR_BROWSERS = ["Chrome", "Safari", "Edge", "Firefox", "Opera"]
GENERATOR_BROWSER_WEIGHTS = [0.58, 0.24, 0.10, 0.06, 0.02]
GENERATOR_COUNTRIES = ["United States", "India", "United Kingdom", "Germany", "Canada", "Australia"]
GENERATOR_COUNTRY_WEIGHTS = [0.40, 0.25, 0.15, 0.08, 0.07, 0.05]
# Relative traffic per hour 00-23 (evening and lunch/afternoon peaks); normalised at runtime.
GENERATOR_HOURLY_WEIGHTS = [
    0.015, 0.010, 0.008, 0.006, 0.006, 0.010,
    0.020, 0.035, 0.050, 0.060, 0.065, 0.060,
    0.065, 0.060, 0.055, 0.050, 0.055, 0.065,
    0.085, 0.095, 0.090, 0.075, 0.045, 0.025,
]

# Bounce model
BASE_BOUNCE_PROBABILITY = 0.38
BOUNCE_DEVICE_ADJUSTMENT = {"Mobile": 0.07, "Desktop": -0.05}
BOUNCE_SOURCE_ADJUSTMENT = {
    "Social Media": 0.12, "Display": 0.12, "Email": -0.10, "Direct": -0.10, "Google": -0.02,
}
BOUNCE_PROBABILITY_RANGE = (0.15, 0.65)
BOUNCE_DURATION_RANGE = (5, 45)      # seconds, bounced sessions have exactly 1 page view

# Engagement model for non-bounced sessions: (mean, std, min, max)
ENGAGEMENT_PROFILES = {
    "Desktop": {"page_views": (5.5, 2.0, 2, 16), "duration": (320, 110, 50, 950)},
    "default": {"page_views": (3.8, 1.5, 2, 12), "duration": (210, 80, 45, 650)},
}

# Conversion model
DEFAULT_CONVERSION_PROBABILITY = 0.08
CONVERSION_SOURCE_PROBABILITY = {
    "Email": 0.13, "Paid Search": 0.13, "Direct": 0.09, "Google": 0.09,
    "Social Media": 0.035, "Display": 0.035,
}
CONVERSION_DEVICE_MULTIPLIER = {"Desktop": 1.25, "Mobile": 0.85}
CONVERSION_HIGH_ENGAGEMENT_PAGE_VIEWS = 6
CONVERSION_HIGH_ENGAGEMENT_MULTIPLIER = 1.4
REVENUE_GAMMA_SHAPE = 3.5
REVENUE_GAMMA_SCALE = 32.0
REVENUE_RANGE = (29.99, 499.99)

# Deliberate data-quality issues injected for the cleaning step to handle.
GENERATOR_DUPLICATE_ROWS = 8
GENERATOR_WHITESPACE_ROWS = 15
GENERATOR_QUALITY_SEED = 42
