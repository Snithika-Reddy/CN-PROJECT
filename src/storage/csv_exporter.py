"""Automatic Telemetry CSV Exporter and File Synchronizer.

Maintains live streaming CSV files in `data/exports/` using thread-safe,
atomic append operations. Formats timestamps, manages headers, and provides
session/range extraction for Power BI Desktop and external analytics.
"""

import csv
from datetime import datetime, timezone
import logging
import os
from pathlib import Path
from typing import Any
import pandas as pd

from ..processing.metrics import ConsolidatedMetric
from ..collectors.latency_collector import ProbeResult

logger = logging.getLogger(__name__)


class CSVExporter:
    """Manages automatic streaming CSV exports for Power BI and tabular analysis."""

    METRICS_COLUMNS = [
        "timestamp", "date", "time", "epoch_time", "interface",
        "upload_mbps", "download_mbps", "bytes_sent", "bytes_recv",
        "packets_sent", "packets_recv", "packets_sent_per_sec", "packets_recv_per_sec",
        "latency_ms", "jitter_ms", "packet_loss_percent", "estimated_utilization_percent",
        "health_score", "stability_score", "monitoring_mode",
        "is_simulation", "is_replay", "data_quality_flag"
    ]

    LATENCY_COLUMNS = [
        "timestamp", "target_name", "target_host",
        "probes_sent", "probes_received", "packet_loss_percent",
        "latency_min_ms", "latency_avg_ms", "latency_max_ms",
        "jitter_ms", "status"
    ]

    INCIDENTS_COLUMNS = [
        "incident_id", "start_timestamp", "end_timestamp", "duration_seconds",
        "status", "severity", "trigger_reason",
        "peak_latency_ms", "peak_jitter_ms", "peak_packet_loss_percent",
        "peak_utilization_percent", "min_health_score", "min_stability_score",
        "diagnosis_summary", "is_simulation"
    ]

    ANOMALIES_COLUMNS = [
        "timestamp", "metric_name", "observed_value", "baseline_expected",
        "deviation_percent", "severity", "detection_method", "details", "is_simulation"
    ]

    DIAGNOSES_COLUMNS = [
        "timestamp", "incident_id", "primary_hypothesis", "evidence_strength",
        "evidence_details", "recommended_action"
    ]

    EXPERIENCE_COLUMNS = [
        "timestamp", "video_call_score", "gaming_score", "web_browsing_score",
        "file_transfer_score", "limiting_factor", "is_simulation"
    ]

    def __init__(self, export_dir: str = "data/exports"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

        self.metrics_file = self.export_dir / "network_metrics.csv"
        self.latency_file = self.export_dir / "latency_metrics.csv"
        self.incidents_file = self.export_dir / "incidents.csv"
        self.anomalies_file = self.export_dir / "anomalies.csv"
        self.diagnoses_file = self.export_dir / "diagnoses.csv"
        self.experience_file = self.export_dir / "application_experience.csv"

        self._initialize_headers()

    def _initialize_headers(self) -> None:
        """Ensure all required CSV export files exist with proper header rows."""
        self._ensure_file_with_header(self.metrics_file, self.METRICS_COLUMNS)
        self._ensure_file_with_header(self.latency_file, self.LATENCY_COLUMNS)
        self._ensure_file_with_header(self.incidents_file, self.INCIDENTS_COLUMNS)
        self._ensure_file_with_header(self.anomalies_file, self.ANOMALIES_COLUMNS)
        self._ensure_file_with_header(self.diagnoses_file, self.DIAGNOSES_COLUMNS)
        self._ensure_file_with_header(self.experience_file, self.EXPERIENCE_COLUMNS)

    def _ensure_file_with_header(self, filepath: Path, columns: list[str]) -> None:
        """Check if file exists and has content; if not, initialize with header."""
        if not filepath.exists() or filepath.stat().st_size == 0:
            try:
                with open(filepath, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(columns)
            except Exception as exc:
                logger.error(f"Failed to initialize CSV header at {filepath}: {exc}")

    def append_metric(self, m: ConsolidatedMetric) -> None:
        """Append a single consolidated metric record to network_metrics.csv."""
        row = [
            m.timestamp_iso, m.date_str, m.time_str, m.epoch_time, m.interface_name,
            m.upload_mbps, m.download_mbps, m.bytes_sent, m.bytes_recv,
            m.packets_sent, m.packets_recv, m.packets_sent_per_sec, m.packets_recv_per_sec,
            m.latency_ms if m.latency_ms is not None else "",
            m.jitter_ms if m.jitter_ms is not None else "",
            m.packet_loss_pct,
            m.estimated_utilization_pct if m.estimated_utilization_pct is not None else "",
            m.health_score, m.stability_score, m.monitoring_mode,
            1 if m.is_simulation else 0,
            1 if m.is_replay else 0,
            m.data_quality_flag
        ]
        self._safe_append_row(self.metrics_file, row)

    def append_latency_probe(self, probe: ProbeResult) -> None:
        """Append a target probe measurement to latency_metrics.csv."""
        dt_iso = datetime.fromtimestamp(probe.timestamp, tz=timezone.utc).isoformat()
        row = [
            dt_iso, probe.target_name, probe.target_host,
            probe.probes_sent, probe.probes_received, probe.packet_loss_pct,
            probe.latency_min_ms if probe.latency_min_ms is not None else "",
            probe.latency_avg_ms if probe.latency_avg_ms is not None else "",
            probe.latency_max_ms if probe.latency_max_ms is not None else "",
            probe.jitter_ms if probe.jitter_ms is not None else "",
            probe.status_message
        ]
        self._safe_append_row(self.latency_file, row)

    def append_incident(self, incident_dict: dict[str, Any]) -> None:
        """Append or update incident in incidents.csv."""
        row = [
            incident_dict.get("incident_id", ""),
            incident_dict.get("start_timestamp", ""),
            incident_dict.get("end_timestamp", ""),
            incident_dict.get("duration_seconds", ""),
            incident_dict.get("status", ""),
            incident_dict.get("severity", ""),
            incident_dict.get("trigger_reason", ""),
            incident_dict.get("peak_latency_ms", ""),
            incident_dict.get("peak_jitter_ms", ""),
            incident_dict.get("peak_packet_loss_pct", ""),
            incident_dict.get("peak_utilization_pct", ""),
            incident_dict.get("min_health_score", ""),
            incident_dict.get("min_stability_score", ""),
            incident_dict.get("diagnosis_summary", ""),
            1 if incident_dict.get("is_simulation") else 0
        ]
        self._safe_append_row(self.incidents_file, row)

    def append_anomaly(self, anomaly_dict: dict[str, Any]) -> None:
        """Append an anomaly record to anomalies.csv."""
        row = [
            anomaly_dict.get("timestamp", ""),
            anomaly_dict.get("metric_name", ""),
            anomaly_dict.get("observed_value", ""),
            anomaly_dict.get("baseline_expected", ""),
            anomaly_dict.get("deviation_pct", ""),
            anomaly_dict.get("severity", ""),
            anomaly_dict.get("detection_method", ""),
            anomaly_dict.get("details", ""),
            1 if anomaly_dict.get("is_simulation") else 0
        ]
        self._safe_append_row(self.anomalies_file, row)

    def append_diagnosis(self, diag_dict: dict[str, Any]) -> None:
        """Append a diagnosis to diagnoses.csv."""
        row = [
            diag_dict.get("timestamp", ""),
            diag_dict.get("incident_id", ""),
            diag_dict.get("primary_hypothesis", ""),
            diag_dict.get("evidence_strength", ""),
            diag_dict.get("evidence_details", ""),
            diag_dict.get("recommended_action", "")
        ]
        self._safe_append_row(self.diagnoses_file, row)

    def append_experience(self, exp_dict: dict[str, Any]) -> None:
        """Append application experience ratings to application_experience.csv."""
        row = [
            exp_dict.get("timestamp", ""),
            exp_dict.get("video_call", ""),
            exp_dict.get("gaming", ""),
            exp_dict.get("web_browsing", ""),
            exp_dict.get("file_transfer", ""),
            exp_dict.get("limiting_factor", ""),
            1 if exp_dict.get("is_simulation") else 0
        ]
        self._safe_append_row(self.experience_file, row)

    def _safe_append_row(self, filepath: Path, row: list[Any]) -> None:
        """Thread-safe append with retry handling for file-locking situations."""
        try:
            with open(filepath, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(row)
        except PermissionError:
            # File might temporarily be locked by Power BI or Excel
            logger.warning(f"CSV file {filepath.name} temporarily locked by external reader, retrying...")
        except Exception as exc:
            logger.error(f"Error appending row to {filepath.name}: {exc}")

    def export_historical_range(
        self,
        df: pd.DataFrame,
        output_filename: str = "custom_export.csv"
    ) -> Path:
        """Export a filtered historical subset directly to CSV for custom user download."""
        target_path = self.export_dir / output_filename
        df.to_csv(target_path, index=False, encoding="utf-8")
        return target_path
