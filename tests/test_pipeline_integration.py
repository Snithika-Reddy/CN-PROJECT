"""Integration test for Collector -> Processor -> Database -> CSV Export data pipeline."""

from pathlib import Path
import pytest
import pandas as pd
from src.storage.database import DatabaseManager
from src.storage.repositories import MetricsRepository
from src.storage.csv_exporter import CSVExporter
from src.processing.validation import DataValidator
from src.processing.metrics import make_consolidated_metric
from src.analytics.health_score import HealthScoreCalculator
from src.analytics.stability_score import StabilityScoreCalculator


def test_full_pipeline_flow(tmp_path):
    db_path = tmp_path / "integration.db"
    csv_dir = tmp_path / "exports"

    # 1. Initialize Pipeline Components
    db = DatabaseManager(db_path=str(db_path), schema_path="database/schema.sql")
    repo = MetricsRepository(db)
    exporter = CSVExporter(export_dir=str(csv_dir))
    validator = DataValidator()
    health_calc = HealthScoreCalculator()
    stab_calc = StabilityScoreCalculator()

    # 2. Simulate raw collector sample
    raw_upload = 12.4
    raw_download = 58.2
    raw_lat = 21.0
    raw_jit = 1.8
    raw_loss = 0.0

    # 3. Process & Validate
    val = validator.validate_metric_sample(
        upload_mbps=raw_upload,
        download_mbps=raw_download,
        latency_ms=raw_lat,
        jitter_ms=raw_jit,
        packet_loss_pct=raw_loss,
        packets_sent_per_sec=20.0,
        packets_recv_per_sec=80.0
    )
    assert val.is_valid is True

    # 4. Score
    stab_calc.add_sample(raw_lat, raw_jit, raw_loss, raw_upload + raw_download)
    stab_eval = stab_calc.evaluate()
    health_eval = health_calc.evaluate(
        latency_ms=raw_lat,
        jitter_ms=raw_jit,
        packet_loss_pct=raw_loss,
        estimated_utilization_pct=10.0,
        upload_mbps=raw_upload,
        download_mbps=raw_download,
        stability_score=stab_eval.stability_score
    )

    # 5. Make Consolidated Metric
    metric = make_consolidated_metric(
        interface_name="Wi-Fi",
        upload_mbps=raw_upload,
        download_mbps=raw_download,
        bytes_sent=10000,
        bytes_recv=50000,
        packets_sent=50,
        packets_recv=200,
        packets_sent_per_sec=20.0,
        packets_recv_per_sec=80.0,
        latency_ms=raw_lat,
        jitter_ms=raw_jit,
        packet_loss_pct=raw_loss,
        interface_speed_mbps=866.0,
        health_score=health_eval.health_score,
        stability_score=stab_eval.stability_score,
        monitoring_mode="NORMAL"
    )

    # 6. Persist to SQLite
    row_id = repo.save_metric(metric)
    assert row_id > 0

    # 7. Append to CSV
    exporter.append_metric(metric)

    # 8. Assertions on SQLite and CSV
    df_db = repo.get_latest_metrics(limit=5)
    assert len(df_db) == 1
    assert df_db.iloc[0]["latency_ms"] == 21.0

    df_csv = pd.read_csv(exporter.metrics_file)
    assert len(df_csv) == 1
    assert df_csv.iloc[0]["download_mbps"] == 58.2
    assert df_csv.iloc[0]["health_score"] == health_eval.health_score
