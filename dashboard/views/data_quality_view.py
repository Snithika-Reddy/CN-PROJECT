"""Page 12: Data Quality & Self-Monitoring Health View."""

import os
import time
import pandas as pd
import psutil
import streamlit as st
from src.collectors.system_collector import SystemCollector


def render_data_quality(metrics_df: pd.DataFrame, db_path: str = "database/network_monitor.db"):
    st.markdown('<div class="section-title">PAGE 12 — DATA QUALITY & SELF-MONITORING INTEGRITY</div>', unsafe_allow_html=True)

    sys_col = SystemCollector(db_path=db_path)
    sys_metrics = sys_col.sample()

    total_samples = len(metrics_df)
    missing_lat = metrics_df["latency_ms"].isna().sum() if "latency_ms" in metrics_df else 0
    resets_detected = (metrics_df["data_quality_flag"] == "COUNTER_RESET").sum() if "data_quality_flag" in metrics_df else 0

    latest_time = metrics_df["epoch_time"].iloc[-1] if not metrics_df.empty else time.time()
    stale_delta = time.time() - latest_time
    is_stale = stale_delta > 15.0

    if is_stale:
        st.error(f"Monitoring data may be stale! Last collection took place {stale_delta:.1f} seconds ago.")
    else:
        st.success(f"Self-monitoring system operating nominally. Telemetry fresh ({stale_delta:.1f}s ago).")

    # Metrics Quality Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Samples Collected</div>
            <div class="kpi-value">{total_samples}</div>
            <div class="kpi-subtext">Total database records</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Missing / Null Latency</div>
            <div class="kpi-value">{missing_lat}</div>
            <div class="kpi-subtext">Probe dropouts or timeouts</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">NIC Counter Resets</div>
            <div class="kpi-value">{resets_detected}</div>
            <div class="kpi-subtext">Rollover / Reconnect events</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">SQLite Storage Size</div>
            <div class="kpi-value">{sys_metrics.db_size_kb:.1f} <span style="font-size:14px; color:#4C3C6E;">KB</span></div>
            <div class="kpi-subtext">Authoritative WAL Database</div>
        </div>
        """, unsafe_allow_html=True)

    # Process Resource Footprint
    st.markdown('<div class="section-title">NetIntel Process Footprint & Overhead</div>', unsafe_allow_html=True)
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Host CPU Utilization</div>
            <div class="kpi-value">{sys_metrics.cpu_percent:.1f}%</div>
            <div class="kpi-subtext">Total host machine load</div>
        </div>
        """, unsafe_allow_html=True)
    with p2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Process Memory Footprint</div>
            <div class="kpi-value">{sys_metrics.memory_used_mb:.1f} <span style="font-size:14px; color:#4C3C6E;">MB</span></div>
            <div class="kpi-subtext">Lightweight RSS RAM</div>
        </div>
        """, unsafe_allow_html=True)
    with p3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Host Virtual Memory</div>
            <div class="kpi-value">{sys_metrics.memory_percent:.1f}%</div>
            <div class="kpi-subtext">Total system commit load</div>
        </div>
        """, unsafe_allow_html=True)
