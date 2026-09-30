# NetIntel Power BI Integration Guide

This directory documents the connection and data modeling workflow for integrating **NetIntel** telemetry into **Microsoft Power BI**.

---

## 1. Architecture Overview

```text
Host Network Interface
        ↓
  Python NetIntel Core Engine
        ↓
SQLite Authoritative Store (database/network_monitor.db)
        ↓
Automatic Real-Time Streaming CSVs (data/exports/*.csv)
        ↓
Microsoft Power BI Desktop / Power BI Service
```

---

## 2. Supported Integration Modes

### Mode A: Local Power BI Desktop (Recommended & Free)
1. Launch **Power BI Desktop**.
2. Click **Get Data** -> **Text/CSV**.
3. Browse to `data/exports/network_metrics.csv` in your NetIntel project root.
4. Click **Load** (or **Transform Data** to inspect schema types).
5. Repeat for `latency_metrics.csv`, `incidents.csv`, and `anomalies.csv`.
6. To update visuals with newly collected network samples, simply click the **Refresh** button on the Home ribbon.

> [!NOTE]
> **Technical Honesty Note:** Local Power BI Desktop is an in-memory tabular analytical tool. It refreshes when you click **Refresh** or trigger a local refresh macro. It does not automatically stream per-second frames without gateway configuration.

### Mode B: Power BI Service / Automated Gateway
For cloud-based automated refresh:
1. Publish your `.pbix` report to a workspace in **Power BI Service**.
2. Install the **On-Premises Data Gateway (Personal or Standard Mode)** on the host machine.
3. Configure scheduled refresh (e.g., every 30 minutes).
4. Alternatively, use the Azure AD Service Principal module in `src/powerbi/refresh.py` with environment variables:
   ```env
   POWERBI_TENANT_ID=your-tenant-uuid
   POWERBI_CLIENT_ID=your-client-id
   POWERBI_CLIENT_SECRET=your-secret
   POWERBI_WORKSPACE_ID=your-workspace-uuid
   POWERBI_DATASET_ID=your-dataset-uuid
   ```

---

## 3. Recommended Visualizations & Dashboard Pages

| Page | Primary Visuals | Key Measures |
| :--- | :--- | :--- |
| **1. Executive Overview** | Card KPIs, Health Trend, Incident Timeline | Avg Health, Current Mode, Open Incidents |
| **2. Traffic & Utilization** | Area Chart (Upload/Download Mbps), Gauge (Interface Utilization %) | Total MB, Peak Mbps, Avg Utilization |
| **3. Latency & Jitter** | Dual-axis Line Chart (Latency vs Jitter), Boxplot | Median Latency, 95th Percentile Jitter |
| **4. Packet Loss & SLA** | Line Chart (% Loss), SLA Compliance Donut | % Samples with 0% Loss, Unavailability Sec |
| **5. Anomalies & Incidents** | Matrix Table (Timestamp, Severity, Details), Bar Chart by Anomaly Type | Total Anomalies, Incident MTTR |
| **6. Diagnosis & Hypotheses** | Clustered Column (Evidence Strength by Hypotheses) | Primary Root Causes Count |
