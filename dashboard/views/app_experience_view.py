"""Page 10: Estimated Application Experience View."""

import pandas as pd
import streamlit as st
from src.experience.application_experience import ApplicationExperienceEngine


def render_app_experience(latest_df: pd.DataFrame):
    st.markdown('<div class="section-title">PAGE 10 — ESTIMATED APPLICATION EXPERIENCE</div>', unsafe_allow_html=True)

    if latest_df.empty:
        st.info("No telemetry available to assess application experience.")
        return

    latest = latest_df.iloc[-1]
    engine = ApplicationExperienceEngine()

    rep = engine.evaluate(
        timestamp_iso=latest.get("timestamp"),
        latency_ms=latest.get("latency_ms"),
        jitter_ms=latest.get("jitter_ms"),
        packet_loss_pct=latest.get("packet_loss_pct", 0.0),
        download_mbps=latest.get("download_mbps", 0.0),
        upload_mbps=latest.get("upload_mbps", 0.0)
    )

    def get_badge(score: str) -> str:
        if score == "EXCELLENT":
            return '<span class="status-badge badge-live">EXCELLENT</span>'
        elif score == "GOOD":
            return '<span class="status-badge badge-live" style="background:rgba(166,227,233,0.2);">GOOD</span>'
        elif score == "FAIR":
            return '<span class="status-badge badge-warning">FAIR</span>'
        else:
            return '<span class="status-badge badge-critical">POOR</span>'

    # App Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Video Calling (Teams/Meet)</div>
            <div style="margin: 8px 0;">{get_badge(rep.video_call_score)}</div>
            <div class="kpi-subtext">Requires <100ms lat, <20ms jitter</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Online Competitive Gaming</div>
            <div style="margin: 8px 0;">{get_badge(rep.gaming_score)}</div>
            <div class="kpi-subtext">Requires <50ms lat, <10ms jitter</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Web Browsing & Streaming</div>
            <div style="margin: 8px 0;">{get_badge(rep.web_browsing_score)}</div>
            <div class="kpi-subtext">Requires <150ms lat, <3% loss</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Bulk File Transfers</div>
            <div style="margin: 8px 0;">{get_badge(rep.file_transfer_score)}</div>
            <div class="kpi-subtext">Requires sustained throughput</div>
        </div>
        """, unsafe_allow_html=True)

    # Limiting Factor Summary
    st.markdown('<div class="section-title">Current Quality of Service Bottleneck Assessment</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background:rgba(17,32,45,0.7); padding:16px 20px; border-radius:10px; border-left:4px solid #71C9CE;">
        <div style="color:#A6E3E9; font-size:12px; text-transform:uppercase;">Primary Limiting Factor</div>
        <div style="font-size:18px; font-weight:600; color:#E3FDFD; margin-top:4px;">{rep.primary_limiting_factor}</div>
        <div style="color:#6C8E99; font-size:12px; margin-top:6px;">
            Note: This evaluation is an empirical estimate computed from physical link telemetry (RTT, IPDV, frame loss, throughput), not deep packet inspection.
        </div>
    </div>
    """, unsafe_allow_html=True)
