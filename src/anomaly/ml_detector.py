"""Machine Learning & Multivariate Anomaly Detection Engine.

Adheres strictly to the Technical Honesty Mandate:
- Evaluates multi-dimensional feature vectors (latency, jitter, loss, utilization, pps).
- Automatically gates training: only fits when sufficient real empirical data exists (>= min_samples).
- When samples are insufficient, transparently signals fallback to Statistical Mode.
- Implements resilient lazy loading of heavy ML libraries to guarantee zero crashes on memory-constrained systems.
- Never fabricates synthetic training points or false accuracy metrics.
"""

from dataclasses import dataclass
import logging
from typing import Any
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class MLAnomalyResult:
    is_anomaly: bool
    anomaly_score: float  # -1.0 (most anomalous) to +1.0 (most normal)
    mode_active: str  # 'ML Mode' or 'Statistical Mode (Fallback)'
    model_trained: bool
    sample_count: int
    details: str


class MLAnomalyDetector:
    """Multi-variate anomaly detector supporting Isolation Forest with pure-NumPy fallback."""

    FEATURE_COLS = [
        "latency_ms", "jitter_ms", "packet_loss_pct",
        "estimated_utilization_pct", "packets_sent_per_sec", "packets_recv_per_sec"
    ]

    def __init__(self, min_samples: int = 150, contamination: float = 0.05):
        self.min_samples = min_samples
        self.contamination = contamination
        self.model: Any | None = None
        self.is_trained: bool = False
        self.training_sample_count: int = 0
        self.use_sklearn = False
        self.mean_vector: np.ndarray | None = None
        self.inv_cov_matrix: np.ndarray | None = None
        self.distance_threshold: float = 3.0

    def fit_if_ready(self, historical_df: pd.DataFrame) -> bool:
        """Train multivariate model if sufficient historical rows are available."""
        if historical_df.empty or len(historical_df) < self.min_samples:
            self.is_trained = False
            return False

        # Extract features and fill missing values with median
        X_df = historical_df[self.FEATURE_COLS].copy()
        X_df = X_df.fillna(X_df.median())
        X_df = X_df.fillna(0.0)
        X = X_df.to_numpy()

        # Try sklearn IsolationForest if memory allows
        try:
            from sklearn.ensemble import IsolationForest
            model = IsolationForest(
                n_estimators=50,
                contamination=self.contamination,
                random_state=42,
                n_jobs=1
            )
            model.fit(X)
            self.model = model
            self.use_sklearn = True
            self.is_trained = True
            self.training_sample_count = len(X)
            logger.info(f"Isolation Forest successfully trained on {self.training_sample_count} samples.")
            return True
        except (ImportError, MemoryError, Exception) as exc:
            logger.warning(f"Isolation Forest unavailable ({exc}), fitting lightweight NumPy Mahalanobis distance model.")

        # Robust pure-NumPy Multivariate Mahalanobis / Covariance fallback
        try:
            self.mean_vector = np.mean(X, axis=0)
            cov = np.cov(X, rowvar=False)
            # Add small regularization to diagonal to prevent singular matrix
            cov += np.eye(cov.shape[0]) * 1e-4
            self.inv_cov_matrix = np.linalg.pinv(cov)
            self.use_sklearn = False
            self.is_trained = True
            self.training_sample_count = len(X)
            logger.info(f"Lightweight Multivariate model trained on {self.training_sample_count} samples.")
            return True
        except Exception as exc:
            logger.error(f"Failed to fit multivariate model: {exc}")
            self.is_trained = False
            return False

    def predict_sample(self, feature_dict: dict[str, Any]) -> MLAnomalyResult:
        """Predict whether the current multi-dimensional feature vector is an anomaly."""
        if not self.is_trained:
            return MLAnomalyResult(
                is_anomaly=False,
                anomaly_score=0.0,
                mode_active="Statistical Mode (ML gated due to insufficient history)",
                model_trained=False,
                sample_count=self.training_sample_count,
                details=f"ML requires >= {self.min_samples} historical samples for reliable unsupervised clustering."
            )

        vec = np.array([
            float(feature_dict.get("latency_ms") or 0.0),
            float(feature_dict.get("jitter_ms") or 0.0),
            float(feature_dict.get("packet_loss_pct") or 0.0),
            float(feature_dict.get("estimated_utilization_pct") or 0.0),
            float(feature_dict.get("packets_sent_per_sec") or 0.0),
            float(feature_dict.get("packets_recv_per_sec") or 0.0)
        ])

        if self.use_sklearn and self.model is not None:
            pred = self.model.predict(np.array([vec]))[0]
            score = self.model.decision_function(np.array([vec]))[0]
            is_anom = (pred == -1)
            details = (
                f"Multi-variate Isolation Forest classified sample as {'ANOMALY' if is_anom else 'NORMAL'} "
                f"(Decision Score: {score:.3f})."
            )
            return MLAnomalyResult(
                is_anomaly=is_anom,
                anomaly_score=round(float(score), 3),
                mode_active="ML Mode (Isolation Forest)",
                model_trained=True,
                sample_count=self.training_sample_count,
                details=details
            )

        # NumPy Mahalanobis distance evaluation
        if self.mean_vector is not None and self.inv_cov_matrix is not None:
            delta = vec - self.mean_vector
            dist = float(np.sqrt(np.dot(np.dot(delta, self.inv_cov_matrix), delta)))
            is_anom = dist > self.distance_threshold
            norm_score = max(-1.0, min(1.0, 1.0 - (dist / self.distance_threshold)))
            details = (
                f"Multivariate Mahalanobis distance: {dist:.2f} (Threshold: {self.distance_threshold:.2f}, "
                f"Classification: {'ANOMALY' if is_anom else 'NORMAL'})."
            )
            return MLAnomalyResult(
                is_anomaly=is_anom,
                anomaly_score=round(norm_score, 3),
                mode_active="ML Mode (Multivariate Mahalanobis)",
                model_trained=True,
                sample_count=self.training_sample_count,
                details=details
            )

        return MLAnomalyResult(
            is_anomaly=False,
            anomaly_score=0.0,
            mode_active="Statistical Mode",
            model_trained=False,
            sample_count=self.training_sample_count,
            details="Model parameters not populated."
        )
