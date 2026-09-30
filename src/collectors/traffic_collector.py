"""Per-NIC Traffic Collector.

Collects cumulative byte and packet counters specifically for the monitored interface
using psutil.net_io_counters(pernic=True) to avoid interface aggregation mismatch.
"""

from dataclasses import dataclass
import time
import psutil
import logging

logger = logging.getLogger(__name__)


@dataclass
class RawCounters:
    timestamp: float
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int
    errin: int
    errout: int
    dropin: int
    dropout: int


@dataclass
class TrafficSample:
    timestamp: float
    interface_name: str
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int
    upload_mbps: float
    download_mbps: float
    packets_sent_per_sec: float
    packets_recv_per_sec: float
    delta_time: float
    counter_reset_detected: bool


class TrafficCollector:
    """Collects network I/O counters and computes rates for a specific interface."""

    def __init__(self, interface_name: str):
        self.interface_name = interface_name
        self.last_counters: RawCounters | None = None

    def set_interface(self, interface_name: str) -> None:
        """Switch monitored interface and reset prior delta baseline."""
        if self.interface_name != interface_name:
            self.interface_name = interface_name
            self.last_counters = None

    def get_raw_counters(self) -> RawCounters | None:
        """Read per-NIC counters for the configured interface."""
        all_counters = psutil.net_io_counters(pernic=True)
        if not all_counters or self.interface_name not in all_counters:
            return None

        c = all_counters[self.interface_name]
        return RawCounters(
            timestamp=time.time(),
            bytes_sent=c.bytes_sent,
            bytes_recv=c.bytes_recv,
            packets_sent=c.packets_sent,
            packets_recv=c.packets_recv,
            errin=c.errin,
            errout=c.errout,
            dropin=c.dropin,
            dropout=c.dropout
        )

    def sample(self) -> TrafficSample | None:
        """Collect current counters and compute throughput and packet rates.

        Guarantees non-negative rates and detects counter rollover/reset.
        """
        current = self.get_raw_counters()
        if not current:
            return None

        if self.last_counters is None:
            # First sample baseline
            self.last_counters = current
            return TrafficSample(
                timestamp=current.timestamp,
                interface_name=self.interface_name,
                bytes_sent=current.bytes_sent,
                bytes_recv=current.bytes_recv,
                packets_sent=current.packets_sent,
                packets_recv=current.packets_recv,
                upload_mbps=0.0,
                download_mbps=0.0,
                packets_sent_per_sec=0.0,
                packets_recv_per_sec=0.0,
                delta_time=0.0,
                counter_reset_detected=False
            )

        dt = current.timestamp - self.last_counters.timestamp
        if dt <= 0:
            dt = 0.001

        delta_bytes_sent = current.bytes_sent - self.last_counters.bytes_sent
        delta_bytes_recv = current.bytes_recv - self.last_counters.bytes_recv
        delta_pkts_sent = current.packets_sent - self.last_counters.packets_sent
        delta_pkts_recv = current.packets_recv - self.last_counters.packets_recv

        # Counter reset detection (e.g., interface reconnect or reboot)
        reset_detected = False
        if delta_bytes_sent < 0 or delta_bytes_recv < 0 or delta_pkts_sent < 0 or delta_pkts_recv < 0:
            logger.warning(f"Counter reset detected on interface {self.interface_name}")
            delta_bytes_sent = max(0, current.bytes_sent)
            delta_bytes_recv = max(0, current.bytes_recv)
            delta_pkts_sent = max(0, current.packets_sent)
            delta_pkts_recv = max(0, current.packets_recv)
            reset_detected = True

        # Convert bytes to Megabits per second: (bytes * 8) / (1_000_000 * dt)
        upload_mbps = round((delta_bytes_sent * 8.0) / (1_000_000.0 * dt), 4)
        download_mbps = round((delta_bytes_recv * 8.0) / (1_000_000.0 * dt), 4)

        pkts_sent_sec = round(delta_pkts_sent / dt, 2)
        pkts_recv_sec = round(delta_pkts_recv / dt, 2)

        sample = TrafficSample(
            timestamp=current.timestamp,
            interface_name=self.interface_name,
            bytes_sent=current.bytes_sent,
            bytes_recv=current.bytes_recv,
            packets_sent=current.packets_sent,
            packets_recv=current.packets_recv,
            upload_mbps=upload_mbps,
            download_mbps=download_mbps,
            packets_sent_per_sec=pkts_sent_sec,
            packets_recv_per_sec=pkts_recv_sec,
            delta_time=round(dt, 4),
            counter_reset_detected=reset_detected
        )

        self.last_counters = current
        return sample
