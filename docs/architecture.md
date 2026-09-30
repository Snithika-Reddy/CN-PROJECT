# NetIntel Architecture Specification

This document provides complete architectural specifications, system diagrams, and data pipeline flows for the **Real-Time Network Intelligence, Performance Diagnosis & Adaptive Optimization Platform (NetIntel)**.

---

## 1. High-Level System Architecture

```mermaid
graph TD
    subgraph DataCollection [1. Telemetry Collection Layer]
        NIC[Active Hardware Interface] -->|pernic=True| TC[Traffic Collector]
        GW[Default Gateway] -->|ICMP Ping Window| LC[Latency & Jitter Collector]
        DNS[8.8.8.8 & 1.1.1.1] -->|ICMP Multi-Target| LC
        SYS[Host Resources] -->|CPU, RAM, DB Size| SC[System Self-Monitor]
    end

    subgraph ProcessingLayer [2. Processing & Validation]
        TC --> VAL[Data Validator & Sanitizer]
        LC --> VAL
        VAL --> JIT[RFC 3550 Jitter Calculator]
        VAL --> UTIL[Estimated Interface Utilization]
        VAL --> CONSOL[Telemetry Consolidator]
        JIT --> CONSOL
        UTIL --> CONSOL
    end

    subgraph StorageLayer [3. Authoritative Storage Layer]
        CONSOL -->|WAL Mode Transactions| SQLITE[(SQLite Historical DB)]
        CONSOL -->|Atomic Thread-Safe Append| CSV[Automatic CSV Exporters]
    end

    subgraph IntelligenceLayer [4. Analytics & Diagnosis Layer]
        SQLITE --> BASE[Empirical Baseline Engine]
        BASE --> ANOM[Statistical & ML Anomaly Detection]
        ANOM --> DIAG[Multi-Signal Diagnosis Engine]
        DIAG --> INC[Incident Lifecycle Manager]
        INC --> ADAPT[Adaptive Sampling Controller]
        ADAPT -.->|Pacing Feedback| DataCollection
    end

    subgraph PresentationLayer [5. Visualization & Reporting]
        SQLITE --> DASH[Streamlit Observability Dashboard]
        CSV --> PBI[Microsoft Power BI Desktop / Service]
        SQLITE --> REP[Viva Technical Report Generator]
    end
```

---

## 2. Telemetry Pipeline Sequence

```mermaid
sequenceDiagram
    autonumber
    participant HW as Network Interface
    participant Col as NetIntel Service
    participant DB as SQLite DB
    participant CSV as data/exports/*.csv
    participant Inc as Incident Manager
    participant UI as Streamlit / Power BI

    Col->>HW: Sample pernic counters & ICMP probes
    HW-->>Col: Raw byte delta, RTT reply window
    Col->>Col: Validate bounds, calculate RFC 3550 jitter & utilization
    Col->>Col: Evaluate Health (0-100) & Stability (0-100)
    Col->>DB: INSERT into network_metrics & latency_probes
    Col->>CSV: Append atomic row to network_metrics.csv
    Col->>Inc: Check hysteresis trigger / resolution threshold
    alt Incident Condition Met
        Inc->>DB: Update incident state & log timeline event
        Inc->>CSV: Append to incidents.csv
    end
    UI->>DB: Read latest historical series & active state
    UI->>UI: Render live graphs, diagnostic hypotheses, & KPIs
```

---

## 3. Database Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    interfaces ||--o{ network_metrics : "measured_on"
    network_metrics ||--o{ anomalies : "triggers"
    incidents ||--|{ incident_timeline : "contains"
    incidents ||--o{ diagnoses : "evaluates"

    interfaces {
        int interface_id PK
        string name UK
        string ip_address
        float speed_mbps
        int is_up
        int is_wireless
    }

    network_metrics {
        int metric_id PK
        string timestamp
        float epoch_time
        string interface_name FK
        float upload_mbps
        float download_mbps
        float latency_ms
        float jitter_ms
        float packet_loss_pct
        float estimated_utilization_pct
        float health_score
        float stability_score
        string monitoring_mode
        int is_simulation
    }

    latency_probes {
        int probe_id PK
        string timestamp
        string target_name
        string target_host
        float latency_avg_ms
        float jitter_ms
        float packet_loss_pct
    }

    incidents {
        string incident_id PK
        string start_timestamp
        string end_timestamp
        float duration_seconds
        string status
        string severity
        string trigger_reason
        float peak_latency_ms
        float peak_packet_loss_pct
        string diagnosis_summary
    }

    incident_timeline {
        int event_id PK
        string incident_id FK
        string timestamp
        string event_type
        string description
    }
```
