# NetIntel Power BI Live Dashboard Blueprint & Visual Layout

This blueprint specifies the exact visual components, field bindings, and layout structure for building a 5-page enterprise live dashboard in **Microsoft Power BI Desktop / Service**.

---

## Page 1: Executive Command Center (Live Mission Control)

### Visual 1.1: KPI Cards Ribbon (Top Row)
* **Visual Type:** Multi-row Card / Individual Card Visuals
* **Fields:**
  * Card 1: `[CurrentHealthScore]` (Callout Value, formatted 0.0)
    * *Conditional Formatting:* Background Color mapped to `[HealthScoreColorHex]`
  * Card 2: `[SystemStabilityIndex]` (Callout Value, formatted 0.0)
  * Card 3: `[P95_LatencyMs]` (Callout Value, e.g. "21.4 ms")
  * Card 4: `[PacketLossPct]` (Callout Value, e.g. "0.0 %")
  * Card 5: `[ActiveIncidentsCount]` (Callout Value, Red alert if > 0)
  * Card 6: `[TotalDataTransferredMB]` (Callout Value, e.g. "452.8 MB")

### Visual 1.2: Real-Time Network Health & Stability Trend
* **Visual Type:** Line Chart with Zoom Slider
* **X-Axis:** `FactNetworkMetrics[timestamp]` (Continuous time)
* **Y-Axis:**
  * Line 1 (Teal #71C9CE): `[AvgHealthScore]`
  * Line 2 (Purple #A78BFA): `[AvgStabilityScore]`
* **Reference Line:** Constant line at 75.0 (Warning threshold) and 50.0 (Critical threshold)

### Visual 1.3: Interface Operational State & Adaptive Mode
* **Visual Type:** Clustered Bar Chart / Donut Chart
* **Category:** `FactNetworkMetrics[monitoring_mode]` (NORMAL, WARNING, CRITICAL, RECOVERY)
* **Values:** `COUNTROWS(FactNetworkMetrics)`
* **Color Mapping:**
  * NORMAL: Emerald Green `#10B981`
  * WARNING: Amber `#F59E0B`
  * CRITICAL: Crimson `#EF4444`
  * RECOVERY: Light Teal `#A6E3E9`

---

## Page 2: Traffic & Throughput Dynamics

### Visual 2.1: Ingress vs. Egress Bandwidth
* **Visual Type:** Area Chart
* **X-Axis:** `FactNetworkMetrics[timestamp]`
* **Y-Axis:**
  * Area 1 (Cyan #71C9CE): `FactNetworkMetrics[download_mbps]`
  * Area 2 (Green #10B981): `FactNetworkMetrics[upload_mbps]`

### Visual 2.2: Packet Velocity (Packets/Sec)
* **Visual Type:** Clustered Column Chart
* **X-Axis:** `FactNetworkMetrics[timestamp]`
* **Values:**
  * `FactNetworkMetrics[packets_recv_per_sec]`
  * `FactNetworkMetrics[packets_sent_per_sec]`

### Visual 2.3: Estimated Interface Capacity Utilization
* **Visual Type:** Gauge Visual
* **Value:** `[AvgInterfaceUtilizationPct]`
* **Target:** 75.0 % (Warning limit)
* **Maximum:** 100.0 %

---

## Page 3: Latency, Jitter & Multi-Target SLA Matrix

### Visual 3.1: Multi-Target ICMP Probe Round-Trip Time
* **Visual Type:** Line Chart (Multi-Series)
* **X-Axis:** `FactLatencyProbes[timestamp]`
* **Y-Axis:** `FactLatencyProbes[latency_avg_ms]`
* **Legend:** `FactLatencyProbes[target_name]` (Gateway, Google DNS, Cloudflare)

### Visual 3.2: Tail Latency Bounds (Median vs P95 vs P99)
* **Visual Type:** Clustered Column or Line Chart
* **Values:**
  * Column 1: `[MedianLatencyMs]`
  * Column 2: `[P95_LatencyMs]` (Tail Latency Bound)
  * Column 3: `[P99_LatencyMs]` (Extreme Spike Bound)

### Visual 3.3: SLA Latency & Packet Loss Compliance Donut
* **Visual Type:** Donut Chart
* **Values:** `[EnterpriseSLACompliancePct]` vs Non-Compliant
* **Center Label:** "% SLA Compliant"

---

## Page 4: Anomaly Radar & Incident Diagnostics

### Visual 4.1: Incidents Lifecycle Matrix Table
* **Visual Type:** Table / Matrix Visual
* **Columns:**
  * `incident_id`
  * `start_timestamp`
  * `duration_seconds`
  * `status` (OPEN / RECOVERING / RESOLVED)
  * `severity` (WARNING / CRITICAL)
  * `trigger_reason`
  * `diagnosis_summary`

### Visual 4.2: ML vs. Statistical Anomaly Distribution
* **Visual Type:** Treemap or Donut Chart
* **Group:** `FactAnomalies[detection_method]` (Z-SCORE, IQR, ISOLATION_FOREST)
* **Values:** `COUNTROWS(FactAnomalies)`

---

## Page 5: Quality of Experience (QoE) Application Ratings

### Visual 5.1: Real-Time Experience Scorecards
* **Visual Type:** Card Visuals
* **Cards:**
  * Video Call Quality (%): `[VideoCallReadinessPct]`
  * Gaming Quality (%): `[GamingReadinessPct]`
  * Web Browsing Responsiveness (%): `[WebBrowsingReadinessPct]`

### Visual 5.2: Experience Timeline
* **Visual Type:** Clustered Bar / 100% Stacked Bar
* **X-Axis:** `FactApplicationExperience[timestamp]`
* **Y-Axis:** Application category
* **Color:** Rating (EXCELLENT, GOOD, FAIR, POOR)
