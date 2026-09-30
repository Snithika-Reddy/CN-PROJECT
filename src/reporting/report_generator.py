"""Executive and Technical Viva Report Generator.

Exports formatted markdown, text, and tabular summary reports of network health,
SLA compliance, incident logs, and diagnostic history for evaluation and Viva defense.
"""

from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Any
import pandas as pd

from ..storage.database import DatabaseManager
from ..storage.repositories import MetricsRepository, IncidentRepository, AnomalyRepository


class ReportGenerator:
    """Generates comprehensive summary reports from authoritative historical database."""

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.metrics_repo = MetricsRepository(db)
        self.incident_repo = IncidentRepository(db)
        self.anomaly_repo = AnomalyRepository(db)

    def generate_viva_defense_summary(self) -> str:
        """Produce a comprehensive technical summary report formatted in Markdown."""
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        total_metrics = self.metrics_repo.count_metrics(is_simulation=False)
        incidents_df = self.incident_repo.get_incident_history(limit=50, is_simulation=False)
        anomalies_df = self.anomaly_repo.get_recent_anomalies(limit=50, is_simulation=False)
        latest_df = self.metrics_repo.get_latest_metrics(limit=100, is_simulation=False)

        avg_health = round(float(latest_df["health_score"].mean()), 1) if not latest_df.empty else 0.0
        avg_lat = round(float(latest_df["latency_ms"].dropna().mean()), 1) if not latest_df.empty else 0.0
        p95_lat = round(float(latest_df["latency_ms"].dropna().quantile(0.95)), 1) if not latest_df.empty else 0.0
        sla_loss_ok = round(float((latest_df["packet_loss_pct"] <= 1.0).mean() * 100.0), 1) if not latest_df.empty else 100.0

        report = f"""# NetIntel Network Intelligence Platform - Viva Defense Report
**Generated:** {now_str}
**Architecture:** Data Collection → Validation → SQLite → Baseline → Anomaly → Diagnosis → Incident → Adaptive → Streamlit / Power BI

---

## 1. Executive Telemetry Overview
- **Total Real Telemetry Samples Captured:** {total_metrics}
- **Average Health Score (Recent Window):** {avg_health} / 100
- **Average Round-Trip Latency:** {avg_lat} ms (95th Percentile: {p95_lat} ms)
- **Packet Loss SLA Compliance (<= 1.0%):** {sla_loss_ok}%
- **Total Historical Incidents Tracked:** {len(incidents_df)}
- **Total Anomalies Flagged:** {len(anomalies_df)}

---

## 2. Recent Incidents History
"""
        if incidents_df.empty:
            report += "No degradation incidents recorded. Network operated nominally.\n"
        else:
            report += "| Incident ID | Severity | Duration (s) | Peak Latency | Peak Loss | Status | Diagnosis |\n"
            report += "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
            for _, row in incidents_df.head(10).iterrows():
                report += f"| {row['incident_id']} | {row['severity']} | {row.get('duration_seconds', 0)}s | {row.get('peak_latency_ms', 0)}ms | {row.get('peak_packet_loss_pct', 0)}% | {row['status']} | {row.get('diagnosis_summary', 'N/A')} |\n"

        report += """
---

## 3. Engineering Rigor & Academic Integrity
1. **RFC 3550 Compliant Jitter:** Inter-packet delay variation strictly calculated via exponential moving variance filter.
2. **Pernic I/O Separation:** Byte counters isolated to active network interface, preventing aggregation mismatch.
3. **Multi-Target Probing:** Disaggregates local gateway latency from upstream ISP and public DNS endpoints.
4. **Hysteresis Debounce:** Incident creation and resolution state machine prevents flapping.
5. **Calibrated Diagnosis:** Avoids declaring black-box certainty; generates ranked competing hypotheses with cited evidence.
"""
        return report

    def save_report_to_file(self, filepath: str = "documentation/viva_report.md") -> str:
        """Write the generated viva report to disk."""
        content = self.generate_viva_defense_summary()
        p = Path(filepath)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        return str(p)
