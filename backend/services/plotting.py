"""Plot proposal and generation utilities."""
from __future__ import annotations

import base64
import io
from typing import Any, Dict, List

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

matplotlib.use("Agg")


def propose_plots(df: pd.DataFrame, column_types: Dict[str, str]) -> List[Dict[str, Any]]:
    """Suggest plots based on detected column types."""
    plots: List[Dict[str, Any]] = []
    numeric_cols = [c for c, t in column_types.items() if t == "numeric"]
    categorical_cols = [c for c, t in column_types.items() if t == "categorical"]
    datetime_cols = [c for c, t in column_types.items() if t == "datetime"]

    if numeric_cols:
        plots.append({"title": "Numeric Distribution", "plot_type": "histogram", "columns": numeric_cols[:3]})
        if len(numeric_cols) >= 2:
            plots.append(
                {"title": "Numeric Relationships", "plot_type": "scatter_matrix", "columns": numeric_cols[:4]}
            )
        plots.append({"title": "Correlation Heatmap", "plot_type": "correlation_heatmap", "columns": numeric_cols})

    for cat in categorical_cols[:2]:
        plots.append({"title": f"Category distribution: {cat}", "plot_type": "bar", "columns": [cat]})

    for dt in datetime_cols[:1]:
        plots.append({"title": f"Time series: {dt}", "plot_type": "timeseries", "columns": [dt]})

    return plots


def _fig_to_base64() -> str:
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def generate_plots(df: pd.DataFrame, plot_requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate matplotlib plots and return base64 payloads."""
    results: List[Dict[str, Any]] = []
    for plot in plot_requests:
        plot_type = plot.get("plot_type")
        columns = plot.get("columns", [])
        title = plot.get("title", plot_type)

        try:
            if plot_type == "histogram":
                plt.figure(figsize=(8, 4))
                for col in columns:
                    if pd.api.types.is_numeric_dtype(df[col]):
                        sns.histplot(df[col].dropna(), kde=True, label=col, bins=20, alpha=0.6)
                plt.legend()
                plt.title(title)
            elif plot_type == "bar" and columns:
                plt.figure(figsize=(8, 4))
                col = columns[0]
                df[col].value_counts().head(15).plot(kind="bar")
                plt.ylabel("Count")
                plt.title(title)
            elif plot_type == "correlation_heatmap" and len(columns) >= 2:
                plt.figure(figsize=(8, 6))
                corr = df[columns].corr().fillna(0)
                sns.heatmap(corr, annot=False, cmap="Blues")
                plt.title(title)
            elif plot_type == "timeseries" and columns:
                plt.figure(figsize=(8, 4))
                col = columns[0]
                series = pd.to_datetime(df[col], errors="coerce")
                series = series.dropna()
                series.value_counts().sort_index().plot()
                plt.ylabel("Count")
                plt.title(title)
            elif plot_type == "scatter_matrix" and len(columns) >= 2:
                sns.pairplot(df[columns].dropna(), corner=True)
                plt.suptitle(title)
            else:
                continue

            payload = _fig_to_base64()
            results.append(
                {
                    "title": title,
                    "plot_type": plot_type,
                    "image_base64": payload,
                    "description": f"Auto-generated {plot_type} for {', '.join(columns)}",
                }
            )
        except Exception:
            # Skip failing plot to keep endpoint resilient
            plt.close()
            continue

    return results


