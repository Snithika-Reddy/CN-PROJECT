"""Page 5: Empirical Baseline Engine View."""

import pandas as pd
import streamlit as st
from src.analytics.baseline import BaselineEngine


def render_baseline(metrics_df: pd.DataFrame):
    st.markdown('<div class="section-title">PAGE 5 — EMPIRICAL STATISTICAL BASELINES</div>', unsafe_allow_html=True)

    engine = BaselineEngine(min_samples_required=30, rolling_window_samples=120)
    baselines = engine.compute_all_baselines(metrics_df)

    sample_count = len(metrics_df)
    if sample_count < 30:
        st.warning(
            f"Insufficient historical data to establish a reliable baseline. "
            f"Currently captured {sample_count} of 30 required samples. "
            f"Baseline engine refuses to fabricate hardcoded universal normal values."
        )
        return

    st.success(f"Empirical baselines active across {sample_count} real network telemetry measurements.")

    latest = metrics_df.iloc[-1]
    rows = []
    for col, base in baselines.items():
        curr_val = latest.get(col)
        curr_str = f"{curr_val:.2f}" if pd.notnull(curr_val) else "N/A"
        if base.is_established:
            dev = ((curr_val - base.median) / base.median) * 100.0 if (curr_val is not None and base.median and base.median > 0) else 0.0
            sign = "+" if dev > 0 else ""
            rows.append({
                "Metric": base.metric_name,
                "Sample Count": base.sample_count,
                "Learned Median": f"{base.median:.2f}",
                "Std Dev": f"{base.std_dev:.2f}",
                "Normal Range (IQR Bounds)": f"{base.lower_bound:.2f} — {base.upper_bound:.2f}",
                "Current Measured": curr_str,
                "Current Deviation": f"{sign}{dev:.1f}%",
                "Status": "NOMINAL" if abs(dev) < 50 else ("ELEVATED" if dev > 0 else "REDUCED")
            })

    b_df = pd.DataFrame(rows)
    st.dataframe(b_df, use_container_width=True, hide_index=True)

    st.markdown("""
    <div style="background:rgba(17,32,45,0.7); padding:14px 18px; border-radius:8px; border-left:3px solid #71C9CE; margin-top:16px;">
        <span style="color:#71C9CE; font-weight:600;">Methodological Integrity:</span>
        <span style="color:#E3FDFD;">
        Baselines use non-parametric median and Interquartile Range (IQR) Tukey fences
        derived exclusively from local hardware and connectivity measurements.
        </span>
    </div>
    """, unsafe_allow_html=True)
