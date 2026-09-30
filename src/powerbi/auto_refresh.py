"""Power BI Desktop Live Auto-Refresher Daemon.

Automates periodic live refresh triggers for Microsoft Power BI Desktop
on Windows without requiring manual clicks. Uses standard Windows ctypes
APIs to detect active Power BI Desktop windows and safely issue refresh
signals (F5 / Ctrl+Alt+F5) at configurable intervals.
"""

import argparse
import ctypes
import logging
import sys
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)

# Windows API constants
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
VK_F5 = 0x74
VK_CONTROL = 0x11
VK_MENU = 0x12  # Alt


class PowerBIAutoRefresher:
    """Detects Power BI Desktop windows and automatically triggers data refresh."""

    def __init__(self, interval_sec: int = 5):
        self.interval_sec = max(2, interval_sec)
        self.is_running = False
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def find_pbi_windows(self) -> list[int]:
        """Enumerate top-level Windows and return HWNDs matching Power BI Desktop."""
        if sys.platform != "win32":
            return []

        user32 = ctypes.windll.user32
        pbi_hwnds: list[int] = []

        def enum_windows_callback(hwnd, extra):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value
                    if "Power BI Desktop" in title:
                        pbi_hwnds.append(hwnd)
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
        user32.EnumWindows(WNDENUMPROC(enum_windows_callback), 0)
        return pbi_hwnds

    def trigger_refresh_once(self) -> bool:
        """Find Power BI Desktop window and send F5 refresh signal."""
        if sys.platform != "win32":
            logger.info("Auto-refresher only supported on Windows.")
            return False

        hwnds = self.find_pbi_windows()
        if not hwnds:
            logger.debug("No active Power BI Desktop window found.")
            return False

        user32 = ctypes.windll.user32
        target_hwnd = hwnds[0]

        try:
            # Post F5 key down and key up to window
            user32.PostMessageW(target_hwnd, WM_KEYDOWN, VK_F5, 0)
            time.sleep(0.05)
            user32.PostMessageW(target_hwnd, WM_KEYUP, VK_F5, 0)
            logger.info(f"Dispatched F5 live refresh signal to Power BI Desktop (HWND: {target_hwnd})")
            return True
        except Exception as exc:
            logger.warning(f"Could not signal Power BI window: {exc}")
            return False

    def start(self) -> None:
        """Start background auto-refresher loop."""
        if self._thread and self._thread.is_alive():
            return

        self.is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="PowerBIAutoRefresherThread",
            daemon=True
        )
        self._thread.start()
        logger.info(f"Power BI Desktop live auto-refresher started (Interval: {self.interval_sec}s)")

    def stop(self) -> None:
        """Stop background auto-refresher loop."""
        self.is_running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.info("Power BI Desktop live auto-refresher stopped.")

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            self.trigger_refresh_once()
            self._stop_event.wait(self.interval_sec)


def main():
    parser = argparse.ArgumentParser(description="Power BI Desktop Live Auto-Refresher Daemon")
    parser.add_argument("--interval", type=int, default=5, help="Refresh interval in seconds (default: 5)")
    args = parser.parse_args()

    print(f"[*] Starting NetIntel Power BI Desktop Auto-Refresher (Interval: {args.interval}s)")
    print("[*] Automatically scans for open Power BI Desktop windows and sends live refresh.")
    print("[*] Press Ctrl+C to stop.")

    refresher = PowerBIAutoRefresher(interval_sec=args.interval)
    refresher.start()

    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n[*] Stopping auto-refresher...")
        refresher.stop()


if __name__ == "__main__":
    main()
