"""Relational Repository Layer for SQLite Data Access.

Provides strongly typed, isolated data access methods for all telemetry,
incident, anomaly, probe, and self-monitoring entities.
"""

from datetime import datetime, timezone
import json
import logging
from typing import Any
import pandas as pd

from .database import DatabaseManager
from ..processing.metrics import ConsolidatedMetric
from ..collectors.interface_collector import InterfaceInfo
from ..collectors.latency_collector import ProbeResult

logger = logging.getLogger(__name__)


class MetricsRepository:
    """Handles persistence and retrieval of core network telemetry samples."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def save_metric(self, m: ConsolidatedMetric) -> int:
        """Insert a single consolidated metric record."""
        sql = """
        INSERT INTO network_metrics (
            timestamp, epoch_time, interface_name,
            upload_mbps, download_mbps, bytes_sent, bytes_recv,
            packets_sent, packets_recv, packets_sent_per_sec, packets_recv_per_sec,
            latency_ms, jitter_ms, packet_loss_pct, estimated_utilization_pct,
            health_score, stability_score, monitoring_mode,
            is_simulation, is_replay, data_quality_flag
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            m.timestamp_iso, m.epoch_time, m.interface_name,
            m.upload_mbps, m.download_mbps, m.bytes_sent, m.bytes_recv,
            m.packets_sent, m.packets_recv, m.packets_sent_per_sec, m.packets_recv_per_sec,
            m.latency_ms, m.jitter_ms, m.packet_loss_pct, m.estimated_utilization_pct,
            m.health_score, m.stability_score, m.monitoring_mode,
            1 if m.is_simulation else 0,
            1 if m.is_replay else 0,
            m.data_quality_flag
        )
        return self.db.execute_non_query(sql, params)

    def get_latest_metrics(self, limit: int = 100, is_simulation: bool = False) -> pd.DataFrame:
        """Fetch the most recent N metric samples ordered chronologically."""
        sql = """
        SELECT * FROM (
            SELECT * FROM network_metrics
            WHERE is_simulation = ?
            ORDER BY epoch_time DESC
            LIMIT ?
        ) ORDER BY epoch_time ASC
        """
        return self.db.query_df(sql, (1 if is_simulation else 0, limit))

    def get_metrics_by_timerange(self, start_iso: str, end_iso: str, is_simulation: bool = False) -> pd.DataFrame:
        """Query metrics between start and end ISO timestamps."""
        sql = """
        SELECT * FROM network_metrics
        WHERE timestamp >= ? AND timestamp <= ? AND is_simulation = ?
        ORDER BY epoch_time ASC
        """
        return self.db.query_df(sql, (start_iso, end_iso, 1 if is_simulation else 0))

    def count_metrics(self, is_simulation: bool = False) -> int:
        """Return total record count for real or simulated samples."""
        sql = "SELECT COUNT(*) as cnt FROM network_metrics WHERE is_simulation = ?"
        res = self.db.execute_query(sql, (1 if is_simulation else 0,))
        return res[0]["cnt"] if res else 0


class InterfaceRepository:
    """Manages the network interfaces hardware catalog."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def upsert_interface(self, info: InterfaceInfo) -> None:
        """Insert or update interface hardware and status details."""
        now_iso = datetime.now(timezone.utc).isoformat()
        sql = """
        INSERT INTO interfaces (
            name, ip_address, mac_address, speed_mbps,
            is_up, is_wireless, is_loopback,
            first_seen_timestamp, last_updated_timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            ip_address = excluded.ip_address,
            mac_address = excluded.mac_address,
            speed_mbps = excluded.speed_mbps,
            is_up = excluded.is_up,
            last_updated_timestamp = excluded.last_updated_timestamp
        """
        params = (
            info.name, info.ip_address, info.mac_address, info.speed_mbps,
            1 if info.is_up else 0,
            1 if info.is_wireless else 0,
            1 if info.is_loopback else 0,
            now_iso, now_iso
        )
        self.db.execute_non_query(sql, params)

    def get_all_interfaces(self) -> pd.DataFrame:
        """Retrieve all cataloged interfaces."""
        return self.db.query_df("SELECT * FROM interfaces ORDER BY name ASC")


class LatencyRepository:
    """Manages multi-target latency, jitter, and packet loss probe measurements."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def save_probe(self, probe: ProbeResult) -> int:
        """Save a target-specific probe result."""
        dt_iso = datetime.fromtimestamp(probe.timestamp, tz=timezone.utc).isoformat()
        sql = """
        INSERT INTO latency_probes (
            timestamp, target_name, target_host,
            probes_sent, probes_received, packet_loss_pct,
            latency_min_ms, latency_avg_ms, latency_max_ms,
            jitter_ms, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            dt_iso, probe.target_name, probe.target_host,
            probe.probes_sent, probe.probes_received, probe.packet_loss_pct,
            probe.latency_min_ms, probe.latency_avg_ms, probe.latency_max_ms,
            probe.jitter_ms, probe.status_message
        )
        return self.db.execute_non_query(sql, params)

    def get_recent_probes(self, limit: int = 100) -> pd.DataFrame:
        """Get latest probe samples across all targets."""
        sql = "SELECT * FROM latency_probes ORDER BY probe_id DESC LIMIT ?"
        return self.db.query_df(sql, (limit,))


class AnomalyRepository:
    """Manages detected anomaly events."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def save_anomaly(
        self,
        timestamp_iso: str,
        metric_name: str,
        observed_value: float,
        baseline_expected: float,
        deviation_pct: float,
        severity: str,
        detection_method: str,
        details: str,
        is_simulation: bool = False
    ) -> int:
        """Persist an anomaly record."""
        sql = """
        INSERT INTO anomalies (
            timestamp, metric_name, observed_value, baseline_expected,
            deviation_pct, severity, detection_method, details, is_simulation
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            timestamp_iso, metric_name, observed_value, baseline_expected,
            deviation_pct, severity, detection_method, details,
            1 if is_simulation else 0
        )
        return self.db.execute_non_query(sql, params)

    def get_recent_anomalies(self, limit: int = 50, is_simulation: bool = False) -> pd.DataFrame:
        """Retrieve recent anomaly log entries."""
        sql = """
        SELECT * FROM anomalies
        WHERE is_simulation = ?
        ORDER BY anomaly_id DESC
        LIMIT ?
        """
        return self.db.query_df(sql, (1 if is_simulation else 0, limit))


class IncidentRepository:
    """Manages the full lifecycle and evidence timeline of network degradation incidents."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def create_incident(
        self,
        incident_id: str,
        start_timestamp_iso: str,
        severity: str,
        trigger_reason: str,
        is_simulation: bool = False
    ) -> None:
        """Create a new OPEN incident."""
        sql = """
        INSERT INTO incidents (
            incident_id, start_timestamp, status, severity, trigger_reason, is_simulation
        ) VALUES (?, ?, 'OPEN', ?, ?, ?)
        """
        self.db.execute_non_query(sql, (incident_id, start_timestamp_iso, severity, trigger_reason, 1 if is_simulation else 0))

    def update_incident_metrics(
        self,
        incident_id: str,
        peak_latency_ms: float | None,
        peak_jitter_ms: float | None,
        peak_packet_loss_pct: float | None,
        peak_utilization_pct: float | None,
        min_health_score: float | None,
        min_stability_score: float | None
    ) -> None:
        """Update incident peak degradation metrics as it evolves."""
        sql = """
        UPDATE incidents SET
            peak_latency_ms = MAX(COALESCE(peak_latency_ms, 0), COALESCE(?, 0)),
            peak_jitter_ms = MAX(COALESCE(peak_jitter_ms, 0), COALESCE(?, 0)),
            peak_packet_loss_pct = MAX(COALESCE(peak_packet_loss_pct, 0), COALESCE(?, 0)),
            peak_utilization_pct = MAX(COALESCE(peak_utilization_pct, 0), COALESCE(?, 0)),
            min_health_score = MIN(COALESCE(min_health_score, 100), COALESCE(?, 100)),
            min_stability_score = MIN(COALESCE(min_stability_score, 100), COALESCE(?, 100))
        WHERE incident_id = ?
        """
        self.db.execute_non_query(
            sql,
            (peak_latency_ms, peak_jitter_ms, peak_packet_loss_pct, peak_utilization_pct,
             min_health_score, min_stability_score, incident_id)
        )

    def set_incident_status(self, incident_id: str, status: str) -> None:
        """Set incident state (OPEN, RECOVERING, RESOLVED)."""
        sql = "UPDATE incidents SET status = ? WHERE incident_id = ?"
        self.db.execute_non_query(sql, (status, incident_id))

    def resolve_incident(
        self,
        incident_id: str,
        end_timestamp_iso: str,
        duration_seconds: float,
        diagnosis_summary: str
    ) -> None:
        """Mark incident RESOLVED with computed duration and final diagnosis."""
        sql = """
        UPDATE incidents SET
            end_timestamp = ?,
            duration_seconds = ?,
            status = 'RESOLVED',
            diagnosis_summary = ?
        WHERE incident_id = ?
        """
        self.db.execute_non_query(sql, (end_timestamp_iso, duration_seconds, diagnosis_summary, incident_id))

    def get_open_incidents(self, is_simulation: bool = False) -> list[dict[str, Any]]:
        """Return currently OPEN or RECOVERING incidents."""
        sql = "SELECT * FROM incidents WHERE status IN ('OPEN', 'RECOVERING') AND is_simulation = ? ORDER BY start_timestamp DESC"
        rows = self.db.execute_query(sql, (1 if is_simulation else 0,))
        return [dict(r) for r in rows]

    def get_incident_history(self, limit: int = 50, is_simulation: bool = False) -> pd.DataFrame:
        """Return incident history DataFrame."""
        sql = "SELECT * FROM incidents WHERE is_simulation = ? ORDER BY start_timestamp DESC LIMIT ?"
        return self.db.query_df(sql, (1 if is_simulation else 0, limit))

    def add_timeline_event(
        self,
        incident_id: str,
        timestamp_iso: str,
        event_type: str,
        description: str,
        metric_name: str | None = None,
        value: float | None = None
    ) -> int:
        """Add an event to an incident's chronological evidence timeline."""
        sql = """
        INSERT INTO incident_timeline (
            incident_id, timestamp, event_type, description, metric_name, value
        ) VALUES (?, ?, ?, ?, ?, ?)
        """
        return self.db.execute_non_query(sql, (incident_id, timestamp_iso, event_type, description, metric_name, value))

    def get_incident_timeline(self, incident_id: str) -> list[dict[str, Any]]:
        """Fetch all chronological timeline events for a given incident."""
        sql = "SELECT * FROM incident_timeline WHERE incident_id = ? ORDER BY event_id ASC"
        rows = self.db.execute_query(sql, (incident_id,))
        return [dict(r) for r in rows]


class DiagnosisRepository:
    """Manages multi-signal diagnostic hypotheses logs."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def save_diagnosis(
        self,
        timestamp_iso: str,
        incident_id: str | None,
        primary_hypothesis: str,
        evidence_strength: str,
        evidence_details: str,
        competing_hypotheses_json: str,
        recommended_action: str
    ) -> int:
        """Save a generated diagnosis."""
        sql = """
        INSERT INTO diagnoses (
            timestamp, incident_id, primary_hypothesis, evidence_strength,
            evidence_details, competing_hypotheses_json, recommended_action
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            timestamp_iso, incident_id, primary_hypothesis, evidence_strength,
            evidence_details, competing_hypotheses_json, recommended_action
        )
        return self.db.execute_non_query(sql, params)

    def get_recent_diagnoses(self, limit: int = 25) -> pd.DataFrame:
        """Fetch latest diagnostic evaluations."""
        sql = "SELECT * FROM diagnoses ORDER BY diagnosis_id DESC LIMIT ?"
        return self.db.query_df(sql, (limit,))


class ApplicationExperienceRepository:
    """Manages application experience suitability logs."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def save_experience(
        self,
        timestamp_iso: str,
        video_call: str,
        gaming: str,
        web_browsing: str,
        file_transfer: str,
        limiting_factor: str,
        is_simulation: bool = False
    ) -> int:
        """Record an application experience assessment."""
        sql = """
        INSERT INTO application_experience (
            timestamp, video_call_score, gaming_score, web_browsing_score,
            file_transfer_score, limiting_factor, is_simulation
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            timestamp_iso, video_call, gaming, web_browsing, file_transfer,
            limiting_factor, 1 if is_simulation else 0
        )
        return self.db.execute_non_query(sql, params)

    def get_latest(self, is_simulation: bool = False) -> dict[str, Any] | None:
        """Get most recent experience rating."""
        sql = "SELECT * FROM application_experience WHERE is_simulation = ? ORDER BY experience_id DESC LIMIT 1"
        rows = self.db.execute_query(sql, (1 if is_simulation else 0,))
        return dict(rows[0]) if rows else None


class MonitoringStateRepository:
    """Persists operational state of the adaptive monitoring loop."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def update_state(
        self,
        active_interface: str,
        monitoring_mode: str,
        interval_sec: float,
        last_timestamp_iso: str,
        reason: str = "",
        is_running: bool = True
    ) -> None:
        """Upsert current monitoring state."""
        sql = """
        INSERT INTO monitoring_state (
            state_id, active_interface, monitoring_mode, current_interval_sec,
            last_collection_timestamp, reason_for_mode, is_running
        ) VALUES (1, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(state_id) DO UPDATE SET
            active_interface = excluded.active_interface,
            monitoring_mode = excluded.monitoring_mode,
            current_interval_sec = excluded.current_interval_sec,
            last_collection_timestamp = excluded.last_collection_timestamp,
            reason_for_mode = excluded.reason_for_mode,
            is_running = excluded.is_running
        """
        self.db.execute_non_query(
            sql,
            (active_interface, monitoring_mode, interval_sec, last_timestamp_iso, reason, 1 if is_running else 0)
        )

    def get_state(self) -> dict[str, Any] | None:
        """Retrieve current monitoring state."""
        rows = self.db.execute_query("SELECT * FROM monitoring_state WHERE state_id = 1")
        return dict(rows[0]) if rows else None
