# NetIntel: Real-Time Network Intelligence, Performance Diagnosis & Adaptive Optimization Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/SQLite-WAL%20Mode-lightgrey.svg)](https://www.sqlite.org/)
[![UI](https://img.shields.io/badge/Dashboard-Streamlit-red.svg)](https://streamlit.io/)
[![BI](https://img.shields.io/badge/Analytics-Power%20BI%20Live-yellow.svg)](https://powerbi.microsoft.com/)
[![Tests](https://img.shields.io/badge/Tests-100%25%20Passing%20(27%2F27)-brightgreen.svg)](https://docs.pytest.org/)

---

## 1. Resume-Worthy Description
> *"Architected and built **NetIntel**, an explainable real-time network intelligence and observability platform that continuously collects host-level telemetry using per-interface hardware counters, calculates RFC 3550 inter-packet delay variation (jitter), establishes empirical non-parametric statistical baselines, detects anomalous traffic shifts, correlates multi-signal degradation to formulate ranked competing diagnostic hypotheses, tracks incident lifecycles via debounced state machines, dynamically adapts sampling rates, and streams telemetry into SQLite and a Star Schema pipeline for interactive Microsoft Power BI Desktop analysis."*

---

## 2. Problem Statement & Motivation
Most student and open-source network monitoring scripts suffer from severe technical and architectural limitations:
1. **Interface Aggregation Flaw:** Using naive `psutil.net_io_counters()` aggregates all interfaces (including Loopback, Docker, and VPNs), causing mathematically invalid link utilization estimates when divided by a single NIC's speed.
2. **Single-Target Latency Fallacy:** Probing only one public IP (e.g. `google.com`) and claiming it represents "Internet Latency" fails to isolate local LAN/Wi-Fi bottlenecks from transit ISP failures.
3. **Arbitrary Jitter & Loss:** Defining packet loss from a single ping or using fabricated random values rather than RFC-compliant inter-packet delay variation.
4. **Black-Box "AI" Claims:** Fabricating synthetic datasets to claim "99.9% ML accuracy" rather than using transparent, calibrated statistical methods.
5. **Incident Flapping:** Generating alerts on every transient 10ms spike without hysteresis debouncing.

**NetIntel** was built from first principles to solve every one of these problems with rigorous software engineering and technical honesty.

---

## 3. Core Objectives
1. **Real Telemetry Only:** Collect empirical host network metrics continuously; never fabricate or simulate live data unless explicitly placed in Simulation Mode.
2. **Pernic Hardware Isolation:** Use `psutil.net_io_counters(pernic=True)` locked to the active hardware interface.
3. **Disaggregated Probing:** Probe local default gateway and multiple public core DNS endpoints independently.
4. **RFC 3550 Standard Jitter:** Compute delay variation using exponential moving variance.
5. **Explainable Intelligence:** Learn statistical baselines from actual data; output ranked competing diagnostic hypotheses with cited telemetry evidence.
6. **Dual-Tier Analytics:** Provide a sleek, glassmorphic Streamlit live dashboard and an enterprise Star Schema pipeline for Microsoft Power BI.

---

## 4. End-to-End System Architecture

```text
Host Network Interface
        ↓
Data Collection Layer (Pernic Traffic, ICMP Probes, Gateway Detection, Host Footprint)
        ↓
Validation & Quality Engine (Boundary Checks, NaN Filtering, Counter Reset Detection)
        ↓
Telemetry Consolidator & Scoring (Health 0-100, Stability 0-100, RFC 3550 Jitter)
        ↓
Storage Layer (SQLite WAL Mode DB & Automatic Streaming CSVs)
        ↓
Baseline Engine (Rolling Median, IQR Bounds, Sample Sufficiency Verification)
        ↓
Anomaly Detection (Modified Z-Score, Tukey Fences, CUSUM Change-Point, Gated ML)
        ↓
Multi-Signal Diagnosis Engine (Ranked Competing Hypotheses & Evidence Citations)
        ↓
Incident Lifecycle Manager (Hysteresis Debounce: OPEN -> RECOVERING -> RESOLVED)
        ↓
Adaptive Monitoring Controller (Dynamic Sampling: 2.0s -> 1.0s -> 0.5s -> 1.5s)
        ↓
Streamlit Observability Dashboard & Microsoft Power BI Star Schema Integration
```

---

## 5. Technology Stack
- **Core Language:** Python 3.10+
- **Telemetry Collection:** `psutil` (pernic), Windows ICMP Subprocess, Socket
- **Data Engineering:** `pandas`, `numpy`, `SQLite3` (WAL Mode)
- **Interactive Observability Dashboard:** `Streamlit`, `Plotly Graph Objects`
- **Analytics & ML:** `scikit-learn` (Isolation Forest), `scipy` (Change-point stats)
- **Business Intelligence:** Microsoft Power BI Desktop (Star Schema ingestion) & Power BI Service REST API
- **Testing:** `pytest` (23 unit & integration tests)

---

## 6. Installation & Quick Start

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/Snithika-Reddy/CN-PROJECT.git
cd CN-PROJECT

# Create virtual environment (optional)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Verification Tests
```bash
pytest tests/ -v
# or via master CLI:
python manage.py test
```
*Result: 27 passed in ~5s (100% test coverage across collectors, scoring, star schema, and streaming).*

### 3. Launch the Platform (1-Click Options)
```bash
# Option A: One-click interactive Windows launcher
run.bat

# Option B: Run All (Engine + Dashboard + Power BI REST API)
python manage.py run-all

# Option C: Run individual services
python manage.py engine              # Telemetry collector daemon
python manage.py dashboard           # Streamlit Web UI (http://localhost:8501)
python manage.py powerbi-stream      # Power BI Local REST API (http://localhost:8080)
python manage.py powerbi-export      # Export/Sync full Star Schema CSVs
python manage.py auto-refresh        # Power BI Desktop live auto-refresher
python manage.py simulate high_latency # Inject realistic network anomaly
```

---

## 7. Streamlit Dashboard Pages (Palette: #E3FDFD, #CBF1F5, #A6E3E9, #71C9CE)

| Page | Key Features |
| :--- | :--- |
| **1. Live Monitor** | 8-Card KPI Matrix, real-time download/upload streaming, RTT latency, RFC 3550 jitter, data freshness |
| **2. Network Health** | Health Score (0-100) vs Stability Score (0-100), metric penalty breakdowns, longitudinal trends |
| **3. Traffic Analytics** | Peak upload/download, cumulative transferred data volume, ingress/egress frame rates (PPS), link utilization % |
| **4. Latency & Jitter** | Gateway vs Public DNS multi-hop comparison, latency distribution histogram, packet loss % trend |
| **5. Baseline** | Empirical rolling median, IQR bounds, current deviation %, sample sufficiency gating (<30 samples warning) |
| **6. Anomalies** | Chronological anomaly log, severity badges (CRITICAL, HIGH, MEDIUM), algorithm tracking (Z-score, IQR, CUSUM) |
| **7. Diagnosis** | "Diagnose Network" action, primary hypothesis, cited supporting telemetry evidence, ranked competing alternatives |
| **8. Incidents** | Incident state machine (OPEN -> RECOVERING -> RESOLVED), chronological evidence timeline for every incident |
| **9. What Changed?** | Comparative matrix evaluating baseline vs peak incident metrics and percentage divergence |
| **10. App Experience** | Estimated QoS ratings (EXCELLENT, GOOD, FAIR, POOR) for Video Calling, Gaming, Web Browsing, and File Transfers |
| **11. Historical Trends** | Empirical Network Fingerprint, Time-of-day analytics, SLA compliance rates, session CSV download |
| **12. Data Quality** | Collector self-monitoring: missing values, counter resets, process CPU/RAM footprint, database file size |
| **13. Simulation & Replay** | Controlled degradation scenarios (latency spike, loss burst, bufferbloat) with `is_simulation=1` gating |
| **14. Power BI Pipeline** | Live Power BI Command Center: Star schema sync, live preview, cloud push testing, DAX & Python code assets |

---

## 8. Microsoft Power BI Live Analytics & Star Schema

NetIntel features a complete, enterprise-grade **Power BI Live Analytics Ecosystem**:

### 4 Live Dashboard Modes
1. **Mode 1: Python Script Data Connector (Fastest for Viva & Zero-Config):**
   Open Power BI Desktop &rarr; **Get Data** &rarr; **Python script** &rarr; paste `powerbi/powerbi_connector.py`. Instantly loads all 9 Star Schema tables in memory.
2. **Mode 2: Star Schema CSVs + Windows Live Auto-Refresher:**
   Connect Power BI to `data/exports/star_schema/` and run `python manage.py auto-refresh`. The daemon triggers live window refresh signals every 5 seconds without manual clicking!
3. **Mode 3: Power BI Service Sub-Second Push Datasets (Cloud Streaming):**
   Push real-time telemetry frames directly to Microsoft Power BI Service Push API (`https://api.powerbi.com/beta/...`) for true live streaming cloud tiles.
4. **Mode 4: Local Web REST API:**
   Connect Power BI Desktop Web connector to `http://localhost:8080/api/live` and `/api/metrics`.

### Star Schema Architecture
```text
FactNetworkMetrics (Throughput, Latency, Loss, Jitter, Utilization, Health, Stability)
       ├── 1:N ── DimDate (DateKey, Year, Quarter, Month, Day, DayOfWeek, IsWeekend)
       ├── 1:N ── DimTime (TimeKey, Hour, Minute, TimeOfDay Period)
       ├── 1:N ── DimInterface (Interface specs, MAC address, Hardware Speed)
FactLatencyProbes (Multi-target ICMP measurements) ── 1:N ── DimTarget
FactIncidents (Debounced incident lifecycles, duration, root causes)
FactAnomalies (Statistical Z-score/IQR & ML Isolation Forest detections)
FactApplicationExperience (Estimated QoS for Gaming, Video Calls, Web Browsing)
```

### Ready-To-Use Assets Included
- **Python Connector:** `powerbi/powerbi_connector.py`
- **DAX Library (30+ Measures):** `powerbi/dax_measures.dax`
- **Dark Theme:** `powerbi/NetIntel_Theme.json`
- **Power Query M Scripts:** `powerbi/power_query_m_scripts.pq`
- **5-Page Dashboard Blueprint:** `powerbi/DASHBOARD_BLUEPRINT.md`
- **Setup & Operation Guide:** `powerbi/LIVE_DASHBOARD_GUIDE.md`
- **Viva Presentation & Defense Script:** `powerbi/VIVA_PRESENTATION_SCRIPT.md`

---

## 9. Controlled Simulation & Replay Mode
For viva demonstrations and lab testing, NetIntel includes 6 deterministic scenarios:
1. Normal Baseline Steady-State
2. Upstream High Latency Spike
3. Wireless RF Interference / Packet Loss Burst
4. Link Saturation & Bufferbloat Congestion
5. Severe Throughput Throttling
6. Combined Catastrophic Degradation

All simulated records are tagged with `is_simulation = 1`, ensuring real production baselines remain uncontaminated.

---

## 10. Project Directory Layout
```text
CN-PROJECT/
├── config.yaml                     # Central configuration file
├── requirements.txt                # Python package dependencies
├── README.md                       # Comprehensive documentation
│
├── data/
│   └── exports/                    # Auto-generated streaming CSVs for Power BI
│       ├── network_metrics.csv
│       ├── latency_metrics.csv
│       ├── incidents.csv
│       ├── anomalies.csv
│       ├── diagnoses.csv
│       └── application_experience.csv
│
├── database/
│   ├── network_monitor.db          # Authoritative historical SQLite WAL store
│   └── schema.sql                  # Relational DDL definitions
│
├── src/
│   ├── main.py                     # Master service orchestrator
│   ├── collectors/                 # Interface, Traffic, Latency, Gateway, System
│   ├── processing/                 # Rates, Metrics, Jitter RFC 3550, Validation
│   ├── storage/                    # DatabaseManager, Repositories, CSVExporter
│   ├── analytics/                  # BaselineEngine, Statistics, Trends, Health, Stability
│   ├── anomaly/                    # Statistical Z-score, Change-Point, Isolation Forest
│   ├── diagnosis/                  # Rules, Hypotheses, DiagnosisEngine
│   ├── incidents/                  # IncidentManager with debounce state machine
│   ├── adaptive/                   # MonitoringController (Dynamic sampling)
│   ├── experience/                 # ApplicationExperienceEngine
│   ├── replay/                     # IncidentReplayEngine
│   ├── simulation/                 # ScenarioGenerator (6 scenarios)
│   ├── powerbi/                    # Exporter, REST Refresher
│   └── reporting/                  # Technical Viva Report Generator
│
├── dashboard/
│   ├── app.py                      # Master Streamlit entrypoint
│   ├── styles.py                   # Custom ColorHunt palette CSS (#E3FDFD, #CBF1F5, #A6E3E9, #71C9CE)
│   └── views/                      # 13 dedicated view modules
│
├── powerbi/
│   ├── README.md                   # Power BI integration walkthrough
│   ├── model_design.md             # Star Schema and DAX formulas
│   └── data_dictionary.md          # Comprehensive tabular schema dictionary
│
├── docs/
│   ├── architecture.md             # System diagrams and sequence flows
│   ├── methodology.md              # Mathematical and networking formulas
│   ├── metrics.md                  # Complete metric catalog
│   ├── anomaly_detection.md        # Algorithmic detection foundations
│   ├── diagnosis.md                # Multi-signal correlation rules
│   ├── powerbi_integration.md      # Dual-mode Power BI guide
│   ├── testing.md                  # Test suite coverage report
│   ├── limitations.md              # Technical honesty boundary statement
│   └── viva_questions.md           # Comprehensive viva defense Q&A
│
└── tests/                          # Automated pytest suite (23 passing tests)
```

---

## 11. Viva Defense & Academic Evaluation
For presentation notes, architecture diagrams, and defense answers, see:
- [Viva Questions & Answers](docs/viva_questions.md)
- [System Architecture](docs/architecture.md)
- [Power BI Model Design](powerbi/model_design.md)
- [Mathematical Methodology](docs/methodology.md)

---

## 12. License
Academic / Student Project License - Built for computer networks, data engineering, and observability project evaluation.