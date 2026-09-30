"""Page 9: 'What Changed?' Incident Comparative Analysis View."""

import pandas as pd
import streamlit as st
from src.incidents.incident_manager import IncidentManager
from src.storage.repositories import IncidentRepository
from src.storage.database import DatabaseManager


def render_what_changed(db: DatabaseManager, baseline_dict: dict[str, float] | None = None):
    st.markdown('<div class="section-title">PAGE 9 — "WHAT CHANGED?" COMPARATIVE IMPACT ANALYSIS</div>', unsafe_allow_html=True)

    repo = IncidentRepository(db)
    incidents_df = repo.get_incident_history(limit=20)

    if incidents_df.empty:
        st.info("No recorded incidents available for comparative 'What Changed?' analysis.")
        return

    inc_manager = IncidentManager(repository=repo)
    inc_list = incidents_df["incident_id"].tolist()
    chosen_inc_id = st.selectbox("Select Incident to Compare Against Baseline:", inc_list)

    inc_row = incidents_df[incidents_df["incident_id"] == chosen_inc_id].iloc[0].to_dict()

    base = baseline_dict or {
        "latency_ms": 22.0,
        "jitter_ms": 3.0,
        "packet_loss_pct": 0.0,
        "utilization_pct": 12.0
    }

    comparison = inc_manager.get_what_changed_analysis(inc_row, base)
    comp_df = pd.DataFrame(comparison)

    st.markdown(f"""
    <div class="kpi-card" style="margin-bottom:16px; border-left: 5px solid #CDAAEA;">
        <div class="kpi-label">Incident Identifier</div>
        <div class="kpi-value" style="font-size:22px;">{inc_row.get('incident_id')}</div>
        <div class="kpi-subtext" style="font-size:13px; margin-top:6px; color:#3B3356;">
            Trigger: {inc_row.get('trigger_reason', 'N/A')} | Severity: <b style="color:#763B9E;">{inc_row.get('severity')}</b> | Status: <b style="color:#15112B;">{inc_row.get('status')}</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Baseline vs. Incident Degradation Matrix</div>', unsafe_allow_html=True)
    st.dataframe(comp_df[["metric", "baseline", "incident_peak", "change"]], use_container_width=True, hide_index=True)

    st.markdown("""
    <div class="palette-banner">
        <span style="color:#763B9E; font-weight:700;">Analytical Purpose:</span>
        <span style="color:#15112B; font-weight:500;">
        This feature isolates metric delta divergence, revealing whether an outage was induced by
        bandwidth saturation, upstream queueing bufferbloat, or link-layer frame drops.
        </span>
    </div>
    """, unsafe_allow_html=True)
