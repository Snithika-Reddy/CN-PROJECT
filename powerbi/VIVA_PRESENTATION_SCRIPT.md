# NetIntel: Viva Presentation & Technical Defense Script

This document prepares you for presenting and defending your Computer Networks (CN) Capstone / Project with high distinction, specifically covering the architecture, mathematical telemetry derivations, and Microsoft Power BI integration.

---

## 1. Project Pitch (30-Second Elevator Pitch)

> *"NetIntel is a production-grade, real-time network intelligence and telemetry observability platform. It continuously measures real physical host network interface metrics—including upload/download throughput, multi-target ICMP probe latencies, packet loss, and RFC 3550 jitter. It builds statistical baselines, detects anomalies via Z-score, IQR, and Isolation Forests, executes multi-signal root-cause diagnoses, and adapts its sampling rate dynamically. For executive analytics, it streams telemetry into Microsoft Power BI through an authoritative Star Schema data warehouse model and live REST streaming push datasets."*

---

## 2. System Architecture Walkthrough

```text
[Host NIC / OS Kernel Counters]
        ↓ (psutil / Windows IP Helper API)
[Raw Telemetry Collector]
        ↓ (Data Sanitizer & Spike Filter)
[Processing & Feature Extraction]
  ├── RFC 3550 Jitter Computation: J(i) = J(i-1) + (|D(i-1, i)| - J(i-1)) / 16
  ├── Rolling Percentile Baseline (P5, P25, P50, P75, P95)
  ├── Dual Anomaly Detection (Statistical Z/IQR + ML Isolation Forest)
  ├── Multi-Signal Diagnostic Engine (Gateway vs Upstream vs Bufferbloat)
  └── Adaptive Controller State Machine (Normal 2s → Warning 1s → Critical 0.5s)
        ↓
[SQLite Database (Authoritative WAL Store)]
        ↓
[Power BI Integration Engine]
  ├── Star Schema Fact & Dimension CSVs (FactNetworkMetrics, DimTime, DimDate, etc.)
  ├── Local REST API Server (http://127.0.0.1:8080/api/live)
  ├── Sub-Second Push Streaming to Power BI Service REST API
  └── Windows Power BI Desktop Live Auto-Refresher Daemon
```

---

## 3. Likely Viva Questions & Technical Answers

### Q1: Why did you choose a Star Schema model for Power BI instead of a single flat table?
**Answer:**
> *"A flat denormalized table creates massive data redundancy—for example, repeating interface specifications, date metadata, and target DNS attributes across every single second's telemetry row. In analytical engines like Microsoft VertiPaq (Power BI's columnar in-memory database), a Star Schema with Fact tables (`FactNetworkMetrics`, `FactIncidents`) and Dimension tables (`DimDate`, `DimTime`, `DimInterface`) optimizes columnar compression, reduces memory footprint by over 60%, eliminates circular relationship ambiguities, and dramatically speeds up complex DAX filtering and time-intelligence calculations."*

---

### Q2: How do you achieve a "Live" dashboard in Power BI given that Power BI Desktop is in-memory?
**Answer:**
> *"We implemented a multi-tiered live architecture to support both local defense and cloud deployment:*
> 1. *For local defense without requiring Azure credentials, we engineered a Windows background auto-refresher daemon that issues non-disruptive refresh signals (F5) directly to the Power BI Desktop window, re-evaluating the in-memory tabular store with newly appended telemetry.*
> 2. *For cloud environments, we built an asynchronous REST push client (`PowerBIStreamer`) that POSTs live telemetry frames directly to Microsoft Power BI Service Push Datasets. Power BI Service natively updates live tile visuals in sub-second latency with zero scheduled refresh lag.*
> 3. *Furthermore, we built an embedded local HTTP REST API on port 8080 so Power BI can query live telemetry via Web Connector."*

---

### Q3: How is Latency Jitter calculated mathematically?
**Answer:**
> *"We adhere strictly to the IETF RFC 3550 standard for RTP jitter calculation. Rather than taking simple standard deviation, RFC 3550 defines interarrival jitter using a first-order exponential smoothing filter:*
> $$D(i-1, i) = (R_i - S_i) - (R_{i-1} - S_{i-1})$$
> $$J_i = J_{i-1} + \frac{|D(i-1, i)| - J_{i-1}}{16}$$
> *This provides an accurate measure of packet arrival variance while smoothing out transient single-packet outliers."*

---

### Q4: Why is 95th Percentile (P95) Latency more important than Average Latency?
**Answer:**
> *"Arithmetic mean hides critical performance degradation. For example, if 95% of packets take 15ms and 5% take 300ms due to router queue buffering, the average latency is only ~29ms—appearing healthy. However, for interactive real-time applications like VoIP and competitive multiplayer gaming, that 5% tail latency causes noticeable stutter and audio dropouts. P95 latency gives a statistically sound tail-bound performance guarantee."*

---

### Q5: How does your system differentiate between a local Wi-Fi issue and an ISP outage?
**Answer:**
> *"We use multi-target ICMP probe correlation:
> - If latency and packet loss spike to both the local default gateway (e.g., 192.168.1.1) AND public targets (8.8.8.8 / 1.1.1.1), the fault is diagnosed as a **Local Link Congestion or Wi-Fi Interference** problem.
> - If the local default gateway has 0% loss and <2ms latency, but public DNS targets exhibit high loss or delay, the fault is isolated to the **Upstream ISP or Transit Provider**."*
