"""Page 6: Anomaly Detection Log & Engine View."""

import pandas as pd
import plotly.express as px
import streamlit as st


def render_anomalies(anomalies_df: pd.DataFrame, is_ml_active: bool = False):
    st.markdown('<div class="section-title">PAGE 6 — ANOMALY DETECTION ENGINE & INCIDENT LOG</div>', unsafe_allow_html=True)

    mode_label = "ML Mode (Isolation Forest / Mahalanobis)" if is_ml_active else "Statistical Mode (Z-Score & IQR Tukey Fences)"
    st.markdown(f"""
    <div style="margin-bottom:16px;">
        <span style="color:#4C3C6E; font-weight:700;">Active Detection Mode:</span>
        <span class="status-badge badge-live" style="margin-left:8px;">{mode_label}</span>
    </div>
    """, unsafe_allow_html=True)

    if anomalies_df.empty:
        st.success("No anomalies detected in the evaluated telemetry buffer. Network behavior remains within expected statistical thresholds.")
        return

    # Cards
    c1, c2, c3, c4 = st.columns(4)
    crit_count = (anomalies_df["severity"] == "CRITICAL").sum() if "severity" in anomalies_df else 0
    high_count = (anomalies_df["severity"] == "HIGH").sum() if "severity" in anomalies_df else 0

    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Anomalies Flagged</div>
            <div class="kpi-value">{len(anomalies_df)}</div>
            <div class="kpi-subtext">Outlier events logged</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Critical Severity</div>
            <div class="kpi-value" style="color:#DC2626;">{crit_count}</div>
            <div class="kpi-subtext">Severe degradation spikes</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">High Severity</div>
            <div class="kpi-value" style="color:#D97706;">{high_count}</div>
            <div class="kpi-subtext">Substantial outlier deviations</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        method_counts = anomalies_df["detection_method"].nunique() if "detection_method" in anomalies_df else 1
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Algorithms Active</div>
            <div class="kpi-value">{method_counts}</div>
            <div class="kpi-subtext">Z-Score, IQR, CUSUM</div>
        </div>
        """, unsafe_allow_html=True)

    # Anomaly Log Table
    st.markdown('<div class="section-title">Chronological Anomaly Log</div>', unsafe_allow_html=True)
    display_df = anomalies_df.head(25)[[
        "timestamp", "metric_name", "observed_value", "baseline_expected",
        "deviation_pct", "severity", "detection_method", "details"
    ]].copy()
    st.dataframe(display_df, use_container_width=True, hide_index=True)
