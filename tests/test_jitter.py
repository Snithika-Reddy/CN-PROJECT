"""Unit tests for RFC 3550 Inter-Packet Delay Variation (IPDV) and statistical Jitter."""

import pytest
from src.processing.jitter import JitterCalculator


def test_jitter_calculator_initialization():
    calc = JitterCalculator(window_size=10)
    assert calc.get_current_jitter() is None


def test_rfc3550_jitter_calculation():
    calc = JitterCalculator(window_size=20)
    # First sample - cannot compute jitter yet
    assert calc.add_sample(20.0) is None

    # Second sample (diff = 4ms)
    # J = 0 + (4 - 0)/16 = 0.25
    j2 = calc.add_sample(24.0)
    assert j2 == 0.25

    # Third sample (diff = |24 - 18| = 6ms)
    # J = 0.25 + (6 - 0.25)/16 = 0.609 -> 0.61
    j3 = calc.add_sample(18.0)
    assert j3 == 0.61


def test_jitter_window_statistics():
    calc = JitterCalculator(window_size=10)
    for lat in [10.0, 15.0, 12.0, 18.0, 14.0]:
        calc.add_sample(lat)

    stats = calc.compute_window_statistics()
    assert stats["jitter_mean"] is not None
    assert stats["jitter_median"] is not None
    assert stats["jitter_std"] is not None
    assert stats["jitter_p95"] is not None
