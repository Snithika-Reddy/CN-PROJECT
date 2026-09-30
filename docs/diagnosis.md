# NetIntel Multi-Signal Diagnosis & Hypotheses Framework

This document details the multi-signal correlation matrix, competing hypotheses ranking, and calibrated evidence scoring system.

---

## 1. Multi-Signal Correlation Matrix

| Condition | Gateway Latency | Public Latency | Packet Loss | Utilization | Jitter | Evaluated Primary Hypothesis |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **A** | Normal (<10ms) | Normal (<30ms) | 0% | Moderate (<50%) | Normal (<3ms) | **Nominal Operating State** |
| **B** | Normal (<10ms) | High (>100ms) | Elevated (>2%) | Low (<40%) | Elevated | **Upstream ISP / Transit WAN Peering** |
| **C** | High (>35ms) | High (>100ms) | Elevated (>2%) | Low (<40%) | High (>15ms) | **Local LAN / Wi-Fi / Router Bottleneck** |
| **D** | Elevated | High (>120ms) | Elevated (>3%) | High (>85%) | High (>25ms) | **Local Interface Congestion / Bufferbloat** |
| **E** | Normal (<10ms) | Normal (<40ms) | High (>5%) | Low (<30%) | Moderate | **Physical Link / Wireless RF Interference** |

---

## 2. Competing Hypotheses & Evidence Strength

NetIntel strictly avoids declaring "Confirmed Root Causes". In distributed networks without access to internal carrier routers, observability systems can only formulate **calibrated hypotheses** supported by empirical evidence.

Each diagnostic report evaluates 4 competing hypotheses simultaneously:
1. `Local Interface Congestion / Bufferbloat`
2. `Local Network / Wi-Fi / Gateway Issue`
3. `Upstream ISP / WAN Peering Degradation`
4. `Physical Link / Wireless RF Interference`

### Evidence Scoring Criteria
- **HIGH Evidence (Score $\ge 0.70$):** Multiple correlating signals point unambiguously toward the hypothesis (e.g. utilization at 95% with 4x baseline latency and 3.8% loss).
- **MEDIUM Evidence (Score $0.40 - 0.69$):** Some supporting signals present, but counter-evidence exists (e.g. latency elevated without high utilization).
- **LOW Evidence (Score $< 0.40$):** Insufficient telemetry indicators to support the hypothesis.
