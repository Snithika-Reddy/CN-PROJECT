"""Power BI & Live Telemetry HTTP REST API Server.

Serves live network metrics and star schema tabular data as standard JSON
over HTTP (default http://127.0.0.1:8080) with full CORS enablement.
Allows Power BI Desktop 'Get Data -> Web' and web dashboards to query
live network intelligence without encountering file-locking issues.
"""

from datetime import datetime, timezone
import http.server
import json
import logging
from pathlib import Path
import socketserver
import threading
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

from ..storage.database import DatabaseManager

logger = logging.getLogger(__name__)


class TelemetryAPIHandler(http.server.BaseHTTPRequestHandler):
    """HTTP Request Handler providing REST endpoints for Power BI and external tools."""

    db: Optional[DatabaseManager] = None
    service: Any = None

    def _set_cors_headers(self, content_type: str = "application/json") -> None:
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")

    def do_OPTIONS(self) -> None:
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query = parse_qs(parsed_url.query)

        db = self.db or DatabaseManager()

        if path in ("/", "/api", "/api/status"):
            self._handle_status(db)
        elif path == "/api/live":
            self._handle_live(db)
        elif path == "/api/metrics":
            limit = int(query.get("limit", [100])[0])
            self._handle_metrics(db, limit)
        elif path == "/api/star-schema/metrics":
            limit = int(query.get("limit", [1000])[0])
            self._handle_table(db, "network_metrics", limit)
        elif path == "/api/star-schema/incidents":
            self._handle_table(db, "incidents", 200)
        elif path == "/api/star-schema/anomalies":
            self._handle_table(db, "anomalies", 500)
        elif path == "/api/star-schema/experience":
            self._handle_table(db, "application_experience", 500)
        elif path == "/api/star-schema/all":
            self._handle_all_summary(db)
        else:
            self.send_response(404)
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"Endpoint {path} not found"}).encode("utf-8"))

    def do_POST(self) -> None:
        parsed_url = urlparse(self.path)
        if parsed_url.path == "/api/powerbi/push-test":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body.decode("utf-8"))
                push_url = data.get("push_url")
                if not push_url:
                    self._send_json({"error": "Missing 'push_url' field"}, status=400)
                    return

                from .streaming import PowerBIStreamer
                streamer = PowerBIStreamer(push_url=push_url)
                test_payload = [{
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "interface_name": "Test-Interface",
                    "upload_mbps": 15.0,
                    "download_mbps": 85.0,
                    "latency_ms": 18.5,
                    "jitter_ms": 2.0,
                    "packet_loss_pct": 0.0,
                    "health_score": 98.0,
                    "stability_score": 96.0,
                    "estimated_utilization_pct": 12.0,
                    "monitoring_mode": "TEST"
                }]
                ok, code, msg = streamer.push_direct_sync(test_payload)
                self._send_json({"success": ok, "status_code": code, "message": msg})
            except Exception as exc:
                self._send_json({"error": str(exc)}, status=500)
        else:
            self.send_response(404)
            self._set_cors_headers()
            self.end_headers()

    def _send_json(self, payload: Any, status: int = 200) -> None:
        response_bytes = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self._set_cors_headers()
        self.send_header("Content-Length", str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

    def _handle_status(self, db: DatabaseManager) -> None:
        try:
            total_metrics = db.query_df("SELECT COUNT(*) as cnt FROM network_metrics")["cnt"].iloc[0]
            total_incidents = db.query_df("SELECT COUNT(*) as cnt FROM incidents")["cnt"].iloc[0]
            total_anomalies = db.query_df("SELECT COUNT(*) as cnt FROM anomalies")["cnt"].iloc[0]
        except Exception:
            total_metrics = 0
            total_incidents = 0
            total_anomalies = 0

        self._send_json({
            "service": "NetIntel Real-Time Telemetry API",
            "version": "1.0.0",
            "status": "ONLINE",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "telemetry_counts": {
                "network_metrics": int(total_metrics),
                "incidents": int(total_incidents),
                "anomalies": int(total_anomalies)
            },
            "endpoints": [
                "/api/live",
                "/api/metrics?limit=100",
                "/api/star-schema/metrics",
                "/api/star-schema/incidents",
                "/api/star-schema/anomalies",
                "/api/star-schema/experience",
                "/api/star-schema/all"
            ]
        })

    def _handle_live(self, db: DatabaseManager) -> None:
        try:
            df = db.query_df("SELECT * FROM network_metrics ORDER BY timestamp DESC LIMIT 1")
            if not df.empty:
                self._send_json(df.to_dict(orient="records")[0])
            else:
                self._send_json({"message": "No telemetry recorded yet"})
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=500)

    def _handle_metrics(self, db: DatabaseManager, limit: int) -> None:
        try:
            df = db.query_df(f"SELECT * FROM network_metrics ORDER BY timestamp DESC LIMIT {min(5000, limit)}")
            self._send_json(df.to_dict(orient="records"))
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=500)

    def _handle_table(self, db: DatabaseManager, table: str, limit: int) -> None:
        try:
            df = db.query_df(f"SELECT * FROM {table} ORDER BY 1 DESC LIMIT {limit}")
            self._send_json(df.to_dict(orient="records"))
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=500)

    def _handle_all_summary(self, db: DatabaseManager) -> None:
        tables = ["network_metrics", "latency_probes", "incidents", "anomalies", "application_experience", "interfaces"]
        summary = {}
        for tbl in tables:
            try:
                cnt = db.query_df(f"SELECT COUNT(*) as cnt FROM {tbl}")["cnt"].iloc[0]
                summary[tbl] = int(cnt)
            except Exception:
                summary[tbl] = 0
        self._send_json({"star_schema_tables": summary})

    def log_message(self, format: str, *args: Any) -> None:
        # Suppress noisy standard request logging unless debug level
        logger.debug("%s - - [%s] %s" % (self.address_string(), self.log_date_time_string(), format % args))


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class PowerBIAPIServer:
    """Manages the background execution of the local Power BI Telemetry REST API."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8080, db_manager: Optional[DatabaseManager] = None):
        self.host = host
        self.port = port
        self.db_manager = db_manager or DatabaseManager()
        self.server: Optional[ThreadedHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start HTTP server in background thread."""
        if self._thread and self._thread.is_alive():
            return

        TelemetryAPIHandler.db = self.db_manager

        try:
            self.server = ThreadedHTTPServer((self.host, self.port), TelemetryAPIHandler)
            self._thread = threading.Thread(
                target=self.server.serve_forever,
                name="PowerBIAPIServerThread",
                daemon=True
            )
            self._thread.start()
            logger.info(f"Power BI REST API server running at http://{self.host}:{self.port}")
        except Exception as exc:
            logger.error(f"Failed to start Power BI REST API on {self.host}:{self.port}: {exc}")

    def stop(self) -> None:
        """Gracefully shut down HTTP server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        logger.info("Power BI REST API server stopped.")


def run_api_server_cli(host: str = "127.0.0.1", port: int = 8080) -> None:
    """Standalone CLI entry point for running the API server."""
    print(f"[*] Starting NetIntel Power BI REST API Server on http://{host}:{port} ...")
    print(f"[*] Endpoints: http://{host}:{port}/api/status, http://{host}:{port}/api/live")
    print("[*] Press Ctrl+C to stop.")
    server = PowerBIAPIServer(host=host, port=port)
    server.start()
    try:
        while True:
            threading.Event().wait(1.0)
    except KeyboardInterrupt:
        print("\n[*] Stopping server...")
        server.stop()


if __name__ == "__main__":
    run_api_server_cli()
