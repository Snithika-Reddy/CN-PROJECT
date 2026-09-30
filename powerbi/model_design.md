# Power BI Star Schema Model Design

This document details the relational data model implemented for NetIntel in Power BI.

---

## 1. Schema Diagram (Star Schema)

```text
       +-----------------------+
       |       DimTime         |
       |-----------------------|
       | Date                  |
       | Hour                  |
       | DayOfWeek             |
       | IsWeekend             |
       +-----------+-----------+
                   | 1
                   |
                   | *
+------------------+------------------+         +-----------------------+
|        FactNetworkMetrics           | *     1 |     DimInterface      |
|-------------------------------------|---------|-----------------------|
| metric_id (PK)                      |         | interface_name (PK)   |
| timestamp                           |         | is_wireless           |
| interface_name (FK)                 |         | speed_mbps            |
| upload_mbps                         |         +-----------------------+
| download_mbps                       |
| packets_sent_per_sec                |         +-----------------------+
| packets_recv_per_sec                | 1     * |      FactIncidents    |
| latency_ms                          |---------|-----------------------|
| jitter_ms                           |         | incident_id (PK)      |
| packet_loss_percent                 |         | start_timestamp       |
| estimated_utilization_percent       |         | severity              |
| health_score                        |         | duration_seconds      |
| stability_score                     |         | diagnosis_summary     |
| is_simulation                       |         +-----------------------+
+-------------------------------------+
                   | 1
                   |
                   | *
       +-----------+-----------+
       |     FactAnomalies     |
       |-----------------------|
       | anomaly_id (PK)       |
       | timestamp             |
       | metric_name           |
       | observed_value        |
       | deviation_percent     |
       | severity              |
       | detection_method      |
       +-----------------------+
```

---

## 2. Key DAX Measures

```dax
// Average Health Score
AvgHealthScore = AVERAGE(FactNetworkMetrics[health_score])

// 95th Percentile Latency
P95_Latency = PERCENTILE.INC(FactNetworkMetrics[latency_ms], 0.95)

// Total Data Volume Transferred (Megabytes)
TotalDataVolumeMB =
    DIVIDE(
        SUM(FactNetworkMetrics[bytes_sent]) + SUM(FactNetworkMetrics[bytes_recv]),
        1048576,
        0
    )

// SLA Latency Compliance Rate (< 50ms)
LatencyCompliancePct =
    DIVIDE(
        COUNTROWS(FILTER(FactNetworkMetrics, FactNetworkMetrics[latency_ms] <= 50.0)),
        COUNTROWS(FactNetworkMetrics),
        0
    ) * 100

// Active Incident Count
ActiveIncidentCount =
    CALCULATE(
        COUNTROWS(FactIncidents),
        FactIncidents[status] = "OPEN" || FactIncidents[status] = "RECOVERING"
    )
```
