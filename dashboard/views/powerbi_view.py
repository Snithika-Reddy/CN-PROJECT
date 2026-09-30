"""Power BI Integration and Live Telemetry Command Center View."""

from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.powerbi.exporter import PowerBIExporter
from src.powerbi.streaming import PowerBIStreamer
from src.powerbi.api_server import PowerBIAPIServer
from src.storage.database import DatabaseManager


# Global API server instance handle in session state
if "pbi_api_server" not in st.session_state:
    st.session_state.pbi_api_server = None
    st.session_state.pbi_api_running = False


def render_powerbi_view(db: DatabaseManager = None, service=None):
    st.markdown('<div class="section-title">MICROSOFT POWER BI COMMAND CENTER & LIVE PIPELINE</div>', unsafe_allow_html=True)

    if db is None:
        db = DatabaseManager()

    export_dir = Path("data/exports").resolve()
    star_dir = export_dir / "star_schema"

    # --- Top Hero Status & Architecture ---
    col_arch, col_stat = st.columns([2, 1])
    with col_arch:
        st.markdown("""
        <div style="background:rgba(17,32,45,0.85); border:1px solid rgba(113,201,206,0.3); border-radius:12px; padding:18px;">
            <div style="font-size:16px; font-weight:700; color:#E3FDFD; margin-bottom:6px;">
                🚀 Multi-Tier Live Power BI Ecosystem
            </div>
            <div style="color:#A6E3E9; font-size:13px; line-height:1.5;">
                NetIntel streams high-velocity network metrics into <b>Microsoft Power BI</b> via 4 enterprise integration modes:
                <b>(1) Direct Python Script Connector</b> for zero-config Desktop loads, 
                <b>(2) Star Schema Relational Store</b> with Windows Auto-Refresh daemon, 
                <b>(3) Sub-Second Push Datasets</b> for cloud streaming tiles, and 
                <b>(4) Local REST API</b> on port 8080.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_stat:
        # Check SQLite DB counts
        try:
            total_metrics = db.query_df("SELECT COUNT(*) as c FROM network_metrics")["c"].iloc[0]
            total_incidents = db.query_df("SELECT COUNT(*) as c FROM incidents")["c"].iloc[0]
        except Exception:
            total_metrics = 0
            total_incidents = 0

        st.markdown(f"""
        <div style="background:rgba(19,38,52,0.85); border:1px solid rgba(166,227,233,0.25); border-radius:12px; padding:18px; text-align:center;">
            <div style="color:#A6E3E9; font-size:11px; text-transform:uppercase; letter-spacing:1px;">Authoritative Telemetry Store</div>
            <div style="font-size:24px; font-weight:800; color:#71C9CE; margin:4px 0;">{total_metrics:,} Rows</div>
            <div style="color:#CBF1F5; font-size:12px;">Active Incidents: <b>{total_incidents}</b></div>
            <div style="margin-top:6px;"><span class="status-badge badge-live">SYNC ENGINE READY</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # --- Section 1: Live Interactive Power BI Visuals Preview ---
    st.markdown('<div class="section-title">1. Live Power BI Report Preview (Simulated In-Memory Rendering)</div>', unsafe_allow_html=True)
    st.caption("Visualizes exactly how the Star Schema Fact and Dimension data renders inside Microsoft Power BI Desktop.")

    try:
        metrics_df = db.query_df("SELECT * FROM network_metrics ORDER BY timestamp DESC LIMIT 60")
    except Exception:
        metrics_df = pd.DataFrame()

    if not metrics_df.empty:
        # Top KPI Cards Ribbon
        avg_h = metrics_df["health_score"].mean()
        p95_lat = metrics_df["latency_ms"].quantile(0.95)
        tot_mb = (metrics_df["bytes_sent"].sum() + metrics_df["bytes_recv"].sum()) / 1048576.0
        avg_loss = metrics_df["packet_loss_pct"].mean()

        kpi_c1, kpi_c2, kpi_c3, kpi_c4 = st.columns(4)
        with kpi_c1:
            st.metric("Avg Health Score", f"{avg_h:.1f} / 100", delta=f"{avg_h - 90.0:.1f} vs Target")
        with kpi_c2:
            st.metric("P95 Tail Latency", f"{p95_lat:.1f} ms", delta="-Optimal" if p95_lat <= 50 else "+High Latency")
        with kpi_c3:
            st.metric("Packet Loss Rate", f"{avg_loss:.2f}%", delta="0% Loss SLA" if avg_loss == 0 else "Degraded")
        with kpi_c4:
            st.metric("Data Transferred", f"{tot_mb:.1f} MB", delta="Aggregated")

        # Visual Charts
        ch_c1, ch_c2 = st.columns(2)
        with ch_c1:
            chart_df = metrics_df.sort_values("timestamp")
            fig_lat = px.line(
                chart_df,
                x="timestamp",
                y=["latency_ms", "jitter_ms"],
                title="Power BI Live Line Chart: Latency & Jitter (ms)",
                color_discrete_map={"latency_ms": "#71C9CE", "jitter_ms": "#A78BFA"},
                template="plotly_dark"
            )
            fig_lat.update_layout(
                plot_bgcolor="rgba(11,20,28,0.9)",
                paper_bgcolor="rgba(11,20,28,0.9)",
                margin=dict(l=20, r=20, t=40, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_lat, use_container_width=True)

        with ch_c2:
            fig_bw = px.area(
                chart_df,
                x="timestamp",
                y=["download_mbps", "upload_mbps"],
                title="Power BI Live Area Chart: Ingress & Egress Throughput (Mbps)",
                color_discrete_map={"download_mbps": "#38BDF8", "upload_mbps": "#10B981"},
                template="plotly_dark"
            )
            fig_bw.update_layout(
                plot_bgcolor="rgba(11,20,28,0.9)",
                paper_bgcolor="rgba(11,20,28,0.9)",
                margin=dict(l=20, r=20, t=40, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_bw, use_container_width=True)
    else:
        st.info("No telemetry samples found in database. Click '⚡ Collect Live Sample' in sidebar to seed telemetry.")

    # --- Section 2: Command Plane & One-Click Actions ---
    st.markdown('<div class="section-title">2. Operational Control Plane</div>', unsafe_allow_html=True)

    act_c1, act_c2, act_c3, act_c4 = st.columns(4)

    with act_c1:
        if st.button("🔄 Sync Star Schema Now", type="primary", use_container_width=True):
            with st.spinner("Extracting & exporting Star Schema tables..."):
                exporter = PowerBIExporter(export_dir=str(export_dir))
                counts = exporter.export_from_database(db)
                total_synced = sum(counts.values())
                st.success(f"Synchronized {len(counts)} Star Schema tables ({total_synced:,} total records)!")
                time.sleep(0.5)
                st.rerun()

    with act_c2:
        if st.button("📂 Open Exports Folder", use_container_width=True):
            try:
                subprocess.Popen(["explorer", str(export_dir)])
                st.success(f"Opened: {export_dir}")
            except Exception as exc:
                st.error(f"Could not open explorer: {exc}")

    with act_c3:
        if st.button("🚀 Launch Power BI Desktop", use_container_width=True):
            try:
                subprocess.Popen(["cmd", "/c", "start", "", "PBIDesktopStore.exe"])
                st.success("Launched Microsoft Power BI Desktop!")
            except Exception:
                try:
                    subprocess.Popen(["start", "PBIDesktopStore.exe"], shell=True)
                    st.success("Launched Microsoft Power BI Desktop!")
                except Exception:
                    st.info("Power BI Desktop can be opened from your Windows Start Menu.")

    with act_c4:
        # Local REST API server control
        if not st.session_state.pbi_api_running:
            if st.button("🌐 Start Local REST API (8080)", use_container_width=True):
                server = PowerBIAPIServer(host="127.0.0.1", port=8080, db_manager=db)
                server.start()
                st.session_state.pbi_api_server = server
                st.session_state.pbi_api_running = True
                st.success("API Server listening on http://127.0.0.1:8080")
                time.sleep(0.5)
                st.rerun()
        else:
            if st.button("🛑 Stop REST API Server", use_container_width=True):
                if st.session_state.pbi_api_server:
                    st.session_state.pbi_api_server.stop()
                st.session_state.pbi_api_server = None
                st.session_state.pbi_api_running = False
                st.info("API Server stopped.")
                time.sleep(0.5)
                st.rerun()

    # --- Section 3: Live Power BI Datasets Status Matrix ---
    st.markdown('<div class="section-title">3. Star Schema Entity Catalog & Export Files</div>', unsafe_allow_html=True)

    star_schema_entities = [
        ("FactNetworkMetrics", "FactNetworkMetrics.csv", "Primary telemetry fact table: throughput, latency, loss, health, stability"),
        ("FactLatencyProbes", "FactLatencyProbes.csv", "Multi-target ICMP probe breakdown (Gateway, Google DNS, Cloudflare)"),
        ("FactIncidents", "FactIncidents.csv", "Historical incidents lifecycle, duration, peak degradation, and recovery"),
        ("FactAnomalies", "FactAnomalies.csv", "Detected statistical and ML anomalies with severity and algorithm tags"),
        ("FactApplicationExperience", "FactApplicationExperience.csv", "Quality of service ratings for video calls, gaming, and browsing"),
        ("DimDate", "DimDate.csv", "Calendar dimension with DateKey, Quarter, DayOfWeek, and Weekend flag"),
        ("DimTime", "DimTime.csv", "Time dimension with TimeKey, Hour, Minute, and TimeOfDay period"),
        ("DimInterface", "DimInterface.csv", "Hardware interface specs, MAC addresses, speeds, and wireless flags"),
        ("DimTarget", "DimTarget.csv", "ICMP probe targets catalog with SLA targets and host types")
    ]

    table_rows = []
    for entity_name, filename, desc in star_schema_entities:
        # Check both star_dir and export_dir
        fpath = star_dir / filename
        if not fpath.exists():
            fpath = export_dir / filename

        exists = fpath.exists()
        size_kb = fpath.stat().st_size / 1024.0 if exists else 0.0
        mtime = datetime.fromtimestamp(fpath.stat().st_mtime).strftime("%H:%M:%S") if exists else "N/A"
        row_count = 0
        if exists:
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    row_count = max(0, sum(1 for _ in f) - 1)
            except Exception:
                row_count = 0

        table_rows.append({
            "Power BI Entity": entity_name,
            "CSV File": filename,
            "Records": f"{row_count:,}",
            "File Size": f"{size_kb:.1f} KB",
            "Last Synced": mtime,
            "Relational Role": "Fact Table" if entity_name.startswith("Fact") else "Dimension Table",
            "Status": "READY" if exists and row_count > 0 else "PENDING SYNC"
        })

    st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

    # --- Section 4: Power BI Service Real-Time Streaming Pusher (Mode 3) ---
    st.markdown('<div class="section-title">4. Real-Time Cloud Push Streaming (Power BI Service)</div>', unsafe_allow_html=True)
    with st.expander("⚡ Configure Live Push Dataset URL (Power BI Service API)", expanded=False):
        st.markdown("""
        In **Power BI Service** ([app.powerbi.com](https://app.powerbi.com)), create a **Streaming Dataset &rarr; API**, 
        then copy the **Push URL** and paste it below. NetIntel will push live telemetry samples directly into your cloud dashboard!
        """)
        push_url_input = st.text_input(
            "Power BI Streaming Dataset Push URL:",
            value=os.environ.get("POWERBI_PUSH_URL", ""),
            placeholder="https://api.powerbi.com/beta/..."
        )

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            if st.button("🧪 Send Live Test Telemetry Frame to Power BI Service"):
                if not push_url_input:
                    st.warning("Please paste a valid Power BI Streaming Push URL first.")
                else:
                    streamer = PowerBIStreamer(push_url=push_url_input)
                    test_payload = [{
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "interface_name": "Wi-Fi (NetIntel)",
                        "upload_mbps": 18.5,
                        "download_mbps": 92.4,
                        "latency_ms": 17.2,
                        "jitter_ms": 1.8,
                        "packet_loss_pct": 0.0,
                        "health_score": 98.0,
                        "stability_score": 96.0,
                        "estimated_utilization_pct": 14.5,
                        "monitoring_mode": "NORMAL"
                    }]
                    ok, code, msg = streamer.push_direct_sync(test_payload)
                    if ok:
                        st.success(f"Successfully pushed live telemetry frame to Power BI Service (HTTP {code})!")
                    else:
                        st.error(f"Failed to push to Power BI API: HTTP {code} - {msg}")

        with col_p2:
            st.info("Push updates stream at sub-second speeds directly to live Power BI dashboard tiles with zero gateway.")

    # --- Section 5: Developer & Viva Resources (Tabs) ---
    st.markdown('<div class="section-title">5. Quick-Connect Tools & Viva Defense Assets</div>', unsafe_allow_html=True)

    tab_py, tab_dax, tab_m, tab_theme, tab_viva = st.tabs([
        "🐍 Python Data Connector (1-Click Load)",
        "📐 DAX Measures Library (30+ Formulas)",
        "⚙️ Power Query M Code",
        "🎨 Dark Theme JSON",
        "🎓 Viva Presentation Script"
    ])

    with tab_py:
        st.markdown("""
        **How to load all 9 Star Schema tables into Power BI Desktop in 30 seconds:**
        1. Open **Power BI Desktop**.
        2. Click **Get Data** &rarr; **More...** &rarr; **Python script** &rarr; **Connect**.
        3. Copy the script below, paste it into Power BI, and click **OK**.
        4. Select all tables in Navigator and click **Load**!
        """)
        connector_file = Path("powerbi/powerbi_connector.py")
        if connector_file.exists():
            with open(connector_file, "r", encoding="utf-8") as f:
                st.code(f.read(), language="python")
        else:
            st.info("Connector file located at `powerbi/powerbi_connector.py`.")

    with tab_dax:
        st.markdown("**Production DAX Measures for Power BI Calculations:**")
        dax_file = Path("powerbi/dax_measures.dax")
        if dax_file.exists():
            with open(dax_file, "r", encoding="utf-8") as f:
                st.code(f.read(), language="dax")
        else:
            st.info("DAX library located at `powerbi/dax_measures.dax`.")

    with tab_m:
        st.markdown("**Advanced Power Query (M) Scripts for File/Text CSV Connectors:**")
        m_file = Path("powerbi/power_query_m_scripts.pq")
        if m_file.exists():
            with open(m_file, "r", encoding="utf-8") as f:
                st.code(f.read(), language="powerquery")
        else:
            st.info("Power Query code located at `powerbi/power_query_m_scripts.pq`.")

    with tab_theme:
        st.markdown("**Custom Power BI Dark Cyber Theme (Import via View &rarr; Themes &rarr; Browse for themes):**")
        theme_file = Path("powerbi/NetIntel_Theme.json")
        if theme_file.exists():
            with open(theme_file, "r", encoding="utf-8") as f:
                st.code(f.read(), language="json")
        else:
            st.info("Theme file located at `powerbi/NetIntel_Theme.json`.")

    with tab_viva:
        st.markdown("**Viva Defense Questions & Technical Answers:**")
        viva_file = Path("powerbi/VIVA_PRESENTATION_SCRIPT.md")
        if viva_file.exists():
            with open(viva_file, "r", encoding="utf-8") as f:
                st.markdown(f.read())
        else:
            st.info("Viva defense guide located at `powerbi/VIVA_PRESENTATION_SCRIPT.md`.")
