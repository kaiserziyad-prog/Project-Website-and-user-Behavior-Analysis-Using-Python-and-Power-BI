"""Plot generation. Each function renders one chart and saves it to disk."""
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

import matplotlib

matplotlib.use("Agg")  # headless backend: safe on servers / CI
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

import config
from src.utils import ensure_dir

logger = logging.getLogger(__name__)


def _save(fig: plt.Figure, path: Path) -> None:
    """Tighten layout, write the figure and release its memory."""
    ensure_dir(path.parent)
    fig.tight_layout()
    fig.savefig(path, dpi=config.FIGURE_DPI)
    plt.close(fig)
    logger.info("Saved figure %s", path.name)


def plot_bar(df: pd.DataFrame, x: str, y: str, title: str, ylabel: str, path: Path,
             size: Tuple[int, int] = config.FIGURE_SIZE_MEDIUM, rotate_labels: bool = False) -> None:
    """Draw a simple bar chart of ``y`` per ``x``."""
    fig, ax = plt.subplots(figsize=size)
    ax.bar(df[x], df[y])
    ax.set(title=title, xlabel=x.replace("_", " "), ylabel=ylabel)
    if rotate_labels:
        plt.setp(ax.get_xticklabels(), rotation=config.LABEL_ROTATION)
    _save(fig, path)


def plot_line(df: pd.DataFrame, x: str, y: str, title: str, path: Path,
              size: Tuple[int, int] = config.FIGURE_SIZE_WIDE, integer_ticks: bool = False) -> None:
    """Draw a line chart of ``y`` over ``x``."""
    fig, ax = plt.subplots(figsize=size)
    ax.plot(df[x], df[y], marker="o")
    ax.set(title=title, xlabel=x, ylabel=y)
    if integer_ticks:
        ax.set_xticks(range(int(df[x].min()), int(df[x].max()) + 1))
    else:
        plt.setp(ax.get_xticklabels(), rotation=config.LABEL_ROTATION)
    _save(fig, path)


def plot_correlation_heatmap(corr: pd.DataFrame, path: Path) -> None:
    """Draw an annotated correlation heatmap."""
    fig, ax = plt.subplots(figsize=config.HEATMAP_SIZE)
    sns.heatmap(corr, annot=True, fmt=".2f", cmap=config.HEATMAP_CMAP, ax=ax)
    ax.set_title(config.HEATMAP_TITLE)
    _save(fig, path)


def render_chart(spec: Dict[str, Any], tables: Dict[str, pd.DataFrame], out_dir: Path) -> Path:
    """Render one chart described by a ``config.CHART_SPECS`` entry and return its path."""
    data = tables[spec["table"]]
    path = out_dir / spec["filename"]
    kind = spec["kind"]
    if kind == "bar":
        plot_bar(data, spec["x"], spec["y"], spec["title"], spec["ylabel"], path,
                 spec.get("size", config.FIGURE_SIZE_MEDIUM), spec.get("rotate_labels", False))
    elif kind == "line":
        plot_line(data, spec["x"], spec["y"], spec["title"], path,
                  spec.get("size", config.FIGURE_SIZE_WIDE), spec.get("integer_ticks", False))
    else:
        raise ValueError(f"Unsupported chart kind: {kind!r}")
    return path


def create_all_charts(tables: Dict[str, pd.DataFrame], corr: pd.DataFrame,
                      out_dir: Path = config.FIGURES_DIR) -> List[Path]:
    """Render every configured chart plus the correlation heatmap; return the file paths."""
    paths = [render_chart(spec, tables, out_dir) for spec in config.CHART_SPECS]
    heatmap_path = out_dir / config.FIG_CORRELATION_HEATMAP
    plot_correlation_heatmap(corr, heatmap_path)
    return paths + [heatmap_path]
