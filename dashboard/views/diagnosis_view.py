"""Page 7: Multi-Signal Diagnosis & Hypotheses Ranking View."""

import pandas as pd
import streamlit as st
from src.diagnosis.diagnosis_engine import DiagnosisEngine


def render_diagnosis(latest_df: pd.DataFrame, probes_df: pd.DataFrame):
    st.markdown('<div class="section-title">PAGE 7 — MULTI-SIGNAL DIAGNOSIS & HYPOTHESES RANKING</div>', unsafe_allow_html=True)

    if latest_df.empty:
        st.info("No telemetry available to execute diagnostic correlation.")
        return

    latest = latest_df.iloc[-1]
    engine = DiagnosisEngine()

    gw_lat = None
    gw_loss = 0.0
    if not probes_df.empty:
        gw_rows = probes_df[probes_df["target_name"] == "gateway"]
        if not gw_rows.empty:
            gw_lat = gw_rows.iloc[0]["latency_avg_ms"]
            gw_loss = gw_rows.iloc[0]["packet_loss_pct"]

    # Action Button
    st.button("Run Live Diagnostic Evaluation", use_container_width=True)

    report = engine.diagnose(
        timestamp_iso=latest.get("timestamp"),
        latency_ms=latest.get("latency_ms"),
        jitter_ms=latest.get("jitter_ms"),
        packet_loss_pct=latest.get("packet_loss_pct", 0.0),
        utilization_pct=latest.get("estimated_utilization_pct"),
        gateway_latency_ms=gw_lat,
        gateway_loss_pct=gw_loss
    )

    pri = report.primary_hypothesis
    badge_style = "badge-live" if pri.evidence_strength == "LOW" else ("badge-warning" if pri.evidence_strength == "MEDIUM" else "badge-critical")

    # Primary Diagnosis Card
    st.markdown(f"""
    <div class="kpi-card" style="border-left: 4px solid #71C9CE; margin-top:16px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div class="kpi-label" style="font-size:13px;">Primary Diagnostic Hypothesis</div>
            <span class="status-badge {badge_style}">Evidence Strength: {pri.evidence_strength}</span>
        </div>
        <div style="font-size:22px; font-weight:700; color:#E3FDFD; margin-top:6px;">{pri.cause}</div>
        <div style="color:#A6E3E9; font-size:13px; margin-top:4px;">Confidence Metric: {pri.confidence_score * 100:.0f}%</div>
    </div>
    """, unsafe_allow_html=True)

    # Cited Supporting Evidence
    st.markdown('<div class="section-title">Supporting Telemetry Evidence</div>', unsafe_allow_html=True)
    if pri.evidence_items:
        for ev in pri.evidence_items:
            st.markdown(f"""
            <div class="timeline-item">
                <span style="color:#E3FDFD; font-weight:500;">{ev}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.write("No adverse physical or protocol symptoms observed.")

    if pri.recommended_action:
        st.info(f"Recommended Engineer Action: {pri.recommended_action}")

    # Competing Hypotheses Ranking Table
    st.markdown('<div class="section-title">Ranked Competing Hypotheses</div>', unsafe_allow_html=True)
    comp_rows = []
    for h in report.competing_hypotheses:
        comp_rows.append({
            "Hypothesis / Possible Cause": h.cause,
            "Evidence Strength": h.evidence_strength,
            "Confidence": f"{h.confidence_score * 100:.0f}%",
            "Key Observation": h.evidence_items[0] if h.evidence_items else (h.counter_evidence[0] if h.counter_evidence else "Nominal bounds"),
            "Action": h.recommended_action
        })

    st.dataframe(pd.DataFrame(comp_rows), use_container_width=True, hide_index=True)
