"""Unit tests for telemetry metric transformations, throughput, and utilization."""

import pytest
from src.processing.rates import bytes_to_mbps, packets_to_pps, format_bandwidth
from src.processing.metrics import compute_estimated_utilization, make_consolidated_metric


def test_bytes_to_mbps():
    # 1,000,000 bytes over 1 second = 8,000,000 bits = 8.0 Mbps
    mbps = bytes_to_mbps(1_000_000, 1.0)
    assert mbps == 8.0

    # 0 delta
    assert bytes_to_mbps(0, 1.0) == 0.0

    # 0 or negative time delta
    assert bytes_to_mbps(1000, 0.0) == 0.0
    assert bytes_to_mbps(1000, -1.0) == 0.0


def test_packets_to_pps():
    assert packets_to_pps(500, 2.0) == 250.0
    assert packets_to_pps(0, 1.0) == 0.0
    assert packets_to_pps(100, 0.0) == 0.0


def test_format_bandwidth():
    assert format_bandwidth(0.5) == "500.0 Kbps"
    assert format_bandwidth(45.678) == "45.68 Mbps"
    assert format_bandwidth(1250.0) == "1.25 Gbps"


def test_compute_estimated_utilization():
    # 100 Mbps link with 10 Mbps down + 10 Mbps up = 20%
    util = compute_estimated_utilization(upload_mbps=10.0, download_mbps=10.0, interface_speed_mbps=100.0)
    assert util == 20.0

    # Unknown or 0 interface speed must return None (NULL) to prevent fabrication
    assert compute_estimated_utilization(10.0, 10.0, None) is None
    assert compute_estimated_utilization(10.0, 10.0, 0.0) is None
    assert compute_estimated_utilization(10.0, 10.0, -100.0) is None

    # Cap at 100%
    assert compute_estimated_utilization(600.0, 600.0, 1000.0) == 100.0


def test_make_consolidated_metric():
    m = make_consolidated_metric(
        interface_name="Wi-Fi",
        upload_mbps=5.0,
        download_mbps=25.0,
        bytes_sent=10000,
        bytes_recv=50000,
        packets_sent=50,
        packets_recv=200,
        packets_sent_per_sec=25.0,
        packets_recv_per_sec=100.0,
        latency_ms=18.4,
        jitter_ms=1.5,
        packet_loss_pct=0.0,
        interface_speed_mbps=1000.0,
        health_score=95.0,
        stability_score=92.0
    )
    assert m.interface_name == "Wi-Fi"
    assert m.estimated_utilization_pct == 3.0
    assert m.health_score == 95.0
    assert m.is_simulation is False
