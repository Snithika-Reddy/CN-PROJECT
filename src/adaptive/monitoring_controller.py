"""Adaptive Monitoring Controller.

Dynamically shifts telemetry sampling rates to balance CPU conservation during steady-state
with high-resolution millisecond granularity during active degradation incidents:
- NORMAL: 2.0s
- WARNING: 1.0s
- CRITICAL: 0.5s
- RECOVERY: 1.5s
"""

from dataclasses import dataclass
import logging
from typing import Any

from ..storage.repositories import MonitoringStateRepository

logger = logging.getLogger(__name__)


@dataclass
class AdaptiveState:
    mode: str  # 'NORMAL', 'WARNING', 'CRITICAL', 'RECOVERY'
    current_interval_sec: float
    reason: str
    active_interface: str


class MonitoringController:
    """Controls adaptive sampling rates and persists state transitions."""

    def __init__(
        self,
        state_repo: MonitoringStateRepository | None = None,
        default_interval: float = 2.0,
        adaptive_enabled: bool = True,
        intervals: dict[str, float] | None = None
    ):
        self.state_repo = state_repo
        self.adaptive_enabled = adaptive_enabled
        self.intervals = intervals or {
            "normal": 2.0,
            "warning": 1.0,
            "critical": 0.5,
            "recovery": 1.5
        }
        self.current_mode = "NORMAL"
        self.current_interval = default_interval
        self.active_interface = "AUTO"
        self.reason = "Initial steady state"

    def update_evaluation(
        self,
        health_score: float,
        stability_score: float,
        has_open_incident: bool,
        incident_severity: str | None,
        active_interface: str,
        timestamp_iso: str
    ) -> AdaptiveState:
        """Evaluate network state and dynamically determine the target sampling rate."""
        self.active_interface = active_interface

        if not self.adaptive_enabled:
            self.current_mode = "NORMAL"
            self.current_interval = self.intervals.get("normal", 2.0)
            self.reason = "Adaptive monitoring disabled (fixed rate)"
            return AdaptiveState(self.current_mode, self.current_interval, self.reason, self.active_interface)

        # Mode transition logic
        if has_open_incident:
            if incident_severity == "CRITICAL" or health_score < 50.0:
                target_mode = "CRITICAL"
                self.reason = "Active CRITICAL incident detected; maximum resolution capture enabled."
            else:
                target_mode = "WARNING"
                self.reason = "Active WARNING incident detected; enhanced sampling enabled."
        elif health_score < 75.0 or stability_score < 65.0:
            target_mode = "WARNING"
            self.reason = "Elevated network jitter/loss or degraded health score."
        elif self.current_mode in ("WARNING", "CRITICAL"):
            target_mode = "RECOVERY"
            self.reason = "Incidents cleared; entering gradual cooldown recovery phase."
        else:
            target_mode = "NORMAL"
            self.reason = "Steady state telemetry within nominal operational boundaries."

        self.current_mode = target_mode
        self.current_interval = self.intervals.get(target_mode.lower(), 2.0)

        if self.state_repo:
            self.state_repo.update_state(
                active_interface=self.active_interface,
                monitoring_mode=self.current_mode,
                interval_sec=self.current_interval,
                last_timestamp_iso=timestamp_iso,
                reason=self.reason,
                is_running=True
            )

        return AdaptiveState(
            mode=self.current_mode,
            current_interval_sec=self.current_interval,
            reason=self.reason,
            active_interface=self.active_interface
        )
