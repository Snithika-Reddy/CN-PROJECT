"""Change-Point Detection Engine (CUSUM & Two-Window Mean Shift).

Detects sudden structural shifts in time series telemetry, distinguishing
transient spikes from persistent regime changes.
"""

from collections import deque
from dataclasses import dataclass
import numpy as np


@dataclass
class ChangePointResult:
    detected: bool
    shift_magnitude: float
    direction: str  # 'INCREASE' or 'DECREASE'
    description: str


class ChangePointDetector:
    """Sliding-window Two-Sample T-test / Welch's Mean Shift detector for telemetry."""

    def __init__(self, window_size: int = 15, sensitivity_sigma: float = 2.5):
        self.window_size = window_size
        self.sensitivity_sigma = sensitivity_sigma
        self.history: deque[float] = deque(maxlen=window_size * 2)

    def add_sample(self, value: float | None) -> ChangePointResult:
        """Add sample and evaluate whether a structural change-point has occurred."""
        if value is None:
            return ChangePointResult(False, 0.0, "NONE", "No measurement.")

        self.history.append(value)
        if len(self.history) < self.window_size * 2:
            return ChangePointResult(False, 0.0, "NONE", "Collecting baseline window samples.")

        # Split into historical window (W1) and recent window (W2)
        full_list = list(self.history)
        w1 = np.array(full_list[:self.window_size])
        w2 = np.array(full_list[self.window_size:])

        mean1 = float(np.mean(w1))
        mean2 = float(np.mean(w2))
        std1 = float(np.std(w1))
        std2 = float(np.std(w2))

        pooled_std = np.sqrt((std1**2 + std2**2) / 2.0)
        if pooled_std < 0.001:
            pooled_std = 0.001

        diff = mean2 - mean1
        z_shift = abs(diff) / pooled_std

        if z_shift >= self.sensitivity_sigma:
            direction = "INCREASE" if diff > 0 else "DECREASE"
            desc = (
                f"Structural change detected: mean shifted from {mean1:.1f} to {mean2:.1f} "
                f"({direction} of {abs(diff):.1f}, Z-Shift: {z_shift:.2f})."
            )
            return ChangePointResult(
                detected=True,
                shift_magnitude=round(abs(diff), 2),
                direction=direction,
                description=desc
            )

        return ChangePointResult(False, round(abs(diff), 2), "NONE", "Series in steady-state.")
