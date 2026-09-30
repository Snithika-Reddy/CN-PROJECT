# NetIntel Power BI Pipeline Specification

This document details the Python -> CSV -> Power BI pipeline, Star Schema architecture, and refresh configuration.

---

## 1. Technical Honesty Mandate on Power BI Live Refresh

> [!IMPORTANT]
> **Power BI Desktop is NOT a WebSocket client.** It does not continuously auto-pull local CSV updates without explicit user refresh action or scheduled gateway execution. Any claim that local Power BI Desktop updates automatically per-second without refresh is technically false.

NetIntel provides two honest, enterprise-grade integration modes:

---

## 2. Integration Modes

### Mode A: Local Power BI Desktop
1. Telemetry records are written atomically by `src/storage/csv_exporter.py` into:
   - `data/exports/network_metrics.csv`
   - `data/exports/latency_metrics.csv`
   - `data/exports/incidents.csv`
   - `data/exports/anomalies.csv`
2. Open **Power BI Desktop**, choose **Get Data** -> **Text/CSV**, and point to these files.
3. Establish relationships as documented in the Star Schema.
4. When telemetry collection is active, clicking **Refresh** in Power BI immediately pulls all new records.

### Mode B: Power BI Service / Automated Gateway
1. Publish the `.pbix` to your Power BI workspace.
2. Install **On-Premises Data Gateway** on the host running NetIntel.
3. Configure scheduled refresh (every 30 mins) or use the Azure AD REST API refresher module in `src/powerbi/refresh.py`.
4. Securely store secrets in `.env` (never commit keys to source control):
   ```env
   POWERBI_TENANT_ID=your-tenant-uuid
   POWERBI_CLIENT_ID=your-client-id
   POWERBI_CLIENT_SECRET=your-secret
   POWERBI_WORKSPACE_ID=your-workspace-uuid
   POWERBI_DATASET_ID=your-dataset-uuid
   ```
