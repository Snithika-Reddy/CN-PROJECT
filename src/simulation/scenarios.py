"""Controlled Network Simulation Scenarios.

Produces deterministic synthetic telemetry streams for demonstration, unit testing,
and viva presentations without affecting real baseline integrity:
1. Normal (Nominal baseline)
2. High Latency Spike
3. Packet Loss Burst
4. High Link Saturation / Bufferbloat
5. Throughput Degradation
6. Combined Catastrophic Degradation

All emitted records are strictly tagged with `is_simulation = True`.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import time
from typing import Any

from ..processing.metrics import ConsolidatedMetric, make_consolidated_metric


@dataclass
class SimulationScenarioDefinition:
    scenario_id: str
    name: str
    description: str
    duration_samples: int
    upload_mbps: float
    download_mbps: float
    latency_ms: float
    jitter_ms: float
    packet_loss_pct: float
    estimated_utilization_pct: float
    health_score: float
    stability_score: float


SCENARIOS: dict[str, SimulationScenarioDefinition] = {
    "normal": SimulationScenarioDefinition(
        scenario_id="normal",
        name="1. Normal Baseline Steady-State",
        description="Nominal home/campus Wi-Fi conditions with low latency and 0% packet loss.",
        duration_samples=20,
        upload_mbps=12.5,
        download_mbps=85.0,
        latency_ms=18.5,
        jitter_ms=2.1,
        packet_loss_pct=0.0,
        estimated_utilization_pct=11.2,
        health_score=96.0,
        stability_score=94.0
    ),
    "high_latency": SimulationScenarioDefinition(
        scenario_id="high_latency",
        name="2. Upstream High Latency Spike",
        description="Transit path route degradation causing elevated round-trip delay.",
        duration_samples=15,
        upload_mbps=8.0,
        download_mbps=45.0,
        latency_ms=185.0,
        jitter_ms=22.5,
        packet_loss_pct=0.5,
        estimated_utilization_pct=15.0,
        health_score=52.0,
        stability_score=58.0
    ),
    "packet_loss": SimulationScenarioDefinition(
        scenario_id="packet_loss",
        name="3. Wireless RF Interference / Packet Loss Burst",
        description="Physical frame drops and Wi-Fi noise causing 12.5% packet drop bursts.",
        duration_samples=15,
        upload_mbps=4.0,
        download_mbps=18.0,
        latency_ms=32.0,
        jitter_ms=14.0,
        packet_loss_pct=12.5,
        estimated_utilization_pct=8.5,
        health_score=38.0,
        stability_score=42.0
    ),
    "bufferbloat": SimulationScenarioDefinition(
        scenario_id="bufferbloat",
        name="4. Link Saturation & Bufferbloat Congestion",
        description="Heavy torrent/streaming upload saturating interface queues, causing latency ballooning.",
        duration_samples=20,
        upload_mbps=420.0,
        download_mbps=430.0,
        latency_ms=165.0,
        jitter_ms=38.0,
        packet_loss_pct=4.2,
        estimated_utilization_pct=98.1,
        health_score=32.0,
        stability_score=35.0
    ),
    "throughput_drop": SimulationScenarioDefinition(
        scenario_id="throughput_drop",
        name="5. Severe Throughput Throttling",
        description="Bandwidth cap or ISP throttling restricting transfer speeds to sub-megabit rates.",
        duration_samples=15,
        upload_mbps=0.15,
        download_mbps=0.45,
        latency_ms=45.0,
        jitter_ms=6.0,
        packet_loss_pct=1.0,
        estimated_utilization_pct=0.1,
        health_score=68.0,
        stability_score=72.0
    ),
    "combined_catastrophe": SimulationScenarioDefinition(
        scenario_id="combined_catastrophe",
        name="6. Combined Catastrophic Degradation",
        description="Full-scale link failure with extreme buffer saturation, 22% loss, and 310ms latency.",
        duration_samples=25,
        upload_mbps=380.0,
        download_mbps=450.0,
        latency_ms=310.0,
        jitter_ms=65.0,
        packet_loss_pct=22.0,
        estimated_utilization_pct=95.8,
        health_score=15.0,
        stability_score=18.0
    )
}


class ScenarioGenerator:
    """Generates synthetic telemetry frames for a selected scenario."""

    def __init__(self, interface_name: str = "Wi-Fi_Simulated", interface_speed_mbps: float = 866.0):
        self.interface_name = interface_name
        self.interface_speed_mbps = interface_speed_mbps

    def generate_sample(self, scenario_id: str, sample_index: int = 0) -> ConsolidatedMetric:
        """Produce a single tagged simulation sample."""
        scen = SCENARIOS.get(scenario_id, SCENARIOS["normal"])
        now = time.time()

        # Add realistic micro-fluctuation to make charts dynamic
        fluct = (hash(f"{scenario_id}_{sample_index}_{now}") % 10 - 5) * 0.05
        lat = max(1.0, scen.latency_ms + (fluct * 10.0))
        jit = max(0.5, scen.jitter_ms + (fluct * 2.0))
        loss = max(0.0, min(100.0, scen.packet_loss_pct + (fluct * 1.5)))
        up = max(0.05, scen.upload_mbps + fluct)
        down = max(0.1, scen.download_mbps + (fluct * 3.0))

        pps_sent = (up * 1_000_000.0) / (8.0 * 1500.0)
        pps_recv = (down * 1_000_000.0) / (8.0 * 1500.0)

        return make_consolidated_metric(
            interface_name=self.interface_name,
            upload_mbps=up,
            download_mbps=down,
            bytes_sent=int(up * 125000 * (sample_index + 1)),
            bytes_recv=int(down * 125000 * (sample_index + 1)),
            packets_sent=int(pps_sent * (sample_index + 1)),
            packets_recv=int(pps_recv * (sample_index + 1)),
            packets_sent_per_sec=pps_sent,
            packets_recv_per_sec=pps_recv,
            latency_ms=lat,
            jitter_ms=jit,
            packet_loss_pct=loss,
            interface_speed_mbps=self.interface_speed_mbps,
            health_score=scen.health_score,
            stability_score=scen.stability_score,
            monitoring_mode=f"SIMULATION_{scen.scenario_id.upper()}",
            is_simulation=True,
            is_replay=False,
            data_quality_flag="SIMULATION",
            override_timestamp=now
        )
