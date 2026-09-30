"""Page 11: Historical Trends, Fingerprinting & SLA Compliance View."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from src.analytics.trends import TrendAnalyzer
from src.analytics.statistics import compute_compliance_rate
from src.storage.csv_exporter import CSVExporter


def render_historical(df: pd.DataFrame):
    st.markdown('<div class="section-title">PAGE 11 — HISTORICAL TRENDS, FINGERPRINT & SLA MONITORING</div>', unsafe_allow_html=True)

    if df.empty:
        st.info("Insufficient telemetry to compute longitudinal trends.")
        return

    analyzer = TrendAnalyzer(min_samples_for_fingerprint=30)
    fp = analyzer.extract_fingerprint(df)

    # 1. SLA / Reliability Compliance Cards
    st.markdown('<div class="section-title">SLA & Reliability Compliance</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)

    lat_sla = compute_compliance_rate(df["latency_ms"], max_threshold=50.0)
    loss_sla = compute_compliance_rate(df["packet_loss_pct"], max_threshold=1.0)
    util_sla = compute_compliance_rate(df["estimated_utilization_pct"], max_threshold=80.0)

    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Latency SLA (< 50ms)</div>
            <div class="kpi-value">{lat_sla:.1f}%</div>
            <div class="kpi-subtext">Compliant probe samples</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Packet Loss SLA (<= 1%)</div>
            <div class="kpi-value">{loss_sla:.1f}%</div>
            <div class="kpi-subtext">Zero/low loss compliance</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Capacity Headroom (<= 80%)</div>
            <div class="kpi-value">{util_sla:.1f}%</div>
            <div class="kpi-subtext">Non-congested link compliance</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Historical Samples Evaluated</div>
            <div class="kpi-value">{len(df)}</div>
            <div class="kpi-subtext">Authoritative SQLite dataset</div>
        </div>
        """, unsafe_allow_html=True)

    # 2. Empirical Network Fingerprint
    st.markdown('<div class="section-title">Empirical Network Fingerprint</div>', unsafe_allow_html=True)
    if not fp.is_available:
        st.warning(fp.summary_message)
    else:
        st.markdown(f"""
        <div class="kpi-card" style="margin-bottom:16px; border-left: 5px solid #CDAAEA;">
            <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap: 14px;">
                <div><span style="color:#4C3C6E; font-weight:600;">Typical Latency:</span> <b style="color:#15112B;">{fp.typical_latency_ms} ms</b></div>
                <div><span style="color:#4C3C6E; font-weight:600;">Typical Jitter:</span> <b style="color:#15112B;">{fp.typical_jitter_ms} ms</b></div>
                <div><span style="color:#4C3C6E; font-weight:600;">Typical Loss:</span> <b style="color:#15112B;">{fp.typical_packet_loss_pct}%</b></div>
                <div><span style="color:#4C3C6E; font-weight:600;">Typical Download:</span> <b style="color:#15112B;">{fp.typical_download_mbps} Mbps</b></div>
                <div><span style="color:#4C3C6E; font-weight:600;">Typical Upload:</span> <b style="color:#15112B;">{fp.typical_upload_mbps} Mbps</b></div>
                <div><span style="color:#4C3C6E; font-weight:600;">Most Unstable Window:</span> <b style="color:#763B9E;">{fp.most_unstable_period}</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 3. CSV Export Action
    st.markdown('<div class="section-title">Telemetry Data Export</div>', unsafe_allow_html=True)
    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Current Session CSV",
            data=csv_data,
            file_name="netintel_session_telemetry.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col_exp2:
        st.caption("Power BI live CSV files are maintained continuously in `data/exports/network_metrics.csv`.")
