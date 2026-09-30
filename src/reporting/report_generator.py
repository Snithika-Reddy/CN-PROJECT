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

    def generate_json_summary(self) -> dict[str, Any]:
        """Generate structured JSON summary of network health and performance."""
        now_str = datetime.now(timezone.utc).isoformat()
        total_metrics = self.metrics_repo.count_metrics(is_simulation=False)
        incidents_df = self.incident_repo.get_incident_history(limit=50, is_simulation=False)
        anomalies_df = self.anomaly_repo.get_recent_anomalies(limit=50, is_simulation=False)
        latest_df = self.metrics_repo.get_latest_metrics(limit=100, is_simulation=False)

        avg_health = round(float(latest_df["health_score"].mean()), 2) if not latest_df.empty else 0.0
        avg_lat = round(float(latest_df["latency_ms"].dropna().mean()), 2) if not latest_df.empty else 0.0
        p95_lat = round(float(latest_df["latency_ms"].dropna().quantile(0.95)), 2) if not latest_df.empty else 0.0
        sla_loss_ok = round(float((latest_df["packet_loss_pct"] <= 1.0).mean() * 100.0), 2) if not latest_df.empty else 100.0

        return {
            "timestamp": now_str,
            "status": "OPERATIONAL",
            "telemetry": {
                "total_samples": total_metrics,
                "health_score_avg": avg_health,
                "latency_avg_ms": avg_lat,
                "latency_p95_ms": p95_lat,
                "packet_loss_sla_compliance_pct": sla_loss_ok,
            },
            "incidents": {
                "total_tracked": len(incidents_df),
                "recent": incidents_df.head(5).to_dict(orient="records") if not incidents_df.empty else [],
            },
            "anomalies": {
                "total_detected": len(anomalies_df),
            },
        }

    def save_report_to_file(self, filepath: str = "output/viva_report.md") -> str:
        """Write the generated viva report to disk."""
        content = self.generate_viva_defense_summary()
        p = Path(filepath)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        return str(p)

    def export_all_outputs(self, output_dir: str = "output") -> dict[str, str]:
        """Export all primary reports, manifests, and snapshots to the designated output folder."""
        import json
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        results = {}

        # 1. Viva Defense Report Markdown
        md_path = out_path / "viva_report.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(self.generate_viva_defense_summary())
        results["viva_report_md"] = str(md_path)

        # 2. Executive Summary JSON
        json_path = out_path / "executive_summary.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.generate_json_summary(), f, indent=2)
        results["executive_summary_json"] = str(json_path)

        # 3. Plain Text Telemetry Snapshot
        txt_path = out_path / "telemetry_summary.txt"
        summary_data = self.generate_json_summary()
        lines = [
            "===========================================================",
            " NETINTEL - REAL-TIME TELEMETRY & OBSERVABILITY OUTPUT",
            f" Generated: {summary_data['timestamp']}",
            "===========================================================",
            f" Status:                      {summary_data['status']}",
            f" Total Real Samples:          {summary_data['telemetry']['total_samples']}",
            f" Recent Average Health Score: {summary_data['telemetry']['health_score_avg']} / 100",
            f" Average Latency:             {summary_data['telemetry']['latency_avg_ms']} ms",
            f" 95th Percentile Latency:     {summary_data['telemetry']['latency_p95_ms']} ms",
            f" Packet Loss SLA Compliance:  {summary_data['telemetry']['packet_loss_sla_compliance_pct']}%",
            f" Total Incidents Tracked:     {summary_data['incidents']['total_tracked']}",
            f" Total Anomalies Flagged:     {summary_data['anomalies']['total_detected']}",
            "===========================================================",
            " Datasets: data/exports/star_schema/ and data/exports/",
            " Live Web Dashboard: http://localhost:8501",
            " Power BI REST Streaming API: http://localhost:8080/api/live",
            "===========================================================",
        ]
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        results["telemetry_summary_txt"] = str(txt_path)

        # 4. Output Index / README
        readme_path = out_path / "README.md"
        readme_content = f"""# NetIntel Output Directory

This directory contains the latest generated intelligence summaries, technical viva defense evaluations, and executive exports from NetIntel.

## Generated Artifacts

- **[`viva_report.md`](file:///./viva_report.md)**: Complete technical summary for college viva defense and evaluation.
- **[`executive_summary.json`](file:///./executive_summary.json)**: Machine-readable JSON telemetry snapshot.
- **[`telemetry_summary.txt`](file:///./telemetry_summary.txt)**: Formatted plain-text summary of health, SLA compliance, and metrics.
- **Power BI Relational Data Mart**: Located at [`../data/exports/star_schema/`](file:///../data/exports/star_schema/)
- **Raw Telemetry Exports**: Located at [`../data/exports/`](file:///../data/exports/)
- **Authoritative Database**: Located at [`../database/network_monitor.db`](file:///../database/network_monitor.db)

## How to Regenerate Outputs

```bash
# Using NetIntel Manager
python manage.py report

# Or using batch launcher
run.bat
```
"""
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)
        results["readme_md"] = str(readme_path)

        return results

