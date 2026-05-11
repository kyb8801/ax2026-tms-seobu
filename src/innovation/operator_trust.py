"""
Operator Trust Calibration (Innovation F)
==========================================

핵심 혁신: XAI는 흔하지만 "운영자가 이 모델을 얼마나 신뢰해야 하는가"는 정량화 안 됨.
본 모듈은 측정 불확도(GUM) + 모델 인식론적 불확도 + XAI 일관성을 결합한
0-100 운영자 신뢰 점수(Operator Trust Score, OTS)를 계산.

운영 정책:
  - OTS ≥ 80 → 자동 권고 (Auto-execute, P1 알람)
  - 60 ≤ OTS < 80 → 운영자 검토 (Review-required, P2 알람)
  - 40 ≤ OTS < 60 → 운영자 승인 필요 (Manual-approve, P3 알람)
  - OTS < 40 → 자동 거부 (Auto-reject, 수동 분석 권고)

작성: 김용범 — 2026 AX 아이디어 경진대회
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from enum import Enum


# =============================================================================
# 1. Trust 등급 정의
# =============================================================================

class TrustLevel(Enum):
    AUTO_EXECUTE = "AUTO_EXECUTE"        # P1 — 자동 실행
    REVIEW_REQUIRED = "REVIEW_REQUIRED"  # P2 — 검토 후 실행
    MANUAL_APPROVE = "MANUAL_APPROVE"    # P3 — 운영자 승인
    AUTO_REJECT = "AUTO_REJECT"          # 수동 분석 필요


def trust_to_level(score: float) -> TrustLevel:
    if score >= 80:
        return TrustLevel.AUTO_EXECUTE
    elif score >= 60:
        return TrustLevel.REVIEW_REQUIRED
    elif score >= 40:
        return TrustLevel.MANUAL_APPROVE
    else:
        return TrustLevel.AUTO_REJECT


# =============================================================================
# 2. Trust Score 계산 — 4 컴포넌트 결합
# =============================================================================

@dataclass
class TrustComponents:
    """OTS의 4개 구성 요소 (각 0~1, 곱하여 결합)."""
    measurement_quality: float   # 측정 신뢰도 (GUM 기반)
    model_confidence: float      # 모델 예측 분산 기반
    xai_consistency: float       # SHAP 설명 안정성
    historical_accuracy: float   # 과거 동일 조건에서의 적중률

    def score(self) -> float:
        """0~100 스케일 OTS."""
        product = (
            self.measurement_quality
            * self.model_confidence
            * self.xai_consistency
            * self.historical_accuracy
        )
        return float(np.clip(product * 100.0, 0.0, 100.0))


# =============================================================================
# 3. 4 컴포넌트 계산기
# =============================================================================

def measurement_quality_score(
    u_c: float,
    measurement_value: float,
    target_relative_uncertainty: float = 0.05,
) -> float:
    """
    측정 신뢰도 (0~1) — 상대 불확도가 목표(5%) 이하면 1.0.
    상대 불확도가 커질수록 점수 감소.

    score = exp(-((u_c / value) / target)²)  for value > 0
    """
    if measurement_value <= 0:
        return 0.0
    rel_u = u_c / measurement_value
    score = np.exp(-((rel_u / target_relative_uncertainty) ** 2))
    return float(np.clip(score, 0.0, 1.0))


def model_confidence_score(
    prediction_std: float,
    prediction_mean: float,
    threshold_relative_std: float = 0.10,
) -> float:
    """
    모델 인식론적 불확도 기반 (0~1).
    예측 표준편차가 평균의 10% 이하면 1.0.
    """
    if prediction_mean <= 0:
        return 0.5
    rel_std = prediction_std / prediction_mean
    score = np.exp(-((rel_std / threshold_relative_std) ** 2))
    return float(np.clip(score, 0.0, 1.0))


def xai_consistency_score(
    shap_values_recent: np.ndarray,
    shap_values_baseline: np.ndarray,
) -> float:
    """
    SHAP 설명 안정성 (0~1).
    최근 N개 예측의 SHAP 값과 베이스라인의 코사인 유사도.

    SHAP 설명이 시간에 따라 크게 변하면 모델 신뢰도 하락 → 점수 낮음.
    """
    if shap_values_recent.size == 0 or shap_values_baseline.size == 0:
        return 0.5

    recent_mean = np.mean(np.abs(shap_values_recent), axis=0)
    baseline_mean = np.mean(np.abs(shap_values_baseline), axis=0)

    # 코사인 유사도
    norm_recent = np.linalg.norm(recent_mean)
    norm_baseline = np.linalg.norm(baseline_mean)
    if norm_recent == 0 or norm_baseline == 0:
        return 0.5

    cosine = float(np.dot(recent_mean, baseline_mean) / (norm_recent * norm_baseline))
    # 코사인은 -1~1, 0~1로 매핑
    return float(np.clip((cosine + 1.0) / 2.0, 0.0, 1.0))


def historical_accuracy_score(
    past_predictions: np.ndarray,
    past_actuals: np.ndarray,
    past_uncertainties: np.ndarray,
    n_recent: int = 100,
) -> float:
    """
    유사 조건에서의 과거 적중률 (0~1).
    예측이 측정 신뢰구간 [actual - 2u, actual + 2u] 안에 들어가는 비율.
    """
    if past_predictions.size < 5:
        return 0.5  # 충분한 이력 없음 — 중립

    recent_pred = past_predictions[-n_recent:]
    recent_actual = past_actuals[-n_recent:]
    recent_unc = past_uncertainties[-n_recent:]

    within = np.abs(recent_pred - recent_actual) <= 2.0 * recent_unc
    accuracy = float(np.mean(within))
    return accuracy


# =============================================================================
# 4. End-to-end OTS 계산
# =============================================================================

@dataclass
class TrustReport:
    score: float
    level: TrustLevel
    components: TrustComponents
    rationale: str

    def __str__(self):
        return (
            f"OTS = {self.score:.1f}/100 [{self.level.value}]\n"
            f"  측정 신뢰도   : {self.components.measurement_quality * 100:.1f}\n"
            f"  모델 신뢰도   : {self.components.model_confidence * 100:.1f}\n"
            f"  XAI 일관성    : {self.components.xai_consistency * 100:.1f}\n"
            f"  과거 적중률   : {self.components.historical_accuracy * 100:.1f}\n"
            f"  → {self.rationale}"
        )


def compute_operator_trust(
    measurement_value: float,
    measurement_uncertainty: float,
    prediction_mean: float,
    prediction_std: float,
    shap_recent: np.ndarray,
    shap_baseline: np.ndarray,
    past_predictions: np.ndarray,
    past_actuals: np.ndarray,
    past_uncertainties: np.ndarray,
) -> TrustReport:
    """End-to-end Operator Trust 계산."""
    components = TrustComponents(
        measurement_quality=measurement_quality_score(measurement_uncertainty, measurement_value),
        model_confidence=model_confidence_score(prediction_std, prediction_mean),
        xai_consistency=xai_consistency_score(shap_recent, shap_baseline),
        historical_accuracy=historical_accuracy_score(past_predictions, past_actuals, past_uncertainties),
    )
    score = components.score()
    level = trust_to_level(score)

    # 가장 약한 컴포넌트를 자동 진단
    comp_dict = {
        "측정": components.measurement_quality,
        "모델": components.model_confidence,
        "설명": components.xai_consistency,
        "이력": components.historical_accuracy,
    }
    weakest = min(comp_dict, key=comp_dict.get)
    weakest_value = comp_dict[weakest]

    if level == TrustLevel.AUTO_EXECUTE:
        rationale = "모든 컴포넌트 양호 — 자동 실행 가능"
    elif level == TrustLevel.REVIEW_REQUIRED:
        rationale = f"{weakest} 신뢰도 보통 ({weakest_value*100:.1f}/100) — 운영자 검토 후 실행"
    elif level == TrustLevel.MANUAL_APPROVE:
        rationale = f"{weakest} 신뢰도 낮음 ({weakest_value*100:.1f}/100) — 운영자 승인 필요"
    else:
        rationale = f"{weakest} 신뢰도 매우 낮음 ({weakest_value*100:.1f}/100) — 수동 분석 권고"

    return TrustReport(score=score, level=level, components=components, rationale=rationale)


# =============================================================================
# 5. 셀프테스트
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Operator Trust Calibration — Self-test")
    print("=" * 70)

    # 시나리오 1: 모든 신호 좋음
    np.random.seed(42)
    shap_baseline = np.random.normal(0, 0.5, (200, 8))
    shap_recent_good = shap_baseline[:50] + np.random.normal(0, 0.05, (50, 8))
    past_pred = np.random.uniform(40, 60, 100)
    past_act = past_pred + np.random.normal(0, 1.0, 100)
    past_unc = np.full(100, 1.5)

    print("\n[시나리오 1: 모든 신호 양호]")
    report1 = compute_operator_trust(
        measurement_value=50.0, measurement_uncertainty=1.0,
        prediction_mean=52.0, prediction_std=2.0,
        shap_recent=shap_recent_good, shap_baseline=shap_baseline,
        past_predictions=past_pred, past_actuals=past_act, past_uncertainties=past_unc,
    )
    print(report1)

    # 시나리오 2: 측정 불확도 큼
    print("\n[시나리오 2: 측정 불확도 큼 (u_c = 5 ppm on 50 ppm = 10%)]")
    report2 = compute_operator_trust(
        measurement_value=50.0, measurement_uncertainty=5.0,
        prediction_mean=52.0, prediction_std=2.0,
        shap_recent=shap_recent_good, shap_baseline=shap_baseline,
        past_predictions=past_pred, past_actuals=past_act, past_uncertainties=past_unc,
    )
    print(report2)

    # 시나리오 3: SHAP 설명 변동 큼 (drift)
    shap_recent_bad = np.random.normal(0, 1.0, (50, 8)) * np.array([1, -1, 1, -1, 1, -1, 1, -1])
    print("\n[시나리오 3: XAI 설명 변동 (모델 drift 의심)]")
    report3 = compute_operator_trust(
        measurement_value=50.0, measurement_uncertainty=1.0,
        prediction_mean=52.0, prediction_std=2.0,
        shap_recent=shap_recent_bad, shap_baseline=shap_baseline,
        past_predictions=past_pred, past_actuals=past_act, past_uncertainties=past_unc,
    )
    print(report3)

    # 시나리오 4: 모델 분산 큼 (예측 자체가 흔들림)
    print("\n[시나리오 4: 모델 예측 분산 큼 (운영 한계)]")
    report4 = compute_operator_trust(
        measurement_value=50.0, measurement_uncertainty=1.0,
        prediction_mean=52.0, prediction_std=10.0,
        shap_recent=shap_recent_good, shap_baseline=shap_baseline,
        past_predictions=past_pred, past_actuals=past_act, past_uncertainties=past_unc,
    )
    print(report4)

    print("\n[등급 정책 요약]")
    print("  OTS ≥ 80  → P1 자동 실행 (Auto-execute)")
    print("  60 ≤ < 80 → P2 운영자 검토 (Review-required)")
    print("  40 ≤ < 60 → P3 운영자 승인 (Manual-approve)")
    print("  OTS < 40  → 수동 분석 권고 (Auto-reject)")
