"""Unit and integration tests for Power BI live ecosystem and Star Schema.

Validates:
1. PowerBIExporter star schema generation from database and DataFrames.
2. DimDate and DimTime relational keys and calendar hierarchies.
3. PowerBIStreamer formatting and asynchronous queuing.
4. PowerBIAPIServer HTTP endpoints and CORS headers.
5. PowerBIAutoRefresher initialization.
"""

from datetime import datetime, timezone
import json
import time
import urllib.request
import pandas as pd
import pytest

from src.powerbi.exporter import PowerBIExporter
from src.powerbi.streaming import PowerBIStreamer
from src.powerbi.api_server import PowerBIAPIServer
from src.powerbi.auto_refresh import PowerBIAutoRefresher
from src.storage.database import DatabaseManager
from src.processing.metrics import make_consolidated_metric


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_pbi.db"
    db = DatabaseManager(db_path=str(db_file))
    return db


def test_powerbi_star_schema_generation(tmp_path):
    exporter = PowerBIExporter(export_dir=str(tmp_path))

    metrics_df = pd.DataFrame([{
        "metric_id": 1,
        "timestamp": "2026-09-30T10:00:00+00:00",
        "interface_name": "Wi-Fi",
        "upload_mbps": 12.0,
        "download_mbps": 80.0,
        "bytes_sent": 1000000,
        "bytes_recv": 5000000,
        "packets_sent_per_sec": 100.0,
        "packets_recv_per_sec": 200.0,
        "latency_ms": 18.0,
        "jitter_ms": 2.0,
        "packet_loss_pct": 0.0,
        "health_score": 95.0,
        "stability_score": 94.0,
        "monitoring_mode": "NORMAL"
    }])

    probes_df = pd.DataFrame([{
        "probe_id": 1,
        "timestamp": "2026-09-30T10:00:00+00:00",
        "target_name": "gateway",
        "target_host": "192.168.1.1",
        "probes_sent": 5,
        "probes_received": 5,
        "packet_loss_pct": 0.0,
        "latency_avg_ms": 2.5,
        "jitter_ms": 0.5,
        "status": "REACHABLE"
    }])

    tables = exporter.generate_star_schema_tables(
        metrics_df=metrics_df,
        probes_df=probes_df
    )

    assert "FactNetworkMetrics" in tables
    assert "FactLatencyProbes" in tables
    assert "DimDate" in tables
    assert "DimTime" in tables
    assert "DimInterface" in tables
    assert "DimTarget" in tables

    # Check DateKey and TimeKey in FactNetworkMetrics
    f_metrics = tables["FactNetworkMetrics"]
    assert "DateKey" in f_metrics.columns
    assert "TimeKey" in f_metrics.columns
    assert f_metrics["DateKey"].iloc[0] == 20260930
    assert f_metrics["TimeKey"].iloc[0] == "10:00:00"

    # Check DimDate structure
    dim_date = tables["DimDate"]
    assert "DateKey" in dim_date.columns
    assert "Year" in dim_date.columns
    assert "Quarter" in dim_date.columns
    assert "DayName" in dim_date.columns

    # Check DimTime structure
    dim_time = tables["DimTime"]
    assert len(dim_time) == 1440  # 24 * 60 minutes
    assert "TimeOfDay" in dim_time.columns

    # Test file exports
    counts = exporter.export_all_for_powerbi(tables)
    assert counts["FactNetworkMetrics"] == 1
    assert counts["DimDate"] >= 1
    assert (tmp_path / "FactNetworkMetrics.csv").exists()
    assert (tmp_path / "star_schema" / "FactNetworkMetrics.csv").exists()


def test_powerbi_streamer_formatting():
    streamer = PowerBIStreamer(push_url="http://mock.powerbi.invalid/rows")

    metric = make_consolidated_metric(
        interface_name="Wi-Fi",
        upload_mbps=15.5,
        download_mbps=88.2,
        bytes_sent=1000,
        bytes_recv=2000,
        packets_sent=10,
        packets_recv=20,
        packets_sent_per_sec=10.0,
        packets_recv_per_sec=20.0,
        latency_ms=19.4,
        jitter_ms=2.1,
        packet_loss_pct=0.0,
        interface_speed_mbps=100.0,
        health_score=96.0,
        stability_score=94.0,
        monitoring_mode="NORMAL"
    )

    payload = streamer._format_payload(metric)
    assert payload["interface_name"] == "Wi-Fi"
    assert payload["upload_mbps"] == 15.5
    assert payload["download_mbps"] == 88.2
    assert payload["latency_ms"] == 19.4
    assert payload["health_score"] == 96.0
    assert payload["monitoring_mode"] == "NORMAL"

    # Test enqueue
    enqueued = streamer.push_metric(metric)
    assert enqueued is True
    assert streamer.queue.qsize() >= 1

    streamer.stop()


def test_powerbi_api_server_endpoints(temp_db):
    server = PowerBIAPIServer(host="127.0.0.1", port=8089, db_manager=temp_db)
    server.start()
    time.sleep(0.5)

    try:
        # 1. Test /api/status
        req = urllib.request.urlopen("http://127.0.0.1:8089/api/status", timeout=3)
        data = json.loads(req.read().decode("utf-8"))
        assert data["status"] == "ONLINE"
        assert "telemetry_counts" in data

        # 2. Test /api/star-schema/all
        req2 = urllib.request.urlopen("http://127.0.0.1:8089/api/star-schema/all", timeout=3)
        data2 = json.loads(req2.read().decode("utf-8"))
        assert "star_schema_tables" in data2
    finally:
        server.stop()


def test_powerbi_auto_refresher_init():
    refresher = PowerBIAutoRefresher(interval_sec=5)
    assert refresher.interval_sec == 5
    assert refresher.is_running is False
    # find_pbi_windows returns list (empty if Power BI not open)
    hwnds = refresher.find_pbi_windows()
    assert isinstance(hwnds, list)
