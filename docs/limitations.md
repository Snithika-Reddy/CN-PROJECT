# NetIntel Limitations & Technical Boundary Statement

In accordance with strict academic integrity, this document details the real-world boundaries, assumptions, and physical constraints of the NetIntel platform.

---

## 1. Network Boundary Constraints

1. **ICMP Filtering:** Many enterprise firewalls and carrier routers prioritize or deprioritize ICMP Echo requests (Control Plane Rate Limiting). While ICMP provides an excellent non-intrusive probe mechanism, packet loss on ICMP may not always 100% reflect TCP data loss.
2. **Interface Speed vs. ISP Subscription:** The operating system knows the negotiated hardware link speed of the physical NIC (e.g. 1000 Mbps Ethernet or 866 Mbps 802.11ac Wi-Fi). It cannot automatically divine the external billing subscription plan of the ISP (e.g. a 150 Mbps fiber tier). Hence, utilization is labeled **"Estimated Interface Utilization"** rather than "ISP Contract Utilization".
3. **Application Experience as an Estimate:** Experience scores for gaming, video calls, web browsing, and file transfers are rule-based estimates derived from physical QoS metrics (RTT, IPDV, packet loss, bandwidth). Deep Packet Inspection (DPI) or per-process socket attribution would require kernel drivers (e.g. WinPcap/NDIS).

---

## 2. Platform & OS Scope
1. **Host-Level Observability:** NetIntel monitors the perspective of the host system. It does not replace internal SNMP/NetFlow monitoring on core enterprise switches and backbone routers.
2. **Power BI Local Refresh:** As documented in the Power BI specifications, local Power BI Desktop requires a manual click of the Refresh button or gateway schedule; it does not support unbounded WebSocket streaming to local files.
