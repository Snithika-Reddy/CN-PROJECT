-- =============================================================================
-- NetIntel SQLite Relational Schema
-- Authoritative Historical Store for Network Telemetry & Intelligence
-- =============================================================================

PRAGMA foreign_keys = ON;

-- 1. Network Interfaces Catalog
CREATE TABLE IF NOT EXISTS interfaces (
    interface_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    ip_address TEXT,
    mac_address TEXT,
    speed_mbps REAL,
    is_up INTEGER DEFAULT 1,
    is_wireless INTEGER DEFAULT 0,
    is_loopback INTEGER DEFAULT 0,
    first_seen_timestamp TEXT NOT NULL,
    last_updated_timestamp TEXT NOT NULL
);

-- 2. Primary Network Metrics Telemetry
CREATE TABLE IF NOT EXISTS network_metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    epoch_time REAL NOT NULL,
    interface_name TEXT NOT NULL,
    upload_mbps REAL NOT NULL,
    download_mbps REAL NOT NULL,
    bytes_sent INTEGER NOT NULL,
    bytes_recv INTEGER NOT NULL,
    packets_sent INTEGER NOT NULL,
    packets_recv INTEGER NOT NULL,
    packets_sent_per_sec REAL NOT NULL,
    packets_recv_per_sec REAL NOT NULL,
    latency_ms REAL,
    jitter_ms REAL,
    packet_loss_pct REAL DEFAULT 0.0,
    estimated_utilization_pct REAL,
    health_score REAL NOT NULL,
    stability_score REAL NOT NULL,
    monitoring_mode TEXT NOT NULL,
    is_simulation INTEGER DEFAULT 0,
    is_replay INTEGER DEFAULT 0,
    data_quality_flag TEXT DEFAULT 'VALID'
);

CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON network_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_metrics_interface ON network_metrics(interface_name);

-- 3. Detailed Multi-Target Latency Probes
CREATE TABLE IF NOT EXISTS latency_probes (
    probe_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    target_name TEXT NOT NULL,
    target_host TEXT NOT NULL,
    probes_sent INTEGER NOT NULL,
    probes_received INTEGER NOT NULL,
    packet_loss_pct REAL NOT NULL,
    latency_min_ms REAL,
    latency_avg_ms REAL,
    latency_max_ms REAL,
    jitter_ms REAL,
    status TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_probes_timestamp ON latency_probes(timestamp);
CREATE INDEX IF NOT EXISTS idx_probes_target ON latency_probes(target_name);

-- 4. Anomaly Detections Log
CREATE TABLE IF NOT EXISTS anomalies (
    anomaly_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    observed_value REAL NOT NULL,
    baseline_expected REAL NOT NULL,
    deviation_pct REAL NOT NULL,
    severity TEXT NOT NULL, -- LOW, MEDIUM, HIGH, CRITICAL
    detection_method TEXT NOT NULL, -- Z-SCORE, IQR, CHANGEPOINT, ISOLATION_FOREST
    details TEXT,
    is_simulation INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_anomalies_timestamp ON anomalies(timestamp);
CREATE INDEX IF NOT EXISTS idx_anomalies_metric ON anomalies(metric_name);

-- 5. Network Incidents Lifecycle
CREATE TABLE IF NOT EXISTS incidents (
    incident_id TEXT PRIMARY KEY,
    start_timestamp TEXT NOT NULL,
    end_timestamp TEXT,
    duration_seconds REAL,
    status TEXT NOT NULL, -- OPEN, RECOVERING, RESOLVED
    severity TEXT NOT NULL, -- WARNING, CRITICAL
    trigger_reason TEXT NOT NULL,
    peak_latency_ms REAL,
    peak_jitter_ms REAL,
    peak_packet_loss_pct REAL,
    peak_utilization_pct REAL,
    min_health_score REAL,
    min_stability_score REAL,
    diagnosis_summary TEXT,
    is_simulation INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
CREATE INDEX IF NOT EXISTS idx_incidents_start ON incidents(start_timestamp);

-- 6. Incident Evidence Timeline
CREATE TABLE IF NOT EXISTS incident_timeline (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    description TEXT NOT NULL,
    metric_name TEXT,
    value REAL,
    FOREIGN KEY(incident_id) REFERENCES incidents(incident_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_timeline_incident ON incident_timeline(incident_id);

-- 7. Diagnostic Hypotheses
CREATE TABLE IF NOT EXISTS diagnoses (
    diagnosis_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    incident_id TEXT,
    primary_hypothesis TEXT NOT NULL,
    evidence_strength TEXT NOT NULL, -- HIGH, MEDIUM, LOW
    evidence_details TEXT NOT NULL,
    competing_hypotheses_json TEXT NOT NULL,
    recommended_action TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_diagnoses_timestamp ON diagnoses(timestamp);

-- 8. Data Quality & Self-Monitoring
CREATE TABLE IF NOT EXISTS data_quality (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    measurements_collected INTEGER DEFAULT 0,
    missing_measurements INTEGER DEFAULT 0,
    invalid_measurements INTEGER DEFAULT 0,
    counter_resets INTEGER DEFAULT 0,
    interface_changes INTEGER DEFAULT 0,
    probe_failures INTEGER DEFAULT 0,
    cpu_usage_pct REAL,
    memory_usage_mb REAL,
    db_size_kb REAL,
    status TEXT NOT NULL -- HEALTHY, DEGRADED, STALE
);

-- 9. Application Experience Estimates
CREATE TABLE IF NOT EXISTS application_experience (
    experience_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    video_call_score TEXT NOT NULL, -- EXCELLENT, GOOD, FAIR, POOR
    gaming_score TEXT NOT NULL,
    web_browsing_score TEXT NOT NULL,
    file_transfer_score TEXT NOT NULL,
    limiting_factor TEXT,
    is_simulation INTEGER DEFAULT 0
);

-- 10. Monitoring Controller State
CREATE TABLE IF NOT EXISTS monitoring_state (
    state_id INTEGER PRIMARY KEY CHECK (state_id = 1),
    active_interface TEXT NOT NULL,
    monitoring_mode TEXT NOT NULL, -- NORMAL, WARNING, CRITICAL, RECOVERY
    current_interval_sec REAL NOT NULL,
    last_collection_timestamp TEXT NOT NULL,
    reason_for_mode TEXT,
    is_running INTEGER DEFAULT 1
);
