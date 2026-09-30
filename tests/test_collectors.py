"""Unit tests for host discovery and telemetry collectors."""

import pytest
from src.collectors.interface_collector import InterfaceCollector
from src.collectors.gateway_detector import get_default_gateway
from src.collectors.system_collector import SystemCollector


def test_interface_discovery():
    col = InterfaceCollector(exclude_loopback=True)
    ifaces = col.get_all_interfaces()
    assert isinstance(ifaces, dict)
    assert len(ifaces) > 0

    active = col.detect_active_interface()
    # On an active network machine, active interface should be found
    if active:
        assert active.ip_address is not None
        assert not active.ip_address.startswith("127.")


def test_gateway_detector():
    gw = get_default_gateway()
    # If network is connected, gateway should be valid IPv4
    if gw:
        parts = gw.split(".")
        assert len(parts) == 4
        assert not gw.startswith("127.")


def test_system_collector():
    col = SystemCollector()
    metrics = col.sample()
    assert metrics.cpu_percent >= 0.0
    assert metrics.memory_used_mb >= 0.0
    assert metrics.process_threads >= 1
