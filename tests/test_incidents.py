"""Unit tests for incident management, hysteresis debounce, and resolution."""

from pathlib import Path
import pytest
from src.incidents.incident_manager import IncidentManager
from src.storage.database import DatabaseManager
from src.storage.repositories import IncidentRepository


@pytest.fixture
def temp_incident_manager(tmp_path):
    db_file = tmp_path / "test_inc.db"
    db = DatabaseManager(db_path=str(db_file), schema_path="database/schema.sql")
    repo = IncidentRepository(db)
    return IncidentManager(repository=repo, debounce_trigger=3, debounce_resolve=3), repo


def test_incident_debounce_trigger_and_resolve(temp_incident_manager):
    mgr, repo = temp_incident_manager

    # 1. First abnormal sample -> debounce count 1, no incident opened yet
    inc1 = mgr.evaluate_sample(
        timestamp_iso="2026-09-30T10:00:00Z",
        epoch_time=1000.0,
        health_score=40.0,
        stability_score=40.0,
        latency_ms=150.0,
        jitter_ms=25.0,
        packet_loss_pct=8.0,
        utilization_pct=90.0
    )
    assert inc1 is None
    assert mgr.consecutive_abnormal_samples == 1

    # 2. Second abnormal sample
    inc2 = mgr.evaluate_sample(
        timestamp_iso="2026-09-30T10:00:02Z",
        epoch_time=1002.0,
        health_score=40.0,
        stability_score=40.0,
        latency_ms=150.0,
        jitter_ms=25.0,
        packet_loss_pct=8.0,
        utilization_pct=90.0
    )
    assert inc2 is None
    assert mgr.consecutive_abnormal_samples == 2

    # 3. Third abnormal sample -> debounce threshold reached (3), incident MUST open
    inc3 = mgr.evaluate_sample(
        timestamp_iso="2026-09-30T10:00:04Z",
        epoch_time=1004.0,
        health_score=40.0,
        stability_score=40.0,
        latency_ms=150.0,
        jitter_ms=25.0,
        packet_loss_pct=8.0,
        utilization_pct=90.0
    )
    assert inc3 is not None
    assert inc3.status == "OPEN"

    # 4. Provide 3 consecutive normal samples to trigger resolution
    for i in range(3):
        res = mgr.evaluate_sample(
            timestamp_iso=f"2026-09-30T10:00:1{i}Z",
            epoch_time=1010.0 + i,
            health_score=95.0,
            stability_score=92.0,
            latency_ms=18.0,
            jitter_ms=1.5,
            packet_loss_pct=0.0,
            utilization_pct=10.0
        )

    # After 3 normal samples, active incident is resolved
    assert mgr.active_incident is None
    resolved_history = repo.get_incident_history(limit=5)
    assert len(resolved_history) == 1
    assert resolved_history.iloc[0]["status"] == "RESOLVED"
