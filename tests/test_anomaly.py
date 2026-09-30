"""Unit tests for statistical and multivariate anomaly detection."""

import numpy as np
import pandas as pd
import pytest
from src.anomaly.statistical_detector import StatisticalAnomalyDetector
from src.anomaly.change_point import ChangePointDetector
from src.analytics.baseline import MetricBaseline


def test_statistical_anomaly_zscore_and_iqr():
    detector = StatisticalAnomalyDetector(zscore_threshold=2.5, iqr_multiplier=1.5)

    base = MetricBaseline(
        metric_name="latency_ms",
        is_established=True,
        sample_count=100,
        median=20.0,
        mean=20.0,
        std_dev=3.0,
        p05=15.0,
        p25=18.0,
        p75=22.0,
        p95=25.0,
        iqr=4.0,
        lower_bound=12.0,
        upper_bound=28.0,
        status_message="Baseline established."
    )

    # Nominal value (22ms) -> No anomaly
    assert detector.evaluate_sample("2026-09-30T10:00:00Z", "latency_ms", 22.0, base) is None

    # Outlier value (95ms) -> Anomaly detected
    anom = detector.evaluate_sample("2026-09-30T10:00:00Z", "latency_ms", 95.0, base)
    assert anom is not None
    assert anom.severity in ("HIGH", "CRITICAL")
    assert anom.observed_value == 95.0


def test_changepoint_detector():
    cp_detector = ChangePointDetector(window_size=5, sensitivity_sigma=2.0)

    # First feed steady low latency (20ms)
    for _ in range(5):
        res = cp_detector.add_sample(20.0)

    # Feed sudden step shift to 120ms
    shift_detected = False
    for _ in range(5):
        res = cp_detector.add_sample(120.0)
        if res.detected:
            shift_detected = True
            break

    assert shift_detected is True
