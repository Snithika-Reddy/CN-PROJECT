"""Page 8: Incident Lifecycle & Evidence Timeline View."""

import pandas as pd
import streamlit as st
from src.storage.repositories import IncidentRepository
from src.storage.database import DatabaseManager


def render_incidents(db: DatabaseManager, is_simulation: bool = False):
    st.markdown('<div class="section-title">PAGE 8 — INCIDENT LIFECYCLE & EVIDENCE TIMELINE</div>', unsafe_allow_html=True)

    repo = IncidentRepository(db)
    incidents_df = repo.get_incident_history(limit=50, is_simulation=is_simulation)

    if incidents_df.empty:
        st.success("No network degradation incidents recorded. Hysteresis debounce filters are operating nominally.")
        return

    # Incident Overview Cards
    open_count = (incidents_df["status"].isin(["OPEN", "RECOVERING"])).sum()
    crit_count = (incidents_df["severity"] == "CRITICAL").sum()
    avg_duration = incidents_df["duration_seconds"].dropna().mean()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Incidents Tracked</div>
            <div class="kpi-value">{len(incidents_df)}</div>
            <div class="kpi-subtext">Historical debounced events</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        o_color = "#DC2626" if open_count > 0 else "#2E7D32"
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Active Incidents</div>
            <div class="kpi-value" style="color:{o_color};">{open_count}</div>
            <div class="kpi-subtext">Currently Open / Recovering</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Critical Incidents</div>
            <div class="kpi-value" style="color:#DC2626;">{crit_count}</div>
            <div class="kpi-subtext">Severe degradation tier</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        dur_str = f"{avg_duration:.1f}s" if pd.notnull(avg_duration) else "N/A"
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Mean Duration (MTTR)</div>
            <div class="kpi-value">{dur_str}</div>
            <div class="kpi-subtext">Incident recovery time</div>
        </div>
        """, unsafe_allow_html=True)

    # Incident Selection & Timeline Inspection
    st.markdown('<div class="section-title">Incident Historical Records</div>', unsafe_allow_html=True)
    st.dataframe(incidents_df[[
        "incident_id", "start_timestamp", "status", "severity",
        "duration_seconds", "peak_latency_ms", "peak_packet_loss_pct", "diagnosis_summary"
    ]], use_container_width=True, hide_index=True)

    selected_id = st.selectbox(
        "Select Incident to Inspect Chronological Evidence Timeline:",
        incidents_df["incident_id"].tolist()
    )

    if selected_id:
        timeline = repo.get_incident_timeline(selected_id)
        st.markdown(f'<div class="section-title">Evidence Timeline for {selected_id}</div>', unsafe_allow_html=True)

        if timeline:
            for ev in timeline:
                st.markdown(f"""
                <div class="timeline-item">
                    <span style="color:#4C3C6E; font-weight:700; font-family:'JetBrains Mono'; font-size:12px;">{ev.get('timestamp', '')}</span>
                    <span class="status-badge badge-live" style="margin-left:8px; font-size:10px;">{ev.get('event_type', '')}</span>
                    <div style="color:#15112B; font-weight:600; margin-top:4px;">{ev.get('description', '')}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No detailed timeline events logged for this incident.")
