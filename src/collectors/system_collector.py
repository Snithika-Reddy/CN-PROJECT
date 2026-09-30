"""System and Health Self-Monitoring Collector.

Gathers host machine resource utilization (CPU %, RAM MB/%, open sockets, database size)
to monitor NetIntel's own operational footprint and data quality integrity.
"""

from dataclasses import dataclass
import os
import time
import psutil


@dataclass
class SystemMetrics:
    timestamp: float
    cpu_percent: float
    memory_used_mb: float
    memory_percent: float
    process_threads: int
    db_size_kb: float


class SystemCollector:
    """Monitors collector process resource consumption and local file health."""

    def __init__(self, db_path: str = "database/network_monitor.db"):
        self.db_path = db_path
        self.process = psutil.Process(os.getpid())

    def sample(self) -> SystemMetrics:
        """Sample host and process resource utilization."""
        now = time.time()
        cpu_pct = psutil.cpu_percent(interval=None)

        try:
            mem_info = self.process.memory_info()
            mem_mb = round(mem_info.rss / (1024.0 * 1024.0), 2)
            threads = self.process.num_threads()
        except Exception:
            mem_mb = 0.0
            threads = 1

        total_mem = psutil.virtual_memory()
        mem_pct = round(total_mem.percent, 2)

        # Database file size
        db_size_kb = 0.0
        if os.path.exists(self.db_path):
            try:
                db_size_kb = round(os.path.getsize(self.db_path) / 1024.0, 2)
            except Exception:
                db_size_kb = 0.0

        return SystemMetrics(
            timestamp=now,
            cpu_percent=round(cpu_pct, 2),
            memory_used_mb=mem_mb,
            memory_percent=mem_pct,
            process_threads=threads,
            db_size_kb=db_size_kb
        )
