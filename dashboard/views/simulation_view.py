"""Simulation Scenarios and Incident Replay Workbench."""

import time
import pandas as pd
import streamlit as st
from src.simulation.scenarios import SCENARIOS, ScenarioGenerator
from src.storage.database import DatabaseManager
from src.storage.repositories import MetricsRepository, IncidentRepository
from src.storage.csv_exporter import CSVExporter


def render_simulation_replay(db: DatabaseManager):
    st.markdown('<div class="section-title">CONTROLLED SIMULATION & INCIDENT REPLAY WORKBENCH</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="palette-banner">
        <span style="color:#763B9E; font-weight:700;">Academic Integrity Gating:</span>
        <span style="color:#15112B; font-weight:500;">
        All synthetic records generated in this workbench are explicitly marked with <code>is_simulation = 1</code>
        in SQLite and CSV exports. Simulated data is isolated from real production baselines.
        </span>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Controlled Simulation Scenarios", "Historical Incident Replay"])

    with tab1:
        st.markdown('<div class="section-title">Inject Controlled Scenario for Viva Demonstration</div>', unsafe_allow_html=True)

        scen_options = {k: v.name for k, v in SCENARIOS.items()}
        selected_key = st.selectbox("Select Network Degradation Scenario:", list(scen_options.keys()), format_func=lambda x: scen_options[x])

        scen_def = SCENARIOS[selected_key]
        st.info(f"**Description:** {scen_def.description}\n\n**Parameters:** Latency: {scen_def.latency_ms}ms, Loss: {scen_def.packet_loss_pct}%, Utilization: {scen_def.estimated_utilization_pct}%, Expected Health: {scen_def.health_score}/100")

        sample_count = st.slider("Number of Samples to Generate:", min_value=5, max_value=50, value=scen_def.duration_samples)

        if st.button("Inject Simulation Telemetry", type="primary", use_container_width=True):
            gen = ScenarioGenerator()
            repo = MetricsRepository(db)
            exporter = CSVExporter()

            progress_bar = st.progress(0)
            injected_metrics = []

            for i in range(sample_count):
                m = gen.generate_sample(selected_key, sample_index=i)
                repo.save_metric(m)
                exporter.append_metric(m)
                injected_metrics.append({
                    "Timestamp": m.timestamp_iso,
                    "Scenario": m.monitoring_mode,
                    "Latency (ms)": m.latency_ms,
                    "Loss (%)": m.packet_loss_pct,
                    "Download (Mbps)": m.download_mbps,
                    "Health": m.health_score
                })
                progress_bar.progress((i + 1) / sample_count)

            st.success(f"Successfully injected {sample_count} simulated telemetry records marked `is_simulation = 1`.")
            st.dataframe(pd.DataFrame(injected_metrics), use_container_width=True, hide_index=True)

    with tab2:
        st.markdown('<div class="section-title">Replay Recorded Historical Degradation</div>', unsafe_allow_html=True)
        inc_repo = IncidentRepository(db)
        incidents = inc_repo.get_incident_history(limit=10, is_simulation=False)

        if incidents.empty:
            st.info("No real-world incidents recorded yet to replay.")
        else:
            st.dataframe(incidents[["incident_id", "start_timestamp", "severity", "duration_seconds", "diagnosis_summary"]], use_container_width=True, hide_index=True)
            st.caption("Replay streams historical frames with timed intervals to reproduce real-time dashboard behavior.")
