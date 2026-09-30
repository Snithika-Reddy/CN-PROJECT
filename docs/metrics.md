# NetIntel Telemetry Metrics Reference

Comprehensive catalog of network telemetry dimensions, units, calculation formulas, physical bounds, and interpretation guidelines.

---

| Metric Identifier | Units | Typical Range | Formula / Origin | Technical Interpretation |
| :--- | :--- | :--- | :--- | :--- |
| `upload_mbps` | Mbps | 0.0 - 1000.0 | $\frac{\Delta\text{BytesSent} \times 8}{\Delta t \times 10^6}$ | Egress transfer throughput on selected NIC. |
| `download_mbps` | Mbps | 0.0 - 1000.0 | $\frac{\Delta\text{BytesRecv} \times 8}{\Delta t \times 10^6}$ | Ingress transfer throughput on selected NIC. |
| `packets_sent_per_sec` | PPS | 0 - 500,000 | $\frac{\Delta\text{PacketsSent}}{\Delta t}$ | Egress packet frame transmission rate. |
| `packets_recv_per_sec` | PPS | 0 - 500,000 | $\frac{\Delta\text{PacketsRecv}}{\Delta t}$ | Ingress packet frame arrival rate. |
| `latency_ms` | ms | 1.0 - 300.0 | ICMP Echo Request RTT | Round-trip propagation and queuing delay. |
| `jitter_ms` | ms | 0.1 - 50.0 | RFC 3550 Filtered Variance | IPDV delay variation indicating buffer instability. |
| `packet_loss_pct` | % | 0.0 - 100.0% | $\frac{\text{Lost}}{\text{Sent}} \times 100$ | Transmission frame loss rate across probe window. |
| `estimated_utilization_pct` | % | 0.0 - 100.0% | $\frac{\text{Upload} + \text{Download}}{\text{NIC Speed}} \times 100$ | Percentage of hardware link capacity utilized. Returns NULL if hardware link speed is unknown. |
| `health_score` | 0-100 | 0.0 - 100.0 | Weighted normalized sum | Comprehensive index: "How good is the network now?" |
| `stability_score` | 0-100 | 0.0 - 100.0 | Rolling variance index | Consistency index: "How stable is the network over time?" |

---

## Technical Clarification: Hardware Utilization vs. ISP Plan
NetIntel labels link saturation explicitly as **"Estimated Interface Utilization"**. This measures the traffic relative to the physical or negotiated link speed of the local NIC (e.g., 1000 Mbps Gigabit Ethernet or 866 Mbps Wi-Fi 5). It does **not** assume knowledge of the external ISP billing tier (e.g. 100 Mbps broadband contract).
