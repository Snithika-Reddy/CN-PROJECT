"""Default Gateway Detector.

Detects the active default gateway IP address on Windows and cross-platform environments.
Provides fallback mechanisms and does not crash if disconnected.
"""

import re
import socket
import subprocess
import logging

logger = logging.getLogger(__name__)


def get_default_gateway() -> str | None:
    """Detect the IPv4 default gateway IP address.

    Returns:
        Gateway IP string (e.g., '192.168.1.1') or None if unavailable/offline.
    """
    # Primary Windows method: parse 'route print 0.0.0.0'
    try:
        output = subprocess.check_output(
            ["route", "print", "0.0.0.0"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=2.0
        )
        for line in output.splitlines():
            line = line.strip()
            # Look for lines with 0.0.0.0 0.0.0.0 <gateway_ip> <interface_ip>
            match = re.search(r"0\.0\.0\.0\s+0\.0\.0\.0\s+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)", line)
            if match:
                gw = match.group(1)
                if not gw.startswith("127.") and gw != "0.0.0.0":
                    return gw
    except Exception as exc:
        logger.debug(f"Failed to detect gateway via route print: {exc}")

    # Fallback Windows method: ipconfig output
    try:
        output = subprocess.check_output(
            ["ipconfig"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=2.0
        )
        for line in output.splitlines():
            if "Default Gateway" in line:
                match = re.search(r":\s*([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)", line)
                if match:
                    gw = match.group(1)
                    if gw != "0.0.0.0":
                        return gw
    except Exception as exc:
        logger.debug(f"Failed to detect gateway via ipconfig: {exc}")

    # Fallback UDP socket connection to find local interface subnet gateway
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        # Connect to public IP (does not send traffic)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        # Assume common router .1 on /24 subnet as emergency fallback
        parts = local_ip.split(".")
        if len(parts) == 4 and parts[0] != "127":
            return f"{parts[0]}.{parts[1]}.{parts[2]}.1"
    except Exception:
        pass

    return None
