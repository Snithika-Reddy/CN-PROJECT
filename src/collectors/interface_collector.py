"""Interface Collector.

Discovers and inspects all network interfaces on the host system.
Resolves IP addresses, MAC addresses, connection speed (Mbps), status (UP/DOWN),
and automatically identifies the primary active outbound network interface.
"""

from dataclasses import dataclass
import logging
import psutil

logger = logging.getLogger(__name__)


@dataclass
class InterfaceInfo:
    name: str
    ip_address: str | None
    mac_address: str | None
    speed_mbps: float | None
    is_up: bool
    is_wireless: bool
    is_loopback: bool
    is_virtual: bool
    duplex: str


class InterfaceCollector:
    """Collects hardware and software network interface details."""

    def __init__(self, exclude_loopback: bool = True, exclude_virtual: bool = False):
        self.exclude_loopback = exclude_loopback
        self.exclude_virtual = exclude_virtual

    def get_all_interfaces(self) -> dict[str, InterfaceInfo]:
        """Query psutil for all network interfaces and hardware statistics."""
        import time
        addrs = {}
        stats = {}
        for _ in range(3):
            try:
                addrs = psutil.net_if_addrs()
                break
            except Exception as e:
                time.sleep(0.1)

        for _ in range(3):
            try:
                stats = psutil.net_if_stats()
                break
            except Exception as e:
                time.sleep(0.1)

        # Fallback if psutil interface syscall failed completely
        if not addrs:
            try:
                io_keys = list(psutil.net_io_counters(pernic=True).keys())
                for k in io_keys:
                    addrs[k] = []
            except Exception:
                addrs["Default Interface"] = []

        results: dict[str, InterfaceInfo] = {}

        for iface_name, addr_list in addrs.items():
            stat = stats.get(iface_name)
            is_up = stat.isup if stat else False
            speed_mbps = float(stat.speed) if (stat and stat.speed > 0) else None
            duplex = str(stat.duplex) if stat else "UNKNOWN"

            ipv4 = None
            mac = None
            for addr in addr_list:
                # AF_INET is IPv4
                if addr.family == psutil.AF_LINK:
                    mac = addr.address
                elif str(addr.family).endswith("AF_INET") or addr.family == 2:
                    ipv4 = addr.address

            lower_name = iface_name.lower()
            is_loopback = (
                "loopback" in lower_name
                or (ipv4 and ipv4.startswith("127."))
                or lower_name == "lo"
            )
            is_wireless = any(k in lower_name for k in ["wi-fi", "wifi", "wlan", "wireless", "802.11"])
            is_virtual = any(
                k in lower_name for k in ["vethernet", "virtual", "vmware", "vbox", "hyper-v", "wsl", "tap", "vpn"]
            )

            if self.exclude_loopback and is_loopback:
                continue
            if self.exclude_virtual and is_virtual:
                continue

            results[iface_name] = InterfaceInfo(
                name=iface_name,
                ip_address=ipv4,
                mac_address=mac,
                speed_mbps=speed_mbps,
                is_up=is_up,
                is_wireless=is_wireless,
                is_loopback=is_loopback,
                is_virtual=is_virtual,
                duplex=duplex
            )

        return results

    def detect_active_interface(self, manual_name: str | None = None) -> InterfaceInfo | None:
        """Identify the active interface.

        If manual_name is provided and exists, uses that.
        Otherwise selects the active interface with an assigned non-link-local IPv4
        and UP status, prioritizing interfaces that have non-zero network traffic counters.
        """
        all_ifaces = self.get_all_interfaces()
        if not all_ifaces:
            return None

        # 1. Manual override
        if manual_name and manual_name in all_ifaces:
            return all_ifaces[manual_name]

        # 2. Check traffic counters to find which interface is actually moving packets
        try:
            io_counters = psutil.net_io_counters(pernic=True)
        except Exception:
            io_counters = {}
        candidates: list[tuple[InterfaceInfo, int]] = []

        for name, info in all_ifaces.items():
            if not info.is_up or not info.ip_address:
                continue
            if info.ip_address.startswith("169.254."):  # APIPA / self-assigned
                continue
            if info.is_loopback:
                continue

            counters = io_counters.get(name)
            total_traffic = (counters.bytes_sent + counters.bytes_recv) if counters else 0
            candidates.append((info, total_traffic))

        if candidates:
            # Sort by physical interface first, non-virtual first, then by total traffic descending
            candidates.sort(key=lambda x: (not x[0].is_virtual, x[1]), reverse=True)
            return candidates[0][0]

        # 3. Fallback: return any UP interface with an IP
        for info in all_ifaces.values():
            if info.is_up and info.ip_address and not info.is_loopback:
                return info

        # 4. Ultimate fallback: first interface
        return next(iter(all_ifaces.values())) if all_ifaces else None
