# NetIntel Verification & Testing Suite

This document describes the automated test suite, coverage areas, and validation methods for the NetIntel platform.

---

## 1. Test Suite Summary

NetIntel features a 100% automated `pytest` test suite covering unit transformations, calculations, data integrity, and end-to-end pipeline flows.

```bash
pytest tests/ -v
```

All 23 test cases execute in ~2.5 seconds with zero mock-only dependencies:

| Test Module | Coverage Area | Key Assertions Verified |
| :--- | :--- | :--- |
| `test_metrics.py` | Rate and utilization calculations | Unit conversions, Mbps/PPS formulas, NULL handling when speed is 0 |
| `test_jitter.py` | RFC 3550 delay variance | Initial undefined sample handling, low-pass filter formula accuracy |
| `test_database.py` | SQLite schema and CRUD | WAL mode activation, table foreign keys, metric/incident storage |
| `test_csv_export.py` | Automatic CSV generation | Header provisioning, atomic append, thread-safe writing |
| `test_anomaly.py` | Statistical & change-point algorithms | Z-score, Tukey IQR bounds, CUSUM step-shift detection |
| `test_diagnosis.py` | Multi-signal correlation rules | Congestion, upstream ISP, Wi-Fi bottlenecks, nominal conditions |
| `test_incidents.py` | Hysteresis state machine | Debounce trigger counter (3 samples), resolution cooldown (3 samples) |
| `test_collectors.py` | Hardware discovery & system collector | Interface catalog, default gateway discovery, process CPU/RAM tracking |
| `test_pipeline_integration.py`| End-to-end data pipeline | Collector -> Processor -> DB -> CSV export data flow validation |
