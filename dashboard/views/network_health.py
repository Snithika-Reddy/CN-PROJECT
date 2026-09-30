"""Page 2: Network Health & Stability Score View."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from src.analytics.health_score import HealthScoreCalculator


def render_network_health(latest_df: pd.DataFrame):
    st.markdown('<div class="section-title">PAGE 2 — NETWORK HEALTH & STABILITY DEEP DIVE</div>', unsafe_allow_html=True)

    if latest_df.empty:
        st.info("No telemetry available to compute health indices.")
        return

    latest = latest_df.iloc[-1]
    health = latest.get("health_score", 100.0)
    stability = latest.get("stability_score", 100.0)

    # Top Overview Cards
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div class="kpi-card" style="border-left: 4px solid #71C9CE;">
            <div class="kpi-label">Current Network Health Score</div>
            <div class="kpi-value">{health:.1f} <span style="font-size:16px; color:#A6E3E9;">/ 100</span></div>
            <div class="kpi-subtext">Answers: <em>'How good is the network right now?'</em></div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card" style="border-left: 4px solid #CBF1F5;">
            <div class="kpi-label">Current Network Stability Score</div>
            <div class="kpi-value">{stability:.1f} <span style="font-size:16px; color:#A6E3E9;">/ 100</span></div>
            <div class="kpi-subtext">Answers: <em>'How consistently does it behave over time?'</em></div>
        </div>
        """, unsafe_allow_html=True)

    # Sub-component Breakdown
    st.markdown('<div class="section-title">Transparent Health Formula & Component Weights</div>', unsafe_allow_html=True)
    calc = HealthScoreCalculator()
    eval_res = calc.evaluate(
        latency_ms=latest.get("latency_ms"),
        jitter_ms=latest.get("jitter_ms"),
        packet_loss_pct=latest.get("packet_loss_pct", 0.0),
        estimated_utilization_pct=latest.get("estimated_utilization_pct"),
        upload_mbps=latest.get("upload_mbps", 0.0),
        download_mbps=latest.get("download_mbps", 0.0),
        stability_score=stability
    )

    sub_cols = st.columns(6)
    for col, (sub_name, sub_val) in zip(sub_cols, eval_res.sub_scores.items()):
        weight_pct = int(eval_res.weights_applied.get(sub_name, 0.0) * 100)
        with col:
            st.markdown(f"""
            <div class="kpi-card" style="padding:10px 14px;">
                <div class="kpi-label" style="font-size:10px;">{sub_name.upper()} ({weight_pct}%)</div>
                <div class="kpi-value" style="font-size:20px;">{sub_val:.1f}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background:rgba(17,32,45,0.7); padding:12px 18px; border-radius:8px; border-left:3px solid #71C9CE; margin-top:8px;">
        <span style="color:#71C9CE; font-weight:600;">Diagnosis Summary:</span>
        <span style="color:#E3FDFD;"> {eval_res.explanation}</span>
    </div>
    """, unsafe_allow_html=True)

    # Health & Stability Longitudinal Trend
    st.markdown('<div class="section-title">Health vs. Stability Longitudinal Trend</div>', unsafe_allow_html=True)
    fig_hs = go.Figure()
    fig_hs.add_trace(go.Scatter(
        x=latest_df["timestamp"],
        y=latest_df["health_score"],
        name="Health Score (0-100)",
        line=dict(color="#71C9CE", width=2.5)
    ))
    fig_hs.add_trace(go.Scatter(
        x=latest_df["timestamp"],
        y=latest_df["stability_score"],
        name="Stability Score (0-100)",
        line=dict(color="#CBF1F5", width=2, dash="dash")
    ))
    fig_hs.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(17,32,45,0.5)",
        margin=dict(l=10, r=10, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=320,
        yaxis=dict(range=[0, 105], showgrid=True, gridcolor="rgba(113,201,206,0.1)", title="Score")
    )
    st.plotly_chart(fig_hs, use_container_width=True)
