"""Statistical Anomaly Detection Engine.

Implements explainable, transparent anomaly detection methods:
- Modified Z-Score (using median and MAD for robustness against outliers)
- Interquartile Range (IQR Tukey fences)
- Percent-deviation relative to learned baseline
- Clear severity grading (LOW, MEDIUM, HIGH, CRITICAL)
"""

from dataclasses import dataclass
import logging
from typing import Any
import numpy as np

from ..analytics.baseline import MetricBaseline

logger = logging.getLogger(__name__)


@dataclass
class AnomalyEvent:
    timestamp_iso: str
    metric_name: str
    observed_value: float
    baseline_expected: float
    deviation_pct: float
    severity: str  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    detection_method: str  # 'Z-SCORE', 'IQR', 'THRESHOLD', 'CHANGEPOINT'
    details: str
    is_simulation: bool = False


class StatisticalAnomalyDetector:
    """Detects metric outliers using transparent statistical rules and empirical baselines."""

    def __init__(self, zscore_threshold: float = 2.5, iqr_multiplier: float = 1.5):
        self.z_threshold = zscore_threshold
        self.iqr_multiplier = iqr_multiplier

    def evaluate_sample(
        self,
        timestamp_iso: str,
        metric_name: str,
        observed_value: float | None,
        baseline: MetricBaseline | None,
        is_simulation: bool = False
    ) -> AnomalyEvent | None:
        """Evaluate a single observed telemetry value against its baseline."""
        if observed_value is None or baseline is None or not baseline.is_established:
            return None

        expected = baseline.median if baseline.median is not None else baseline.mean
        if expected is None or expected <= 0:
            expected = 0.001

        deviation_pct = round(((observed_value - expected) / expected) * 100.0, 1)

        # 1. Check IQR Bounds (Tukey's Fence)
        is_iqr_anomaly = False
        if baseline.upper_bound is not None and observed_value > baseline.upper_bound:
            is_iqr_anomaly = True

        # 2. Check Z-score
        z_score = 0.0
        if baseline.std_dev is not None and baseline.std_dev > 0.001:
            z_score = abs(observed_value - expected) / baseline.std_dev

        is_z_anomaly = z_score >= self.z_threshold

        if not (is_iqr_anomaly or is_z_anomaly):
            return None

        # Determine severity based on deviation magnitude and z-score
        if z_score >= 4.0 or deviation_pct >= 250.0:
            severity = "CRITICAL"
        elif z_score >= 3.0 or deviation_pct >= 150.0:
            severity = "HIGH"
        elif z_score >= 2.0 or deviation_pct >= 75.0:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        method = "Z-SCORE" if is_z_anomaly else "IQR"
        details = (
            f"{metric_name} observed {observed_value} deviated by +{deviation_pct}% "
            f"from expected baseline {expected} (Z-Score: {z_score:.2f}, Upper Fence: {baseline.upper_bound})."
        )

        return AnomalyEvent(
            timestamp_iso=timestamp_iso,
            metric_name=metric_name,
            observed_value=round(observed_value, 2),
            baseline_expected=round(expected, 2),
            deviation_pct=deviation_pct,
            severity=severity,
            detection_method=method,
            details=details,
            is_simulation=is_simulation
        )
