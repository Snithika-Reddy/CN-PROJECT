"""Power BI Live Streaming Pusher & Real-Time Push Dataset Extension.

Enables true sub-second live streaming into Microsoft Power BI Service
via standard REST Push API endpoints. When enabled, telemetry frames
are dispatched asynchronously to Power BI streaming datasets with zero
blocking of the core network probe cycle.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import logging
import os
import queue
import threading
import time
from typing import Any, Optional
import requests

logger = logging.getLogger(__name__)


@dataclass
class StreamingStats:
    total_pushed: int = 0
    total_failed: int = 0
    last_status_code: Optional[int] = None
    last_push_timestamp: Optional[str] = None
    last_error: Optional[str] = None
    is_active: bool = False


class PowerBIStreamer:
    """Manages asynchronous live streaming push to Microsoft Power BI Service."""

    def __init__(self, push_url: Optional[str] = None, max_queue_size: int = 500):
        self.push_url = push_url or os.environ.get("POWERBI_PUSH_URL", "")
        self.queue: queue.Queue = queue.Queue(maxsize=max_queue_size)
        self.stats = StreamingStats(is_active=bool(self.push_url))
        self._stop_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None

        if self.is_configured():
            self.start()

    def is_configured(self) -> bool:
        """Check whether a valid Power BI Push REST API URL is configured."""
        return bool(self.push_url and self.push_url.startswith("http"))

    def set_push_url(self, url: str) -> None:
        """Dynamically update push URL and start/restart background pusher."""
        self.push_url = url.strip()
        self.stats.is_active = self.is_configured()
        if self.is_configured() and (not self._worker_thread or not self._worker_thread.is_alive()):
            self.start()

    def start(self) -> None:
        """Start asynchronous background streaming pusher worker thread."""
        if self._worker_thread and self._worker_thread.is_alive():
            return

        self._stop_event.clear()
        self._worker_thread = threading.Thread(
            target=self._streaming_worker,
            name="PowerBIStreamingWorker",
            daemon=True
        )
        self._worker_thread.start()
        self.stats.is_active = True
        logger.info("Power BI Real-Time Streaming Pusher worker started.")

    def stop(self) -> None:
        """Gracefully stop background pusher."""
        self._stop_event.set()
        if self._worker_thread:
            self._worker_thread.join(timeout=2.0)
        self.stats.is_active = False
        logger.info("Power BI Streaming Pusher stopped.")

    def push_metric(self, metric: Any) -> bool:
        """Enqueue a consolidated telemetry metric for live Power BI push.

        Non-blocking: if queue is full, oldest record is dropped to ensure
        telemetry loop is never stalled by network lag.
        """
        if not self.is_configured():
            return False

        # Format payload conforming to Power BI Streaming Dataset JSON specification
        payload = self._format_payload(metric)

        try:
            self.queue.put_nowait(payload)
            return True
        except queue.Full:
            try:
                # Discard oldest to keep fresh
                _ = self.queue.get_nowait()
                self.queue.put_nowait(payload)
                return True
            except Exception:
                return False

    def push_direct_sync(self, payload: list[dict[str, Any]], timeout: float = 3.0) -> tuple[bool, int, str]:
        """Synchronously push a payload for testing or validation."""
        if not self.is_configured():
            return False, 400, "Power BI Push URL not configured."

        try:
            resp = requests.post(
                self.push_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=timeout
            )
            success = resp.status_code in (200, 201, 202)
            self.stats.last_status_code = resp.status_code
            self.stats.last_push_timestamp = datetime.now(timezone.utc).isoformat()
            if success:
                self.stats.total_pushed += len(payload)
                self.stats.last_error = None
                return True, resp.status_code, "OK"
            else:
                self.stats.total_failed += len(payload)
                self.stats.last_error = resp.text
                return False, resp.status_code, resp.text
        except Exception as exc:
            self.stats.total_failed += len(payload)
            self.stats.last_error = str(exc)
            return False, 500, str(exc)

    def _format_payload(self, m: Any) -> dict[str, Any]:
        """Convert metric object/dict into normalized Power BI streaming row."""
        # Handle ConsolidatedMetric object
        if hasattr(m, "timestamp_iso"):
            iso_time = m.timestamp_iso
        elif isinstance(m, dict) and "timestamp" in m:
            iso_time = str(m["timestamp"])
        else:
            iso_time = datetime.now(timezone.utc).isoformat()

        def _val(attr: str, default: Any = 0.0) -> Any:
            if hasattr(m, attr):
                val = getattr(m, attr)
                return val if val is not None else default
            if isinstance(m, dict):
                return m.get(attr, default)
            return default

        return {
            "timestamp": iso_time,
            "interface_name": str(_val("interface_name", "Wi-Fi")),
            "upload_mbps": float(_val("upload_mbps", 0.0)),
            "download_mbps": float(_val("download_mbps", 0.0)),
            "latency_ms": float(_val("latency_ms", 0.0)),
            "jitter_ms": float(_val("jitter_ms", 0.0)),
            "packet_loss_pct": float(_val("packet_loss_pct", 0.0)),
            "health_score": float(_val("health_score", 100.0)),
            "stability_score": float(_val("stability_score", 100.0)),
            "estimated_utilization_pct": float(_val("estimated_utilization_pct", 0.0)),
            "monitoring_mode": str(_val("monitoring_mode", "NORMAL"))
        }

    def _streaming_worker(self) -> None:
        """Worker thread pulling from queue and batch POSTing to Power BI Service."""
        batch: list[dict[str, Any]] = []

        while not self._stop_event.is_set():
            try:
                # Wait for up to 1 second for a metric
                item = self.queue.get(timeout=1.0)
                batch.append(item)

                # Drain any additional pending items up to 10
                while len(batch) < 10:
                    try:
                        batch.append(self.queue.get_nowait())
                    except queue.Empty:
                        break

                if batch:
                    self._dispatch_batch(batch)
                    batch = []

            except queue.Empty:
                continue
            except Exception as exc:
                logger.debug(f"Pusher loop exception: {exc}")

        # Flush any remaining items before exiting
        if batch:
            self._dispatch_batch(batch)

    def _dispatch_batch(self, batch: list[dict[str, Any]]) -> None:
        """Send JSON batch payload to Power BI REST endpoint."""
        if not self.is_configured():
            return

        try:
            resp = requests.post(
                self.push_url,
                json=batch,
                headers={"Content-Type": "application/json"},
                timeout=4.0
            )
            self.stats.last_status_code = resp.status_code
            self.stats.last_push_timestamp = datetime.now(timezone.utc).isoformat()

            if resp.status_code in (200, 201, 202):
                self.stats.total_pushed += len(batch)
                self.stats.last_error = None
            else:
                self.stats.total_failed += len(batch)
                self.stats.last_error = f"HTTP {resp.status_code}: {resp.text[:120]}"
                logger.warning(f"Power BI Push API rejected batch: {resp.status_code}")
        except Exception as exc:
            self.stats.total_failed += len(batch)
            self.stats.last_error = str(exc)
            logger.warning(f"Network error pushing live batch to Power BI: {exc}")
