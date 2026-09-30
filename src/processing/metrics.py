"""Metric processing and Estimated Interface Utilization calculations."""

from dataclasses import dataclass
from datetime import datetime, timezone
import time


@dataclass
class ConsolidatedMetric:
    timestamp_iso: str
    date_str: str
    time_str: str
    epoch_time: float
    interface_name: str
    upload_mbps: float
    download_mbps: float
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int
    packets_sent_per_sec: float
    packets_recv_per_sec: float
    latency_ms: float | None
    jitter_ms: float | None
    packet_loss_pct: float
    estimated_utilization_pct: float | None
    health_score: float
    stability_score: float
    monitoring_mode: str
    is_simulation: bool
    is_replay: bool
    data_quality_flag: str


def compute_estimated_utilization(
    upload_mbps: float,
    download_mbps: float,
    interface_speed_mbps: float | None
) -> float | None:
    """Calculate Estimated Interface Utilization percentage.

    Note: This measures the link bandwidth utilization against the hardware link speed
    (e.g., 1000 Mbps Gigabit Ethernet or negotiated Wi-Fi rate), NOT the external ISP plan.
    If hardware speed is unknown or zero, returns None (NULL) to prevent misleading fabrication.
    """
    if interface_speed_mbps is None or interface_speed_mbps <= 0:
        return None

    total_traffic_mbps = max(0.0, upload_mbps) + max(0.0, download_mbps)
    utilization = (total_traffic_mbps / interface_speed_mbps) * 100.0
    return round(min(100.0, max(0.0, utilization)), 2)


def make_consolidated_metric(
    interface_name: str,
    upload_mbps: float,
    download_mbps: float,
    bytes_sent: int,
    bytes_recv: int,
    packets_sent: int,
    packets_recv: int,
    packets_sent_per_sec: float,
    packets_recv_per_sec: float,
    latency_ms: float | None,
    jitter_ms: float | None,
    packet_loss_pct: float,
    interface_speed_mbps: float | None,
    health_score: float,
    stability_score: float,
    monitoring_mode: str = "NORMAL",
    is_simulation: bool = False,
    is_replay: bool = False,
    data_quality_flag: str = "VALID",
    override_timestamp: float | None = None
) -> ConsolidatedMetric:
    """Consolidate disparate collector readings into an authoritative telemetry record."""
    now_epoch = override_timestamp if override_timestamp is not None else time.time()
    dt = datetime.fromtimestamp(now_epoch, tz=timezone.utc)

    utilization = compute_estimated_utilization(upload_mbps, download_mbps, interface_speed_mbps)

    return ConsolidatedMetric(
        timestamp_iso=dt.isoformat(),
        date_str=dt.strftime("%Y-%m-%d"),
        time_str=dt.strftime("%H:%M:%S"),
        epoch_time=now_epoch,
        interface_name=interface_name,
        upload_mbps=round(upload_mbps, 4),
        download_mbps=round(download_mbps, 4),
        bytes_sent=bytes_sent,
        bytes_recv=bytes_recv,
        packets_sent=packets_sent,
        packets_recv=packets_recv,
        packets_sent_per_sec=round(packets_sent_per_sec, 2),
        packets_recv_per_sec=round(packets_recv_per_sec, 2),
        latency_ms=round(latency_ms, 2) if latency_ms is not None else None,
        jitter_ms=round(jitter_ms, 2) if jitter_ms is not None else None,
        packet_loss_pct=round(packet_loss_pct, 2),
        estimated_utilization_pct=utilization,
        health_score=round(health_score, 1),
        stability_score=round(stability_score, 1),
        monitoring_mode=monitoring_mode,
        is_simulation=is_simulation,
        is_replay=is_replay,
        data_quality_flag=data_quality_flag
    )
