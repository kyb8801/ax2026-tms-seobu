"""
Streamlit Demo — 2026 AX 아이디어 경진대회 (한국서부발전 TMS)
=============================================================

평가위원이 브라우저에서 직접 시연 가능한 인터랙티브 대시보드.

배포: streamlit.io Community Cloud (무료, public repo)
URL: https://kyb8801-ax2026-tms-seobu.streamlit.app  (가정)

작성: 김용범 — 2026 AX 아이디어 경진대회
"""

from __future__ import annotations

import sys
import os
from pathlib import Path

# Path 설정
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

import numpy as np

# Streamlit은 환경 구축 후 활성. import 시도 → 실패 시 안내.
try:
    import streamlit as st
    import plotly.graph_objects as go
    import plotly.express as px
    _HAS_STREAMLIT = True
except ImportError:
    _HAS_STREAMLIT = False
    print("[안내] Streamlit 미설치 — pip install -r requirements.txt 후 실행")
    sys.exit(0)


# 모듈 import (try/except로 graceful)
try:
    from src.innovation.gum_uncertainty import (
        gum_uncertainty_array,
        build_tms_uncertainty_budget,
        combined_uncertainty,
        expanded_uncertainty,
    )
    from src.innovation.measurement_aware_loss import (
        gum_weighted_mse_numpy,
        measurement_consistency_score,
    )
    from src.innovation.calibration_drift import (
        StationGeometry,
        detect_drift_cross_source,
    )
    from src.innovation.operator_trust import (
        compute_operator_trust,
    )
    from src.extension.cbam_impact import (
        simulate_cbam_savings,
        sensitivity_grid,
        PlantOperationParameters,
        CBAMParameters,
    )
except ImportError as e:
    st.error(f"모듈 import 실패: {e}. requirements.txt 설치 확인.")
    st.stop()


# =============================================================================
# 1. 페이지 설정
# =============================================================================

st.set_page_config(
    page_title="AX 2026 — 한국서부발전 TMS",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🏭 2026 AX 아이디어 경진대회 — 한국서부발전 TMS")
st.caption("Measurement-aware AI + Cross-Source Calibration Drift + Operator Trust + CBAM Impact")
st.caption("작성: 김용범 (Ph.D., 측정과학·나노계측) | ISO 18516:2019 1저자")

# =============================================================================
# 2. 사이드바 — 시나리오 선택
# =============================================================================

with st.sidebar:
    st.header("🎛 시뮬레이션 설정")
    pollutant = st.selectbox("오염물질", ["SOx", "NOx", "PM", "CO"])
    measurement_value = st.slider("측정 농도 (ppm 또는 mg/m³)", 10, 200, 50)
    calibration_days = st.slider("교정 후 경과 일수", 0, 180, 30)

    st.divider()
    st.markdown("### 📊 모듈 선택")
    show_gum = st.checkbox("GUM 측정 불확도", value=True)
    show_drift = st.checkbox("Cross-Source Calibration Drift", value=True)
    show_trust = st.checkbox("Operator Trust Calibration", value=True)
    show_cbam = st.checkbox("CBAM 무역 영향", value=True)


# =============================================================================
# 3. 메인 — 모듈별 시각화
# =============================================================================

# --- 3.1 GUM 측정 불확도 ---
if show_gum:
    st.header("1️⃣ GUM 측정 불확도 (Innovation A의 토대)")
    components = build_tms_uncertainty_budget(measurement_value, pollutant, calibration_days)
    u_c = combined_uncertainty(components)
    U = expanded_uncertainty(u_c)
    relative_pct = (U / measurement_value) * 100 if measurement_value > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("합성표준불확도 u_c", f"{u_c:.3f}")
    col2.metric("확장불확도 U (k=2)", f"±{U:.3f}")
    col3.metric("상대 불확도", f"{relative_pct:.2f}%")

    # 성분 기여 차트
    names = [c.name for c in components]
    contribs = [c.variance_contribution() for c in components]
    fig = go.Figure(go.Bar(x=names, y=contribs, marker_color="#0b4a8b"))
    fig.update_layout(
        title="불확도 성분별 분산 기여 (제곱 합 = u_c²)",
        yaxis_title="Variance Contribution",
        height=350,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        f"""
**해석**: 측정값 {measurement_value}ppm은 95% 확률로 **[{measurement_value - U:.2f}, {measurement_value + U:.2f}]** 사이에 있음.
이 신뢰도가 ML loss에 가중치(1/u²)로 통합됨 → **Innovation A**.
"""
    )
    st.divider()


# --- 3.2 Calibration Drift ---
if show_drift:
    st.header("2️⃣ Cross-Source Calibration Drift Detection")
    np.random.seed(42)
    n = 500

    base = measurement_value
    drift_amplitude = st.slider("가상 드리프트 폭 (ppm)", 0.0, 10.0, 3.0, 0.5)
    drift = np.linspace(0, drift_amplitude, n)
    tms_values = base + drift + np.random.normal(0, 1.5, n)
    airkorea_values = base * 0.6 + np.random.normal(0, 1.0, n)

    tms_st = StationGeometry(lat=36.91, lon=126.27, elevation_m=80, name="Taean TPP")
    airkorea_st = StationGeometry(lat=36.94, lon=126.30, elevation_m=10, name="Taean AQ Station")
    wind = np.random.uniform(2, 6, n)

    report = detect_drift_cross_source(
        tms_values=tms_values,
        airkorea_values=airkorea_values,
        timestamps=np.arange(n),
        tms_station=tms_st,
        airkorea_station=airkorea_st,
        wind_speed_ms=wind,
        drift_threshold=30.0,
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Drift Score", f"{report.drift_score:.3f}")
    col2.metric("교정 권고", "Yes" if report.recommended_calibration else "No")
    col3.metric("권고 시점", f"{report.days_to_next_calibration}일 후")

    # 드리프트 시각화
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(y=tms_values, name="TMS", line_color="#1e4f8a"))
    fig2.add_trace(go.Scatter(y=airkorea_values, name="에어코리아 (인근)", line_color="#d9534f"))
    fig2.update_layout(title="TMS vs 인근 에어코리아 (5분 단위)", height=300)
    st.plotly_chart(fig2, use_container_width=True)

    cycle = 90
    if report.recommended_calibration and report.days_to_next_calibration < cycle:
        st.success(f"📈 데이터 기반 권고가 정기 교정({cycle}일)보다 이른 {report.days_to_next_calibration}일 → 측정 정확도 우선")
    elif report.days_to_next_calibration > cycle:
        st.info(f"💰 정기 교정({cycle}일) 대비 {report.days_to_next_calibration - cycle}일 연장 가능 → 비용 절감")
    st.divider()


# --- 3.3 Operator Trust ---
if show_trust:
    st.header("3️⃣ Operator Trust Calibration")

    pred_mean = st.slider("모델 예측 평균", 30.0, 200.0, float(measurement_value + 5))
    pred_std = st.slider("모델 예측 표준편차", 0.0, 50.0, 3.0)

    np.random.seed(42)
    shap_baseline = np.random.normal(0, 0.5, (200, 8))
    shap_recent = shap_baseline[:50] + np.random.normal(0, 0.05, (50, 8))
    past_pred = np.random.uniform(40, 60, 100)
    past_act = past_pred + np.random.normal(0, 1.0, 100)
    past_unc = np.full(100, 1.5)

    if show_gum:
        u_for_trust = u_c
    else:
        components_local = build_tms_uncertainty_budget(measurement_value, pollutant, calibration_days)
        u_for_trust = combined_uncertainty(components_local)

    trust = compute_operator_trust(
        measurement_value=float(measurement_value),
        measurement_uncertainty=u_for_trust,
        prediction_mean=pred_mean,
        prediction_std=pred_std,
        shap_recent=shap_recent,
        shap_baseline=shap_baseline,
        past_predictions=past_pred,
        past_actuals=past_act,
        past_uncertainties=past_unc,
    )

    col1, col2 = st.columns([1, 2])
    col1.metric("OTS (0~100)", f"{trust.score:.1f}", help=trust.rationale)
    col1.metric("등급", trust.level.value)

    # 4 컴포넌트 막대
    comp_names = ["측정", "모델", "XAI", "이력"]
    comp_values = [
        trust.components.measurement_quality * 100,
        trust.components.model_confidence * 100,
        trust.components.xai_consistency * 100,
        trust.components.historical_accuracy * 100,
    ]
    fig3 = go.Figure(go.Bar(x=comp_names, y=comp_values, marker_color="#1abc9c"))
    fig3.update_layout(title="OTS 4 컴포넌트 (각 0~100)", yaxis_range=[0, 100], height=300)
    col2.plotly_chart(fig3, use_container_width=True)

    color_map = {
        "AUTO_EXECUTE": "🟢",
        "REVIEW_REQUIRED": "🟡",
        "MANUAL_APPROVE": "🟠",
        "AUTO_REJECT": "🔴",
    }
    st.info(f"{color_map.get(trust.level.value, '⚪')} **{trust.level.value}** — {trust.rationale}")
    st.divider()


# --- 3.4 CBAM Impact ---
if show_cbam:
    st.header("4️⃣ CBAM 무역 영향 (Extension D)")

    annual_co2 = st.slider("연간 CO2 배출량 (만 톤)", 100, 1000, 500) * 1e4
    eu_price = st.slider("EU CBAM 가격 (€/t)", 60, 150, 90)
    baseline_unc = st.slider("현행 측정 정확도 (%)", 1.0, 10.0, 5.0)
    improved_unc = st.slider("개선 후 정확도 (%)", 1.0, 10.0, 3.0)

    plant = PlantOperationParameters(
        annual_co2_emission_ton=annual_co2,
        measurement_relative_uncertainty_baseline=baseline_unc / 100,
        measurement_relative_uncertainty_improved=improved_unc / 100,
    )
    cbam = CBAMParameters(eu_eta_price_eur_per_ton_co2=eu_price)
    rep = simulate_cbam_savings(plant, cbam)

    col1, col2, col3 = st.columns(3)
    col1.metric("현행 CBAM 비용", f"{rep.baseline_cost_krw / 1e8:,.0f} 억원/년")
    col2.metric("개선 후 비용", f"{rep.improved_cost_krw / 1e8:,.0f} 억원/년")
    col3.metric("연간 절감", f"{rep.annual_saving_krw / 1e8:,.0f} 억원 ({rep.saving_pct:.1f}%)")

    # 민감도 표
    grid = sensitivity_grid()
    import pandas as pd

    df_grid = pd.DataFrame(grid)
    fig_grid = px.scatter(
        df_grid,
        x="price_eur",
        y="annual_saving_krw_eok",
        size="accuracy_improvement_pp",
        color="accuracy_improvement_pp",
        labels={"annual_saving_krw_eok": "연간 절감 (억원)", "price_eur": "EU 가격 (€/t)",
                "accuracy_improvement_pp": "정확도 개선 (%p)"},
        title="EU 가격 × 정확도 개선 → 연간 절감",
    )
    st.plotly_chart(fig_grid, use_container_width=True)


# =============================================================================
# 4. 푸터
# =============================================================================

st.divider()
st.markdown(
    """
**📚 참조 표준**: ISO/IEC Guide 98-3 (GUM) · ISO/IEC 17025:2017 · ISO 17034:2016 · **ISO 18516:2019** (본 연구자 1저자 기여)
**📊 데이터 소스**: TMS · AirKorea · KMA · KPX EPSIS

*본 시연은 가상 데이터 기반. 5/2 데이터 도착 후 실제 한국서부발전 TMS 데이터로 갱신 예정.*
"""
)
