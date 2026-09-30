# NetIntel: Live Power BI Dashboard Setup & Operation Guide

This guide walks you through setting up and running a **real-time live dashboard in Microsoft Power BI** using NetIntel's telemetry engine.

---

## 4 Ways to Run a Live Power BI Dashboard

| Mode | Target Platform | Live Mechanism | Best For |
| :--- | :--- | :--- | :--- |
| **Mode 1: Python Data Connector** | Power BI Desktop (Local) | Single script paste | **Fastest setup & Project Viva (No file path issues)** |
| **Mode 2: Star Schema CSV + Auto-Refresher** | Power BI Desktop (Local) | Windows Background Auto-Refresh | **Hands-free local mission control screen** |
| **Mode 3: Power BI Service Push Dataset** | Power BI Service (Cloud) | REST API sub-second Push | **True cloud live streaming tiles & mobile app** |
| **Mode 4: Local Web REST API** | Power BI Desktop / Web | Web.Contents / JSON polling | **Multi-device local network consumption** |

---

## Mode 1: Instant Setup via Python Connector (Recommended for Viva)

1. Launch **Microsoft Power BI Desktop**.
2. On the **Home** ribbon, click **Get Data** &rarr; **More...** &rarr; select **Python script** &rarr; click **Connect**.
3. Open `powerbi/powerbi_connector.py` in your code editor, copy the entire script, and paste it into the Python script box.
4. Click **OK**.
5. In the **Navigator** window, check the boxes for:
   * `FactNetworkMetrics`
   * `FactLatencyProbes`
   * `FactIncidents`
   * `FactAnomalies`
   * `FactApplicationExperience`
   * `DimDate`
   * `DimTime`
   * `DimInterface`
   * `DimTarget`
6. Click **Load**.
7. Power BI will import all 9 relational tables into its high-speed in-memory engine.

---

## Mode 2: Live Hands-Free Refreshing in Power BI Desktop

Power BI Desktop displays local files in-memory. To make it refresh continuously on your monitor without manual clicks:

1. Connect to the Star Schema CSVs located in `data/exports/star_schema/` (or run `python manage.py powerbi-export`).
2. Import the dark theme: In Power BI Desktop, go to **View** ribbon &rarr; **Themes dropdown** &rarr; **Browse for themes** &rarr; select `powerbi/NetIntel_Theme.json`.
3. In a terminal, run NetIntel's Auto-Refresher daemon:
   ```powershell
   python manage.py auto-refresh --interval 5
   ```
4. Keep Power BI Desktop open on your screen. The daemon will automatically trigger live refresh signals (F5), updating all charts, metrics, and KPI cards with new network telemetry every 5 seconds!

---

## Mode 3: Sub-Second Live Cloud Streaming (Power BI Service)

To stream live metrics directly into **Power BI Service in the cloud** with sub-second animation and zero gateway:

1. Open your browser and go to [app.powerbi.com](https://app.powerbi.com).
2. Go to **My Workspace** (or any workspace) &rarr; click **New** &rarr; select **Streaming dataset**.
3. Select **API** &rarr; click **Next**.
4. Dataset name: `NetIntel Live Telemetry`.
5. Add the following fields:
   * `timestamp` (DateTime)
   * `interface_name` (Text)
   * `upload_mbps` (Number)
   * `download_mbps` (Number)
   * `latency_ms` (Number)
   * `jitter_ms` (Number)
   * `packet_loss_pct` (Number)
   * `health_score` (Number)
   * `stability_score` (Number)
   * `monitoring_mode` (Text)
6. Switch **Historic data analysis** to **ON** &rarr; click **Create**.
7. Power BI will display a **Push URL** (e.g., `https://api.powerbi.com/beta/.../rows?key=...`). Copy this URL.
8. Set the push URL in your `.env` file or run:
   ```powershell
   $env:POWERBI_PUSH_URL="https://api.powerbi.com/beta/..."
   python manage.py engine
   ```
   *(Or paste it into the Power BI Pipeline view in NetIntel's web dashboard!)*
9. In Power BI Service, create a new **Dashboard** &rarr; click **Add tile** &rarr; **Real-Time Data** &rarr; select `NetIntel Live Telemetry`. Add a **Card** for `health_score` and a **Line chart** for `latency_ms` and `download_mbps`.
10. Watch the charts animate live in real time as packets flow through your network!

---

## Mode 4: Local REST API Server

Power BI Desktop can also connect directly to NetIntel's local HTTP API:

1. Start the API server:
   ```powershell
   python manage.py powerbi-stream
   ```
2. The server runs on `http://127.0.0.1:8080`.
3. In Power BI Desktop: Click **Get Data** &rarr; **Web** &rarr; paste:
   ```text
   http://127.0.0.1:8080/api/metrics?limit=500
   ```
4. Click **OK** &rarr; Power BI converts the live JSON records into a table.
