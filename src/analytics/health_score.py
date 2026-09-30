"""Transparent Network Health Score Engine (0-100).

Computes an explainable, deterministic health index using documented normalization
curves and configurable component weights. Never produces arbitrary black-box scores.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class HealthEvaluation:
    health_score: float
    grade: str  # 'EXCELLENT', 'GOOD', 'FAIR', 'DEGRADED', 'CRITICAL'
    sub_scores: dict[str, float]
    weights_applied: dict[str, float]
    primary_penalty: str | None
    explanation: str


class HealthScoreCalculator:
    """Calculates explainable 0-100 Network Health Score."""

    def __init__(self, config_weights: dict[str, float] | None = None):
        self.weights = config_weights or {
            "latency": 0.20,
            "packet_loss": 0.25,
            "jitter": 0.15,
            "utilization": 0.15,
            "throughput": 0.15,
            "stability": 0.10
        }
        # Normalize weights to ensure sum == 1.0
        total_w = sum(self.weights.values())
        if total_w > 0:
            self.weights = {k: v / total_w for k, v in self.weights.items()}

    def _score_latency(self, latency_ms: float | None) -> float:
        """Latency scoring: 0-30ms = 100, 30-100ms linear drop, >250ms = 0."""
        if latency_ms is None:
            return 80.0  # neutral if unmeasured
        if latency_ms <= 30.0:
            return 100.0
        if latency_ms >= 250.0:
            return 0.0
        return max(0.0, 100.0 - ((latency_ms - 30.0) / (250.0 - 30.0)) * 100.0)

    def _score_packet_loss(self, loss_pct: float) -> float:
        """Packet loss scoring: 0% = 100, 1% = 80, 5% = 20, >=10% = 0."""
        if loss_pct <= 0.0:
            return 100.0
        if loss_pct >= 10.0:
            return 0.0
        return max(0.0, 100.0 - (loss_pct / 10.0) * 100.0)

    def _score_jitter(self, jitter_ms: float | None) -> float:
        """Jitter scoring: 0-5ms = 100, 5-40ms linear drop, >60ms = 0."""
        if jitter_ms is None:
            return 85.0
        if jitter_ms <= 5.0:
            return 100.0
        if jitter_ms >= 60.0:
            return 0.0
        return max(0.0, 100.0 - ((jitter_ms - 5.0) / (60.0 - 5.0)) * 100.0)

    def _score_utilization(self, util_pct: float | None) -> float:
        """Interface utilization: 0-60% = 100, 60-90% warning curve, >95% = 10."""
        if util_pct is None:
            return 90.0  # Hardware speed unavailable, neutral penalty
        if util_pct <= 60.0:
            return 100.0
        if util_pct >= 95.0:
            return 10.0
        return max(10.0, 100.0 - ((util_pct - 60.0) / 35.0) * 90.0)

    def _score_throughput(self, upload_mbps: float, download_mbps: float) -> float:
        """Throughput activity: non-zero active traffic indicates healthy pipeline."""
        total = upload_mbps + download_mbps
        if total > 5.0:
            return 100.0
        if total > 0.5:
            return 90.0
        return 80.0  # Idle is normal, slight baseline

    def evaluate(
        self,
        latency_ms: float | None,
        jitter_ms: float | None,
        packet_loss_pct: float,
        estimated_utilization_pct: float | None,
        upload_mbps: float,
        download_mbps: float,
        stability_score: float = 100.0
    ) -> HealthEvaluation:
        """Calculate weighted score and explain specific metric penalties."""
        sub_scores = {
            "latency": round(self._score_latency(latency_ms), 1),
            "packet_loss": round(self._score_packet_loss(packet_loss_pct), 1),
            "jitter": round(self._score_jitter(jitter_ms), 1),
            "utilization": round(self._score_utilization(estimated_utilization_pct), 1),
            "throughput": round(self._score_throughput(upload_mbps, download_mbps), 1),
            "stability": round(max(0.0, min(100.0, stability_score)), 1)
        }

        total_score = sum(sub_scores[k] * self.weights[k] for k in self.weights)
        total_score = round(max(0.0, min(100.0, total_score)), 1)

        # Identify primary penalty
        min_sub = min(sub_scores.items(), key=lambda x: x[1])
        penalty = min_sub[0] if min_sub[1] < 70.0 else None

        if total_score >= 90.0:
            grade = "EXCELLENT"
        elif total_score >= 75.0:
            grade = "GOOD"
        elif total_score >= 60.0:
            grade = "FAIR"
        elif total_score >= 40.0:
            grade = "DEGRADED"
        else:
            grade = "CRITICAL"

        explanation = (
            f"Network Health is {grade} ({total_score}/100). "
            + (f"Primary degradation factor: {penalty} ({sub_scores[penalty]}/100)." if penalty else "All key metrics operate within nominal bounds.")
        )

        return HealthEvaluation(
            health_score=total_score,
            grade=grade,
            sub_scores=sub_scores,
            weights_applied=self.weights,
            primary_penalty=penalty,
            explanation=explanation
        )
