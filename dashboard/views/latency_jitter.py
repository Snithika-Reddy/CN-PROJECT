"""Page 4: Latency, RFC 3550 Jitter, and Packet Loss View."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def render_latency_jitter(metrics_df: pd.DataFrame, probes_df: pd.DataFrame):
    st.markdown('<div class="section-title">PAGE 4 — LATENCY, RFC 3550 JITTER & PACKET LOSS</div>', unsafe_allow_html=True)

    if metrics_df.empty:
        st.info("No latency telemetry recorded yet.")
        return

    lat_clean = metrics_df["latency_ms"].dropna()
    jit_clean = metrics_df["jitter_ms"].dropna()

    p50_lat = np.percentile(lat_clean, 50) if not lat_clean.empty else 0.0
    p95_lat = np.percentile(lat_clean, 95) if not lat_clean.empty else 0.0
    p95_jit = np.percentile(jit_clean, 95) if not jit_clean.empty else 0.0
    loss_mean = metrics_df["packet_loss_pct"].mean()

    # Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Median Latency (p50)</div>
            <div class="kpi-value">{p50_lat:.1f} <span style="font-size:14px; color:#A6E3E9;">ms</span></div>
            <div class="kpi-subtext">Nominal round-trip delay</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">95th Percentile Latency</div>
            <div class="kpi-value">{p95_lat:.1f} <span style="font-size:14px; color:#A6E3E9;">ms</span></div>
            <div class="kpi-subtext">Tail latency spike bound</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">95th Percentile Jitter</div>
            <div class="kpi-value">{p95_jit:.1f} <span style="font-size:14px; color:#A6E3E9;">ms</span></div>
            <div class="kpi-subtext">RFC 3550 Delay Variation</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Average Packet Loss</div>
            <div class="kpi-value">{loss_mean:.2f} <span style="font-size:14px; color:#A6E3E9;">%</span></div>
            <div class="kpi-subtext">Multi-probe transmission loss</div>
        </div>
        """, unsafe_allow_html=True)

    # Multi-Target Comparison Chart
    if not probes_df.empty:
        st.markdown('<div class="section-title">Hop Comparison: Default Gateway vs. Public DNS Targets</div>', unsafe_allow_html=True)
        fig_targets = go.Figure()
        for target in probes_df["target_name"].unique():
            t_df = probes_df[probes_df["target_name"] == target]
            fig_targets.add_trace(go.Scatter(
                x=t_df["timestamp"],
                y=t_df["latency_avg_ms"],
                name=f"{target} ({t_df['target_host'].iloc[0]})",
                mode="lines+markers"
            ))
        fig_targets.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(17,32,45,0.5)",
            margin=dict(l=10, r=10, t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=300,
            yaxis=dict(title="RTT Latency (ms)", showgrid=True, gridcolor="rgba(113,201,206,0.1)")
        )
        st.plotly_chart(fig_targets, use_container_width=True)

    # Jitter & Packet Loss Distribution
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-title">Latency Distribution Histogram</div>', unsafe_allow_html=True)
        fig_hist = go.Figure(data=[go.Histogram(
            x=lat_clean,
            marker_color="#71C9CE",
            opacity=0.8,
            nbinsx=25
        )])
        fig_hist.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(17,32,45,0.5)",
            margin=dict(l=10, r=10, t=20, b=20),
            height=260,
            xaxis=dict(title="Latency (ms)"),
            yaxis=dict(title="Frequency", showgrid=True, gridcolor="rgba(113,201,206,0.1)")
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    with col2:
        st.markdown('<div class="section-title">Rolling Packet Loss Trend (%)</div>', unsafe_allow_html=True)
        fig_loss = go.Figure()
        fig_loss.add_trace(go.Scatter(
            x=metrics_df["timestamp"],
            y=metrics_df["packet_loss_pct"],
            mode="lines+markers",
            line=dict(color="#F94144", width=2),
            fill="tozeroy",
            fillcolor="rgba(249, 65, 68, 0.15)"
        ))
        fig_loss.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(17,32,45,0.5)",
            margin=dict(l=10, r=10, t=20, b=20),
            height=260,
            yaxis=dict(range=[0, max(10, metrics_df["packet_loss_pct"].max() + 2)], title="Loss %", showgrid=True, gridcolor="rgba(113,201,206,0.1)")
        )
        st.plotly_chart(fig_loss, use_container_width=True)
