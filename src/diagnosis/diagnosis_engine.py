"""Multi-Signal Network Diagnosis Engine.

Produces calibrated, ranked competing hypotheses with transparent evidence citations.
Strictly avoids declaring unverified root causes, using calibrated probability bounds.
"""

from datetime import datetime, timezone
import logging
from typing import Any

from .hypotheses import DiagnosisHypothesis, DiagnosticReport
from .rules import (
    evaluate_local_congestion,
    evaluate_local_lan_gateway_issue,
    evaluate_upstream_isp_issue,
    evaluate_link_layer_loss
)

logger = logging.getLogger(__name__)


class DiagnosisEngine:
    """Evaluates multi-signal telemetry and ranks plausible competing causes."""

    def diagnose(
        self,
        timestamp_iso: str | None = None,
        incident_id: str | None = None,
        latency_ms: float | None = None,
        baseline_latency_ms: float | None = None,
        jitter_ms: float | None = None,
        packet_loss_pct: float = 0.0,
        utilization_pct: float | None = None,
        gateway_latency_ms: float | None = None,
        gateway_loss_pct: float = 0.0
    ) -> DiagnosticReport:
        """Run full correlation across all diagnostic hypotheses."""
        now_iso = timestamp_iso or datetime.now(timezone.utc).isoformat()

        # Run hypotheses
        h_congestion = evaluate_local_congestion(
            utilization_pct, latency_ms, baseline_latency_ms, packet_loss_pct, jitter_ms
        )
        h_gateway = evaluate_local_lan_gateway_issue(
            gateway_latency_ms, gateway_loss_pct, latency_ms
        )
        h_upstream = evaluate_upstream_isp_issue(
            gateway_latency_ms, latency_ms, baseline_latency_ms, packet_loss_pct
        )
        h_physical = evaluate_link_layer_loss(
            packet_loss_pct, latency_ms, utilization_pct
        )

        all_hypotheses = [h_congestion, h_gateway, h_upstream, h_physical]
        # Sort descending by confidence score
        all_hypotheses.sort(key=lambda h: h.confidence_score, reverse=True)

        primary = all_hypotheses[0]
        competing = all_hypotheses[1:]

        # If highest score is low, network is operating nominally
        if primary.confidence_score < 0.30:
            nominal_hypothesis = DiagnosisHypothesis(
                cause="Nominal Performance (No Significant Issue)",
                evidence_strength="HIGH",
                confidence_score=0.95,
                evidence_items=[
                    f"Latency ({latency_ms if latency_ms is not None else 'N/A'} ms) and loss ({packet_loss_pct}%) within normal tolerances.",
                    "No sustained interface saturation or upstream path degradation detected."
                ],
                counter_evidence=[],
                recommended_action="Continue regular monitoring; no intervention required."
            )
            return DiagnosticReport(
                timestamp_iso=now_iso,
                incident_id=incident_id,
                primary_hypothesis=nominal_hypothesis,
                competing_hypotheses=all_hypotheses,
                network_state_summary="Network performance is stable with no acute abnormalities detected.",
                overall_confidence=0.95
            )

        summary = (
            f"Possible primary cause: {primary.cause} (Evidence: {primary.evidence_strength}). "
            f"Evaluated {len(competing)} competing hypotheses."
        )

        return DiagnosticReport(
            timestamp_iso=now_iso,
            incident_id=incident_id,
            primary_hypothesis=primary,
            competing_hypotheses=competing,
            network_state_summary=summary,
            overall_confidence=primary.confidence_score
        )
