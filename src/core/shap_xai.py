"""
SHAP XAI Wrapper (Core)
=========================

SHAP 기반 XAI + Operator Trust 통합 출력.

기존 SHAP 활용은 단순 변수 중요도 시각화에 그침.
본 wrapper는 SHAP 안정성을 Operator Trust 컴포넌트(xai_consistency)로 변환.

작성: 김용범 — 2026 AX 아이디어 경진대회
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass

try:
    import shap
    _HAS_SHAP = True
except ImportError:
    _HAS_SHAP = False


# =============================================================================
# 1. NumPy 베이스라인 — Permutation Importance (SHAP 없을 때)
# =============================================================================

def permutation_importance_numpy(
    model_predict_fn,
    X: np.ndarray,
    y: np.ndarray,
    n_repeats: int = 5,
    metric_fn=None,
) -> np.ndarray:
    """
    Permutation importance — 한 변수를 셔플했을 때 점수 변화량.
    SHAP 미설치 환경에서 변수 중요도 확보용.
    """
    if metric_fn is None:
        metric_fn = lambda y_true, y_pred: -np.mean((y_true - y_pred) ** 2)

    baseline_score = metric_fn(y, model_predict_fn(X))
    n_features = X.shape[1]
    importances = np.zeros(n_features)

    rng = np.random.default_rng(42)
    for j in range(n_features):
        scores = []
        for _ in range(n_repeats):
            X_perm = X.copy()
            X_perm[:, j] = rng.permutation(X_perm[:, j])
            scores.append(baseline_score - metric_fn(y, model_predict_fn(X_perm)))
        importances[j] = np.mean(scores)
    return importances


# =============================================================================
# 2. SHAP wrapper — sklearn 호환 모델용
# =============================================================================

@dataclass
class SHAPReport:
    feature_importances: np.ndarray
    shap_values: np.ndarray
    feature_names: list[str]
    base_value: float
    consistency_score: float        # 0~1, Operator Trust용
    rank_stability: float           # 0~1, 변수 순위 안정성

    def top_k_features(self, k: int = 5) -> list[tuple[str, float]]:
        idx = np.argsort(-np.abs(self.feature_importances))[:k]
        return [(self.feature_names[i], float(self.feature_importances[i])) for i in idx]


def explain_with_shap(
    model,
    X_baseline: np.ndarray,
    X_explain: np.ndarray,
    feature_names: list[str] | None = None,
) -> SHAPReport:
    """
    SHAP 기반 설명 — Tree 모델은 TreeExplainer, 기타는 KernelExplainer.

    Returns
    -------
    SHAPReport — 변수 중요도 + 일관성 점수 (Operator Trust 직접 입력)
    """
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(X_explain.shape[1])]

    if _HAS_SHAP:
        # sklearn 모델 가정 — 실제 사용 시 모델 종류에 따라 분기
        explainer = shap.Explainer(model, X_baseline)
        explanation = explainer(X_explain)
        shap_values = explanation.values
        base_value = float(explanation.base_values[0]) if hasattr(explanation, "base_values") else 0.0
    else:
        # Fallback: permutation importance 1회
        importances = permutation_importance_numpy(
            lambda x: model.predict(x) if hasattr(model, "predict") else x.mean(axis=1),
            X_explain,
            np.zeros(len(X_explain)),
        )
        # 흉내: 모든 샘플에 동일한 중요도 부여
        shap_values = np.tile(importances, (len(X_explain), 1))
        base_value = 0.0

    feature_importances = np.mean(np.abs(shap_values), axis=0)

    # 일관성 점수 — 상위 절반 vs 하위 절반의 SHAP 값 코사인 유사도
    n_half = len(shap_values) // 2
    if n_half > 1:
        upper_mean = np.mean(np.abs(shap_values[:n_half]), axis=0)
        lower_mean = np.mean(np.abs(shap_values[n_half:]), axis=0)
        n_u, n_l = np.linalg.norm(upper_mean), np.linalg.norm(lower_mean)
        if n_u * n_l > 0:
            consistency = float(np.dot(upper_mean, lower_mean) / (n_u * n_l))
        else:
            consistency = 0.5
    else:
        consistency = 0.5

    # 순위 안정성 — 상하 분할에서 top-3 변수가 같은지
    if n_half > 1:
        top_upper = set(np.argsort(-upper_mean)[:3])
        top_lower = set(np.argsort(-lower_mean)[:3])
        rank_stability = len(top_upper & top_lower) / 3.0
    else:
        rank_stability = 0.5

    return SHAPReport(
        feature_importances=feature_importances,
        shap_values=shap_values,
        feature_names=feature_names,
        base_value=base_value,
        consistency_score=float(np.clip(consistency, 0.0, 1.0)),
        rank_stability=float(rank_stability),
    )


# =============================================================================
# 3. 셀프테스트
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("SHAP XAI Wrapper — Self-test")
    print("=" * 60)

    np.random.seed(42)
    n, d = 200, 6
    X = np.random.normal(0, 1, (n, d))
    # y = 1*x0 + 2*x1 - 0.5*x2 + noise
    true_weights = np.array([1.0, 2.0, -0.5, 0.0, 0.0, 0.0])
    y = X @ true_weights + np.random.normal(0, 0.3, n)

    # 가짜 모델: 평균
    class DummyModel:
        def predict(self, x):
            return x @ true_weights

    model = DummyModel()
    feature_names = ["TMS_SOx", "Wind_speed", "Temperature", "Humidity", "Pressure", "Utilization"]

    report = explain_with_shap(
        model=model,
        X_baseline=X[:50],
        X_explain=X[50:150],
        feature_names=feature_names,
    )

    print("\n[변수 중요도 (Top 5)]")
    for name, imp in report.top_k_features(5):
        print(f"  {name:18s}: {imp:+.4f}")

    print(f"\n[XAI 신뢰도 지표]")
    print(f"  consistency_score : {report.consistency_score:.3f} (1.0=상하 분할 SHAP 코사인=1)")
    print(f"  rank_stability    : {report.rank_stability:.3f} (1.0=top-3 변수 동일)")
    print(f"\n[Operator Trust 입력]")
    print(f"  → xai_consistency_score = {report.consistency_score:.3f}")
    print(f"  (SHAP 패키지 사용: {_HAS_SHAP})")
