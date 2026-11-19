"""Schema-free profiling and statistics for any uploaded table.

Nothing here assumes particular column names: column roles (numeric, date, category,
text, identifier) are detected automatically, and every statistic is computed only from
the columns that actually exist. Functions take and return DataFrames/lists only.
"""
import io
import json
import re
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from pandas.api import types as ptypes

SUPPORTED_EXTENSIONS = ["csv", "tsv", "txt", "xlsx", "json"]
MAX_CATEGORIES = 50              # a text column with more distinct values is "text", not a category
MAX_DISCRETE_NUMERIC = 12        # numeric columns with <= this many values can also be grouped by
MAX_HEATMAP_COLUMNS = 20
_MOSTLY = 0.9                    # share of values that must parse for a column to be numeric/date
_NUMBER_JUNK = r"[,\s₹$€£%]"
_ID_TOKENS = {"id", "index", "idx", "uuid", "key", "unnamed"}
FREQUENCIES = {"Day": "D", "Week": "W", "Month": "MS", "Year": "YS"}
AGGREGATIONS = ["sum", "mean", "median", "min", "max", "count"]


# --- Reading ---------------------------------------------------------------
def read_table(content: bytes, filename: str) -> pd.DataFrame:
    """Read CSV/TSV/TXT (any delimiter or encoding), Excel (.xlsx) or JSON bytes into a DataFrame.

    Raises:
        ValueError: if the file is empty or cannot be interpreted as a table.
    """
    if not content or not content.strip():
        raise ValueError("The uploaded file is empty.")
    ext = Path(filename).suffix.lower().lstrip(".")
    try:
        if ext == "xlsx":
            frame = pd.read_excel(io.BytesIO(content))
        elif ext == "json":
            frame = _read_json(content)
        else:
            frame = _read_delimited(content, "\t" if ext == "tsv" else None)
    except ImportError as exc:
        raise ValueError("Reading Excel files needs the 'openpyxl' package (pip install openpyxl).") from exc
    except Exception as exc:  # noqa: BLE001 - any parser failure becomes a friendly error
        raise ValueError(f"Could not read '{filename}' as a table: {exc}") from exc
    if frame.shape[1] == 0:
        raise ValueError("No columns were found in the file.")
    return frame


def _read_delimited(content: bytes, sep: Optional[str]) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            text = content.decode(encoding)
        except UnicodeDecodeError:
            continue
        frame = pd.read_csv(io.StringIO(text), sep=sep or ",", on_bad_lines="skip")
        if sep is None and frame.shape[1] == 1:        # maybe ; | or tab separated
            try:
                sniffed = pd.read_csv(io.StringIO(text), sep=None, engine="python", on_bad_lines="skip")
                if sniffed.shape[1] > 1:
                    frame = sniffed
            except Exception:  # noqa: BLE001 - keep the single-column result
                pass
        return frame
    raise ValueError("Unsupported text encoding.")


def _read_json(content: bytes) -> pd.DataFrame:
    text = content.decode("utf-8-sig", errors="replace")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return pd.read_json(io.StringIO(text), lines=True)      # JSON Lines
    if isinstance(data, dict):
        lists = [value for value in data.values() if isinstance(value, list)]
        data = lists[0] if lists else [data]
    if data and not all(isinstance(item, dict) for item in data):
        return pd.DataFrame({"value": data})
    return pd.json_normalize(data)


# --- Profiling -------------------------------------------------------------
@dataclass
class Profile:
    """A tidied table plus the detected role of each column."""
    frame: pd.DataFrame
    numeric: List[str] = field(default_factory=list)
    datetime: List[str] = field(default_factory=list)
    categorical: List[str] = field(default_factory=list)
    text: List[str] = field(default_factory=list)
    identifier: List[str] = field(default_factory=list)
    constant: List[str] = field(default_factory=list)
    dropped_empty_columns: List[str] = field(default_factory=list)
    duplicate_rows: int = 0

    @property
    def group_columns(self) -> List[str]:
        """Columns suitable for 'group by' analysis (categories and small discrete numerics)."""
        discrete = [c for c in self.numeric if 2 <= self.frame[c].nunique() <= MAX_DISCRETE_NUMERIC
                    and (self.frame[c].dropna() % 1 == 0).all()]
        return self.categorical + [c for c in discrete if c not in self.categorical]

    @property
    def varying_numeric(self) -> List[str]:
        """Numeric columns that are not constant (usable for histograms/correlations)."""
        return [c for c in self.numeric if c not in self.constant]

    def role_of(self, column: str) -> str:
        for role in ("numeric", "datetime", "categorical", "text", "identifier"):
            if column in getattr(self, role):
                return role
        return "empty"


def _unique_names(columns) -> List[str]:
    seen: Dict[str, int] = {}
    names = []
    for index, raw in enumerate(columns):
        name = str(raw).strip() or f"Column_{index + 1}"
        seen[name] = seen.get(name, 0) + 1
        names.append(name if seen[name] == 1 else f"{name}_{seen[name]}")
    return names


def _as_text(series: pd.Series) -> pd.Series:
    try:
        return series.astype("string").str.strip()
    except (TypeError, ValueError):
        return series.astype(str).str.strip()


def _numeric_if_mostly(text: pd.Series) -> Optional[pd.Series]:
    present = int(text.notna().sum())
    converted = pd.to_numeric(text.str.replace(_NUMBER_JUNK, "", regex=True), errors="coerce")
    return converted if present and converted.notna().sum() / present >= _MOSTLY else None


def _datetime_if_mostly(text: pd.Series) -> Optional[pd.Series]:
    present = text.dropna()
    if present.empty:
        return None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        sample = pd.to_datetime(present.head(500), errors="coerce", format="mixed")
        if sample.notna().mean() < _MOSTLY:
            return None
        return pd.to_datetime(text, errors="coerce", format="mixed")


def _looks_like_identifier(name: str, series: pd.Series) -> bool:
    tokens = set(re.split(r"[^a-z0-9]+", name.lower()))
    named_like_id = bool(tokens & _ID_TOKENS) or re.search(r"[a-z]ID$", name) is not None
    present = series.dropna()
    return named_like_id and len(present) >= 20 and present.nunique() == len(present)


def prepare_table(raw: pd.DataFrame) -> Profile:
    """Tidy ``raw`` (names, empty rows/columns) and detect each column's role."""
    frame = raw.copy()
    frame.columns = _unique_names(frame.columns)
    frame = frame.dropna(how="all")
    profile = Profile(frame=frame)

    for name in list(frame.columns):
        series = frame[name]
        if series.notna().sum() == 0:
            profile.dropped_empty_columns.append(name)
            continue
        if ptypes.is_bool_dtype(series):
            frame[name] = series.astype(str)
            profile.categorical.append(name)
        elif ptypes.is_datetime64_any_dtype(series):
            if getattr(series.dt, "tz", None) is not None:
                frame[name] = series.dt.tz_localize(None)
            profile.datetime.append(name)
        elif ptypes.is_numeric_dtype(series):
            _register_numeric(profile, name, series)
        else:
            text = _as_text(series)
            numeric = _numeric_if_mostly(text)
            dates = None if numeric is not None else _datetime_if_mostly(text)
            if numeric is not None:
                frame[name] = numeric
                _register_numeric(profile, name, numeric)
            elif dates is not None:
                frame[name] = dates
                profile.datetime.append(name)
            else:
                frame[name] = text
                _register_text(profile, name, text)

    profile.frame = frame.drop(columns=profile.dropped_empty_columns).reset_index(drop=True)
    profile.duplicate_rows = int(profile.frame.duplicated().sum())
    return profile


def _register_numeric(profile: Profile, name: str, series: pd.Series) -> None:
    if _looks_like_identifier(name, series):
        profile.identifier.append(name)
        return
    profile.numeric.append(name)
    if series.nunique() <= 1:
        profile.constant.append(name)


def _register_text(profile: Profile, name: str, text: pd.Series) -> None:
    distinct, present = text.nunique(), int(text.notna().sum())
    if distinct <= MAX_CATEGORIES and (distinct <= 0.5 * present or distinct <= 12):
        profile.categorical.append(name)
        if distinct <= 1:
            profile.constant.append(name)
    elif distinct >= 0.95 * present:
        profile.identifier.append(name)
    else:
        profile.text.append(name)


# --- Statistics ------------------------------------------------------------
def numeric_summary(frame: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Descriptive statistics, one row per numeric column."""
    data = frame[columns]
    out = pd.DataFrame({
        "Count": data.count(), "Missing": len(data) - data.count(), "Mean": data.mean(),
        "Median": data.median(), "Std": data.std(), "Min": data.min(), "Max": data.max(),
        "Sum": data.sum(),
    })
    out.index.name = "Column"
    return out.reset_index()


def column_overview(profile: Profile) -> pd.DataFrame:
    """One row per column: detected type, completeness and distinct values."""
    frame = profile.frame
    rows = []
    for name in frame.columns:
        series = frame[name]
        example = series.dropna()
        rows.append({
            "Column": name, "Type": profile.role_of(name), "Non-null": int(series.notna().sum()),
            "Missing %": round(series.isna().mean() * 100, 2), "Unique": int(series.nunique()),
            "Example": str(example.iloc[0]) if len(example) else "",
        })
    return pd.DataFrame(rows)


def missing_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Columns that have missing values, most missing first."""
    missing = frame.isna().sum()
    out = pd.DataFrame({"Column": missing.index, "Missing": missing.values,
                        "Missing %": (missing.values / max(len(frame), 1) * 100).round(2)})
    return out[out["Missing"] > 0].sort_values("Missing", ascending=False).reset_index(drop=True)


def category_counts(series: pd.Series, top: int = 15) -> pd.DataFrame:
    """Value counts with share, keeping the ``top`` values and grouping the rest as 'Other'."""
    counts = series.dropna().astype(str).value_counts()
    total = int(counts.sum())
    head = counts.head(top)
    values = list(head.items())
    if len(counts) > top:
        values.append(("Other", int(counts.iloc[top:].sum())))
    out = pd.DataFrame(values, columns=[series.name or "Value", "Count"])
    out["Share %"] = (out["Count"] / max(total, 1) * 100).round(2)
    return out


def numeric_by_category(frame: pd.DataFrame, category: str, value: str, agg: str, top: int = 15) -> pd.DataFrame:
    """Aggregate ``value`` for each ``category`` (largest first)."""
    grouped = frame.assign(**{category: frame[category].astype(str)}).groupby(category)[value].agg(agg)
    return grouped.sort_values(ascending=False).head(top).rename(f"{agg} of {value}").reset_index()


def auto_frequency(dates: pd.Series) -> str:
    """Pick a sensible time bucket (Day/Week/Month/Year) for the date span."""
    dates = dates.dropna()
    span = (dates.max() - dates.min()).days if len(dates) else 0
    return "Day" if span <= 90 else "Week" if span <= 730 else "Month" if span <= 365 * 8 else "Year"


def time_series(frame: pd.DataFrame, date_col: str, value_col: Optional[str], agg: str, frequency: str) -> pd.DataFrame:
    """Aggregate over time; ``value_col=None`` counts rows."""
    data = frame.dropna(subset=[date_col])
    if data.empty:
        return pd.DataFrame(columns=[date_col, "Value"])
    grouper = pd.Grouper(key=date_col, freq=FREQUENCIES[frequency])
    result = (data.groupby(grouper).size() if value_col is None
              else data.groupby(grouper)[value_col].agg(agg))
    return result.rename("Value").reset_index()


def correlation_matrix(frame: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Pearson correlations for up to ``MAX_HEATMAP_COLUMNS`` non-constant numeric columns."""
    usable = [c for c in columns if frame[c].nunique() > 1][:MAX_HEATMAP_COLUMNS]
    return frame[usable].corr() if len(usable) >= 2 else pd.DataFrame()


def top_correlations(corr: pd.DataFrame, top: int = 8) -> pd.DataFrame:
    """Strongest column pairs by absolute correlation."""
    if corr.empty:
        return pd.DataFrame(columns=["Column A", "Column B", "Correlation"])
    mask = np.triu(np.ones(corr.shape, dtype=bool), k=1)
    pairs = corr.where(mask).stack().rename("Correlation").reset_index()
    pairs.columns = ["Column A", "Column B", "Correlation"]
    order = pairs["Correlation"].abs().sort_values(ascending=False).index
    return pairs.loc[order].head(top).round(3).reset_index(drop=True)


def quick_insights(profile: Profile) -> List[str]:
    """A few plain-language observations derived from whatever columns exist."""
    frame, notes = profile.frame, []
    notes.append(f"The data has {len(frame):,} rows and {frame.shape[1]} columns "
                 f"({len(profile.numeric)} numeric, {len(profile.categorical)} categorical, "
                 f"{len(profile.datetime)} date).")
    missing = missing_summary(frame)
    if not missing.empty:
        worst = missing.iloc[0]
        notes.append(f"{len(missing)} column(s) have missing values; the most is '{worst['Column']}' "
                     f"({worst['Missing %']:.1f}% missing).")
    for column in profile.categorical[:2]:
        top = category_counts(frame[column], top=1).iloc[0]
        notes.append(f"Most common '{column}': {top.iloc[0]} ({top['Share %']:.1f}% of rows).")
    pairs = top_correlations(correlation_matrix(frame, profile.numeric), top=1)
    if not pairs.empty and abs(pairs.loc[0, "Correlation"]) >= 0.3:
        row = pairs.loc[0]
        notes.append(f"Strongest relationship: '{row['Column A']}' and '{row['Column B']}' "
                     f"(correlation {row['Correlation']:+.2f}).")
    if profile.constant:
        notes.append("Constant columns (a single value, so no variation): " + ", ".join(profile.constant) + ".")
    if profile.duplicate_rows:
        notes.append(f"{profile.duplicate_rows:,} duplicate row(s) are present (kept as uploaded).")
    return notes
