"""Diagnostic Hypotheses Data Models.

Defines competing diagnosis structures with evidence strength indicators
adhering strictly to prompt requirement: never claim certainty, present
calibrated hypotheses with transparent evidence citations.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DiagnosisHypothesis:
    cause: str
    evidence_strength: str  # 'HIGH', 'MEDIUM', 'LOW'
    confidence_score: float  # 0.0 - 1.0
    evidence_items: list[str] = field(default_factory=list)
    counter_evidence: list[str] = field(default_factory=list)
    recommended_action: str = ""


@dataclass
class DiagnosticReport:
    timestamp_iso: str
    incident_id: str | None
    primary_hypothesis: DiagnosisHypothesis
    competing_hypotheses: list[DiagnosisHypothesis]
    network_state_summary: str
    overall_confidence: float
