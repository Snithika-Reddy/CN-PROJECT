# NetIntel Power BI Data Dictionary

Comprehensive column definitions, data types, physical constraints, and business logic for all exported tabular datasets.

---

### Table: `network_metrics.csv` (FactNetworkMetrics)

| Column Name | Data Type | Description | Range / Example |
| :--- | :--- | :--- | :--- |
| `timestamp` | DateTime (ISO) | UTC Timestamp of measurement | `2026-09-30T09:15:00.000Z` |
| `date` | Date | Extracted date component | `2026-09-30` |
| `time` | Time | Extracted time component | `14:45:02` |
| `epoch_time` | Float | POSIX epoch time in seconds | `1790760302.12` |
| `interface` | Text | Name of the monitored NIC | `Wi-Fi`, `Ethernet` |
| `upload_mbps` | Decimal | Upload rate calculated via differential byte count | `0.0000 - 10000.0000` |
| `download_mbps` | Decimal | Download rate calculated via differential byte count | `0.0000 - 10000.0000` |
| `bytes_sent` | Integer (64) | Cumulative bytes transmitted on NIC | `0 to 2^63-1` |
| `bytes_recv` | Integer (64) | Cumulative bytes received on NIC | `0 to 2^63-1` |
| `packets_sent` | Integer (64) | Cumulative packets transmitted | `0 to 2^63-1` |
| `packets_recv` | Integer (64) | Cumulative packets received | `0 to 2^63-1` |
| `packets_sent_per_sec` | Decimal | Egress packet rate (PPS) | `0.00 to 500000.00` |
| `packets_recv_per_sec` | Decimal | Ingress packet rate (PPS) | `0.00 to 500000.00` |
| `latency_ms` | Decimal | ICMP round-trip time in milliseconds | `0.1 to 10000.0` (or empty) |
| `jitter_ms` | Decimal | RFC 3550 Inter-Packet Delay Variation | `0.0 to 1000.0` (or empty) |
| `packet_loss_percent` | Decimal | Loss % over multi-probe window | `0.00 to 100.00%` |
| `estimated_utilization_percent` | Decimal | Throughput / Hardware Link Speed | `0.00 to 100.00%` (or empty) |
| `health_score` | Decimal | Weighted 0-100 holistic health index | `0.0 to 100.0` |
| `stability_score` | Decimal | Rolling variance consistency index | `0.0 to 100.0` |
| `monitoring_mode` | Text | Adaptive frequency mode | `NORMAL`, `WARNING`, `CRITICAL`, `RECOVERY` |
| `is_simulation` | Integer | Flag: 0 = Real hardware telemetry, 1 = Synthetic | `0` or `1` |
| `is_replay` | Integer | Flag: 0 = Live real-time, 1 = Replay stream | `0` or `1` |
| `data_quality_flag` | Text | Validation result | `VALID`, `COUNTER_RESET`, `SUSPECT` |

---

### Table: `latency_metrics.csv` (FactLatency)

| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `timestamp` | DateTime | Probe sample timestamp |
| `target_name` | Text | Target identifier (`gateway`, `google_dns`, `cloudflare_dns`) |
| `target_host` | Text | Target IPv4 address (e.g., `192.168.1.1`, `8.8.8.8`) |
| `probes_sent` | Integer | Probes dispatched in window (e.g., 5) |
| `probes_received` | Integer | Valid echo replies received |
| `packet_loss_percent`| Decimal | Loss % across probe window |
| `latency_min_ms` | Decimal | Minimum RTT among probes |
| `latency_avg_ms` | Decimal | Mean RTT among probes |
| `latency_max_ms` | Decimal | Maximum RTT among probes |
| `jitter_ms` | Decimal | Mean consecutive RTT variation |
| `status` | Text | Reached status or error summary |

---

### Table: `incidents.csv` (FactIncidents)

| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `incident_id` | Text (PK) | Unique incident ID (e.g. `INC-1790760302-a1b2c3`) |
| `start_timestamp` | DateTime | Timestamp when debounce threshold exceeded |
| `end_timestamp` | DateTime | Timestamp when recovery stabilized |
| `duration_seconds` | Decimal | Total incident lifetime in seconds |
| `status` | Text | `OPEN`, `RECOVERING`, `RESOLVED` |
| `severity` | Text | `WARNING`, `CRITICAL` |
| `trigger_reason` | Text | Explicit textual trigger conditions |
| `peak_latency_ms` | Decimal | Worst latency recorded during incident |
| `peak_jitter_ms` | Decimal | Worst jitter recorded during incident |
| `peak_packet_loss_percent`| Decimal | Worst loss recorded during incident |
| `peak_utilization_percent` | Decimal | Worst link saturation recorded |
| `min_health_score` | Decimal | Lowest health score reached |
| `min_stability_score` | Decimal | Lowest stability score reached |
| `diagnosis_summary`| Text | Multi-signal diagnostic outcome |
| `is_simulation` | Integer | 0 = Real, 1 = Simulated |
