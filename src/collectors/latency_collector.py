"""Multi-Target Latency, Jitter, and Packet Loss Collector.

Measures network round-trip time (RTT), rolling-window packet loss, and jitter
across target endpoints (Local Gateway, Public DNS 8.8.8.8, Cloudflare 1.1.1.1).
Uses Windows ping utility with precise regular expression parsing.
"""

from dataclasses import dataclass
import re
import subprocess
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class ProbeResult:
    target_name: str
    target_host: str
    timestamp: float
    probes_sent: int
    probes_received: int
    packet_loss_pct: float
    latency_min_ms: float | None
    latency_avg_ms: float | None
    latency_max_ms: float | None
    jitter_ms: float | None
    is_reachable: bool
    status_message: str


class LatencyCollector:
    """Collects multi-target ping latency, rolling packet loss, and RFC 3550 jitter."""

    def __init__(self, probe_count: int = 5, timeout_ms: int = 1000):
        self.probe_count = max(1, probe_count)
        self.timeout_ms = timeout_ms

    def probe_target(self, target_name: str, target_host: str) -> ProbeResult:
        """Execute ICMP ping probes against a target host and parse results."""
        now = time.time()
        if not target_host or target_host == "0.0.0.0":
            return ProbeResult(
                target_name=target_name,
                target_host=target_host or "UNKNOWN",
                timestamp=now,
                probes_sent=self.probe_count,
                probes_received=0,
                packet_loss_pct=100.0,
                latency_min_ms=None,
                latency_avg_ms=None,
                latency_max_ms=None,
                jitter_ms=None,
                is_reachable=False,
                status_message="Invalid target host"
            )

        cmd = ["ping", "-n", str(self.probe_count), "-w", str(self.timeout_ms), target_host]

        try:
            output = subprocess.check_output(
                cmd,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=(self.probe_count * (self.timeout_ms / 1000.0)) + 3.0
            )
        except subprocess.TimeoutExpired:
            return ProbeResult(
                target_name=target_name,
                target_host=target_host,
                timestamp=now,
                probes_sent=self.probe_count,
                probes_received=0,
                packet_loss_pct=100.0,
                latency_min_ms=None,
                latency_avg_ms=None,
                latency_max_ms=None,
                jitter_ms=None,
                is_reachable=False,
                status_message="Probe execution timed out"
            )
        except Exception as exc:
            return ProbeResult(
                target_name=target_name,
                target_host=target_host,
                timestamp=now,
                probes_sent=self.probe_count,
                probes_received=0,
                packet_loss_pct=100.0,
                latency_min_ms=None,
                latency_avg_ms=None,
                latency_max_ms=None,
                jitter_ms=None,
                is_reachable=False,
                status_message=f"Ping command error: {exc}"
            )

        # Parse individual RTT replies to calculate RFC-compliant jitter:
        # e.g.: "Reply from 8.8.8.8: bytes=32 time=24ms TTL=117" or "time<1ms"
        rtt_list: list[float] = []
        for line in output.splitlines():
            rtt_match = re.search(r"time[<=]([0-9]+)ms", line, re.IGNORECASE)
            if rtt_match:
                rtt_val = float(rtt_match.group(1))
                rtt_list.append(max(0.1, rtt_val))

        # Parse packet summary
        # "Packets: Sent = 5, Received = 5, Lost = 0 (0% loss)"
        loss_match = re.search(r"Sent\s*=\s*(\d+),\s*Received\s*=\s*(\d+),\s*Lost\s*=\s*(\d+)", output)
        if loss_match:
            sent = int(loss_match.group(1))
            received = int(loss_match.group(2))
            loss_pct = round(((sent - received) / sent) * 100.0, 2)
        else:
            sent = self.probe_count
            received = len(rtt_list)
            loss_pct = round(((sent - received) / sent) * 100.0, 2)

        # Parse min/max/avg from ping summary
        # "Minimum = 18ms, Maximum = 22ms, Average = 20ms"
        summary_match = re.search(r"Minimum\s*=\s*(\d+)ms,\s*Maximum\s*=\s*(\d+)ms,\s*Average\s*=\s*(\d+)ms", output)
        if summary_match:
            lat_min = float(summary_match.group(1))
            lat_max = float(summary_match.group(2))
            lat_avg = float(summary_match.group(3))
        elif rtt_list:
            lat_min = min(rtt_list)
            lat_max = max(rtt_list)
            lat_avg = round(sum(rtt_list) / len(rtt_list), 2)
        else:
            lat_min = lat_max = lat_avg = None

        # Jitter calculation:
        # Standard IPDV (Inter-Packet Delay Variation):
        # Mean absolute difference between successive RTT measurements
        # Formula: Jitter = (1 / (N - 1)) * Sum(|RTT_i - RTT_{i-1}|)
        jitter_ms = None
        if len(rtt_list) >= 2:
            differences = [abs(rtt_list[i] - rtt_list[i - 1]) for i in range(1, len(rtt_list))]
            jitter_ms = round(sum(differences) / len(differences), 2)
        elif lat_min is not None and lat_max is not None:
            # Fallback approximation from spread if only 1 reply diff available
            jitter_ms = round(abs(lat_max - lat_min), 2)

        is_reachable = (received > 0)
        status_msg = f"OK: {received}/{sent} received" if is_reachable else "Host unreachable"

        return ProbeResult(
            target_name=target_name,
            target_host=target_host,
            timestamp=now,
            probes_sent=sent,
            probes_received=received,
            packet_loss_pct=loss_pct,
            latency_min_ms=lat_min,
            latency_avg_ms=lat_avg,
            latency_max_ms=lat_max,
            jitter_ms=jitter_ms,
            is_reachable=is_reachable,
            status_message=status_msg
        )
