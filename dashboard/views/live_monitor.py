"""Page 1: Live Telemetry Monitor View."""

from datetime import datetime, timezone
import time
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def render_live_monitor(latest_df: pd.DataFrame, probes_df: pd.DataFrame, active_state: dict | None = None):
    st.markdown('<div class="section-title">PAGE 1 — REAL-TIME TELEMETRY MONITOR</div>', unsafe_allow_html=True)

    if latest_df.empty:
        st.info("No telemetry collected yet. Click 'Collect Sample' or ensure collector service is active.")
        return

    latest = latest_df.iloc[-1]
    epoch_time = latest.get("epoch_time", time.time())
    now_epoch = time.time()
    seconds_ago = round(max(0.0, now_epoch - epoch_time), 1)

    freshness_class = "badge-live" if seconds_ago <= 10.0 else "badge-warning"
    freshness_text = f"LIVE ({seconds_ago}s ago)" if seconds_ago <= 10.0 else f"STALE ({seconds_ago}s ago)"

    mode = latest.get("monitoring_mode", "NORMAL")
    mode_class = "badge-live" if mode == "NORMAL" else ("badge-warning" if mode == "WARNING" else "badge-critical")

    # Header Status Bar
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(17,32,45,0.7); padding:10px 16px; border-radius:8px; border:1px solid rgba(113,201,206,0.2); margin-bottom:16px;">
        <div>
            <span style="color:#A6E3E9; font-weight:600;">Monitored Interface:</span> <span style="color:#E3FDFD; font-weight:700;">{latest.get('interface_name', 'Wi-Fi')}</span>
        </div>
        <div>
            <span class="status-badge {mode_class}">MODE: {mode}</span>
            <span class="status-badge {freshness_class}" style="margin-left:8px;">{freshness_text}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 8-Card KPI Matrix
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Download Throughput</div>
            <div class="kpi-value">{latest.get('download_mbps', 0.0):.2f} <span style="font-size:14px; color:#A6E3E9;">Mbps</span></div>
            <div class="kpi-subtext">Rx Rate: {latest.get('packets_recv_per_sec', 0.0):.0f} pps</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Upload Throughput</div>
            <div class="kpi-value">{latest.get('upload_mbps', 0.0):.2f} <span style="font-size:14px; color:#A6E3E9;">Mbps</span></div>
            <div class="kpi-subtext">Tx Rate: {latest.get('packets_sent_per_sec', 0.0):.0f} pps</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        lat = latest.get("latency_ms")
        lat_str = f"{lat:.1f}" if pd.notnull(lat) else "N/A"
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Round-Trip Latency</div>
            <div class="kpi-value">{lat_str} <span style="font-size:14px; color:#A6E3E9;">ms</span></div>
            <div class="kpi-subtext">Internet Target (8.8.8.8)</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        jit = latest.get("jitter_ms")
        jit_str = f"{jit:.1f}" if pd.notnull(jit) else "N/A"
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">RFC 3550 Jitter</div>
            <div class="kpi-value">{jit_str} <span style="font-size:14px; color:#A6E3E9;">ms</span></div>
            <div class="kpi-subtext">Delay Variance IPDV</div>
        </div>
        """, unsafe_allow_html=True)

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        loss = latest.get("packet_loss_pct", 0.0)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Rolling Packet Loss</div>
            <div class="kpi-value">{loss:.1f} <span style="font-size:14px; color:#A6E3E9;">%</span></div>
            <div class="kpi-subtext">Multi-Probe Window</div>
        </div>
        """, unsafe_allow_html=True)
    with c6:
        util = latest.get("estimated_utilization_pct")
        util_str = f"{util:.1f}%" if pd.notnull(util) else "NULL (Speed N/A)"
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Est. Interface Utilization</div>
            <div class="kpi-value" style="font-size:22px;">{util_str}</div>
            <div class="kpi-subtext">Hardware Capacity Saturation</div>
        </div>
        """, unsafe_allow_html=True)
    with c7:
        health = latest.get("health_score", 100.0)
        h_color = "#71C9CE" if health >= 75 else ("#F9C74F" if health >= 50 else "#F94144")
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Network Health Score</div>
            <div class="kpi-value" style="color:{h_color};">{health:.1f} <span style="font-size:14px; color:#A6E3E9;">/100</span></div>
            <div class="kpi-subtext">Explainable Weighted Index</div>
        </div>
        """, unsafe_allow_html=True)
    with c8:
        stab = latest.get("stability_score", 100.0)
        s_color = "#71C9CE" if stab >= 70 else ("#F9C74F" if stab >= 50 else "#F94144")
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Network Stability Score</div>
            <div class="kpi-value" style="color:{s_color};">{stab:.1f} <span style="font-size:14px; color:#A6E3E9;">/100</span></div>
            <div class="kpi-subtext">Longitudinal Variance Index</div>
        </div>
        """, unsafe_allow_html=True)

    # Real-Time Telemetry Streaming Charts
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown('<div class="section-title">Throughput Streaming (Mbps)</div>', unsafe_allow_html=True)
        fig_tput = go.Figure()
        fig_tput.add_trace(go.Scatter(
            x=latest_df["timestamp"],
            y=latest_df["download_mbps"],
            name="Download (Mbps)",
            mode="lines+markers",
            line=dict(color="#71C9CE", width=2.5),
            fill="tozeroy",
            fillcolor="rgba(113, 201, 206, 0.15)"
        ))
        fig_tput.add_trace(go.Scatter(
            x=latest_df["timestamp"],
            y=latest_df["upload_mbps"],
            name="Upload (Mbps)",
            mode="lines+markers",
            line=dict(color="#A6E3E9", width=2, dash="dot"),
            fill="tozeroy",
            fillcolor="rgba(166, 227, 233, 0.08)"
        ))
        fig_tput.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(17,32,45,0.5)",
            margin=dict(l=10, r=10, t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=280,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(113,201,206,0.1)", title="Mbps")
        )
        st.plotly_chart(fig_tput, use_container_width=True)

    with col_chart2:
        st.markdown('<div class="section-title">Latency & Jitter (ms)</div>', unsafe_allow_html=True)
        fig_lat = go.Figure()
        fig_lat.add_trace(go.Scatter(
            x=latest_df["timestamp"],
            y=latest_df["latency_ms"],
            name="Latency RTT (ms)",
            mode="lines+markers",
            line=dict(color="#CBF1F5", width=2)
        ))
        fig_lat.add_trace(go.Scatter(
            x=latest_df["timestamp"],
            y=latest_df["jitter_ms"],
            name="Jitter (ms)",
            mode="lines",
            line=dict(color="#F9C74F", width=2, dash="dash")
        ))
        fig_lat.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(17,32,45,0.5)",
            margin=dict(l=10, r=10, t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=280,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(113,201,206,0.1)", title="ms")
        )
        st.plotly_chart(fig_lat, use_container_width=True)

    # Multi-Target Probes Matrix
    if not probes_df.empty:
        st.markdown('<div class="section-title">Target Disaggregation (Gateway vs Public DNS)</div>', unsafe_allow_html=True)
        recent_probes = probes_df.head(6)[["timestamp", "target_name", "target_host", "latency_avg_ms", "jitter_ms", "packet_loss_pct", "status"]]
        st.dataframe(recent_probes, use_container_width=True, hide_index=True)
