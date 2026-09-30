"""NetIntel Dashboard Master Application.

Real-Time Network Intelligence, Performance Diagnosis & Adaptive Optimization Platform.
Adheres strictly to custom ColorHunt palette (#E3FDFD, #CBF1F5, #A6E3E9, #71C9CE)
and professional software engineering standards.
"""

from pathlib import Path
import sys
import time

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from dashboard.styles import get_custom_css
from dashboard.views.live_monitor import render_live_monitor
from dashboard.views.network_health import render_network_health
from dashboard.views.traffic_analytics import render_traffic_analytics
from dashboard.views.latency_jitter import render_latency_jitter
from dashboard.views.baseline_view import render_baseline
from dashboard.views.anomalies_view import render_anomalies
from dashboard.views.diagnosis_view import render_diagnosis
from dashboard.views.incidents_view import render_incidents
from dashboard.views.what_changed_view import render_what_changed
from dashboard.views.app_experience_view import render_app_experience
from dashboard.views.historical_view import render_historical
from dashboard.views.data_quality_view import render_data_quality
from dashboard.views.simulation_view import render_simulation_replay
from dashboard.views.powerbi_view import render_powerbi_view

from src.main import NetIntelService
from src.storage.database import DatabaseManager
from src.storage.repositories import (
    MetricsRepository,
    LatencyRepository,
    AnomalyRepository,
    IncidentRepository
)

# Page Configuration
st.set_page_config(
    page_title="NetIntel | Network Intelligence Platform",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject Custom Styling
st.markdown(get_custom_css(), unsafe_allow_html=True)


@st.cache_resource
def get_service_and_db():
    """Singleton database manager and telemetry service."""
    db = DatabaseManager(db_path="database/network_monitor.db")
    service = NetIntelService(config_path="config.yaml")
    return db, service


db, service = get_service_and_db()
metrics_repo = MetricsRepository(db)
latency_repo = LatencyRepository(db)
anomaly_repo = AnomalyRepository(db)
incident_repo = IncidentRepository(db)

# Sidebar Navigation & Controls
st.sidebar.markdown("""
<div style="text-align:center; padding: 10px 0;">
    <h2 style="color:#E3FDFD; margin:0; font-size:22px; font-weight:700;">🌐 NetIntel</h2>
    <div style="color:#A6E3E9; font-size:11px; letter-spacing:0.5px;">Network Observability Platform</div>
</div>
""", unsafe_allow_html=True)

nav_page = st.sidebar.radio(
    "NAVIGATION",
    [
        "1. Live Monitor",
        "2. Network Health",
        "3. Traffic Analytics",
        "4. Latency & Jitter",
        "5. Baseline",
        "6. Anomalies",
        "7. Diagnosis",
        "8. Incidents",
        "9. What Changed?",
        "10. App Experience",
        "11. Historical Trends",
        "12. Data Quality",
        "13. Simulation & Replay",
        "14. Power BI Pipeline"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown('<div class="kpi-label">CONTROL PLANE</div>', unsafe_allow_html=True)

# Single sample manual collection trigger
if st.sidebar.button("⚡ Collect Live Sample", type="primary", use_container_width=True):
    with st.spinner("Executing real network probes..."):
        sample = service.step()
        if sample:
            st.sidebar.success(f"Sampled: {sample.latency_ms or 0:.1f}ms, Health: {sample.health_score}/100")
            time.sleep(0.5)
            st.rerun()

# Auto Refresh Control
auto_refresh = st.sidebar.checkbox("Enable Auto-Refresh", value=False)
refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", min_value=2, max_value=30, value=3)

# Data Filter
include_simulation = st.sidebar.checkbox("Include Simulated Telemetry", value=False)

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="font-size:11px; color:#6C8E99; text-align:center;">
    NetIntel v1.0.0<br/>
    Real-Time Telemetry & Diagnostic Engine<br/>
    Power BI Pipeline Ready
</div>
""", unsafe_allow_html=True)

# Top Application Banner
st.markdown("""
<div class="netintel-header">
    <div>
        <h1 class="netintel-title">Real-Time Network Intelligence Platform</h1>
        <p class="netintel-subtitle">Continuous Telemetry Collection • Empirical Baselines • Multi-Signal Diagnosis • Adaptive Sampling</p>
    </div>
    <div style="text-align:right;">
        <span class="status-badge badge-live">SYSTEM ACTIVE</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Fetch Telemetry Data
latest_df = metrics_repo.get_latest_metrics(limit=100, is_simulation=include_simulation)
probes_df = latency_repo.get_recent_probes(limit=40)
anomalies_df = anomaly_repo.get_recent_anomalies(limit=50, is_simulation=include_simulation)

# Page Routing
if nav_page.startswith("1."):
    render_live_monitor(latest_df, probes_df)
elif nav_page.startswith("2."):
    render_network_health(latest_df)
elif nav_page.startswith("3."):
    render_traffic_analytics(latest_df)
elif nav_page.startswith("4."):
    render_latency_jitter(latest_df, probes_df)
elif nav_page.startswith("5."):
    render_baseline(latest_df)
elif nav_page.startswith("6."):
    render_anomalies(anomalies_df)
elif nav_page.startswith("7."):
    render_diagnosis(latest_df, probes_df)
elif nav_page.startswith("8."):
    render_incidents(db, is_simulation=include_simulation)
elif nav_page.startswith("9."):
    render_what_changed(db)
elif nav_page.startswith("10."):
    render_app_experience(latest_df)
elif nav_page.startswith("11."):
    render_historical(latest_df)
elif nav_page.startswith("12."):
    render_data_quality(latest_df)
elif nav_page.startswith("13."):
    render_simulation_replay(db)
elif nav_page.startswith("14."):
    render_powerbi_view(db=db, service=service)

# Auto refresh handler
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
