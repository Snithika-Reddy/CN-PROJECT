# NetIntel Viva Presentation Q&A Defense Guide

This document contains detailed academic, networking, and software engineering questions with comprehensive answers for college viva presentation and project defense.

---

### Q1: What makes NetIntel different from a typical student network dashboard project?
**Answer:** Most student projects are either static mockups, read global counters without interface separation, or generate random numbers. NetIntel is an end-to-end network observability and intelligence platform:
1. It measures **real physical telemetry** using `pernic=True` to prevent interface aggregation mismatch.
2. It implements the official **RFC 3550 standard** for inter-packet delay variation (jitter).
3. It uses a **multi-target probing architecture** separating local gateway health from wide-area Internet transit.
4. It enforces **hysteresis debouncing** on incidents to prevent flapping.
5. It performs **multi-signal diagnostic correlation** outputting calibrated competing hypotheses with cited evidence rather than black-box guesses.
6. It automatically feeds a **Star Schema pipeline** into Microsoft Power BI with technical honesty regarding refresh mechanics.

---

### Q2: Why did you use `psutil.net_io_counters(pernic=True)` instead of the default `net_io_counters()`?
**Answer:** The default `net_io_counters()` returns the global sum of bytes across all interfaces (including Loopback, Docker virtual bridges, and VPN adapters). Calculating link utilization by dividing global aggregate traffic by the hardware speed of a single Wi-Fi card is mathematically flawed and generates false saturation spikes. `pernic=True` isolates counters specifically to the active outbound NIC.

---

### Q3: How is Jitter calculated in your platform?
**Answer:** We implement the official **RFC 3550 RTP specification** algorithm:
$$D(i-1, i) = |RTT_i - RTT_{i-1}|$$
$$J(i) = J(i-1) + \frac{D(i-1, i) - J(i-1)}{16}$$
It computes the absolute difference between consecutive ping replies and updates an exponential moving average low-pass filter with a smoothing parameter of 16.

---

### Q4: How do you differentiate between a local Wi-Fi issue and an external ISP issue?
**Answer:** Through multi-target probing:
- If round-trip latency to the local default gateway (`192.168.1.1`) is elevated (>25ms) or showing packet loss, the issue is on the local LAN, Wi-Fi access point, or router.
- If gateway latency is fast and stable (<10ms, 0% loss) but public endpoints (`8.8.8.8`, `1.1.1.1`) show elevated latency (>90ms) or loss, the bottleneck is downstream in the ISP transit or peering path.

---

### Q5: Why does your Anomaly Detection engine gate the Machine Learning model?
**Answer:** To uphold technical honesty. Unsupervised models like Isolation Forest require sufficient representative training distribution (at least 150-200 samples) to establish true clustering boundaries. When insufficient data exists, claiming "99% ML accuracy" on fabricated data is academically dishonest. NetIntel transparently operates in **Statistical Mode** (using robust Modified Z-score and Tukey IQR fences) and only promotes to **ML Mode** when sufficient empirical history has been captured.

---

### Q6: How does the Incident Management debounce mechanism prevent incident spam?
**Answer:** Transient single-sample spikes (e.g. a single 70ms ping) are common on wireless links. NetIntel requires **3 consecutive abnormal samples** before opening an incident. Once open, it tracks the incident through an active lifecycle (`OPEN` $\to$ `RECOVERING` $\to$ `RESOLVED`), requiring **5 consecutive nominal samples** before declaring full resolution.

---

### Q7: What is the "What Changed?" analysis?
**Answer:** When an incident occurs, the platform automatically compares peak incident degradation against the learned pre-incident empirical baseline across latency, jitter, loss, and utilization, computing exact percentage divergence to help network engineers pinpoint the triggering metric.

---

### Q8: How does the Power BI integration work, and can it refresh automatically?
**Answer:** NetIntel maintains streaming CSV files in `data/exports/` adhering to a documented Star Schema (`FactNetworkMetrics`, `DimTime`, `DimInterface`).
- In **Power BI Desktop**, the user clicks **Refresh** to ingest all newly appended records into memory.
- For automated scheduled cloud refresh, NetIntel provides an enterprise extension point using the **On-Premises Data Gateway** or **Azure AD Service Principal REST API**. We explicitly do not falsely claim that local desktop files stream live without refresh configuration.
