"""Estimated Application Experience Engine.

Evaluates empirical physical layer telemetry against profile-specific QoS requirements
for Video Conferencing, Online Gaming, Web Browsing, and Large File Transfers.
Explicitly labeled as 'Estimated Application Experience' based on network parameters.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class AppExperienceReport:
    timestamp_iso: str
    video_call_score: str  # 'EXCELLENT', 'GOOD', 'FAIR', 'POOR'
    gaming_score: str
    web_browsing_score: str
    file_transfer_score: str
    primary_limiting_factor: str
    detailed_evaluations: dict[str, dict[str, Any]]


class ApplicationExperienceEngine:
    """Calculates QoS satisfaction for typical network workloads."""

    def __init__(self, profiles: dict[str, dict[str, float]] | None = None):
        self.profiles = profiles or {
            "video_call": {
                "max_latency_ms": 100.0,
                "max_jitter_ms": 20.0,
                "max_packet_loss_pct": 1.5,
                "min_download_mbps": 3.0,
                "min_upload_mbps": 1.5
            },
            "gaming": {
                "max_latency_ms": 50.0,
                "max_jitter_ms": 10.0,
                "max_packet_loss_pct": 0.5,
                "min_download_mbps": 5.0,
                "min_upload_mbps": 2.0
            },
            "web_browsing": {
                "max_latency_ms": 150.0,
                "max_jitter_ms": 35.0,
                "max_packet_loss_pct": 3.0,
                "min_download_mbps": 2.0,
                "min_upload_mbps": 0.5
            },
            "file_transfer": {
                "max_latency_ms": 300.0,
                "max_jitter_ms": 50.0,
                "max_packet_loss_pct": 5.0,
                "min_download_mbps": 15.0,
                "min_upload_mbps": 5.0
            }
        }

    def _evaluate_profile(
        self,
        profile_key: str,
        latency_ms: float | None,
        jitter_ms: float | None,
        loss_pct: float,
        down_mbps: float,
        up_mbps: float
    ) -> tuple[str, list[str]]:
        """Grade profile satisfaction and identify specific bottleneck metrics."""
        cfg = self.profiles.get(profile_key, {})
        lat = latency_ms or 20.0
        jit = jitter_ms or 2.0
        bottlenecks: list[str] = []

        penalty_points = 0
        if lat > cfg.get("max_latency_ms", 100.0):
            penalty_points += 2
            bottlenecks.append(f"Latency {lat:.1f}ms exceeds limit {cfg.get('max_latency_ms')}ms")
        elif lat > cfg.get("max_latency_ms", 100.0) * 0.7:
            penalty_points += 1

        if jit > cfg.get("max_jitter_ms", 20.0):
            penalty_points += 2
            bottlenecks.append(f"Jitter {jit:.1f}ms exceeds limit {cfg.get('max_jitter_ms')}ms")

        if loss_pct > cfg.get("max_packet_loss_pct", 1.0):
            penalty_points += 3
            bottlenecks.append(f"Packet loss {loss_pct:.1f}% exceeds limit {cfg.get('max_packet_loss_pct')}%")

        if down_mbps < cfg.get("min_download_mbps", 5.0) and down_mbps > 0.1:
            penalty_points += 1
            bottlenecks.append(f"Download {down_mbps:.1f}Mbps below target")

        if up_mbps < cfg.get("min_upload_mbps", 1.0) and up_mbps > 0.1:
            penalty_points += 1
            bottlenecks.append(f"Upload {up_mbps:.1f}Mbps below target")

        if penalty_points == 0:
            return "EXCELLENT", bottlenecks
        elif penalty_points <= 2:
            return "GOOD", bottlenecks
        elif penalty_points <= 4:
            return "FAIR", bottlenecks
        else:
            return "POOR", bottlenecks

    def evaluate(
        self,
        timestamp_iso: str,
        latency_ms: float | None,
        jitter_ms: float | None,
        packet_loss_pct: float,
        download_mbps: float,
        upload_mbps: float
    ) -> AppExperienceReport:
        """Generate comprehensive application experience assessment."""
        v_score, v_bot = self._evaluate_profile("video_call", latency_ms, jitter_ms, packet_loss_pct, download_mbps, upload_mbps)
        g_score, g_bot = self._evaluate_profile("gaming", latency_ms, jitter_ms, packet_loss_pct, download_mbps, upload_mbps)
        w_score, w_bot = self._evaluate_profile("web_browsing", latency_ms, jitter_ms, packet_loss_pct, download_mbps, upload_mbps)
        f_score, f_bot = self._evaluate_profile("file_transfer", latency_ms, jitter_ms, packet_loss_pct, download_mbps, upload_mbps)

        all_bottlenecks = v_bot + g_bot + w_bot + f_bot
        primary_limit = all_bottlenecks[0] if all_bottlenecks else "None (Conditions optimal)"

        return AppExperienceReport(
            timestamp_iso=timestamp_iso,
            video_call_score=v_score,
            gaming_score=g_score,
            web_browsing_score=w_score,
            file_transfer_score=f_score,
            primary_limiting_factor=primary_limit,
            detailed_evaluations={
                "video_call": {"score": v_score, "bottlenecks": v_bot},
                "gaming": {"score": g_score, "bottlenecks": g_bot},
                "web_browsing": {"score": w_score, "bottlenecks": w_bot},
                "file_transfer": {"score": f_score, "bottlenecks": f_bot}
            }
        )
