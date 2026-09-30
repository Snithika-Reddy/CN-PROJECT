"""NetIntel Power BI Desktop Direct Python Data Connector.

Instructions for Power BI Desktop:
1. Open Power BI Desktop.
2. Click 'Get Data' -> 'More...' -> 'Python script' -> 'Connect'.
3. Paste the entire content of this script into the dialog.
4. Click 'OK'. In the Navigator window, select the tables:
   - FactNetworkMetrics
   - FactLatencyProbes
   - FactIncidents
   - FactAnomalies
   - FactApplicationExperience
   - DimDate
   - DimTime
   - DimInterface
   - DimTarget
5. Click 'Load'. All tables are loaded with high-speed in-memory indexing!
"""

import os
from pathlib import Path
import sqlite3
import pandas as pd

# 1. Resolve Project Root
# Tries relative path, environment variable, or fixed fallback
potential_paths = [
    Path(os.getcwd()),
    Path(__file__).resolve().parent.parent if "__file__" in locals() else None,
    Path("C:/PROJECTS/CN-PROJECT"),
    Path("D:/PROJECTS/CN-PROJECT"),
]

project_root = None
for p in potential_paths:
    if p and (p / "database" / "network_monitor.db").exists():
        project_root = p
        break

if not project_root:
    project_root = Path("C:/PROJECTS/CN-PROJECT")

db_path = project_root / "database" / "network_monitor.db"
export_dir = project_root / "data" / "exports"


def load_table(table_name: str, fallback_csv: str) -> pd.DataFrame:
    """Read from SQLite with fallback to CSV."""
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            conn.close()
            if not df.empty:
                return df
        except Exception:
            pass

    csv_file = export_dir / fallback_csv
    if csv_file.exists():
        try:
            return pd.read_csv(csv_file)
        except Exception:
            pass

    return pd.DataFrame()


# 2. Extract Raw Tables
raw_metrics = load_table("network_metrics", "network_metrics.csv")
raw_probes = load_table("latency_probes", "latency_metrics.csv")
raw_incidents = load_table("incidents", "incidents.csv")
raw_anomalies = load_table("anomalies", "anomalies.csv")
raw_experience = load_table("application_experience", "application_experience.csv")
raw_interfaces = load_table("interfaces", "DimInterface.csv")

# 3. Build Star Schema Fact & Dimension Tables

# --- FactNetworkMetrics ---
if not raw_metrics.empty:
    FactNetworkMetrics = raw_metrics.copy()
    FactNetworkMetrics["dt"] = pd.to_datetime(FactNetworkMetrics["timestamp"], errors="coerce")
    FactNetworkMetrics["DateKey"] = FactNetworkMetrics["dt"].dt.strftime("%Y%m%d").fillna("19700101").astype(int)
    FactNetworkMetrics["TimeKey"] = FactNetworkMetrics["dt"].dt.strftime("%H:%M:%S").fillna("00:00:00")
    if "metric_id" not in FactNetworkMetrics.columns:
        FactNetworkMetrics["metric_id"] = range(1, len(FactNetworkMetrics) + 1)
    if "bytes_sent" in FactNetworkMetrics.columns and "bytes_recv" in FactNetworkMetrics.columns:
        FactNetworkMetrics["TotalDataVolumeMB"] = (FactNetworkMetrics["bytes_sent"] + FactNetworkMetrics["bytes_recv"]) / 1048576.0
else:
    FactNetworkMetrics = pd.DataFrame(columns=[
        "metric_id", "timestamp", "DateKey", "TimeKey", "interface_name",
        "upload_mbps", "download_mbps", "latency_ms", "jitter_ms", "packet_loss_pct",
        "health_score", "stability_score", "monitoring_mode"
    ])

# --- FactLatencyProbes ---
if not raw_probes.empty:
    FactLatencyProbes = raw_probes.copy()
    FactLatencyProbes["dt"] = pd.to_datetime(FactLatencyProbes["timestamp"], errors="coerce")
    FactLatencyProbes["DateKey"] = FactLatencyProbes["dt"].dt.strftime("%Y%m%d").fillna("19700101").astype(int)
    FactLatencyProbes["TimeKey"] = FactLatencyProbes["dt"].dt.strftime("%H:%M:%S").fillna("00:00:00")
else:
    FactLatencyProbes = pd.DataFrame(columns=[
        "probe_id", "timestamp", "DateKey", "TimeKey", "target_name", "target_host",
        "packet_loss_pct", "latency_avg_ms", "jitter_ms", "status"
    ])

# --- FactIncidents ---
if not raw_incidents.empty:
    FactIncidents = raw_incidents.copy()
    FactIncidents["dt"] = pd.to_datetime(FactIncidents["start_timestamp"], errors="coerce")
    FactIncidents["DateKey"] = FactIncidents["dt"].dt.strftime("%Y%m%d").fillna("19700101").astype(int)
else:
    FactIncidents = pd.DataFrame(columns=[
        "incident_id", "start_timestamp", "DateKey", "duration_seconds", "status", "severity", "trigger_reason"
    ])

# --- FactAnomalies ---
if not raw_anomalies.empty:
    FactAnomalies = raw_anomalies.copy()
    FactAnomalies["dt"] = pd.to_datetime(FactAnomalies["timestamp"], errors="coerce")
    FactAnomalies["DateKey"] = FactAnomalies["dt"].dt.strftime("%Y%m%d").fillna("19700101").astype(int)
else:
    FactAnomalies = pd.DataFrame(columns=[
        "anomaly_id", "timestamp", "DateKey", "metric_name", "observed_value", "deviation_pct", "severity"
    ])

# --- FactApplicationExperience ---
if not raw_experience.empty:
    FactApplicationExperience = raw_experience.copy()
    FactApplicationExperience["dt"] = pd.to_datetime(FactApplicationExperience["timestamp"], errors="coerce")
    FactApplicationExperience["DateKey"] = FactApplicationExperience["dt"].dt.strftime("%Y%m%d").fillna("19700101").astype(int)
else:
    FactApplicationExperience = pd.DataFrame(columns=[
        "experience_id", "timestamp", "DateKey", "video_call_score", "gaming_score", "web_browsing_score"
    ])

# --- DimDate ---
all_ts = []
if not FactNetworkMetrics.empty and "timestamp" in FactNetworkMetrics.columns:
    all_ts.extend(FactNetworkMetrics["timestamp"].dropna().tolist())
if all_ts:
    ts_series = pd.to_datetime(pd.Series(all_ts), errors="coerce").dropna()
    min_date = ts_series.dt.date.min()
    max_date = ts_series.dt.date.max()
else:
    min_date = pd.to_datetime("today").date()
    max_date = min_date

date_range = pd.date_range(start=min_date, end=max_date, freq="D")
DimDate = pd.DataFrame({"Date": date_range.date})
dts = pd.to_datetime(DimDate["Date"])
DimDate["DateKey"] = dts.dt.strftime("%Y%m%d").astype(int)
DimDate["Year"] = dts.dt.year
DimDate["Quarter"] = "Q" + dts.dt.quarter.astype(str)
DimDate["Month"] = dts.dt.month
DimDate["MonthName"] = dts.dt.month_name()
DimDate["Day"] = dts.dt.day
DimDate["DayOfWeek"] = dts.dt.dayofweek + 1
DimDate["DayName"] = dts.dt.day_name()
DimDate["IsWeekend"] = dts.dt.weekday >= 5

# --- DimTime ---
time_keys = [f"{h:02d}:{m:02d}:00" for h in range(24) for m in range(60)]
DimTime = pd.DataFrame({"TimeKey": time_keys})
DimTime["Hour"] = DimTime["TimeKey"].apply(lambda t: int(t.split(":")[0]))
DimTime["Minute"] = DimTime["TimeKey"].apply(lambda t: int(t.split(":")[1]))


def _time_period(h: int) -> str:
    if 6 <= h < 12:
        return "Morning (06:00-12:00)"
    elif 12 <= h < 17:
        return "Afternoon (12:00-17:00)"
    elif 17 <= h < 22:
        return "Evening (17:00-22:00)"
    return "Night (22:00-06:00)"


DimTime["TimeOfDay"] = DimTime["Hour"].apply(_time_period)

# --- DimInterface ---
if not raw_interfaces.empty:
    DimInterface = raw_interfaces.copy()
    if "name" in DimInterface.columns and "interface_name" not in DimInterface.columns:
        DimInterface["interface_name"] = DimInterface["name"]
else:
    DimInterface = pd.DataFrame({
        "interface_name": ["Wi-Fi", "Ethernet"],
        "speed_mbps": [100.0, 1000.0],
        "is_wireless": [1, 0]
    })

# --- DimTarget ---
DimTarget = pd.DataFrame([
    {"target_name": "gateway", "target_host": "Default Gateway", "target_type": "Local LAN Gateway", "expected_sla_ms": 5.0},
    {"target_name": "google_dns", "target_host": "8.8.8.8", "target_type": "Public Anycast DNS", "expected_sla_ms": 30.0},
    {"target_name": "cloudflare_dns", "target_host": "1.1.1.1", "target_type": "Public Edge DNS", "expected_sla_ms": 20.0},
])

print(f"NetIntel Data Connector loaded {len(FactNetworkMetrics)} metrics, {len(FactIncidents)} incidents.")
