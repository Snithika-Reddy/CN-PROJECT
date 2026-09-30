"""Telemetry Data Quality & Validation Engine.

Performs sanity checks, boundary validation, missing-field detection,
and counter reset flagging to guarantee data integrity across the pipeline.
"""

from dataclasses import dataclass
import math
from typing import Any


@dataclass
class ValidationResult:
    is_valid: bool
    quality_flag: str  # 'VALID', 'SUSPECT', 'COUNTER_RESET', 'STALE', 'CORRUPT'
    anomalies: list[str]
    sanitized_data: dict[str, Any]


class DataValidator:
    """Validates raw and processed network telemetry metrics against physical and logical bounds."""

    def __init__(
        self,
        max_reasonable_latency_ms: float = 10000.0,
        max_reasonable_throughput_mbps: float = 100000.0,  # 100 Gbps
        max_reasonable_pps: float = 5000000.0  # 5M pps
    ):
        self.max_latency = max_reasonable_latency_ms
        self.max_throughput = max_reasonable_throughput_mbps
        self.max_pps = max_reasonable_pps

    def validate_metric_sample(
        self,
        upload_mbps: float,
        download_mbps: float,
        latency_ms: float | None,
        jitter_ms: float | None,
        packet_loss_pct: float,
        packets_sent_per_sec: float,
        packets_recv_per_sec: float,
        counter_reset: bool = False
    ) -> ValidationResult:
        """Validate sample fields, apply boundary clamping if needed, and assess data quality."""
        anomalies: list[str] = []
        flag = "VALID"

        if counter_reset:
            flag = "COUNTER_RESET"
            anomalies.append("Interface counter rollover or system reset detected")

        # Check Throughput
        clean_upload = upload_mbps
        clean_download = download_mbps
        if math.isnan(upload_mbps) or upload_mbps < 0:
            anomalies.append("Negative or NaN upload throughput")
            clean_upload = 0.0
            flag = "SUSPECT"
        elif upload_mbps > self.max_throughput:
            anomalies.append(f"Upload throughput exceeds physical bound: {upload_mbps} Mbps")
            clean_upload = self.max_throughput
            flag = "SUSPECT"

        if math.isnan(download_mbps) or download_mbps < 0:
            anomalies.append("Negative or NaN download throughput")
            clean_download = 0.0
            flag = "SUSPECT"
        elif download_mbps > self.max_throughput:
            anomalies.append(f"Download throughput exceeds physical bound: {download_mbps} Mbps")
            clean_download = self.max_throughput
            flag = "SUSPECT"

        # Check Latency
        clean_latency = latency_ms
        if latency_ms is not None:
            if math.isnan(latency_ms) or latency_ms < 0:
                anomalies.append("Negative or NaN latency")
                clean_latency = None
                flag = "SUSPECT"
            elif latency_ms > self.max_latency:
                anomalies.append(f"Latency exceeds upper threshold: {latency_ms} ms")
                clean_latency = self.max_latency
                flag = "SUSPECT"

        # Check Jitter
        clean_jitter = jitter_ms
        if jitter_ms is not None:
            if math.isnan(jitter_ms) or jitter_ms < 0:
                anomalies.append("Negative or NaN jitter")
                clean_jitter = 0.0
                flag = "SUSPECT"

        # Check Packet Loss %
        clean_loss = packet_loss_pct
        if math.isnan(packet_loss_pct) or packet_loss_pct < 0.0:
            anomalies.append("Negative or NaN packet loss")
            clean_loss = 0.0
            flag = "SUSPECT"
        elif packet_loss_pct > 100.0:
            anomalies.append("Packet loss exceeds 100%")
            clean_loss = 100.0
            flag = "SUSPECT"

        # Check Packet Rates
        clean_pps_sent = max(0.0, packets_sent_per_sec) if not math.isnan(packets_sent_per_sec) else 0.0
        clean_pps_recv = max(0.0, packets_recv_per_sec) if not math.isnan(packets_recv_per_sec) else 0.0

        is_valid = (flag in ("VALID", "COUNTER_RESET"))

        return ValidationResult(
            is_valid=is_valid,
            quality_flag=flag,
            anomalies=anomalies,
            sanitized_data={
                "upload_mbps": clean_upload,
                "download_mbps": clean_download,
                "latency_ms": clean_latency,
                "jitter_ms": clean_jitter,
                "packet_loss_pct": clean_loss,
                "packets_sent_per_sec": clean_pps_sent,
                "packets_recv_per_sec": clean_pps_recv
            }
        )
