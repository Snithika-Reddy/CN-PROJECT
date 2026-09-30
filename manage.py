#!/usr/bin/env python3
"""NetIntel Master Management & Execution CLI.

Provides unified command-line control for the entire NetIntel platform:
- Telemetry Collection Engine
- Streamlit Web Observability Dashboard
- Power BI Live REST Streaming API Server
- Power BI Desktop Auto-Refresher Daemon
- Star Schema Data Exporter
- Controlled Network Simulation Engine
- Automated Test Suite Runner
"""

import argparse
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))


def print_banner():
    banner = r"""
  _   _      _   ___       _       _ 
 | \ | | ___| |_|_ _|_ __ | |_ ___| |
 |  \| |/ _ \ __|| || '_ \| __/ _ \ |
 | |\  |  __/ |_ | || | | | ||  __/ |
 |_| \_|\___|\__|___|_| |_|\__\___|_|
   Real-Time Network Telemetry & Intelligence
   Live Power BI Streaming & Analytics Platform
    """
    print(banner)


def cmd_engine(args):
    """Run continuous telemetry collection service."""
    from src.main import NetIntelService
    print("[*] Starting NetIntel Core Telemetry Engine...")
    service = NetIntelService(config_path=args.config)
    if args.once:
        sample = service.step()
        if sample:
            print(f"[+] Sample collected: Health={sample.health_score}/100, Latency={sample.latency_ms or 0:.1f}ms")
    else:
        service.run_loop()


def cmd_dashboard(args):
    """Launch Streamlit web observability dashboard."""
    print(f"[*] Launching Streamlit Web Dashboard on port {args.port}...")
    app_path = Path("dashboard/app.py").resolve()
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path), "--server.port", str(args.port)]
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n[*] Dashboard stopped.")


def cmd_powerbi_stream(args):
    """Start local Power BI HTTP REST streaming server."""
    from src.powerbi.api_server import PowerBIAPIServer
    print(f"[*] Starting Power BI Live REST API on http://{args.host}:{args.port}...")
    print(f"[*] Endpoint: http://{args.host}:{args.port}/api/live")
    print(f"[*] Endpoint: http://{args.host}:{args.port}/api/metrics")
    server = PowerBIAPIServer(host=args.host, port=args.port)
    server.start()
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n[*] Stopping Power BI API server...")
        server.stop()


def cmd_powerbi_export(args):
    """Extract and export full Star Schema tables from SQLite to CSV."""
    from src.storage.database import DatabaseManager
    from src.powerbi.exporter import PowerBIExporter

    print("[*] Generating authoritative Star Schema for Power BI...")
    db = DatabaseManager()
    exporter = PowerBIExporter()
    counts = exporter.export_from_database(db)

    print("[+] Successfully exported Star Schema tables to data/exports/star_schema/:")
    for tbl, count in counts.items():
        print(f"    - {tbl:<26}: {count:>5} records")


def cmd_auto_refresh(args):
    """Run Power BI Desktop auto-refresher daemon."""
    from src.powerbi.auto_refresh import PowerBIAutoRefresher
    print(f"[*] Starting Power BI Desktop Auto-Refresher (Interval: {args.interval}s)...")
    refresher = PowerBIAutoRefresher(interval_sec=args.interval)
    refresher.start()
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n[*] Stopping auto-refresher...")
        refresher.stop()


def cmd_simulate(args):
    """Inject a realistic synthetic network scenario."""
    from src.simulation.scenarios import SCENARIOS
    from src.storage.database import DatabaseManager
    from src.storage.repositories import MetricsRepository
    from src.storage.csv_exporter import CSVExporter
    from src.processing.metrics import make_consolidated_metric

    scenario_key = args.scenario
    if scenario_key not in SCENARIOS:
        print(f"[-] Unknown scenario '{scenario_key}'. Choose from: {list(SCENARIOS.keys())}")
        return

    sc = SCENARIOS[scenario_key]
    print(f"[*] Injecting simulation: {sc.name}")
    print(f"    Description: {sc.description}")

    db = DatabaseManager()
    metrics_repo = MetricsRepository(db)
    csv_exporter = CSVExporter()

    for i in range(args.count):
        metric = make_consolidated_metric(
            interface_name="Wi-Fi (Simulated)",
            upload_mbps=sc.upload_mbps,
            download_mbps=sc.download_mbps,
            bytes_sent=int(sc.upload_mbps * 125000),
            bytes_recv=int(sc.download_mbps * 125000),
            packets_sent=150,
            packets_recv=300,
            packets_sent_per_sec=150.0,
            packets_recv_per_sec=300.0,
            latency_ms=sc.latency_ms,
            jitter_ms=sc.jitter_ms,
            packet_loss_pct=sc.packet_loss_pct,
            interface_speed_mbps=100.0,
            health_score=sc.health_score,
            stability_score=sc.stability_score,
            monitoring_mode="SIMULATION",
            is_simulation=True
        )
        metrics_repo.save_metric(metric)
        csv_exporter.append_metric(metric)
        print(f"    Sample {i+1}/{args.count}: Latency={metric.latency_ms:.1f}ms, Loss={metric.packet_loss_pct:.1f}%, Health={metric.health_score:.0f}/100")
        time.sleep(0.5)

    print("[+] Simulation samples injected successfully!")


def cmd_run_all(args):
    """Launch engine, dashboard, and Power BI API server concurrently."""
    print_banner()
    print("[*] Launching NetIntel Unified Multi-Process Stack...")

    processes = []

    # 1. Start Power BI REST API in a daemon thread
    from src.powerbi.api_server import PowerBIAPIServer
    api_server = PowerBIAPIServer(host="127.0.0.1", port=8080)
    api_server.start()
    print("[+] Power BI Live REST API listening at http://127.0.0.1:8080")

    # 2. Launch Core Telemetry Engine in background thread
    from src.main import NetIntelService
    stop_event = threading.Event()
    service = NetIntelService()
    engine_thread = threading.Thread(
        target=service.run_loop,
        kwargs={"stop_event": stop_event},
        name="EngineThread",
        daemon=True
    )
    engine_thread.start()
    print("[+] Core Telemetry Engine running continuously.")

    # 3. Export Star Schema initially
    from src.powerbi.exporter import PowerBIExporter
    exporter = PowerBIExporter()
    exporter.export_from_database(service.db)
    print("[+] Star Schema tables synchronized for Power BI.")

    # 4. Launch Streamlit Web Dashboard (foreground blocking)
    app_path = Path("dashboard/app.py").resolve()
    print(f"[+] Starting Streamlit Dashboard on http://localhost:{args.port} ...")
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path), "--server.port", str(args.port)]

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n[*] Stopping NetIntel services...")
    finally:
        stop_event.set()
        api_server.stop()
        print("[*] All NetIntel services stopped cleanly.")


def cmd_test(args):
    """Run full test suite."""
    print("[*] Running pytest validation suite...")
    cmd = [sys.executable, "-m", "pytest", "-v"]
    if args.k:
        cmd.extend(["-k", args.k])
    subprocess.run(cmd)


def cmd_status(args):
    """Display system status, database metrics, and export file details."""
    from src.storage.database import DatabaseManager

    db = DatabaseManager()
    print("\n--- NetIntel System Status ---")
    try:
        metrics_cnt = db.query_df("SELECT COUNT(*) as c FROM network_metrics")["c"].iloc[0]
        probes_cnt = db.query_df("SELECT COUNT(*) as c FROM latency_probes")["c"].iloc[0]
        inc_cnt = db.query_df("SELECT COUNT(*) as c FROM incidents")["c"].iloc[0]
        anom_cnt = db.query_df("SELECT COUNT(*) as c FROM anomalies")["c"].iloc[0]
        print(f"Database Path : {db.db_path} (Size: {db.db_path.stat().st_size / 1024:.1f} KB)")
        print(f"Metrics Rows  : {metrics_cnt}")
        print(f"Probes Rows   : {probes_cnt}")
        print(f"Incidents     : {inc_cnt}")
        print(f"Anomalies     : {anom_cnt}")
    except Exception as exc:
        print(f"Could not read database stats: {exc}")

    print("\n--- Power BI Export Datasets ---")
    export_dir = Path("data/exports")
    if export_dir.exists():
        for csv_file in sorted(export_dir.glob("*.csv")):
            size_kb = csv_file.stat().st_size / 1024
            mtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(csv_file.stat().st_mtime))
            print(f"  {csv_file.name:<28} : {size_kb:>6.1f} KB (Updated: {mtime})")


def cmd_report(args):
    """Generate comprehensive intelligence and viva reports to output/ directory."""
    from src.storage.database import DatabaseManager
    from src.reporting.report_generator import ReportGenerator

    print("[*] Generating NetIntel evaluation & intelligence reports...")
    db = DatabaseManager()
    rep = ReportGenerator(db)
    results = rep.export_all_outputs(output_dir=args.outdir)

    print(f"\n[+] Successfully generated output artifacts in '{args.outdir}/':")
    for key, path in results.items():
        print(f"    - {key:<24}: {path}")

    txt_path = results.get("telemetry_summary_txt")
    if txt_path and Path(txt_path).exists():
        print("\n" + Path(txt_path).read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description="NetIntel Real-Time Network Intelligence Platform")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # run-all
    p_all = subparsers.add_parser("run-all", help="Launch engine, dashboard, and Power BI API concurrently")
    p_all.add_argument("--port", type=int, default=8501, help="Dashboard port")

    # engine
    p_eng = subparsers.add_parser("engine", help="Run telemetry collection engine")
    p_eng.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    p_eng.add_argument("--once", action="store_true", help="Run single collection sample and exit")

    # dashboard
    p_dash = subparsers.add_parser("dashboard", help="Launch Streamlit web dashboard")
    p_dash.add_argument("--port", type=int, default=8501, help="Streamlit port")

    # powerbi-stream
    p_pbi = subparsers.add_parser("powerbi-stream", help="Start Power BI local REST API server")
    p_pbi.add_argument("--host", default="127.0.0.1", help="Host interface")
    p_pbi.add_argument("--port", type=int, default=8080, help="Port")

    # powerbi-export
    subparsers.add_parser("powerbi-export", help="Synchronize full Star Schema CSVs for Power BI")

    # auto-refresh
    p_ar = subparsers.add_parser("auto-refresh", help="Run Power BI Desktop live auto-refresher daemon")
    p_ar.add_argument("--interval", type=int, default=5, help="Refresh interval in seconds")

    # simulate
    p_sim = subparsers.add_parser("simulate", help="Inject simulated network scenarios")
    p_sim.add_argument("scenario", default="high_latency", nargs="?", help="Scenario key (normal, high_latency, packet_loss, etc.)")
    p_sim.add_argument("--count", type=int, default=10, help="Number of samples to inject")

    # test
    p_test = subparsers.add_parser("test", help="Execute test suite")
    p_test.add_argument("-k", help="Filter test names")

    # status
    subparsers.add_parser("status", help="Print system & telemetry status")

    # report
    p_rep = subparsers.add_parser("report", help="Generate comprehensive intelligence & viva report into output/")
    p_rep.add_argument("--outdir", default="output", help="Target output directory")

    args = parser.parse_args()

    if not args.command:
        print_banner()
        parser.print_help()
        return

    dispatch = {
        "run-all": cmd_run_all,
        "engine": cmd_engine,
        "dashboard": cmd_dashboard,
        "powerbi-stream": cmd_powerbi_stream,
        "powerbi-export": cmd_powerbi_export,
        "auto-refresh": cmd_auto_refresh,
        "simulate": cmd_simulate,
        "test": cmd_test,
        "status": cmd_status,
        "report": cmd_report,
    }

    fn = dispatch.get(args.command)
    if fn:
        fn(args)


if __name__ == "__main__":
    main()
