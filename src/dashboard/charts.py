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


def render_correlation_heatmap(data: pd.DataFrame) -> plt.Figure:
    """Render a correlation heatmap and return its figure."""
    fig, ax = plt.subplots(figsize=config.HEATMAP_SIZE)
    sns.heatmap(data, annot=True, fmt=".2f", cmap=config.HEATMAP_CMAP, ax=ax)
    ax.set_title(config.HEATMAP_TITLE)
    fig.tight_layout()
    return fig
