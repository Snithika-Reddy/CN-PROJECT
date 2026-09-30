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
    <div style="background:rgba(17,32,45,0.8); border:1px solid rgba(113,201,206,0.25); border-radius:10px; padding:16px; margin-bottom:16px;">
        <div style="color:#A6E3E9; font-size:12px; text-transform:uppercase;">Incident Identifier</div>
        <div style="font-size:20px; font-weight:700; color:#E3FDFD;">{inc_row.get('incident_id')}</div>
        <div style="color:#CBF1F5; font-size:13px; margin-top:4px;">
            Trigger: {inc_row.get('trigger_reason', 'N/A')} | Severity: <b>{inc_row.get('severity')}</b> | Status: <b>{inc_row.get('status')}</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Baseline vs. Incident Degradation Matrix</div>', unsafe_allow_html=True)
    st.dataframe(comp_df[["metric", "baseline", "incident_peak", "change"]], use_container_width=True, hide_index=True)

    st.markdown("""
    <div style="background:rgba(17,32,45,0.7); padding:14px 18px; border-radius:8px; border-left:3px solid #71C9CE; margin-top:16px;">
        <span style="color:#71C9CE; font-weight:600;">Analytical Purpose:</span>
        <span style="color:#E3FDFD;">
        This feature isolates metric delta divergence, revealing whether an outage was induced by
        bandwidth saturation, upstream queueing bufferbloat, or link-layer frame drops.
        </span>
    </div>
    """, unsafe_allow_html=True)
