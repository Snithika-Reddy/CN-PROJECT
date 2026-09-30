"""Page 3: Traffic Analytics & Utilization View."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def render_traffic_analytics(df: pd.DataFrame):
    st.markdown('<div class="section-title">PAGE 3 — TRAFFIC ANALYTICS & INTERFACE CAPACITY</div>', unsafe_allow_html=True)

    if df.empty:
        st.info("No traffic telemetry available.")
        return

    latest = df.iloc[-1]
    peak_down = df["download_mbps"].max()
    peak_up = df["upload_mbps"].max()
    total_bytes = (latest.get("bytes_sent", 0) + latest.get("bytes_recv", 0)) / (1024.0 * 1024.0)

    # Top Metric Summary Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Peak Download Observed</div>
            <div class="kpi-value">{peak_down:.2f} <span style="font-size:14px; color:#A6E3E9;">Mbps</span></div>
            <div class="kpi-subtext">Session Maximum</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Peak Upload Observed</div>
            <div class="kpi-value">{peak_up:.2f} <span style="font-size:14px; color:#A6E3E9;">Mbps</span></div>
            <div class="kpi-subtext">Session Maximum</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Cumulative Data Volume</div>
            <div class="kpi-value">{total_bytes:.1f} <span style="font-size:14px; color:#A6E3E9;">MB</span></div>
            <div class="kpi-subtext">Tx + Rx Transferred</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        avg_pps = (df["packets_sent_per_sec"].mean() + df["packets_recv_per_sec"].mean())
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Mean Packet Processing Rate</div>
            <div class="kpi-value">{avg_pps:.0f} <span style="font-size:14px; color:#A6E3E9;">PPS</span></div>
            <div class="kpi-subtext">Egress + Ingress Frame Rate</div>
        </div>
        """, unsafe_allow_html=True)

    # Packet Rates Chart
    st.markdown('<div class="section-title">Packet Processing Rate (PPS)</div>', unsafe_allow_html=True)
    fig_pps = go.Figure()
    fig_pps.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["packets_recv_per_sec"],
        name="Packets Recv / Sec",
        line=dict(color="#71C9CE", width=2)
    ))
    fig_pps.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["packets_sent_per_sec"],
        name="Packets Sent / Sec",
        line=dict(color="#A6E3E9", width=2, dash="dot")
    ))
    fig_pps.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(17,32,45,0.5)",
        margin=dict(l=10, r=10, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=280,
        yaxis=dict(title="Packets / Sec", showgrid=True, gridcolor="rgba(113,201,206,0.1)")
    )
    st.plotly_chart(fig_pps, use_container_width=True)

    # Interface Utilization
    st.markdown('<div class="section-title">Estimated Interface Hardware Utilization (%)</div>', unsafe_allow_html=True)
    fig_util = go.Figure()
    fig_util.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["estimated_utilization_pct"],
        name="Estimated Interface Utilization",
        line=dict(color="#CBF1F5", width=2.5),
        fill="tozeroy",
        fillcolor="rgba(203, 241, 245, 0.15)"
    ))
    fig_util.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(17,32,45,0.5)",
        margin=dict(l=10, r=10, t=20, b=20),
        height=260,
        yaxis=dict(range=[0, 100], title="Utilization %", showgrid=True, gridcolor="rgba(113,201,206,0.1)")
    )
    st.plotly_chart(fig_util, use_container_width=True)
