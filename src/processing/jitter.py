"""RFC 3550 Inter-Packet Delay Variation (IPDV) and statistical Jitter calculations."""

from collections import deque
import numpy as np


class JitterCalculator:
    """Calculates network delay variance and rolling jitter over time windows.

    RFC 3550 Standard definition:
    J(i) = J(i-1) + (|D(i-1, i)| - J(i-1)) / 16
    Where D(i-1, i) is the difference in relative transit time between packets.
    For ICMP RTT samples:
    Instantaneous Jitter = |RTT_i - RTT_{i-1}|
    Mean Jitter = (1 / (N - 1)) * Sum_{k=2}^N |RTT_k - RTT_{k-1}|
    """

    def __init__(self, window_size: int = 20):
        self.window_size = window_size
        self.history: deque[float] = deque(maxlen=window_size)
        self.rfc_jitter: float = 0.0

    def add_sample(self, rtt_ms: float | None) -> float | None:
        """Record an RTT sample and update the exponential rolling RFC 3550 jitter."""
        if rtt_ms is None or rtt_ms < 0:
            return self.get_current_jitter()

        if not self.history:
            self.history.append(rtt_ms)
            return None

        prev_rtt = self.history[-1]
        diff = abs(rtt_ms - prev_rtt)
        # RFC 3550 filter: J = J + (|D| - J)/16
        self.rfc_jitter = self.rfc_jitter + (diff - self.rfc_jitter) / 16.0
        self.history.append(rtt_ms)
        return round(self.rfc_jitter, 2)

    def get_current_jitter(self) -> float | None:
        """Return the current smoothed RFC 3550 jitter value."""
        if len(self.history) < 2:
            return None
        return round(self.rfc_jitter, 2)

    def compute_window_statistics(self) -> dict[str, float | None]:
        """Compute comprehensive statistical metrics over the current sample window."""
        if len(self.history) < 2:
            return {
                "jitter_mean": None,
                "jitter_median": None,
                "jitter_std": None,
                "jitter_p95": None
            }

        arr = np.array(list(self.history))
        diffs = np.abs(np.diff(arr))

        return {
            "jitter_mean": round(float(np.mean(diffs)), 2),
            "jitter_median": round(float(np.median(diffs)), 2),
            "jitter_std": round(float(np.std(diffs)), 2),
            "jitter_p95": round(float(np.percentile(diffs, 95)), 2)
        }
