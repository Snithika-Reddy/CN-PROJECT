"""Rate calculation and throughput unit conversion utilities."""


def bytes_to_mbps(byte_delta: int | float, time_delta_sec: float) -> float:
    """Convert a byte delta over a given time interval to Megabits per second (Mbps)."""
    if time_delta_sec <= 0:
        return 0.0
    return round((float(byte_delta) * 8.0) / (1_000_000.0 * time_delta_sec), 4)


def packets_to_pps(packet_delta: int | float, time_delta_sec: float) -> float:
    """Convert packet count delta over a time interval to packets per second (PPS)."""
    if time_delta_sec <= 0:
        return 0.0
    return round(float(packet_delta) / time_delta_sec, 2)


def format_bandwidth(mbps: float) -> str:
    """Format bandwidth into readable human-friendly string (Kbps, Mbps, Gbps)."""
    if mbps is None:
        return "0.0 Mbps"
    if mbps < 1.0:
        return f"{round(mbps * 1000.0, 1)} Kbps"
    if mbps >= 1000.0:
        return f"{round(mbps / 1000.0, 2)} Gbps"
    return f"{round(mbps, 2)} Mbps"
