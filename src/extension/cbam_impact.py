"""
CBAM (Carbon Border Adjustment Mechanism) Impact Simulation
=============================================================

EU 탄소국경조정메커니즘 2026.1.1 본격 시행.
TMS 측정 정확도 1% 개선이 CBAM 보고·납부 비용에 미치는 영향 정량화.

핵심 논리:
1. TMS 측정 불확도 → CO2 배출량 측정 불확도
2. CBAM 보고는 보수적 가정 (불확도 큰 만큼 위쪽으로 보고) 권고
3. 측정 정확도 개선 → 보수적 마진 축소 → CBAM 납부 비용 절감

Extension D — 다른 참가자 0%.
작성: 김용범 — 2026 AX 아이디어 경진대회
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass


# =============================================================================
# 1. 매개변수 — 시장 가격 / 변환 계수
# =============================================================================

@dataclass
class CBAMParameters:
    """2026년 기준 CBAM 매개변수."""
    eu_eta_price_eur_per_ton_co2: float = 90.0     # 2026 평균 (실제 80-100 변동)
    eur_to_krw: float = 1450.0                     # 환율
    free_allowance_pct: float = 0.0                # 2026년 무상 할당 (전환 기간 종료 가정)
    conservative_margin_factor: float = 2.0        # 측정 불확도 × k (보수 보고 권고)


@dataclass
class PlantOperationParameters:
    """발전소(호기) 운영 매개변수 — 한국서부발전 평균 가정."""
    annual_co2_emission_ton: float = 5_000_000.0   # 1호기 약 500만 톤/년
    measurement_relative_uncertainty_baseline: float = 0.05   # 현행 ±5%
    measurement_relative_uncertainty_improved: float = 0.03   # 제안 ±3%


# =============================================================================
# 2. CBAM 비용 계산
# =============================================================================

def cbam_reported_emission(
    actual_emission_ton: float,
    relative_uncertainty: float,
    margin_factor: float = 2.0,
) -> float:
    """
    보수적 보고 = 실제 + (k × u_rel × 실제).
    k=2는 95% 신뢰구간 상한.
    """
    upper_bound = actual_emission_ton * (1 + margin_factor * relative_uncertainty)
    return upper_bound


def cbam_cost_krw(
    reported_emission_ton: float,
    params: CBAMParameters,
) -> float:
    """
    CBAM 비용 = 보고 배출량 × (1 - 무상할당) × ETS 가격 × 환율.
    """
    chargeable = reported_emission_ton * (1 - params.free_allowance_pct)
    cost_eur = chargeable * params.eu_eta_price_eur_per_ton_co2
    return cost_eur * params.eur_to_krw


# =============================================================================
# 3. 시나리오 비교
# =============================================================================

@dataclass
class CBAMSavingReport:
    baseline_cost_krw: float
    improved_cost_krw: float
    annual_saving_krw: float
    saving_pct: float
    payback_years: float | None    # 솔루션 도입 비용 / 연간 절감

    def summary(self) -> str:
        return (
            f"현행 측정정확도 ±{cbam_default_baseline_unc()*100:.1f}% → "
            f"제안 ±{cbam_default_improved_unc()*100:.1f}%\n"
            f"  현행 CBAM 비용  : {self.baseline_cost_krw / 1e8:>10,.2f} 억원/년\n"
            f"  제안 CBAM 비용  : {self.improved_cost_krw / 1e8:>10,.2f} 억원/년\n"
            f"  연간 절감       : {self.annual_saving_krw / 1e8:>10,.2f} 억원/년 ({self.saving_pct:.1f}%)"
        )


def cbam_default_baseline_unc() -> float:
    return PlantOperationParameters().measurement_relative_uncertainty_baseline


def cbam_default_improved_unc() -> float:
    return PlantOperationParameters().measurement_relative_uncertainty_improved


def simulate_cbam_savings(
    plant_params: PlantOperationParameters | None = None,
    cbam_params: CBAMParameters | None = None,
    solution_capex_krw: float = 500_000_000.0,    # 솔루션 도입 비용 5억 가정
) -> CBAMSavingReport:
    plant = plant_params or PlantOperationParameters()
    cbam = cbam_params or CBAMParameters()

    # 보고량
    reported_baseline = cbam_reported_emission(
        plant.annual_co2_emission_ton,
        plant.measurement_relative_uncertainty_baseline,
        cbam.conservative_margin_factor,
    )
    reported_improved = cbam_reported_emission(
        plant.annual_co2_emission_ton,
        plant.measurement_relative_uncertainty_improved,
        cbam.conservative_margin_factor,
    )

    cost_baseline = cbam_cost_krw(reported_baseline, cbam)
    cost_improved = cbam_cost_krw(reported_improved, cbam)
    saving = cost_baseline - cost_improved
    saving_pct = saving / cost_baseline * 100

    payback = solution_capex_krw / saving if saving > 0 else None

    return CBAMSavingReport(
        baseline_cost_krw=cost_baseline,
        improved_cost_krw=cost_improved,
        annual_saving_krw=saving,
        saving_pct=saving_pct,
        payback_years=payback,
    )


# =============================================================================
# 4. 민감도 분석 — 가격·정확도 변동
# =============================================================================

def sensitivity_grid(
    eu_prices_eur: list[float] = [60, 80, 100, 120],
    accuracy_improvements: list[float] = [0.01, 0.02, 0.03],
    plant_params: PlantOperationParameters | None = None,
) -> list[dict]:
    """
    가격 × 정확도 개선 grid → 절감액 표.
    """
    plant = plant_params or PlantOperationParameters()
    results = []
    for price in eu_prices_eur:
        for improve_delta in accuracy_improvements:
            cbam = CBAMParameters(eu_eta_price_eur_per_ton_co2=price)
            modified_plant = PlantOperationParameters(
                annual_co2_emission_ton=plant.annual_co2_emission_ton,
                measurement_relative_uncertainty_baseline=plant.measurement_relative_uncertainty_baseline,
                measurement_relative_uncertainty_improved=plant.measurement_relative_uncertainty_baseline - improve_delta,
            )
            report = simulate_cbam_savings(modified_plant, cbam)
            results.append({
                "price_eur": price,
                "accuracy_improvement_pp": improve_delta * 100,
                "annual_saving_krw_eok": report.annual_saving_krw / 1e8,
                "saving_pct": report.saving_pct,
            })
    return results


# =============================================================================
# 5. 셀프테스트
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("CBAM Impact Simulation (Extension D)")
    print("=" * 70)

    print("\n[기본 시나리오 — 한국서부발전 1호기 (500만 톤 CO2/년)]")
    report = simulate_cbam_savings()
    print(report.summary())
    if report.payback_years:
        print(f"  솔루션 5억원 가정 시 회수기간: {report.payback_years:.2f} 년")

    print("\n[민감도 분석 — EU 가격 × 측정 정확도 개선]")
    grid = sensitivity_grid()
    print(f"  {'EU 가격(€/t)':12s} {'정확도 개선(%p)':18s} {'절감(억원/년)':15s} {'절감율(%)':10s}")
    for row in grid:
        print(f"  {row['price_eur']:>10.0f}    {row['accuracy_improvement_pp']:>10.1f}        "
              f"{row['annual_saving_krw_eok']:>10.2f}      {row['saving_pct']:>6.1f}")

    print("\n[정책 함의]")
    print("  - EU CBAM 가격이 €120 도달 시 절감 효과 1.5배")
    print("  - 측정 정확도 1%p 개선 ≈ 연 ~억원 단위 절감 (호기당)")
    print("  - 한국서부발전 5개 호기 적용 시 효과 5배")
