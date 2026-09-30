"""Multi-Signal Diagnostic Correlation Rules.

Correlates combinations of telemetry signals:
- Gateway latency vs. Public Internet endpoints
- Throughput vs. Interface link capacity (utilization)
- Packet loss vs. Jitter and Round-Trip Delay
"""

from typing import Any
from .hypotheses import DiagnosisHypothesis


def evaluate_local_congestion(
    utilization_pct: float | None,
    latency_ms: float | None,
    baseline_lat: float | None,
    packet_loss_pct: float,
    jitter_ms: float | None
) -> DiagnosisHypothesis:
    """Hypothesis 1: Local link saturation / Interface buffer bloat."""
    evidence: list[str] = []
    counter: list[str] = []
    score = 0.0

    if utilization_pct is not None and utilization_pct >= 85.0:
        score += 0.45
        evidence.append(f"Interface link utilization is severely elevated ({utilization_pct}%).")
    elif utilization_pct is not None and utilization_pct >= 70.0:
        score += 0.25
        evidence.append(f"Interface link utilization is high ({utilization_pct}%).")
    else:
        counter.append(f"Interface utilization is low ({utilization_pct if utilization_pct is not None else 'N/A'}%).")

    if latency_ms and baseline_lat and latency_ms > (baseline_lat * 2.0):
        score += 0.30
        evidence.append(f"Latency ({latency_ms} ms) is {latency_ms/baseline_lat:.1f}x higher than baseline.")
    elif latency_ms and latency_ms > 80.0:
        score += 0.20
        evidence.append(f"Latency is elevated ({latency_ms} ms).")

    if packet_loss_pct > 1.0:
        score += 0.25
        evidence.append(f"Packet loss is active ({packet_loss_pct}%).")

    strength = "HIGH" if score >= 0.7 else ("MEDIUM" if score >= 0.4 else "LOW")
    action = "Throttle heavy background bandwidth consumers or inspect active network transfers."

    return DiagnosisHypothesis(
        cause="Local Interface Congestion / Bufferbloat",
        evidence_strength=strength,
        confidence_score=min(1.0, score),
        evidence_items=evidence,
        counter_evidence=counter,
        recommended_action=action
    )


def evaluate_local_lan_gateway_issue(
    gateway_lat_ms: float | None,
    gateway_loss_pct: float,
    public_lat_ms: float | None
) -> DiagnosisHypothesis:
    """Hypothesis 2: Local LAN / Wi-Fi / Default Gateway bottleneck."""
    evidence: list[str] = []
    counter: list[str] = []
    score = 0.0

    if gateway_lat_ms is not None and gateway_lat_ms > 25.0:
        score += 0.50
        evidence.append(f"Default gateway round-trip time is elevated ({gateway_lat_ms} ms).")
    elif gateway_lat_ms is not None:
        counter.append(f"Gateway latency is low and healthy ({gateway_lat_ms} ms).")

    if gateway_loss_pct > 2.0:
        score += 0.40
        evidence.append(f"Experiencing direct packet loss to the local gateway ({gateway_loss_pct}%).")

    if public_lat_ms and public_lat_ms > 70.0 and score > 0.3:
        score += 0.15
        evidence.append("Downstream internet latency is simultaneously elevated due to local gateway hop.")

    strength = "HIGH" if score >= 0.65 else ("MEDIUM" if score >= 0.35 else "LOW")
    action = "Check physical Ethernet cable, move closer to Wi-Fi access point, or restart local router."

    return DiagnosisHypothesis(
        cause="Local Network / Wi-Fi / Gateway Issue",
        evidence_strength=strength,
        confidence_score=min(1.0, score),
        evidence_items=evidence,
        counter_evidence=counter,
        recommended_action=action
    )


def evaluate_upstream_isp_issue(
    gateway_lat_ms: float | None,
    public_lat_ms: float | None,
    baseline_public_lat: float | None,
    public_loss_pct: float
) -> DiagnosisHypothesis:
    """Hypothesis 3: External ISP / Upstream transit degradation."""
    evidence: list[str] = []
    counter: list[str] = []
    score = 0.0

    gateway_ok = (gateway_lat_ms is not None and gateway_lat_ms < 15.0)
    has_public_degradation = False

    if public_lat_ms and (public_lat_ms > 90.0 or (baseline_public_lat and public_lat_ms > baseline_public_lat * 2.5)):
        score += 0.45
        has_public_degradation = True
        evidence.append(f"Internet endpoint latency is significantly elevated ({public_lat_ms} ms).")

    if public_loss_pct > 2.0:
        score += 0.30
        has_public_degradation = True
        evidence.append(f"Packet loss observed on Internet targets ({public_loss_pct}%).")

    if has_public_degradation and gateway_ok:
        score += 0.35
        evidence.append(f"Local gateway hop is fast and healthy ({gateway_lat_ms} ms), indicating bottleneck is upstream.")
    elif not has_public_degradation:
        counter.append("Internet endpoint latency and loss operate within nominal limits.")

    strength = "HIGH" if score >= 0.70 else ("MEDIUM" if score >= 0.40 else "LOW")
    action = "Verify ISP service health status or contact internet service provider if problem persists."

    return DiagnosisHypothesis(
        cause="Upstream ISP / WAN Peering Degradation",
        evidence_strength=strength,
        confidence_score=min(1.0, score),
        evidence_items=evidence,
        counter_evidence=counter,
        recommended_action=action
    )


def evaluate_link_layer_loss(
    packet_loss_pct: float,
    latency_ms: float | None,
    utilization_pct: float | None
) -> DiagnosisHypothesis:
    """Hypothesis 4: Physical layer packet drops / RF interference."""
    evidence: list[str] = []
    counter: list[str] = []
    score = 0.0

    if packet_loss_pct >= 3.0:
        score += 0.50
        evidence.append(f"Significant packet drops detected ({packet_loss_pct}% loss).")
        if utilization_pct is not None and utilization_pct < 50.0:
            score += 0.30
            evidence.append(f"Packet drops occur despite low link utilization ({utilization_pct}%).")
        if latency_ms and latency_ms < 45.0:
            score += 0.20
            evidence.append(f"Latency remains relatively low ({latency_ms} ms), indicating non-queue drops.")
    else:
        counter.append(f"Packet loss is minimal ({packet_loss_pct}%).")

    strength = "HIGH" if score >= 0.65 else ("MEDIUM" if score >= 0.35 else "LOW")
    action = "Inspect wireless channel congestion, 2.4/5GHz interference, or test physical cable."

    return DiagnosisHypothesis(
        cause="Physical Link / Wireless RF Interference",
        evidence_strength=strength,
        confidence_score=min(1.0, score),
        evidence_items=evidence,
        counter_evidence=counter,
        recommended_action=action
    )
