"""Chart rendering helpers for the Streamlit dashboard (return figures, never save)."""
from typing import Tuple

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

import config


def render_bar_chart(data: pd.DataFrame, x: str, y: str, title: str, ylabel: str,
                     figsize: Tuple[int, int] = config.DASHBOARD_FIGSIZE_BAR) -> plt.Figure:
    """Render a bar chart and return its figure."""
    fig, ax = plt.subplots(figsize=figsize)
    ax.bar(data[x].astype(str), data[y])
    ax.set(title=title, xlabel=x.replace("_", " "), ylabel=ylabel)
    ax.tick_params(axis="x", labelrotation=config.LABEL_ROTATION)
    fig.tight_layout()
    return fig


def render_line_chart(data: pd.DataFrame, x: str, y: str, title: str, ylabel: str,
                      figsize: Tuple[int, int] = config.DASHBOARD_FIGSIZE_LINE) -> plt.Figure:
    """Render a line chart and return its figure."""
    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(data[x], data[y], marker="o")
    ax.set(title=title, xlabel=x, ylabel=ylabel)
    fig.autofmt_xdate()
    fig.tight_layout()
    return fig


def render_correlation_heatmap(data: pd.DataFrame, annot: bool = True) -> plt.Figure:
    """Render a correlation heatmap and return its figure."""
    fig, ax = plt.subplots(figsize=config.HEATMAP_SIZE)
    sns.heatmap(data, annot=annot, fmt=".2f", cmap=config.HEATMAP_CMAP, ax=ax, vmin=-1, vmax=1)
    ax.set_title(config.HEATMAP_TITLE)
    fig.tight_layout()
    return fig


def render_histogram(values: pd.Series, title: str) -> plt.Figure:
    """Distribution of a numeric column (bars per value when it has few distinct values)."""
    values = values.dropna()
    fig, ax = plt.subplots(figsize=(6, 4))
    if values.nunique() <= 15:
        counts = values.value_counts().sort_index()
        ax.bar(counts.index.astype(str), counts.values)
        ax.tick_params(axis="x", labelrotation=config.LABEL_ROTATION)
    else:
        bins = int(min(40, max(8, len(values) ** 0.5)))
        ax.hist(values, bins=bins)
        ax.axvline(values.mean(), color="red", linestyle="--", linewidth=1, label=f"Mean {values.mean():,.2f}")
        ax.legend()
    ax.set(title=title, xlabel=str(values.name), ylabel="Frequency")
    fig.tight_layout()
    return fig


def render_scatter(data: pd.DataFrame, x: str, y: str) -> plt.Figure:
    """Scatter plot of two numeric columns."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(data[x], data[y], alpha=0.5, s=14)
    ax.set(title=f"{y} vs {x}", xlabel=x, ylabel=y)
    fig.tight_layout()
    return fig


def render_horizontal_bars(labels: pd.Series, values: pd.Series, title: str, xlabel: str) -> plt.Figure:
    """Horizontal bar chart (readable for long labels); first row is drawn on top."""
    fig, ax = plt.subplots(figsize=(8, max(3, 0.4 * len(labels) + 1)))
    ax.barh(labels.astype(str)[::-1], values[::-1])
    ax.set(title=title, xlabel=xlabel)
    fig.tight_layout()
    return fig
