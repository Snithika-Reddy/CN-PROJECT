# NetIntel Telemetry & Engineering Methodology

This document details the mathematical, networking, and statistical methodologies underpinning **NetIntel**.

---

## 1. Per-NIC Traffic Isolation vs. Aggregation Flaw

### The Flaw in Naive Collectors
Conventional monitoring scripts invoke `psutil.net_io_counters()` without arguments, which returns the sum total across all physical, loopback, and virtual interfaces on the system. When interface utilization is subsequently calculated using the link speed of a single network card (e.g. 866 Mbps Wi-Fi), the numerator contains loopback, Docker, and VPN traffic while the denominator represents only the Wi-Fi link. This introduces severe mathematical inconsistency and false utilization spikes.

### NetIntel Pernic Solution
NetIntel enforces:
```python
psutil.net_io_counters(pernic=True)[active_interface_name]
```
Traffic rates are calculated strictly against the specific active hardware interface:
$$\Delta\text{Bytes} = \text{Bytes}_t - \text{Bytes}_{t-1}$$
$$\text{Throughput (Mbps)} = \frac{\Delta\text{Bytes} \times 8}{\Delta t \times 1,000,000}$$

Counter resets (from interface reconnects or machine reboot where $\Delta\text{Bytes} < 0$) are detected with hysteresis clamping to prevent negative throughput anomalies.

---

## 2. Multi-Target Probing & Gateway Disaggregation

### Why Single-Endpoint Latency is Misleading
Labeling a ping to `google.com` as "Internet Latency" fails to identify where bottlenecks reside. If round-trip delay spikes to 120 ms, the user cannot determine if their home Wi-Fi is congested or if an upstream transit provider is experiencing route flaps.

### Disaggregated Multi-Target Probing
NetIntel actively disaggregates network segments:
1. **Local Default Gateway:** Probes the first-hop router IP (auto-detected via route tables). Isolates local Wi-Fi, Ethernet, and home router health.
2. **Public Core Anycast DNS (8.8.8.8 & 1.1.1.1):** Measures wide-area Internet transit latency.

Diagnostic Rule:
$$\text{If } \text{RTT}_{\text{gateway}} \le 10\text{ms} \text{ and } \text{RTT}_{\text{public}} \ge 90\text{ms} \implies \text{Upstream ISP/Transit Issue}$$
$$\text{If } \text{RTT}_{\text{gateway}} \ge 35\text{ms} \text{ and } \text{RTT}_{\text{public}} \ge 90\text{ms} \implies \text{Local Wi-Fi / LAN Bottleneck}$$

---

## 3. RFC 3550 Inter-Packet Delay Variation (Jitter)

NetIntel calculates jitter using the official **RFC 3550 standard algorithm** (RTP: A Transport Protocol for Real-Time Applications):
$$D(i-1, i) = |RTT_i - RTT_{i-1}|$$
$$J(i) = J(i-1) + \frac{D(i-1, i) - J(i-1)}{16}$$

This first-order low-pass filter provides a smooth, statistically robust estimate of delay variation that eliminates transient single-probe noise while remaining responsive to sustained queue jitter.

---

## 4. Multi-Probe Window Packet Loss

Packet loss is never defined from a single isolated ping request. NetIntel uses a configurable probe burst window ($N \in [5, 10]$):
$$\text{Packet Loss \%} = \frac{N_{\text{sent}} - N_{\text{received}}}{N_{\text{sent}}} \times 100$$
This prevents false alarms from solitary dropped frames while rapidly capturing sustained bursts.
