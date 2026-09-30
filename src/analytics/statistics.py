"""Descriptive and Distributional Network Statistics."""

from typing import Any
import numpy as np
import pandas as pd


def compute_distribution_summary(series: pd.Series) -> dict[str, float | None]:
    """Compute standard distribution summary metrics for a numerical series."""
    clean = series.dropna()
    if clean.empty:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
            "std": None,
            "p25": None,
            "p75": None,
            "p95": None,
            "p99": None
        }

    arr = clean.to_numpy()
    return {
        "count": int(len(arr)),
        "min": round(float(np.min(arr)), 2),
        "max": round(float(np.max(arr)), 2),
        "mean": round(float(np.mean(arr)), 2),
        "median": round(float(np.median(arr)), 2),
        "std": round(float(np.std(arr)), 2),
        "p25": round(float(np.percentile(arr, 25)), 2),
        "p75": round(float(np.percentile(arr, 75)), 2),
        "p95": round(float(np.percentile(arr, 95)), 2),
        "p99": round(float(np.percentile(arr, 99)), 2)
    }


def compute_compliance_rate(series: pd.Series, max_threshold: float) -> float:
    """Calculate SLA compliance percentage (measurements below or equal to threshold)."""
    clean = series.dropna()
    if clean.empty:
        return 100.0
    compliant = (clean <= max_threshold).sum()
    return round((compliant / len(clean)) * 100.0, 2)
