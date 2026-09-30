"""Incident Lifecycle & Debounce Management Engine.

Tracks incidents across state transitions:
NORMAL -> WARNING -> CRITICAL -> RECOVERY -> RESOLVED

Maintains hysteresis counters to prevent flapping / incident spam, logs chronological
evidence timelines, and generates 'What Changed?' comparative incident impact profiles.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
import time
from typing import Any
import uuid

from ..storage.repositories import IncidentRepository
from ..storage.csv_exporter import CSVExporter
from ..diagnosis.diagnosis_engine import DiagnosisEngine
from ..analytics.baseline import BaselineEngine

logger = logging.getLogger(__name__)


@dataclass
class ActiveIncidentState:
    incident_id: str
    start_epoch: float
    start_iso: str
    severity: str
    trigger_reason: str
    status: str  # 'OPEN', 'RECOVERING'
    peak_latency_ms: float
    peak_jitter_ms: float
    peak_loss_pct: float
    peak_util_pct: float
    min_health: float
    min_stability: float
    pre_incident_metrics: dict[str, float]
    consecutive_normal_samples: int = 0
    is_simulation: bool = False


class IncidentManager:
    """Manages creation, evolution, timeline journaling, and resolution of network incidents."""

    def __init__(
        self,
        repository: IncidentRepository,
        csv_exporter: CSVExporter | None = None,
        diagnosis_engine: DiagnosisEngine | None = None,
        debounce_trigger: int = 3,
        debounce_resolve: int = 5
    ):
        self.repo = repository
        self.csv_exporter = csv_exporter
        self.diagnosis_engine = diagnosis_engine or DiagnosisEngine()
        self.debounce_trigger = debounce_trigger
        self.debounce_resolve = debounce_resolve

        self.consecutive_abnormal_samples: int = 0
        self.active_incident: ActiveIncidentState | None = None

    def evaluate_sample(
        self,
        timestamp_iso: str,
        epoch_time: float,
        health_score: float,
        stability_score: float,
        latency_ms: float | None,
        jitter_ms: float | None,
        packet_loss_pct: float,
        utilization_pct: float | None,
        gateway_latency_ms: float | None = None,
        gateway_loss_pct: float = 0.0,
        baseline_latency: float | None = None,
        is_simulation: bool = False
    ) -> ActiveIncidentState | None:
        """Process current sample through debounce state machine."""
        # Define abnormal condition: health < 70 OR loss > 3% OR latency > 100ms
        is_abnormal = (
            health_score < 70.0
            or packet_loss_pct >= 3.0
            or (latency_ms is not None and latency_ms >= 100.0)
            or (utilization_pct is not None and utilization_pct >= 90.0)
        )

        lat_val = latency_ms or 0.0
        jit_val = jitter_ms or 0.0
        util_val = utilization_pct or 0.0

        # Scenario 1: Currently NO active incident
        if self.active_incident is None:
            if is_abnormal:
                self.consecutive_abnormal_samples += 1
                if self.consecutive_abnormal_samples >= self.debounce_trigger:
                    # Open new Incident
                    inc_id = f"INC-{int(epoch_time)}-{uuid.uuid4().hex[:6]}"
                    severity = "CRITICAL" if (health_score < 50.0 or packet_loss_pct >= 8.0) else "WARNING"
                    reason = f"Health dropped to {health_score}/100 with {packet_loss_pct}% loss and {lat_val:.1f}ms latency."

                    self.active_incident = ActiveIncidentState(
                        incident_id=inc_id,
                        start_epoch=epoch_time,
                        start_iso=timestamp_iso,
                        severity=severity,
                        trigger_reason=reason,
                        status="OPEN",
                        peak_latency_ms=lat_val,
                        peak_jitter_ms=jit_val,
                        peak_loss_pct=packet_loss_pct,
                        peak_util_pct=util_val,
                        min_health=health_score,
                        min_stability=stability_score,
                        pre_incident_metrics={
                            "latency_ms": baseline_latency or lat_val,
                            "health_score": 95.0,
                            "stability_score": 95.0,
                            "packet_loss_pct": 0.0
                        },
                        consecutive_normal_samples=0,
                        is_simulation=is_simulation
                    )

                    # Persist to DB and CSV
                    self.repo.create_incident(inc_id, timestamp_iso, severity, reason, is_simulation)
                    self.repo.add_timeline_event(inc_id, timestamp_iso, "TRIGGER", f"Incident opened: {reason}", "health_score", health_score)

                    if self.csv_exporter:
                        self.csv_exporter.append_incident({
                            "incident_id": inc_id,
                            "start_timestamp": timestamp_iso,
                            "status": "OPEN",
                            "severity": severity,
                            "trigger_reason": reason,
                            "is_simulation": is_simulation
                        })
                    logger.warning(f"Opened {severity} incident {inc_id}: {reason}")
            else:
                self.consecutive_abnormal_samples = 0

            return self.active_incident

        # Scenario 2: Active incident is in progress
        inc = self.active_incident
        # Update peak degradation stats
        inc.peak_latency_ms = max(inc.peak_latency_ms, lat_val)
        inc.peak_jitter_ms = max(inc.peak_jitter_ms, jit_val)
        inc.peak_loss_pct = max(inc.peak_loss_pct, packet_loss_pct)
        inc.peak_util_pct = max(inc.peak_util_pct, util_val)
        inc.min_health = min(inc.min_health, health_score)
        inc.min_stability = min(inc.min_stability, stability_score)

        self.repo.update_incident_metrics(
            inc.incident_id, inc.peak_latency_ms, inc.peak_jitter_ms,
            inc.peak_loss_pct, inc.peak_util_pct, inc.min_health, inc.min_stability
        )

        if is_abnormal:
            inc.consecutive_normal_samples = 0
            if inc.status == "RECOVERING":
                inc.status = "OPEN"
                self.repo.set_incident_status(inc.incident_id, "OPEN")
                self.repo.add_timeline_event(inc.incident_id, timestamp_iso, "RELAPSE", "Metrics degraded again after partial recovery.")
        else:
            inc.consecutive_normal_samples += 1
            if inc.consecutive_normal_samples == 1 and inc.status == "OPEN":
                inc.status = "RECOVERING"
                self.repo.set_incident_status(inc.incident_id, "RECOVERING")
                self.repo.add_timeline_event(inc.incident_id, timestamp_iso, "RECOVERY_START", "Metrics returned toward normal baseline.")

            # Full resolution condition reached
            if inc.consecutive_normal_samples >= self.debounce_resolve:
                duration_sec = round(epoch_time - inc.start_epoch, 1)

                # Final Diagnosis
                diag_report = self.diagnosis_engine.diagnose(
                    timestamp_iso=timestamp_iso,
                    incident_id=inc.incident_id,
                    latency_ms=inc.peak_latency_ms,
                    baseline_latency_ms=baseline_latency,
                    jitter_ms=inc.peak_jitter_ms,
                    packet_loss_pct=inc.peak_loss_pct,
                    utilization_pct=inc.peak_util_pct,
                    gateway_latency_ms=gateway_latency_ms,
                    gateway_loss_pct=gateway_loss_pct
                )
                diag_summary = f"{diag_report.primary_hypothesis.cause} (Strength: {diag_report.primary_hypothesis.evidence_strength})"

                self.repo.resolve_incident(inc.incident_id, timestamp_iso, duration_sec, diag_summary)
                self.repo.add_timeline_event(
                    inc.incident_id, timestamp_iso, "RESOLVED",
                    f"Incident resolved after {duration_sec}s. Diagnosis: {diag_summary}."
                )

                if self.csv_exporter:
                    self.csv_exporter.append_incident({
                        "incident_id": inc.incident_id,
                        "start_timestamp": inc.start_iso,
                        "end_timestamp": timestamp_iso,
                        "duration_seconds": duration_sec,
                        "status": "RESOLVED",
                        "severity": inc.severity,
                        "trigger_reason": inc.trigger_reason,
                        "peak_latency_ms": inc.peak_latency_ms,
                        "peak_jitter_ms": inc.peak_jitter_ms,
                        "peak_packet_loss_pct": inc.peak_loss_pct,
                        "peak_utilization_pct": inc.peak_util_pct,
                        "min_health_score": inc.min_health,
                        "min_stability_score": inc.min_stability,
                        "diagnosis_summary": diag_summary,
                        "is_simulation": inc.is_simulation
                    })

                logger.info(f"Resolved incident {inc.incident_id} after {duration_sec}s")
                resolved_state = self.active_incident
                self.active_incident = None
                self.consecutive_abnormal_samples = 0
                return resolved_state

        return self.active_incident

    def get_what_changed_analysis(self, incident: dict[str, Any], baseline_dict: dict[str, float]) -> list[dict[str, Any]]:
        """Generate 'What Changed?' comparative table between baseline and incident peak."""
        metrics_compared = [
            ("Latency", baseline_dict.get("latency_ms", 25.0), incident.get("peak_latency_ms", 25.0), "ms"),
            ("Jitter", baseline_dict.get("jitter_ms", 3.0), incident.get("peak_jitter_ms", 3.0), "ms"),
            ("Packet Loss", baseline_dict.get("packet_loss_pct", 0.0), incident.get("peak_packet_loss_pct", 0.0), "%"),
            ("Utilization", baseline_dict.get("utilization_pct", 15.0), incident.get("peak_utilization_pct", 15.0), "%"),
            ("Health Score", 95.0, incident.get("min_health_score", 95.0), "/100"),
            ("Stability Score", 90.0, incident.get("min_stability_score", 90.0), "/100")
        ]

        result: list[dict[str, Any]] = []
        for name, base_val, inc_val, unit in metrics_compared:
            b_val = float(base_val or 0.001)
            i_val = float(inc_val or 0.0)
            diff = i_val - b_val
            pct = round((diff / b_val) * 100.0, 1) if b_val > 0 else 0.0
            sign = "+" if diff > 0 else ""
            result.append({
                "metric": name,
                "baseline": f"{b_val:.1f} {unit}",
                "incident_peak": f"{i_val:.1f} {unit}",
                "change": f"{sign}{diff:.1f} {unit} ({sign}{pct}%)",
                "is_degraded": diff > 0 if name not in ("Health Score", "Stability Score") else diff < 0
            })

        return result
