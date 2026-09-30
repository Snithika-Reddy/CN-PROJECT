"""Historical Incident Replay Engine.

Streams previously captured historical incidents frame-by-frame in simulated real-time
for viva presentations, lab debugging, and model validation.
All emitted samples are strictly marked with `is_replay = True`.
"""

from collections.abc import Generator
import logging
import time
from typing import Any
import pandas as pd

from ..processing.metrics import ConsolidatedMetric
from ..storage.repositories import MetricsRepository

logger = logging.getLogger(__name__)


class IncidentReplayEngine:
    """Replays historical telemetry sessions chronologically."""

    def __init__(self, metrics_repo: MetricsRepository):
        self.repo = metrics_repo
        self.is_active = False

    def load_incident_records(self, start_iso: str, end_iso: str) -> pd.DataFrame:
        """Fetch recorded real telemetry for a given incident time bracket."""
        df = self.repo.get_metrics_by_timerange(start_iso, end_iso, is_simulation=False)
        return df

    def stream_replay(
        self,
        records_df: pd.DataFrame,
        speed_multiplier: float = 1.0
    ) -> Generator[dict[str, Any], None, None]:
        """Generator yielding historical records with paced time delays."""
        if records_df.empty:
            return

        self.is_active = True
        records = records_df.to_dict(orient="records")

        for i, row in enumerate(records):
            if not self.is_active:
                break

            # Explicitly mark replay flag
            row["is_replay"] = True
            row["monitoring_mode"] = "REPLAY"

            yield row

            if i < len(records) - 1:
                # Time delta pacing
                t_curr = row.get("epoch_time", 0.0)
                t_next = records[i + 1].get("epoch_time", t_curr + 1.0)
                delay = max(0.1, min(5.0, (t_next - t_curr) / max(0.1, speed_multiplier)))
                time.sleep(delay)

        self.is_active = False

    def stop(self) -> None:
        """Halt active replay streaming."""
        self.is_active = False
