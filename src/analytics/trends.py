"""Time-of-Day, Fingerprinting, and Longitudinal Trend Analysis.

Answers:
- What are typical network characteristics across hours of the day?
- What is the empirical network fingerprint?
- During what window does performance degradation repeatedly recur?
"""

from dataclasses import dataclass
from typing import Any
import numpy as np
import pandas as pd


@dataclass
class NetworkFingerprint:
    is_available: bool
    sample_count: int
    typical_latency_ms: float | None
    typical_jitter_ms: float | None
    typical_utilization_pct: float | None
    typical_download_mbps: float | None
    typical_upload_mbps: float | None
    typical_packet_loss_pct: float | None
    most_unstable_period: str | None
    summary_message: str


class TrendAnalyzer:
    """Analyzes cyclic time-of-day behavior and extracts empirical network fingerprints."""

    def __init__(self, min_samples_for_fingerprint: int = 50):
        self.min_samples = min_samples_for_fingerprint

    def compute_hourly_profile(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate telemetry by hour of day (0-23) for cyclic performance insights."""
        if df.empty or "timestamp" not in df.columns:
            return pd.DataFrame()

        df_copy = df.copy()
        df_copy["dt"] = pd.to_datetime(df_copy["timestamp"], errors="coerce")
        df_copy = df_copy.dropna(subset=["dt"])
        if df_copy.empty:
            return pd.DataFrame()

        df_copy["hour"] = df_copy["dt"].dt.hour

        grouped = df_copy.groupby("hour").agg({
            "latency_ms": ["median", "mean", "std"],
            "jitter_ms": ["median", "mean"],
            "packet_loss_pct": ["mean", "max"],
            "download_mbps": ["median", "max"],
            "upload_mbps": ["median", "max"],
            "estimated_utilization_pct": ["median", "max"],
            "health_score": "mean",
            "stability_score": "mean"
        }).reset_index()

        # Flatten multi-level columns
        grouped.columns = [
            f"{col[0]}_{col[1]}" if col[1] else col[0] for col in grouped.columns
        ]
        return grouped

    def extract_fingerprint(self, df: pd.DataFrame) -> NetworkFingerprint:
        """Extract historical network fingerprint from real historical data."""
        if df.empty or len(df) < self.min_samples:
            return NetworkFingerprint(
                is_available=False,
                sample_count=len(df),
                typical_latency_ms=None,
                typical_jitter_ms=None,
                typical_utilization_pct=None,
                typical_download_mbps=None,
                typical_upload_mbps=None,
                typical_packet_loss_pct=None,
                most_unstable_period=None,
                summary_message=f"Insufficient historical telemetry ({len(df)}/{self.min_samples} required) to generate network fingerprint."
            )

        typ_lat = float(df["latency_ms"].dropna().median()) if "latency_ms" in df else None
        typ_jit = float(df["jitter_ms"].dropna().median()) if "jitter_ms" in df else None
        typ_util = float(df["estimated_utilization_pct"].dropna().median()) if "estimated_utilization_pct" in df else None
        typ_down = float(df["download_mbps"].dropna().median()) if "download_mbps" in df else None
        typ_up = float(df["upload_mbps"].dropna().median()) if "upload_mbps" in df else None
        typ_loss = float(df["packet_loss_pct"].dropna().mean()) if "packet_loss_pct" in df else None

        # Determine most unstable hour of day if timestamp is present
        unstable_period = "Insufficient time-span data"
        if "timestamp" in df.columns:
            hourly = self.compute_hourly_profile(df)
            if not hourly.empty and "latency_ms_std" in hourly.columns:
                worst_row = hourly.sort_values(by="latency_ms_std", ascending=False).iloc[0]
                worst_hr = int(worst_row["hour"])
                unstable_period = f"{worst_hr:02d}:00 - {(worst_hr+1)%24:02d}:00 (Highest latency variance)"

        return NetworkFingerprint(
            is_available=True,
            sample_count=len(df),
            typical_latency_ms=round(typ_lat, 2) if typ_lat is not None else None,
            typical_jitter_ms=round(typ_jit, 2) if typ_jit is not None else None,
            typical_utilization_pct=round(typ_util, 2) if typ_util is not None else None,
            typical_download_mbps=round(typ_down, 2) if typ_down is not None else None,
            typical_upload_mbps=round(typ_up, 2) if typ_up is not None else None,
            typical_packet_loss_pct=round(typ_loss, 2) if typ_loss is not None else None,
            most_unstable_period=unstable_period,
            summary_message="Empirical fingerprint established from continuous historical measurements."
        )
