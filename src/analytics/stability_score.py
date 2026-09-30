"""Network Stability Score Engine (0-100).

Answers: 'How consistently does the network behave over time?'
Evaluates variance in round-trip latency, jitter fluctuation, packet-loss bursts,
and throughput volatility across a rolling sample window.
"""

from collections import deque
from dataclasses import dataclass
import numpy as np


@dataclass
class StabilityEvaluation:
    stability_score: float
    grade: str  # 'ROCK_SOLID', 'STABLE', 'MODERATE_FLUCTUATION', 'UNSTABLE'
    latency_variance_score: float
    jitter_variance_score: float
    loss_burst_score: float
    throughput_volatility_score: float
    summary: str


class StabilityScoreCalculator:
    """Computes operational consistency over a rolling time window."""

    def __init__(self, window_samples: int = 20):
        self.window_samples = window_samples
        self.latency_window: deque[float] = deque(maxlen=window_samples)
        self.jitter_window: deque[float] = deque(maxlen=window_samples)
        self.loss_window: deque[float] = deque(maxlen=window_samples)
        self.throughput_window: deque[float] = deque(maxlen=window_samples)

    def add_sample(
        self,
        latency_ms: float | None,
        jitter_ms: float | None,
        loss_pct: float,
        throughput_mbps: float
    ) -> None:
        """Add latest sample to rolling stability windows."""
        if latency_ms is not None:
            self.latency_window.append(latency_ms)
        if jitter_ms is not None:
            self.jitter_window.append(jitter_ms)
        self.loss_window.append(loss_pct)
        self.throughput_window.append(max(0.0, throughput_mbps))

    def evaluate(self) -> StabilityEvaluation:
        """Compute stability score from rolling distributions."""
        if len(self.latency_window) < 3:
            return StabilityEvaluation(
                stability_score=100.0,
                grade="INITIALIZING",
                latency_variance_score=100.0,
                jitter_variance_score=100.0,
                loss_burst_score=100.0,
                throughput_volatility_score=100.0,
                summary="Insufficient window history to compute variance (<3 samples)."
            )

        # 1. Latency std dev: std <= 5ms = 100, std >= 50ms = 0
        lat_std = float(np.std(list(self.latency_window)))
        lat_score = max(0.0, min(100.0, 100.0 - (lat_std / 50.0) * 100.0))

        # 2. Jitter variance: std <= 3ms = 100, std >= 25ms = 0
        jit_std = float(np.std(list(self.jitter_window))) if self.jitter_window else 0.0
        jit_score = max(0.0, min(100.0, 100.0 - (jit_std / 25.0) * 100.0))

        # 3. Loss burst: any sample with loss > 0% penalizes stability
        loss_arr = np.array(list(self.loss_window))
        max_loss = float(np.max(loss_arr))
        loss_score = max(0.0, 100.0 - (max_loss * 10.0))  # 10% loss gives 0 score

        # 4. Throughput coefficient of variation (std / mean)
        tput_arr = np.array(list(self.throughput_window))
        mean_tput = float(np.mean(tput_arr))
        std_tput = float(np.std(tput_arr))
        if mean_tput > 1.0:
            cv = std_tput / mean_tput
            tput_score = max(0.0, min(100.0, 100.0 - (cv / 2.0) * 100.0))
        else:
            tput_score = 100.0

        # Weighted combination
        weights = {"lat": 0.30, "jit": 0.25, "loss": 0.25, "tput": 0.20}
        total_score = round(
            lat_score * weights["lat"] +
            jit_score * weights["jit"] +
            loss_score * weights["loss"] +
            tput_score * weights["tput"],
            1
        )

        if total_score >= 85.0:
            grade = "ROCK_SOLID"
        elif total_score >= 70.0:
            grade = "STABLE"
        elif total_score >= 50.0:
            grade = "MODERATE_FLUCTUATION"
        else:
            grade = "UNSTABLE"

        summary = f"Stability is {grade} ({total_score}/100). Latency Std Dev: {lat_std:.1f}ms, Loss Burst Peak: {max_loss:.1f}%."

        return StabilityEvaluation(
            stability_score=total_score,
            grade=grade,
            latency_variance_score=round(lat_score, 1),
            jitter_variance_score=round(jit_score, 1),
            loss_burst_score=round(loss_score, 1),
            throughput_volatility_score=round(tput_score, 1),
            summary=summary
        )
