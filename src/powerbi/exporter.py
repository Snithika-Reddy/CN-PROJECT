"""Power BI Exporter & Star Schema Transformer.

Prepares analytics-ready Star Schema dimension and fact tabular structures
and writes them directly to `data/exports/` and `data/exports/star_schema/`
for seamless ingestion into Microsoft Power BI Desktop and Power BI Service.
"""

from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class PowerBIExporter:
    """Prepares and validates Fact and Dimension schemas for Power BI Desktop."""

    def __init__(self, export_dir: str = "data/exports", star_schema_subdir: str = "star_schema"):
        self.export_dir = Path(export_dir)
        self.star_dir = self.export_dir / star_schema_subdir
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.star_dir.mkdir(parents=True, exist_ok=True)

    def generate_star_schema_tables(
        self,
        metrics_df: Optional[pd.DataFrame] = None,
        probes_df: Optional[pd.DataFrame] = None,
        incidents_df: Optional[pd.DataFrame] = None,
        anomalies_df: Optional[pd.DataFrame] = None,
        experience_df: Optional[pd.DataFrame] = None,
        interfaces_df: Optional[pd.DataFrame] = None,
    ) -> dict[str, pd.DataFrame]:
        """Transform raw telemetry into a unified, relational Star Schema.

        Returns a dictionary of DataFrames:
          - FactNetworkMetrics
          - FactLatencyProbes
          - FactIncidents
          - FactAnomalies
          - FactApplicationExperience
          - DimDate
          - DimTime
          - DimInterface
          - DimTarget
        """
        tables: dict[str, pd.DataFrame] = {}

        # -------------------------------------------------------------
        # 1. FactNetworkMetrics
        # -------------------------------------------------------------
        if metrics_df is not None and not metrics_df.empty:
            f_metrics = metrics_df.copy()
            f_metrics["dt"] = pd.to_datetime(f_metrics["timestamp"], errors="coerce")

            # Keys for relational joins to DimDate and DimTime
            f_metrics["DateKey"] = f_metrics["dt"].dt.strftime("%Y%m%d").fillna("19700101").astype(int)
            f_metrics["TimeKey"] = f_metrics["dt"].dt.strftime("%H:%M:%S").fillna("00:00:00")
            f_metrics["TotalDataVolumeMB"] = (
                f_metrics.get("bytes_sent", 0) + f_metrics.get("bytes_recv", 0)
            ) / (1024.0 * 1024.0)

            # Ensure metric_id exists
            if "metric_id" not in f_metrics.columns:
                f_metrics["metric_id"] = range(1, len(f_metrics) + 1)

            cols_to_keep = [
                col for col in [
                    "metric_id", "timestamp", "DateKey", "TimeKey", "interface_name",
                    "upload_mbps", "download_mbps", "bytes_sent", "bytes_recv", "TotalDataVolumeMB",
                    "packets_sent_per_sec", "packets_recv_per_sec",
                    "latency_ms", "jitter_ms", "packet_loss_pct",
                    "estimated_utilization_pct", "health_score", "stability_score",
                    "monitoring_mode", "is_simulation", "data_quality_flag"
                ] if col in f_metrics.columns
            ]
            tables["FactNetworkMetrics"] = f_metrics[cols_to_keep]

        # -------------------------------------------------------------
        # 2. FactLatencyProbes
        # -------------------------------------------------------------
        if probes_df is not None and not probes_df.empty:
            f_probes = probes_df.copy()
            f_probes["dt"] = pd.to_datetime(f_probes["timestamp"], errors="coerce")
            f_probes["DateKey"] = f_probes["dt"].dt.strftime("%Y%m%d").fillna("19700101").astype(int)
            f_probes["TimeKey"] = f_probes["dt"].dt.strftime("%H:%M:%S").fillna("00:00:00")
            if "probe_id" not in f_probes.columns:
                f_probes["probe_id"] = range(1, len(f_probes) + 1)

            p_cols = [
                col for col in [
                    "probe_id", "timestamp", "DateKey", "TimeKey",
                    "target_name", "target_host", "probes_sent", "probes_received",
                    "packet_loss_pct", "latency_min_ms", "latency_avg_ms", "latency_max_ms",
                    "jitter_ms", "status"
                ] if col in f_probes.columns
            ]
            tables["FactLatencyProbes"] = f_probes[p_cols]

        # -------------------------------------------------------------
        # 3. FactIncidents
        # -------------------------------------------------------------
        if incidents_df is not None and not incidents_df.empty:
            f_inc = incidents_df.copy()
            f_inc["dt"] = pd.to_datetime(f_inc["start_timestamp"], errors="coerce")
            f_inc["DateKey"] = f_inc["dt"].dt.strftime("%Y%m%d").fillna("19700101").astype(int)
            f_inc["TimeKey"] = f_inc["dt"].dt.strftime("%H:%M:%S").fillna("00:00:00")
            tables["FactIncidents"] = f_inc

        # -------------------------------------------------------------
        # 4. FactAnomalies
        # -------------------------------------------------------------
        if anomalies_df is not None and not anomalies_df.empty:
            f_anom = anomalies_df.copy()
            f_anom["dt"] = pd.to_datetime(f_anom["timestamp"], errors="coerce")
            f_anom["DateKey"] = f_anom["dt"].dt.strftime("%Y%m%d").fillna("19700101").astype(int)
            f_anom["TimeKey"] = f_anom["dt"].dt.strftime("%H:%M:%S").fillna("00:00:00")
            tables["FactAnomalies"] = f_anom

        # -------------------------------------------------------------
        # 5. FactApplicationExperience
        # -------------------------------------------------------------
        if experience_df is not None and not experience_df.empty:
            f_exp = experience_df.copy()
            f_exp["dt"] = pd.to_datetime(f_exp["timestamp"], errors="coerce")
            f_exp["DateKey"] = f_exp["dt"].dt.strftime("%Y%m%d").fillna("19700101").astype(int)
            f_exp["TimeKey"] = f_exp["dt"].dt.strftime("%H:%M:%S").fillna("00:00:00")
            tables["FactApplicationExperience"] = f_exp

        # -------------------------------------------------------------
        # 6. DimDate (Calendar Dimension)
        # -------------------------------------------------------------
        timestamps = []
        if metrics_df is not None and not metrics_df.empty and "timestamp" in metrics_df.columns:
            timestamps.extend(metrics_df["timestamp"].dropna().tolist())
        if probes_df is not None and not probes_df.empty and "timestamp" in probes_df.columns:
            timestamps.extend(probes_df["timestamp"].dropna().tolist())

        if timestamps:
            ts_series = pd.to_datetime(pd.Series(timestamps), errors="coerce").dropna()
            min_date = ts_series.dt.date.min()
            max_date = ts_series.dt.date.max()
        else:
            min_date = datetime.now(timezone.utc).date()
            max_date = min_date

        date_range = pd.date_range(start=min_date, end=max_date, freq="D")
        dim_date = pd.DataFrame({"Date": date_range.date})
        dt_col = pd.to_datetime(dim_date["Date"])
        dim_date["DateKey"] = dt_col.dt.strftime("%Y%m%d").astype(int)
        dim_date["Year"] = dt_col.dt.year
        dim_date["Quarter"] = "Q" + dt_col.dt.quarter.astype(str)
        dim_date["Month"] = dt_col.dt.month
        dim_date["MonthName"] = dt_col.dt.month_name()
        dim_date["Day"] = dt_col.dt.day
        dim_date["DayOfWeek"] = dt_col.dt.dayofweek + 1  # 1 = Monday
        dim_date["DayName"] = dt_col.dt.day_name()
        dim_date["IsWeekend"] = dt_col.dt.weekday >= 5
        tables["DimDate"] = dim_date

        # -------------------------------------------------------------
        # 7. DimTime (Time-of-Day Dimension)
        # -------------------------------------------------------------
        time_strings = []
        for hour in range(24):
            for minute in range(60):
                time_strings.append(f"{hour:02d}:{minute:02d}:00")

        dim_time = pd.DataFrame({"TimeKey": time_strings})
        dim_time["Hour"] = dim_time["TimeKey"].apply(lambda t: int(t.split(":")[0]))
        dim_time["Minute"] = dim_time["TimeKey"].apply(lambda t: int(t.split(":")[1]))

        def _get_time_of_day(hour: int) -> str:
            if 6 <= hour < 12:
                return "Morning (06:00-12:00)"
            elif 12 <= hour < 17:
                return "Afternoon (12:00-17:00)"
            elif 17 <= hour < 22:
                return "Evening (17:00-22:00)"
            else:
                return "Night (22:00-06:00)"

        dim_time["TimeOfDay"] = dim_time["Hour"].apply(_get_time_of_day)
        tables["DimTime"] = dim_time

        # -------------------------------------------------------------
        # 8. DimInterface
        # -------------------------------------------------------------
        if interfaces_df is not None and not interfaces_df.empty:
            dim_iface = interfaces_df.copy()
            if "name" in dim_iface.columns and "interface_name" not in dim_iface.columns:
                dim_iface["interface_name"] = dim_iface["name"]
            tables["DimInterface"] = dim_iface
        else:
            iface_names = []
            if metrics_df is not None and not metrics_df.empty and "interface_name" in metrics_df.columns:
                iface_names = metrics_df["interface_name"].dropna().unique().tolist()
            if not iface_names:
                iface_names = ["Wi-Fi", "Ethernet"]
            tables["DimInterface"] = pd.DataFrame({
                "interface_name": iface_names,
                "speed_mbps": [100.0] * len(iface_names),
                "is_wireless": [1 if "wi" in name.lower() or "wlan" in name.lower() else 0 for name in iface_names],
                "is_loopback": [0] * len(iface_names)
            })

        # -------------------------------------------------------------
        # 9. DimTarget (Probe Targets)
        # -------------------------------------------------------------
        targets = [
            {"target_name": "gateway", "target_host": "Default Gateway", "target_type": "Local LAN Gateway", "expected_sla_ms": 5.0},
            {"target_name": "google_dns", "target_host": "8.8.8.8", "target_type": "Public Anycast DNS", "expected_sla_ms": 30.0},
            {"target_name": "cloudflare_dns", "target_host": "1.1.1.1", "target_type": "Public Edge DNS", "expected_sla_ms": 20.0},
        ]
        tables["DimTarget"] = pd.DataFrame(targets)

        return tables

    def export_from_database(self, db_manager: Any) -> dict[str, int]:
        """Query authoritative SQLite database and export full Star Schema tables.

        Returns a dictionary mapping table name to record count written.
        """
        try:
            metrics_df = db_manager.query_df("SELECT * FROM network_metrics ORDER BY timestamp DESC LIMIT 10000")
        except Exception:
            metrics_df = pd.DataFrame()

        try:
            probes_df = db_manager.query_df("SELECT * FROM latency_probes ORDER BY timestamp DESC LIMIT 5000")
        except Exception:
            probes_df = pd.DataFrame()

        try:
            incidents_df = db_manager.query_df("SELECT * FROM incidents ORDER BY start_timestamp DESC")
        except Exception:
            incidents_df = pd.DataFrame()

        try:
            anomalies_df = db_manager.query_df("SELECT * FROM anomalies ORDER BY timestamp DESC LIMIT 2000")
        except Exception:
            anomalies_df = pd.DataFrame()

        try:
            experience_df = db_manager.query_df("SELECT * FROM application_experience ORDER BY timestamp DESC LIMIT 5000")
        except Exception:
            experience_df = pd.DataFrame()

        try:
            interfaces_df = db_manager.query_df("SELECT * FROM interfaces")
        except Exception:
            interfaces_df = pd.DataFrame()

        tables = self.generate_star_schema_tables(
            metrics_df=metrics_df,
            probes_df=probes_df,
            incidents_df=incidents_df,
            anomalies_df=anomalies_df,
            experience_df=experience_df,
            interfaces_df=interfaces_df
        )

        counts = self.export_all_for_powerbi(tables)
        return counts

    def export_all_for_powerbi(self, tables_dict: dict[str, pd.DataFrame]) -> dict[str, int]:
        """Save transformed star schema tables as CSVs into both export dirs."""
        counts = {}
        for name, table in tables_dict.items():
            if table is None or table.empty:
                counts[name] = 0
                continue

            # Write to both root exports and star_schema subfolder for maximum compatibility
            path1 = self.export_dir / f"{name}.csv"
            path2 = self.star_dir / f"{name}.csv"

            try:
                table.to_csv(path1, index=False, encoding="utf-8")
                table.to_csv(path2, index=False, encoding="utf-8")
                counts[name] = len(table)
            except Exception as exc:
                logger.error(f"Error saving {name} for Power BI: {exc}")
                counts[name] = 0

        return counts
