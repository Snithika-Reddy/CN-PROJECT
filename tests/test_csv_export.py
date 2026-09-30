"""Unit tests for automatic CSV export generation and appending."""

from pathlib import Path
import pytest
import pandas as pd
from src.storage.csv_exporter import CSVExporter
from src.processing.metrics import make_consolidated_metric


@pytest.fixture
def temp_exporter(tmp_path):
    return CSVExporter(export_dir=str(tmp_path))


def test_csv_headers_initialization(temp_exporter):
    assert temp_exporter.metrics_file.exists()
    assert temp_exporter.latency_file.exists()
    assert temp_exporter.incidents_file.exists()
    assert temp_exporter.anomalies_file.exists()

    df = pd.read_csv(temp_exporter.metrics_file)
    assert "upload_mbps" in df.columns
    assert "download_mbps" in df.columns
    assert "latency_ms" in df.columns
    assert "jitter_ms" in df.columns
    assert "health_score" in df.columns


def test_csv_append_metric(temp_exporter):
    m = make_consolidated_metric(
        interface_name="Wi-Fi",
        upload_mbps=15.0,
        download_mbps=85.0,
        bytes_sent=5000,
        bytes_recv=25000,
        packets_sent=50,
        packets_recv=250,
        packets_sent_per_sec=25.0,
        packets_recv_per_sec=125.0,
        latency_ms=19.2,
        jitter_ms=1.1,
        packet_loss_pct=0.0,
        interface_speed_mbps=1000.0,
        health_score=97.0,
        stability_score=95.0
    )
    temp_exporter.append_metric(m)

    df = pd.read_csv(temp_exporter.metrics_file)
    assert len(df) == 1
    assert df.iloc[0]["interface"] == "Wi-Fi"
    assert df.iloc[0]["download_mbps"] == 85.0
