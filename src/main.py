"""NetIntel Core Telemetry & Intelligence Service.

Coordinates the end-to-end data pipeline:
Collects -> Validates -> Stores -> Learns Baseline -> Detects Anomalies ->
Diagnoses -> Manages Incidents -> Adapts Sampling Rate -> Exports to CSV / Power BI.
"""

import argparse
from datetime import datetime, timezone
import logging
import os
from pathlib import Path
import sys
import threading
import time
from typing import Any
import yaml

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.collectors import (
    InterfaceCollector,
    TrafficCollector,
    LatencyCollector,
    get_default_gateway,
    SystemCollector,
    InterfaceInfo
)
from src.processing import (
    DataValidator,
    JitterCalculator,
    make_consolidated_metric,
    ConsolidatedMetric
)
from src.storage import (
    DatabaseManager,
    MetricsRepository,
    InterfaceRepository,
    LatencyRepository,
    AnomalyRepository,
    IncidentRepository,
    DiagnosisRepository,
    ApplicationExperienceRepository,
    MonitoringStateRepository,
    CSVExporter
)
from src.analytics import (
    BaselineEngine,
    HealthScoreCalculator,
    StabilityScoreCalculator
)
from src.anomaly import (
    StatisticalAnomalyDetector,
    MLAnomalyDetector
)
from src.diagnosis import DiagnosisEngine
from src.incidents import IncidentManager
from src.adaptive import MonitoringController
from src.experience import ApplicationExperienceEngine
from src.powerbi import PowerBIExporter, PowerBIStreamer


def setup_logging(log_level: str = "INFO", log_file: str = "logs/netintel.log") -> logging.Logger:
    """Configure unified logging to file and console."""
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logger = logging.getLogger("NetIntel")
    logger.setLevel(numeric_level)

    # Avoid duplicate handlers if re-initialized
    if not logger.handlers:
        c_handler = logging.StreamHandler(sys.stdout)
        c_format = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s", datefmt="%H:%M:%S")
        c_handler.setFormatter(c_format)
        logger.addHandler(c_handler)

        try:
            f_handler = logging.FileHandler(str(log_path), encoding="utf-8")
            f_format = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
            f_handler.setFormatter(f_format)
            logger.addHandler(f_handler)
        except Exception as exc:
            print(f"Warning: Could not initialize file handler for logging: {exc}")

    return logger


class NetIntelService:
    """Master orchestrator for real-time network intelligence platform."""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = self._load_config(config_path)

        log_cfg = self.config.get("app", {})
        self.logger = setup_logging(
            log_level=log_cfg.get("log_level", "INFO"),
            log_file=log_cfg.get("log_file", "logs/netintel.log")
        )

        # Storage & Exporter
        db_path = self.config.get("storage", {}).get("database_path", "database/network_monitor.db")
        csv_dir = self.config.get("storage", {}).get("csv_export_dir", "data/exports")
        self.db = DatabaseManager(db_path=db_path)
        self.csv_exporter = CSVExporter(export_dir=csv_dir)

        # Repositories
        self.metrics_repo = MetricsRepository(self.db)
        self.interface_repo = InterfaceRepository(self.db)
        self.latency_repo = LatencyRepository(self.db)
        self.anomaly_repo = AnomalyRepository(self.db)
        self.incident_repo = IncidentRepository(self.db)
        self.diagnosis_repo = DiagnosisRepository(self.db)
        self.experience_repo = ApplicationExperienceRepository(self.db)
        self.state_repo = MonitoringStateRepository(self.db)

        # Discovery & Collectors
        iface_cfg = self.config.get("interface", {})
        self.iface_collector = InterfaceCollector(
            exclude_loopback=iface_cfg.get("exclude_loopback", True),
            exclude_virtual=iface_cfg.get("exclude_virtual", False)
        )
        self.active_interface_info = self._resolve_active_interface()
        active_name = self.active_interface_info.name if self.active_interface_info else "Wi-Fi"

        self.traffic_collector = TrafficCollector(interface_name=active_name)
        probe_cfg = self.config.get("probes", {})
        self.latency_collector = LatencyCollector(
            probe_count=probe_cfg.get("ping_count", 5),
            timeout_ms=probe_cfg.get("timeout_ms", 1000)
        )
        self.system_collector = SystemCollector(db_path=db_path)

        # Processing & Validation
        self.validator = DataValidator()
        self.jitter_calc = JitterCalculator(window_size=20)

        # Analytics & Scoring
        health_weights = self.config.get("health", {}).get("weights")
        self.health_calc = HealthScoreCalculator(config_weights=health_weights)
        self.stability_calc = StabilityScoreCalculator(
            window_samples=self.config.get("stability", {}).get("window_samples", 20)
        )
        base_cfg = self.config.get("baseline", {})
        self.baseline_engine = BaselineEngine(
            min_samples_required=base_cfg.get("min_samples_required", 30),
            rolling_window_samples=base_cfg.get("rolling_window_samples", 120)
        )

        # Anomaly Detectors
        anom_cfg = self.config.get("anomaly", {})
        self.stat_anomaly_detector = StatisticalAnomalyDetector(
            zscore_threshold=anom_cfg.get("zscore_threshold", 2.5),
            iqr_multiplier=anom_cfg.get("iqr_multiplier", 1.5)
        )
        self.ml_anomaly_detector = MLAnomalyDetector(
            min_samples=anom_cfg.get("ml_min_samples", 150),
            contamination=anom_cfg.get("isolation_forest_contamination", 0.05)
        )

        # Diagnosis & Incidents
        self.diagnosis_engine = DiagnosisEngine()
        inc_cfg = self.config.get("incidents", {})
        self.incident_manager = IncidentManager(
            repository=self.incident_repo,
            csv_exporter=self.csv_exporter,
            diagnosis_engine=self.diagnosis_engine,
            debounce_trigger=inc_cfg.get("debounce_samples_to_trigger", 3),
            debounce_resolve=inc_cfg.get("debounce_samples_to_resolve", 5)
        )

        # Adaptive Monitoring Controller
        col_cfg = self.config.get("collection", {})
        self.adaptive_controller = MonitoringController(
            state_repo=self.state_repo,
            default_interval=col_cfg.get("default_interval_sec", 2.0),
            adaptive_enabled=col_cfg.get("adaptive_enabled", True),
            intervals=col_cfg.get("adaptive_intervals")
        )

        # Experience Engine
        self.experience_engine = ApplicationExperienceEngine(
            profiles=self.config.get("application_experience")
        )

        self.is_running = False
        self._stop_event = threading.Event()
        self.cached_baselines: dict[str, Any] = {}

        # Power BI Integration
        pbi_cfg = self.config.get("powerbi", {})
        self.powerbi_exporter = PowerBIExporter(export_dir=csv_dir)
        pbi_url = pbi_cfg.get("push_url") or os.environ.get("POWERBI_PUSH_URL")
        self.powerbi_streamer = PowerBIStreamer(push_url=pbi_url)
        self.pbi_sync_interval = pbi_cfg.get("sync_interval_samples", 10)
        self._sample_count = 0

    def _load_config(self, path: str) -> dict[str, Any]:
        """Safely load YAML configuration."""
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def _resolve_active_interface(self) -> InterfaceInfo | None:
        """Detect and catalog active interface."""
        mode = self.config.get("interface", {}).get("mode", "auto")
        manual_name = self.config.get("interface", {}).get("manual_name")
        iface = self.iface_collector.detect_active_interface(manual_name if mode == "manual" else None)
        if iface:
            self.interface_repo.upsert_interface(iface)
        return iface

    def step(self) -> ConsolidatedMetric | None:
        """Execute a single end-to-end telemetry cycle."""
        now_epoch = time.time()
        now_iso = datetime.fromtimestamp(now_epoch, tz=timezone.utc).isoformat()

        # 1. Interface & Traffic
        if not self.active_interface_info:
            self.active_interface_info = self._resolve_active_interface()

        iface_name = self.active_interface_info.name if self.active_interface_info else "Wi-Fi"
        iface_speed = self.active_interface_info.speed_mbps if self.active_interface_info else None

        traffic_sample = self.traffic_collector.sample()
        if not traffic_sample:
            self.logger.warning("Unable to acquire traffic counters from interface.")
            return None

        # 2. Multi-Target Latency Probes
        gw_ip = get_default_gateway() or "192.168.1.1"
        gw_probe = self.latency_collector.probe_target("gateway", gw_ip)
        pub_probe = self.latency_collector.probe_target("google_dns", "8.8.8.8")

        self.latency_repo.save_probe(gw_probe)
        self.latency_repo.save_probe(pub_probe)
        self.csv_exporter.append_latency_probe(gw_probe)
        self.csv_exporter.append_latency_probe(pub_probe)

        primary_lat = pub_probe.latency_avg_ms if pub_probe.is_reachable else gw_probe.latency_avg_ms
        primary_loss = pub_probe.packet_loss_pct
        primary_jitter = self.jitter_calc.add_sample(primary_lat)

        # 3. Data Validation
        val_res = self.validator.validate_metric_sample(
            upload_mbps=traffic_sample.upload_mbps,
            download_mbps=traffic_sample.download_mbps,
            latency_ms=primary_lat,
            jitter_ms=primary_jitter,
            packet_loss_pct=primary_loss,
            packets_sent_per_sec=traffic_sample.packets_sent_per_sec,
            packets_recv_per_sec=traffic_sample.packets_recv_per_sec,
            counter_reset=traffic_sample.counter_reset_detected
        )
        clean = val_res.sanitized_data

        # 4. Stability & Health Scores
        self.stability_calc.add_sample(
            latency_ms=clean["latency_ms"],
            jitter_ms=clean["jitter_ms"],
            loss_pct=clean["packet_loss_pct"],
            throughput_mbps=clean["upload_mbps"] + clean["download_mbps"]
        )
        stab_eval = self.stability_calc.evaluate()

        health_eval = self.health_calc.evaluate(
            latency_ms=clean["latency_ms"],
            jitter_ms=clean["jitter_ms"],
            packet_loss_pct=clean["packet_loss_pct"],
            estimated_utilization_pct=None, # computed below
            upload_mbps=clean["upload_mbps"],
            download_mbps=clean["download_mbps"],
            stability_score=stab_eval.stability_score
        )

        # 5. Baseline Refresh (Cached or computed periodically)
        recent_df = self.metrics_repo.get_latest_metrics(limit=100, is_simulation=False)
        if len(recent_df) >= 30:
            self.cached_baselines = self.baseline_engine.compute_all_baselines(recent_df)
            if not self.ml_anomaly_detector.is_trained:
                self.ml_anomaly_detector.fit_if_ready(recent_df)

        base_lat = self.cached_baselines.get("latency_ms")
        base_lat_val = base_lat.median if (base_lat and base_lat.is_established) else None

        # 6. Anomaly Detection
        anom_event = self.stat_anomaly_detector.evaluate_sample(
            timestamp_iso=now_iso,
            metric_name="latency_ms",
            observed_value=clean["latency_ms"],
            baseline=base_lat,
            is_simulation=False
        )
        if anom_event:
            self.anomaly_repo.save_anomaly(
                timestamp_iso=anom_event.timestamp_iso,
                metric_name=anom_event.metric_name,
                observed_value=anom_event.observed_value,
                baseline_expected=anom_event.baseline_expected,
                deviation_pct=anom_event.deviation_pct,
                severity=anom_event.severity,
                detection_method=anom_event.detection_method,
                details=anom_event.details,
                is_simulation=False
            )
            self.csv_exporter.append_anomaly({
                "timestamp": anom_event.timestamp_iso,
                "metric_name": anom_event.metric_name,
                "observed_value": anom_event.observed_value,
                "baseline_expected": anom_event.baseline_expected,
                "deviation_pct": anom_event.deviation_pct,
                "severity": anom_event.severity,
                "detection_method": anom_event.detection_method,
                "details": anom_event.details,
                "is_simulation": False
            })

        # 7. Incident Lifecycle Management
        active_inc = self.incident_manager.evaluate_sample(
            timestamp_iso=now_iso,
            epoch_time=now_epoch,
            health_score=health_eval.health_score,
            stability_score=stab_eval.stability_score,
            latency_ms=clean["latency_ms"],
            jitter_ms=clean["jitter_ms"],
            packet_loss_pct=clean["packet_loss_pct"],
            utilization_pct=None,
            gateway_latency_ms=gw_probe.latency_avg_ms,
            gateway_loss_pct=gw_probe.packet_loss_pct,
            baseline_latency=base_lat_val,
            is_simulation=False
        )

        # 8. Adaptive Monitoring Rate Controller
        adaptive_state = self.adaptive_controller.update_evaluation(
            health_score=health_eval.health_score,
            stability_score=stab_eval.stability_score,
            has_open_incident=(active_inc is not None),
            incident_severity=active_inc.severity if active_inc else None,
            active_interface=iface_name,
            timestamp_iso=now_iso
        )

        # 9. Application Experience Assessment
        exp_report = self.experience_engine.evaluate(
            timestamp_iso=now_iso,
            latency_ms=clean["latency_ms"],
            jitter_ms=clean["jitter_ms"],
            packet_loss_pct=clean["packet_loss_pct"],
            download_mbps=clean["download_mbps"],
            upload_mbps=clean["upload_mbps"]
        )
        self.experience_repo.save_experience(
            timestamp_iso=now_iso,
            video_call=exp_report.video_call_score,
            gaming=exp_report.gaming_score,
            web_browsing=exp_report.web_browsing_score,
            file_transfer=exp_report.file_transfer_score,
            limiting_factor=exp_report.primary_limiting_factor,
            is_simulation=False
        )
        self.csv_exporter.append_experience({
            "timestamp": now_iso,
            "video_call": exp_report.video_call_score,
            "gaming": exp_report.gaming_score,
            "web_browsing": exp_report.web_browsing_score,
            "file_transfer": exp_report.file_transfer_score,
            "limiting_factor": exp_report.primary_limiting_factor,
            "is_simulation": False
        })

        # 10. Make and Persist Consolidated Telemetry Metric
        metric = make_consolidated_metric(
            interface_name=iface_name,
            upload_mbps=clean["upload_mbps"],
            download_mbps=clean["download_mbps"],
            bytes_sent=traffic_sample.bytes_sent,
            bytes_recv=traffic_sample.bytes_recv,
            packets_sent=traffic_sample.packets_sent,
            packets_recv=traffic_sample.packets_recv,
            packets_sent_per_sec=clean["packets_sent_per_sec"],
            packets_recv_per_sec=clean["packets_recv_per_sec"],
            latency_ms=clean["latency_ms"],
            jitter_ms=clean["jitter_ms"],
            packet_loss_pct=clean["packet_loss_pct"],
            interface_speed_mbps=iface_speed,
            health_score=health_eval.health_score,
            stability_score=stab_eval.stability_score,
            monitoring_mode=adaptive_state.mode,
            is_simulation=False,
            is_replay=False,
            data_quality_flag=val_res.quality_flag,
            override_timestamp=now_epoch
        )

        self.metrics_repo.save_metric(metric)
        self.csv_exporter.append_metric(metric)

        # Live Power BI Streaming & Star Schema Sync
        self.powerbi_streamer.push_metric(metric)
        self._sample_count += 1
        if self._sample_count % self.pbi_sync_interval == 0:
            try:
                self.powerbi_exporter.export_from_database(self.db)
            except Exception as exc:
                self.logger.debug(f"Periodic star schema sync exception: {exc}")

        self.logger.info(
            f"[{adaptive_state.mode}] {iface_name} | Up: {metric.upload_mbps:.2f} Mbps | "
            f"Down: {metric.download_mbps:.2f} Mbps | Lat: {metric.latency_ms or 0:.1f} ms | "
            f"Loss: {metric.packet_loss_pct:.1f}% | Health: {metric.health_score}/100"
        )

        return metric

    def run_loop(self, stop_event: threading.Event | None = None) -> None:
        """Run continuous monitoring loop with adaptive pacing."""
        self.is_running = True
        self._stop_event = stop_event or threading.Event()
        self.logger.info("Starting NetIntel Real-Time Monitoring Loop...")

        try:
            while not self._stop_event.is_set():
                start_time = time.time()
                self.step()

                # Get current interval from adaptive controller
                sleep_sec = self.adaptive_controller.current_interval
                elapsed = time.time() - start_time
                target_sleep = max(0.1, sleep_sec - elapsed)

                self._stop_event.wait(target_sleep)
        except KeyboardInterrupt:
            self.logger.info("Monitoring loop interrupted by user.")
        finally:
            self.is_running = False
            self.powerbi_streamer.stop()
            self.logger.info("NetIntel Monitoring Loop stopped.")


def main():
    parser = argparse.ArgumentParser(description="NetIntel Real-Time Network Intelligence Platform")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--once", action="store_true", help="Run a single collection iteration and exit")
    args = parser.parse_args()

    service = NetIntelService(config_path=args.config)
    if args.once:
        service.step()
    else:
        service.run_loop()


if __name__ == "__main__":
    main()
