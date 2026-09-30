# NetIntel Output Directory

This directory contains the latest generated intelligence summaries, technical viva defense evaluations, and executive exports from NetIntel.

## Generated Artifacts

- **[`viva_report.md`](file:///./viva_report.md)**: Complete technical summary for college viva defense and evaluation.
- **[`executive_summary.json`](file:///./executive_summary.json)**: Machine-readable JSON telemetry snapshot.
- **[`telemetry_summary.txt`](file:///./telemetry_summary.txt)**: Formatted plain-text summary of health, SLA compliance, and metrics.
- **Power BI Relational Data Mart**: Located at [`../data/exports/star_schema/`](file:///../data/exports/star_schema/)
- **Raw Telemetry Exports**: Located at [`../data/exports/`](file:///../data/exports/)
- **Authoritative Database**: Located at [`../database/network_monitor.db`](file:///../database/network_monitor.db)

## How to Regenerate Outputs

```bash
# Using NetIntel Manager
python manage.py report

# Or using batch launcher
run.bat
```
