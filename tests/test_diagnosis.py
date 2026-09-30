"""Unit tests for multi-signal diagnosis engine and competing hypotheses."""

import pytest
from src.diagnosis.diagnosis_engine import DiagnosisEngine


def test_nominal_network_diagnosis():
    engine = DiagnosisEngine()
    report = engine.diagnose(
        latency_ms=18.0,
        baseline_latency_ms=20.0,
        jitter_ms=1.5,
        packet_loss_pct=0.0,
        utilization_pct=15.0,
        gateway_latency_ms=2.0
    )
    assert "Nominal" in report.primary_hypothesis.cause
    assert report.primary_hypothesis.evidence_strength == "HIGH"


def test_local_congestion_diagnosis():
    engine = DiagnosisEngine()
    # High utilization (95%) + High latency (160ms vs 20ms baseline) + Loss (4%)
    report = engine.diagnose(
        latency_ms=160.0,
        baseline_latency_ms=20.0,
        jitter_ms=25.0,
        packet_loss_pct=4.0,
        utilization_pct=95.0,
        gateway_latency_ms=5.0
    )
    assert "Congestion" in report.primary_hypothesis.cause
    assert report.primary_hypothesis.evidence_strength in ("HIGH", "MEDIUM")


def test_upstream_isp_diagnosis():
    engine = DiagnosisEngine()
    # Gateway latency fast (3ms), Internet latency degraded (180ms), Packet loss 6%
    report = engine.diagnose(
        latency_ms=180.0,
        baseline_latency_ms=25.0,
        jitter_ms=20.0,
        packet_loss_pct=6.0,
        utilization_pct=10.0,
        gateway_latency_ms=3.0
    )
    assert "Upstream" in report.primary_hypothesis.cause
