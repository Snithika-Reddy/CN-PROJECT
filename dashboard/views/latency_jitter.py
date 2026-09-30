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
            <div class="kpi-value">{p50_lat:.1f} <span style="font-size:14px; color:#4C3C6E;">ms</span></div>
            <div class="kpi-subtext">Nominal round-trip delay</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">95th Percentile Latency</div>
            <div class="kpi-value">{p95_lat:.1f} <span style="font-size:14px; color:#4C3C6E;">ms</span></div>
            <div class="kpi-subtext">Tail latency spike bound</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">95th Percentile Jitter</div>
            <div class="kpi-value">{p95_jit:.1f} <span style="font-size:14px; color:#4C3C6E;">ms</span></div>
            <div class="kpi-subtext">RFC 3550 Delay Variation</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Average Packet Loss</div>
            <div class="kpi-value">{loss_mean:.2f} <span style="font-size:14px; color:#4C3C6E;">%</span></div>
            <div class="kpi-subtext">Multi-probe transmission loss</div>
        </div>
        """, unsafe_allow_html=True)

    from dashboard.styles import apply_plotly_theme

    # Multi-Target Comparison Chart
    if not probes_df.empty:
        st.markdown('<div class="section-title">Hop Comparison: Default Gateway vs. Public DNS Targets</div>', unsafe_allow_html=True)
        fig_targets = go.Figure()
        colors = ["#7B32A8", "#2563EB", "#059669", "#D97706"]
        for idx, target in enumerate(probes_df["target_name"].unique()):
            t_df = probes_df[probes_df["target_name"] == target]
            fig_targets.add_trace(go.Scatter(
                x=t_df["timestamp"],
                y=t_df["latency_avg_ms"],
                name=f"{target} ({t_df['target_host'].iloc[0]})",
                mode="lines+markers",
                line=dict(color=colors[idx % len(colors)], width=2.5)
            ))
        apply_plotly_theme(fig_targets)
        fig_targets.update_layout(height=300, yaxis=dict(title="RTT Latency (ms)"))
        st.plotly_chart(fig_targets, use_container_width=True)

    # Jitter & Packet Loss Distribution
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-title">Latency Distribution Histogram</div>', unsafe_allow_html=True)
        fig_hist = go.Figure(data=[go.Histogram(
            x=lat_clean,
            marker_color="#CDAAEA",
            marker_line=dict(color="#6A2D94", width=1.5),
            opacity=0.85,
            nbinsx=25
        )])
        apply_plotly_theme(fig_hist)
        fig_hist.update_layout(height=260, xaxis=dict(title="Latency (ms)"), yaxis=dict(title="Frequency"))
        st.plotly_chart(fig_hist, use_container_width=True)

    with col2:
        st.markdown('<div class="section-title">Rolling Packet Loss Trend (%)</div>', unsafe_allow_html=True)
        fig_loss = go.Figure()
        fig_loss.add_trace(go.Scatter(
            x=metrics_df["timestamp"],
            y=metrics_df["packet_loss_pct"],
            mode="lines+markers",
            line=dict(color="#DC2626", width=2),
            fill="tozeroy",
            fillcolor="rgba(220, 38, 38, 0.15)"
        ))
        apply_plotly_theme(fig_loss)
        fig_loss.update_layout(
            height=260,
            yaxis=dict(range=[0, max(10, metrics_df["packet_loss_pct"].max() + 2)], title="Loss %")
        )
        st.plotly_chart(fig_loss, use_container_width=True)
