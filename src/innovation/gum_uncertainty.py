"""
GUM (Guide to the Expression of Uncertainty in Measurement) — 합성표준불확도 계산

ISO/IEC Guide 98-3 (GUM) 및 ISO 17034, ISO/IEC 17025 기반.
한국서부발전 TMS 측정 불확도를 ML 모델에 통합하기 위한 핵심 모듈.

작성: 김용범 (2026 AX 아이디어 경진대회)
References:
  - JCGM 100:2008 (GUM with minor corrections)
  - ISO 18516:2019 (1저자 기여)
  - 환경부 굴뚝 원격감시체계 운영 가이드라인
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Sequence


# =============================================================================
# 1. 불확도 성분 정의 (Type A / Type B)
# =============================================================================

@dataclass
class UncertaintyComponent:
    """단일 불확도 성분.

    GUM은 불확도 성분을 두 종류로 구분:
      - Type A: 통계적 분석 (반복 측정의 표준편차)
      - Type B: 비통계적 (제조사 사양, 교정증명서, 경험)
    """
    name: str
    standard_uncertainty: float        # u_i (1-sigma 등가)
    sensitivity_coefficient: float = 1.0  # c_i = ∂y/∂x_i
    type: str = "B"                    # "A" or "B"
    distribution: str = "normal"       # "normal" / "rectangular" / "triangular"
    degrees_of_freedom: float = np.inf  # ν_i (Type A는 n-1)
    description: str = ""

    def variance_contribution(self) -> float:
        """이 성분이 합성표준불확도의 분산에 기여하는 양 = (c_i × u_i)²"""
        return (self.sensitivity_coefficient * self.standard_uncertainty) ** 2


# =============================================================================
# 2. TMS 측정에 대한 표준 불확도 budget (예시)
# =============================================================================

def build_tms_uncertainty_budget(
    measurement_value: float,
    pollutant: str = "SOx",
    calibration_date_days_ago: int = 30,
) -> list[UncertaintyComponent]:
    """TMS 측정값에 대한 표준 불확도 예산을 구성.

    실제 발전소 운영 환경 기반 (한국서부발전 TMS 매뉴얼 + ISO 17025 권고).
    데이터 수신 후(5/2~) 실측치로 정밀화.

    Parameters
    ----------
    measurement_value : float
        TMS 측정 농도 (ppm 또는 μg/m³)
    pollutant : str
        "SOx", "NOx", "PM", "CO" 중 하나
    calibration_date_days_ago : int
        직전 교정 후 경과 일수 (드리프트 영향)
    """
    # 제조사 사양 기반 기본 분류 (Siemens Ultramat, ABB AO2000 등 일반치)
    sensor_specs = {
        "SOx":  {"linearity": 0.02, "drift_per_30d": 0.015, "noise": 0.005},
        "NOx":  {"linearity": 0.025, "drift_per_30d": 0.020, "noise": 0.008},
        "PM":   {"linearity": 0.05, "drift_per_30d": 0.030, "noise": 0.020},
        "CO":   {"linearity": 0.03, "drift_per_30d": 0.025, "noise": 0.010},
    }
    spec = sensor_specs.get(pollutant, sensor_specs["SOx"])

    components = [
        UncertaintyComponent(
            name="센서 선형성",
            standard_uncertainty=measurement_value * spec["linearity"] / np.sqrt(3),
            distribution="rectangular",
            type="B",
            description="제조사 사양: 측정 범위 내 비선형성 (직사각형 분포 가정)",
        ),
        UncertaintyComponent(
            name="교정 기준 가스 인증값",
            standard_uncertainty=measurement_value * 0.01,
            distribution="normal",
            type="B",
            description="ISO 17034 인증 표준가스 (k=2 인증서, u = U/2)",
        ),
        UncertaintyComponent(
            name="센서 드리프트 (시간 의존)",
            standard_uncertainty=(
                measurement_value
                * spec["drift_per_30d"]
                * (calibration_date_days_ago / 30.0)
                / np.sqrt(3)
            ),
            distribution="rectangular",
            type="B",
            description="교정 이후 시간에 따른 드리프트 (직사각형 분포)",
        ),
        UncertaintyComponent(
            name="환경 노이즈 (Type A)",
            standard_uncertainty=measurement_value * spec["noise"],
            distribution="normal",
            type="A",
            degrees_of_freedom=29,
            description="5분 평균 30회 반복 표준편차 (n=30)",
        ),
        UncertaintyComponent(
            name="디지털화 분해능",
            standard_uncertainty=0.5 / np.sqrt(12),
            distribution="rectangular",
            type="B",
            description="A/D 변환 분해능 1 LSB = 1.0 (직사각형 분포)",
        ),
        UncertaintyComponent(
            name="온도·습도 환경 보정",
            standard_uncertainty=measurement_value * 0.008,
            distribution="normal",
            type="B",
            description="굴뚝 내부 환경 변동에 따른 보정 잔차",
        ),
    ]
    return components


# =============================================================================
# 3. 합성표준불확도 (Combined Standard Uncertainty)
# =============================================================================

def combined_uncertainty(
    components: Sequence[UncertaintyComponent],
    correlations: dict[tuple[str, str], float] | None = None,
) -> float:
    """
    GUM Eq. 13: u_c²(y) = Σ (c_i × u_i)² + 2 × Σ_{i<j} c_i × c_j × u_i × u_j × r(x_i, x_j)

    Parameters
    ----------
    components : sequence of UncertaintyComponent
    correlations : dict, optional
        {(name_i, name_j): r_ij} — 상관계수 -1 ≤ r ≤ 1

    Returns
    -------
    u_c : float
        합성표준불확도 (1-sigma 등가)
    """
    # 비상관 항
    variance = sum(c.variance_contribution() for c in components)

    # 상관 항
    if correlations:
        comp_dict = {c.name: c for c in components}
        for (name_i, name_j), r_ij in correlations.items():
            if name_i not in comp_dict or name_j not in comp_dict:
                continue
            c_i, c_j = comp_dict[name_i], comp_dict[name_j]
            cross_term = (
                2.0
                * c_i.sensitivity_coefficient * c_i.standard_uncertainty
                * c_j.sensitivity_coefficient * c_j.standard_uncertainty
                * r_ij
            )
            variance += cross_term

    return float(np.sqrt(max(variance, 0.0)))


# =============================================================================
# 4. 확장불확도 (Expanded Uncertainty) — k=2 (95% 신뢰수준)
# =============================================================================

def expanded_uncertainty(u_c: float, coverage_factor: float = 2.0) -> float:
    """U = k × u_c. k=2는 정규 가정 95% 신뢰구간."""
    return coverage_factor * u_c


def welch_satterthwaite_dof(
    components: Sequence[UncertaintyComponent],
    u_c: float,
) -> float:
    """
    Welch-Satterthwaite 식 — 합성 자유도.
    Type A 성분이 섞여 있을 때 t-분포 보정 k 결정에 사용.
    """
    numerator = u_c ** 4
    denominator = sum(
        (c.sensitivity_coefficient * c.standard_uncertainty) ** 4 / max(c.degrees_of_freedom, 1.0)
        for c in components
    )
    if denominator == 0:
        return float("inf")
    return numerator / denominator


# =============================================================================
# 5. 벡터화 — 시계열 전체에 대한 GUM 적용
# =============================================================================

def gum_uncertainty_array(
    measurements: np.ndarray,
    pollutant: str = "SOx",
    calibration_dates_days_ago: np.ndarray | None = None,
) -> np.ndarray:
    """
    측정 시계열 전체에 대한 합성표준불확도 배열을 반환.

    Measurement-aware ML 의 weight = 1 / u_c² 입력으로 사용.
    """
    measurements = np.asarray(measurements, dtype=float)
    if calibration_dates_days_ago is None:
        calibration_dates_days_ago = np.full_like(measurements, 30.0)

    u_c_array = np.empty_like(measurements)
    for i, (m, days) in enumerate(zip(measurements, calibration_dates_days_ago)):
        components = build_tms_uncertainty_budget(
            measurement_value=float(m),
            pollutant=pollutant,
            calibration_date_days_ago=int(days),
        )
        u_c_array[i] = combined_uncertainty(components)
    return u_c_array


# =============================================================================
# 6. 셀프테스트 (실데이터 도착 전 검증)
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("GUM Uncertainty Self-test — 한국서부발전 TMS")
    print("=" * 60)

    # 예시: SOx 50 ppm, 30일 전 교정
    components = build_tms_uncertainty_budget(50.0, "SOx", 30)
    print("\n[성분별 분산 기여]")
    for c in components:
        contrib = c.variance_contribution()
        print(f"  {c.name:20s}: u_i = {c.standard_uncertainty:.4f}, "
              f"contribution = {contrib:.6f} ({c.type})")

    u_c = combined_uncertainty(components)
    U = expanded_uncertainty(u_c)
    dof = welch_satterthwaite_dof(components, u_c)
    relative = (U / 50.0) * 100

    print(f"\n[합성결과]")
    print(f"  합성표준불확도 u_c = {u_c:.4f} ppm")
    print(f"  확장불확도 U (k=2) = {U:.4f} ppm  (= ±{relative:.2f}% 상대)")
    print(f"  Welch-Satterthwaite DoF = {dof:.1f}")

    # 시계열 적용 예
    print("\n[시계열 적용 예시]")
    np.random.seed(42)
    sample_measurements = np.random.uniform(20, 80, size=10)
    sample_calibration_days = np.random.randint(1, 90, size=10)
    u_array = gum_uncertainty_array(sample_measurements, "SOx", sample_calibration_days)
    weights = 1.0 / (u_array ** 2)
    print(f"  측정값 (ppm)         : {sample_measurements.round(2)}")
    print(f"  교정 후 일수         : {sample_calibration_days}")
    print(f"  u_c (ppm)            : {u_array.round(4)}")
    print(f"  GUM weights (정규화) : {(weights / weights.sum()).round(3)}")

    print("\n[해석] 정밀하게 측정된 값이 더 큰 가중치를 받음 → ML loss에 그대로 적용.")
