"""Unit tests for SQLite storage layer and repository entities."""

import os
from pathlib import Path
import pytest
from src.storage.database import DatabaseManager
from src.storage.repositories import (
    MetricsRepository,
    AnomalyRepository,
    IncidentRepository
)
from src.processing.metrics import make_consolidated_metric


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_network.db"
    schema_file = Path("database/schema.sql")
    return DatabaseManager(db_path=str(db_file), schema_path=str(schema_file))


def test_database_initialization(temp_db):
    # Verify tables were created
    rows = temp_db.execute_query("SELECT name FROM sqlite_master WHERE type='table';")
    table_names = [r["name"] for r in rows]
    assert "network_metrics" in table_names
    assert "incidents" in table_names
    assert "anomalies" in table_names
    assert "latency_probes" in table_names


def test_metrics_crud(temp_db):
    repo = MetricsRepository(temp_db)
    m = make_consolidated_metric(
        interface_name="Wi-Fi",
        upload_mbps=10.0,
        download_mbps=50.0,
        bytes_sent=1000,
        bytes_recv=5000,
        packets_sent=10,
        packets_recv=50,
        packets_sent_per_sec=5.0,
        packets_recv_per_sec=25.0,
        latency_ms=22.5,
        jitter_ms=2.1,
        packet_loss_pct=0.0,
        interface_speed_mbps=1000.0,
        health_score=95.0,
        stability_score=90.0
    )
    row_id = repo.save_metric(m)
    assert row_id > 0

    df = repo.get_latest_metrics(limit=10)
    assert len(df) == 1
    assert df.iloc[0]["interface_name"] == "Wi-Fi"
    assert df.iloc[0]["latency_ms"] == 22.5


def test_incidents_crud(temp_db):
    repo = IncidentRepository(temp_db)
    inc_id = "INC-TEST-001"
    repo.create_incident(inc_id, "2026-09-30T10:00:00Z", "WARNING", "High latency spike")

    open_incidents = repo.get_open_incidents()
    assert len(open_incidents) == 1
    assert open_incidents[0]["incident_id"] == inc_id

    # Add timeline event
    repo.add_timeline_event(inc_id, "2026-09-30T10:00:01Z", "METRIC_SPIKE", "Latency rose to 150ms")
    events = repo.get_incident_timeline(inc_id)
    assert len(events) == 1
    assert events[0]["event_type"] == "METRIC_SPIKE"

    # Resolve
    repo.resolve_incident(inc_id, "2026-09-30T10:05:00Z", 300.0, "Resolved after route normalized")
    open_now = repo.get_open_incidents()
    assert len(open_now) == 0
