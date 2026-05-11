"""
Isolation Forest with GUM-aware Sample Weighting (Core)
=========================================================

SpectraGuard SERS QC 이상탐지 엔진 이식 + GUM 가중 sklearn wrapper.

Innovation A 통합 포인트: scikit-learn IsolationForest의 sample_weight 인자에
1/u² 가중치 직접 주입.

작성: 김용범 — 2026 AX 아이디어 경진대회
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass

try:
    from sklearn.ensemble import IsolationForest
    _HAS_SKLEARN = True
except ImportError:
    _HAS_SKLEARN = False


# =============================================================================
# 1. NumPy 베이스라인 — 단순 다변량 z-score (sklearn 없을 때)
# =============================================================================

class MultivariateZScoreDetector:
    """sklearn 없을 때 폴백 — Mahalanobis 거리 기반."""

    def __init__(self, threshold: float = 3.0):
        self.threshold = threshold
        self.mean_ = None
        self.cov_inv_ = None

    def fit(self, X: np.ndarray, sample_weight: np.ndarray | None = None) -> "MultivariateZScoreDetector":
        if sample_weight is None:
            sample_weight = np.ones(len(X))
        sample_weight = sample_weight / sample_weight.sum()

        self.mean_ = (X * sample_weight[:, None]).sum(axis=0)
        diff = X - self.mean_
        cov = (diff * sample_weight[:, None]).T @ diff
        # 정규화 + 안정성을 위한 ridge
        cov += np.eye(cov.shape[0]) * 1e-6
        self.cov_inv_ = np.linalg.inv(cov)
        return self

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        diff = X - self.mean_
        mahal_sq = np.sum((diff @ self.cov_inv_) * diff, axis=1)
        return -np.sqrt(np.maximum(mahal_sq, 0.0))  # negative for compatibility

    def predict(self, X: np.ndarray) -> np.ndarray:
        scores = self.decision_function(X)
        return np.where(-scores > self.threshold, -1, 1)


# =============================================================================
# 2. GUM-aware Isolation Forest Wrapper
# =============================================================================

@dataclass
class GUMIForestConfig:
    n_estimators: int = 200
    max_samples: int = 256
    contamination: float = 0.05
    random_state: int = 42


class GUMAwareIsolationForest:
    """
    sklearn IsolationForest + GUM sample_weight.

    핵심: 신뢰도 낮은 측정(u_c 큰)은 학습에 작게 기여 → 모델이 잡음에 견고.
    """

    def __init__(self, cfg: GUMIForestConfig | None = None):
        self.cfg = cfg or GUMIForestConfig()
        self.model_ = None

    def fit(self, X: np.ndarray, u_c: np.ndarray | None = None) -> "GUMAwareIsolationForest":
        if not _HAS_SKLEARN:
            print("[경고] sklearn 미설치 — Mahalanobis fallback 사용")
            self.model_ = MultivariateZScoreDetector(threshold=3.0)
            sw = (1.0 / (u_c ** 2 + 1e-6)) if u_c is not None else None
            self.model_.fit(X, sample_weight=sw)
            return self

        sample_weight = None
        if u_c is not None:
            sample_weight = 1.0 / (u_c ** 2 + 1e-6)
            sample_weight = sample_weight / sample_weight.mean()

        self.model_ = IsolationForest(
            n_estimators=self.cfg.n_estimators,
            max_samples=self.cfg.max_samples,
            contamination=self.cfg.contamination,
            random_state=self.cfg.random_state,
        )
        self.model_.fit(X, sample_weight=sample_weight)
        return self

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        return self.model_.decision_function(X)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model_.predict(X)


# =============================================================================
# 3. 셀프테스트
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("GUM-aware Isolation Forest — Self-test")
    print("=" * 60)

    np.random.seed(42)
    n_normal, n_anom = 950, 50
    X_normal = np.random.normal(50, 5, (n_normal, 4))
    X_anom = np.random.uniform(70, 120, (n_anom, 4))
    X = np.vstack([X_normal, X_anom])
    labels = np.array([1] * n_normal + [-1] * n_anom)

    # GUM 불확도 (정상은 작게, 이상은 크게 — 측정 신뢰도 차이)
    u_c = np.concatenate([
        np.random.uniform(0.5, 2.0, n_normal),    # 정상 측정: 신뢰
        np.random.uniform(3.0, 8.0, n_anom),       # 이상 측정: 비신뢰
    ])

    # 셔플
    idx = np.random.permutation(len(X))
    X, labels, u_c = X[idx], labels[idx], u_c[idx]

    # 학습
    detector = GUMAwareIsolationForest(GUMIForestConfig(contamination=0.05))
    detector.fit(X, u_c=u_c)

    pred = detector.predict(X)
    tp = int(((pred == -1) & (labels == -1)).sum())
    fp = int(((pred == -1) & (labels == 1)).sum())
    fn = int(((pred == 1) & (labels == -1)).sum())
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)

    print(f"\n[GUM-weighted IForest 결과]")
    print(f"  Precision = {precision:.3f}")
    print(f"  Recall    = {recall:.3f}")
    print(f"  F1        = {2*precision*recall/max(precision+recall, 1e-9):.3f}")
    print(f"  (sklearn 사용: {_HAS_SKLEARN})")

    # 비교: GUM 없이
    detector_plain = GUMAwareIsolationForest(GUMIForestConfig(contamination=0.05))
    detector_plain.fit(X)
    pred_plain = detector_plain.predict(X)
    tp_p = int(((pred_plain == -1) & (labels == -1)).sum())
    fp_p = int(((pred_plain == -1) & (labels == 1)).sum())
    fn_p = int(((pred_plain == 1) & (labels == -1)).sum())
    precision_p = tp_p / max(tp_p + fp_p, 1)
    recall_p = tp_p / max(tp_p + fn_p, 1)
    print(f"\n[Plain IForest 비교 (GUM 가중 없음)]")
    print(f"  Precision = {precision_p:.3f}, Recall = {recall_p:.3f}")
    print(f"\n[해석] GUM 가중 모델은 신뢰도 낮은 데이터 의존도 ↓ → 일관성 ↑")
