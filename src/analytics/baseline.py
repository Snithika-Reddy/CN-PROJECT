"""Historical Baseline Analytics Engine.

Learns normal operating distributions from empirical telemetry records using
robust statistics (rolling median, IQR, percentiles, and standard deviation).
Strictly adheres to data honesty: refuses to fabricate baselines when samples are insufficient.
"""

from dataclasses import dataclass
import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class MetricBaseline:
    metric_name: str
    is_established: bool
    sample_count: int
    median: float | None
    mean: float | None
    std_dev: float | None
    p05: float | None
    p25: float | None
    p75: float | None
    p95: float | None
    iqr: float | None
    lower_bound: float | None
    upper_bound: float | None
    status_message: str


class BaselineEngine:
    """Computes empirical baselines across latency, jitter, loss, and throughput."""

    def __init__(self, min_samples_required: int = 30, rolling_window_samples: int = 120):
        self.min_samples = min_samples_required
        self.window_samples = rolling_window_samples

    def calculate_metric_baseline(self, series: pd.Series, metric_name: str) -> MetricBaseline:
        """Calculate statistical baseline for a single metric series."""
        clean_series = series.dropna()
        count = len(clean_series)

        if count < self.min_samples:
            return MetricBaseline(
                metric_name=metric_name,
                is_established=False,
                sample_count=count,
                median=None,
                mean=None,
                std_dev=None,
                p05=None,
                p25=None,
                p75=None,
                p95=None,
                iqr=None,
                lower_bound=None,
                upper_bound=None,
                status_message=f"Insufficient historical data to establish a reliable baseline ({count}/{self.min_samples} samples)."
            )

        # Use recent window if series is large
        recent_data = clean_series.tail(self.window_samples)
        values = recent_data.to_numpy()

        p05 = float(np.percentile(values, 5))
        p25 = float(np.percentile(values, 25))
        median = float(np.median(values))
        p75 = float(np.percentile(values, 75))
        p95 = float(np.percentile(values, 95))
        mean = float(np.mean(values))
        std = float(np.std(values))

        iqr = p75 - p25
        # Tukey's fence for normal range bounds
        lower_bound = max(0.0, p25 - 1.5 * iqr)
        upper_bound = p75 + 1.5 * iqr

        return MetricBaseline(
            metric_name=metric_name,
            is_established=True,
            sample_count=count,
            median=round(median, 2),
            mean=round(mean, 2),
            std_dev=round(std, 2),
            p05=round(p05, 2),
            p25=round(p25, 2),
            p75=round(p75, 2),
            p95=round(p95, 2),
            iqr=round(iqr, 2),
            lower_bound=round(lower_bound, 2),
            upper_bound=round(upper_bound, 2),
            status_message="Baseline established from actual historical data."
        )

    def compute_all_baselines(self, df: pd.DataFrame) -> dict[str, MetricBaseline]:
        """Compute baselines for all core operational telemetry dimensions."""
        baselines: dict[str, MetricBaseline] = {}
        metrics_to_evaluate = [
            ("latency_ms", "Latency"),
            ("jitter_ms", "Jitter"),
            ("packet_loss_pct", "Packet Loss"),
            ("download_mbps", "Download Speed"),
            ("upload_mbps", "Upload Speed"),
            ("estimated_utilization_pct", "Estimated Utilization"),
            ("packets_sent_per_sec", "Packets Sent/Sec"),
            ("packets_recv_per_sec", "Packets Recv/Sec")
        ]

        for col, label in metrics_to_evaluate:
            if col in df.columns:
                baselines[col] = self.calculate_metric_baseline(df[col], label)

        return baselines
