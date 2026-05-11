"""
End-to-End Pipeline Integration Test
======================================

9개 모듈을 한 번에 연결해서 가상 시나리오 1회 실행.
5/2 데이터 도착 즉시 0버그 시작을 보장.

실행: python tests/test_e2e_pipeline.py
또는: pytest tests/test_e2e_pipeline.py -v

작성: 김용범 — 2026 AX 아이디어 경진대회
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
from datetime import datetime, timedelta


# =============================================================================
# 1. 가상 4-source 데이터 생성
# =============================================================================

def make_synthetic_4source(n_hours: int = 720, anomaly_ratio: float = 0.05, seed: int = 42):
    """
    30일 × 24h = 720 시간 단위 가상 데이터.
    - TMS: SOx/NOx/PM/CO 4종 (5분 → 60분 평균)
    - AirKorea: PM25, NO2 (1시간)
    - KMA: 기온/습도/풍속/풍향 (1시간)
    - KPX: 이용률/열효율 (1시간)
    이상 패턴 5% 주입.
    """
    rng = np.random.default_rng(seed)
    timestamps = np.arange(n_hours).astype(float) * 3600

    # TMS (정상 데이터 + 이상 데이터)
    sox_normal = rng.normal(50, 5, n_hours)
    nox_normal = rng.normal(120, 15, n_hours)
    pm_normal = rng.normal(15, 3, n_hours)
    co_normal = rng.normal(8, 2, n_hours)

    # 이상 주입 (5%)
    n_anom = int(n_hours * anomaly_ratio)
    anom_idx = rng.choice(n_hours, n_anom, replace=False)
    sox_normal[anom_idx] += rng.uniform(20, 50, n_anom)
    nox_normal[anom_idx] += rng.uniform(40, 80, n_anom)
    pm_normal[anom_idx] += rng.uniform(10, 30, n_anom)

    # 시간에 따른 점진 드리프트 (TMS 측정기 노화)
    drift = np.linspace(0, 4.0, n_hours)
    sox_with_drift = sox_normal + drift

    labels = np.zeros(n_hours, dtype=int)
    labels[anom_idx] = 1

    tms_data = {
        "timestamp": timestamps,
        "SOx_ppm": sox_with_drift,
        "NOx_ppm": nox_normal,
        "PM_mgm3": pm_normal,
        "CO_ppm": co_normal,
    }
    airkorea_data = {
        "timestamp": timestamps,
        "PM25": rng.normal(20, 7, n_hours),
        "NO2_ppm": rng.normal(0.03, 0.01, n_hours),
    }
    kma_data = {
        "timestamp": timestamps,
        "temperature_c": 15 + 10 * np.sin(np.arange(n_hours) * 2 * np.pi / 24) + rng.normal(0, 1, n_hours),
        "humidity_pct": rng.uniform(40, 80, n_hours),
        "wind_speed_ms": rng.uniform(2, 6, n_hours),
        "wind_direction_deg": rng.uniform(0, 360, n_hours),
    }
    kpx_data = {
        "timestamp": timestamps,
        "utilization_pct": rng.uniform(60, 95, n_hours),
        "thermal_efficiency": rng.uniform(0.40, 0.46, n_hours),
    }

    return tms_data, airkorea_data, kma_data, kpx_data, labels


# =============================================================================
# 2. End-to-End 파이프라인
# =============================================================================

def run_e2e_pipeline():
    """9개 모듈 한 번에 실행."""

    print("=" * 70)
    print("End-to-End Pipeline Test — 2026 AX 한국서부발전")
    print("=" * 70)

    # ----- Step 1: 4-source ETL -----
    print("\n[Step 1/8] 4-Source ETL")
    from src.core.etl_4source import fuse_datasets, quality_report, fill_missing_linear

    tms, airkorea, kma, kpx, labels = make_synthetic_4source(720)

    # 일부 결측 주입
    nan_idx = np.random.RandomState(42).choice(720, 30, replace=False)
    tms["SOx_ppm"] = tms["SOx_ppm"].copy()
    tms["SOx_ppm"][nan_idx] = np.nan
    tms["SOx_ppm"] = fill_missing_linear(tms["SOx_ppm"], max_gap=6)

    fused = fuse_datasets(tms, airkorea, kma, kpx)
    qr = quality_report(fused)
    print(f"  ✓ Fused dataset: {fused.n_samples()} samples")
    print(f"  ✓ Total missing values handled: {sum(qr.n_missing.values())}")

    # ----- Step 2: GUM 측정 불확도 -----
    print("\n[Step 2/8] GUM Measurement Uncertainty")
    from src.innovation.gum_uncertainty import gum_uncertainty_array

    sox_values = fused.tms["SOx_ppm"]
    cal_days = np.random.RandomState(42).randint(1, 90, len(sox_values))
    u_c_array = gum_uncertainty_array(sox_values, "SOx", cal_days)
    print(f"  ✓ GUM uncertainty array: u_c mean={u_c_array.mean():.3f}, max={u_c_array.max():.3f}")

    # ----- Step 3: Cross-Source Calibration Drift -----
    print("\n[Step 3/8] Cross-Source Calibration Drift Detection")
    from src.innovation.calibration_drift import StationGeometry, detect_drift_cross_source

    tms_st = StationGeometry(lat=36.91, lon=126.27, elevation_m=80, name="Taean")
    air_st = StationGeometry(lat=36.94, lon=126.30, elevation_m=10, name="Taean AQ")

    drift_report = detect_drift_cross_source(
        tms_values=sox_values,
        airkorea_values=fused.airkorea["PM25"] * 2.0,  # 가짜 SO2 등가
        timestamps=np.arange(len(sox_values)),
        tms_station=tms_st,
        airkorea_station=air_st,
        wind_speed_ms=fused.kma["wind_speed_ms"],
        drift_threshold=30.0,
    )
    print(f"  ✓ Drift score: {drift_report.drift_score:.3f}")
    print(f"  ✓ Recommend calibration: {drift_report.recommended_calibration}")
    print(f"  ✓ Days to next calibration: {drift_report.days_to_next_calibration}")

    # ----- Step 4: PCA Baseline Anomaly Detection -----
    print("\n[Step 4/8] LSTM-AE Baseline (PCA fallback)")
    from src.core.lstm_autoencoder import PCAAutoencoderBaseline

    feature_matrix = fused.feature_matrix("SOx_ppm")
    pca_ae = PCAAutoencoderBaseline(n_components=2)
    pca_ae.fit(feature_matrix[labels == 0])
    recon_errors = pca_ae.reconstruction_error(feature_matrix)
    threshold = np.percentile(recon_errors[labels == 0], 95)
    pca_predictions = (recon_errors > threshold).astype(int)

    tp = int(((pca_predictions == 1) & (labels == 1)).sum())
    fp = int(((pca_predictions == 1) & (labels == 0)).sum())
    fn = int(((pca_predictions == 0) & (labels == 1)).sum())
    p = tp / max(tp + fp, 1); r = tp / max(tp + fn, 1)
    f1_pca = 2 * p * r / max(p + r, 1e-9)
    print(f"  ✓ PCA F1: {f1_pca:.3f} (P={p:.3f}, R={r:.3f})")

    # ----- Step 5: GUM-aware Isolation Forest -----
    print("\n[Step 5/8] GUM-aware Isolation Forest")
    from src.core.isolation_forest_gum import GUMAwareIsolationForest, GUMIForestConfig

    detector = GUMAwareIsolationForest(GUMIForestConfig(contamination=0.05))
    detector.fit(feature_matrix, u_c=u_c_array)
    iforest_pred = detector.predict(feature_matrix)  # -1: anomaly, 1: normal
    iforest_anomaly = (iforest_pred == -1).astype(int)

    tp = int(((iforest_anomaly == 1) & (labels == 1)).sum())
    fp = int(((iforest_anomaly == 1) & (labels == 0)).sum())
    fn = int(((iforest_anomaly == 0) & (labels == 1)).sum())
    p = tp / max(tp + fp, 1); r = tp / max(tp + fn, 1)
    f1_if = 2 * p * r / max(p + r, 1e-9)
    print(f"  ✓ IForest F1: {f1_if:.3f} (P={p:.3f}, R={r:.3f})")

    # ----- Step 6: SHAP XAI -----
    print("\n[Step 6/8] SHAP XAI")
    from src.core.shap_xai import explain_with_shap

    class DummyModel:
        def predict(self, x):
            return x.mean(axis=1)

    feature_names = ["TMS_SOx", "AK_PM25", "AK_NO2", "KMA_temp", "KMA_humid", "KMA_wind", "KPX_util", "KPX_eff"]
    shap_report = explain_with_shap(
        model=DummyModel(),
        X_baseline=feature_matrix[:100],
        X_explain=feature_matrix[100:200],
        feature_names=feature_names,
    )
    print(f"  ✓ XAI consistency: {shap_report.consistency_score:.3f}")
    print(f"  ✓ Top features: {[name for name, _ in shap_report.top_k_features(3)]}")

    # ----- Step 7: GUM-weighted Loss Evaluation -----
    print("\n[Step 7/8] Measurement-aware Loss Evaluation")
    from src.innovation.measurement_aware_loss import (
        gum_weighted_mse_numpy,
        measurement_consistency_score,
    )
    # 가짜 예측: 정답 + noise
    sox_pred = sox_values + np.random.RandomState(42).normal(0, 1.5, len(sox_values))
    plain_mse = float(np.mean((sox_values - sox_pred) ** 2))
    gum_loss = gum_weighted_mse_numpy(sox_values, sox_pred, u_c_array)
    consistency = measurement_consistency_score(sox_values, sox_pred, u_c_array)
    print(f"  ✓ Plain MSE: {plain_mse:.3f}")
    print(f"  ✓ GUM-weighted MSE: {gum_loss:.3f}")
    print(f"  ✓ 95% Coverage: {consistency['coverage_rate_95']:.3f}")
    print(f"  ✓ RMS z-score: {consistency['rms_z_score']:.3f}")

    # ----- Step 8: Operator Trust + CBAM -----
    print("\n[Step 8/8] Operator Trust + CBAM Impact")
    from src.innovation.operator_trust import compute_operator_trust
    from src.extension.cbam_impact import simulate_cbam_savings, PlantOperationParameters, CBAMParameters

    # OTS 계산 (마지막 측정값 기준)
    rng = np.random.default_rng(42)
    shap_baseline = rng.normal(0, 0.5, (200, 8))
    shap_recent = shap_baseline[:50] + rng.normal(0, 0.05, (50, 8))
    past_pred = sox_pred[-100:]
    past_act = sox_values[-100:]
    past_unc = u_c_array[-100:]

    trust = compute_operator_trust(
        measurement_value=float(sox_values[-1]),
        measurement_uncertainty=float(u_c_array[-1]),
        prediction_mean=float(sox_pred[-1]),
        prediction_std=2.0,
        shap_recent=shap_recent,
        shap_baseline=shap_baseline,
        past_predictions=past_pred,
        past_actuals=past_act,
        past_uncertainties=past_unc,
    )
    print(f"  ✓ OTS: {trust.score:.1f} → {trust.level.value}")

    # CBAM (한국서부발전 1호기 가정)
    cbam_report = simulate_cbam_savings(
        PlantOperationParameters(annual_co2_emission_ton=5_000_000),
        CBAMParameters(eu_eta_price_eur_per_ton_co2=90),
    )
    print(f"  ✓ CBAM 연간 절감: {cbam_report.annual_saving_krw / 1e8:.1f} 억원/년 "
          f"({cbam_report.saving_pct:.1f}%)")

    # ----- 최종 결과 요약 -----
    print("\n" + "=" * 70)
    print("Final Summary")
    print("=" * 70)
    print(f"  데이터 처리            : {fused.n_samples()} 샘플 × {feature_matrix.shape[1]} feature")
    print(f"  PCA 베이스라인 F1      : {f1_pca:.3f}")
    print(f"  GUM IForest F1         : {f1_if:.3f}")
    print(f"  Drift 검출             : {'권고' if drift_report.recommended_calibration else '정상'}")
    print(f"  XAI 일관성             : {shap_report.consistency_score:.3f}")
    print(f"  측정 일관성 (95% Cov)  : {consistency['coverage_rate_95']:.3f}")
    print(f"  Operator Trust         : {trust.score:.1f}/100 [{trust.level.value}]")
    print(f"  CBAM 연간 절감         : {cbam_report.annual_saving_krw / 1e8:.0f} 억원/년")
    print()
    print("✅ End-to-End 파이프라인 통합 테스트 통과 — 5/2 데이터 도착 즉시 가동 가능")

    return {
        "n_samples": fused.n_samples(),
        "f1_pca": f1_pca,
        "f1_iforest": f1_if,
        "drift_score": drift_report.drift_score,
        "xai_consistency": shap_report.consistency_score,
        "coverage_95": consistency["coverage_rate_95"],
        "ots": trust.score,
        "ots_level": trust.level.value,
        "cbam_saving_eok": cbam_report.annual_saving_krw / 1e8,
    }


# =============================================================================
# 3. pytest 호환 함수
# =============================================================================

def test_e2e_pipeline_runs():
    """pytest 호환 — 통합 파이프라인이 예외 없이 실행되는지."""
    result = run_e2e_pipeline()
    assert result["n_samples"] > 0
    assert 0.0 <= result["xai_consistency"] <= 1.0
    assert 0.0 <= result["coverage_95"] <= 1.0
    assert 0.0 <= result["ots"] <= 100.0


if __name__ == "__main__":
    run_e2e_pipeline()
