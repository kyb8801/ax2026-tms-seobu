"""
Cross-Source Calibration Drift Detection
==========================================

핵심 혁신: TMS 측정값을 인근 에어코리아 측정소와 자동 비교하여
시간에 따른 측정기 드리프트를 탐지하고 교정 시점을 예측.

기존: 정기 교정 (3~6개월) → 사이 드리프트는 다음 교정까지 모름
제안: 데이터 기반 드리프트 탐지 → 필요 시점 교정 권고
       → 연 교정 비용 30-50% 절감 + 측정 정확도 항상 유지

작성: 김용범 — 2026 AX 아이디어 경진대회
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import Optional


# =============================================================================
# 1. 두 측정 소스 간의 보정 모델
# =============================================================================

@dataclass
class StationGeometry:
    """측정소 위치·고도·기상 메타데이터."""
    lat: float
    lon: float
    elevation_m: float
    name: str = ""


def haversine_distance_km(s1: StationGeometry, s2: StationGeometry) -> float:
    """두 측정소 간 지표 거리 (km)."""
    R = 6371.0
    lat1, lon1 = np.radians([s1.lat, s1.lon])
    lat2, lon2 = np.radians([s2.lat, s2.lon])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c


def expected_concentration_decay(
    source_concentration: np.ndarray,
    distance_km: float,
    elevation_diff_m: float,
    wind_speed_ms: np.ndarray,
    decay_constant: float = 0.15,
    elevation_factor: float = 0.002,
) -> np.ndarray:
    """
    Gaussian Plume의 단순화 — 거리·고도·풍속에 따른 농도 감쇠 추정.
    실측 데이터(5/2~) 기반으로 decay_constant 회귀 보정 예정.

    C(distance) ≈ C₀ × exp(-k × d) × exp(-α × |Δz|) × wind_dilution(u)
    """
    spatial_decay = np.exp(-decay_constant * distance_km)
    elevation_decay = np.exp(-elevation_factor * abs(elevation_diff_m))
    wind_dilution = 1.0 / (1.0 + 0.1 * wind_speed_ms)
    return source_concentration * spatial_decay * elevation_decay * wind_dilution


# =============================================================================
# 2. 드리프트 탐지 — Page-Hinkley + CUSUM
# =============================================================================

class PageHinkleyDriftDetector:
    """
    Page-Hinkley test — 평균 변화점 검출.

    참조: Page, E. S. (1954) "Continuous Inspection Schemes". Biometrika.
    환경 측정 시계열에 적용 시 점진적 드리프트 검출에 효과적.
    """

    def __init__(self, delta: float = 0.005, threshold: float = 50.0):
        self.delta = delta            # 허용 잡음 폭 (sigma 단위)
        self.threshold = threshold    # 알람 임계
        self.cumsum_pos = 0.0
        self.cumsum_neg = 0.0
        self.min_pos = 0.0
        self.max_neg = 0.0
        self.mean = None
        self.n = 0
        self.alarms: list[int] = []

    def update(self, value: float, t_index: int) -> Optional[str]:
        self.n += 1
        if self.mean is None:
            self.mean = value
            return None

        # 누적합 업데이트
        deviation = value - self.mean - self.delta
        self.cumsum_pos += deviation
        self.cumsum_neg -= (value - self.mean + self.delta)
        self.min_pos = min(self.min_pos, self.cumsum_pos)
        self.max_neg = max(self.max_neg, self.cumsum_neg)

        ph_pos = self.cumsum_pos - self.min_pos
        ph_neg = self.cumsum_neg - self.max_neg

        # 이동평균 갱신
        self.mean = self.mean + (value - self.mean) / self.n

        if ph_pos > self.threshold:
            self.alarms.append(t_index)
            self._reset()
            return "POSITIVE_DRIFT"
        if ph_neg > self.threshold:
            self.alarms.append(t_index)
            self._reset()
            return "NEGATIVE_DRIFT"
        return None

    def _reset(self):
        self.cumsum_pos = 0.0
        self.cumsum_neg = 0.0
        self.min_pos = 0.0
        self.max_neg = 0.0


# =============================================================================
# 3. 메인 — Cross-Source Drift Detector
# =============================================================================

@dataclass
class DriftReport:
    """드리프트 분석 결과."""
    drift_score: float              # 0~1, 높을수록 드리프트 심각
    drift_alarms: list[int]         # 알람 발생 시점 인덱스
    recommended_calibration: bool   # 교정 권고 여부
    days_to_next_calibration: int   # 권고 시점까지 일수
    deviation_mean: float
    deviation_std: float
    method: str = "page_hinkley"


def detect_drift_cross_source(
    tms_values: np.ndarray,
    airkorea_values: np.ndarray,
    timestamps: np.ndarray,
    tms_station: StationGeometry,
    airkorea_station: StationGeometry,
    wind_speed_ms: np.ndarray,
    drift_threshold: float = 50.0,
    days_calibration_cycle: int = 90,
) -> DriftReport:
    """
    TMS와 인근 에어코리아 측정소의 측정값을 비교하여 드리프트 탐지.

    Parameters
    ----------
    tms_values : np.ndarray
        TMS 측정 농도 시계열 (5분 간격 권장 → 시간 평균 처리됨)
    airkorea_values : np.ndarray
        같은 시간대 에어코리아 측정값
    timestamps : np.ndarray of datetime
    tms_station, airkorea_station : StationGeometry
    wind_speed_ms : np.ndarray
        같은 시간대 풍속

    Returns
    -------
    DriftReport
    """
    # 1) 거리·고도·풍속 보정으로 "기대 농도" 계산
    distance = haversine_distance_km(tms_station, airkorea_station)
    elevation_diff = tms_station.elevation_m - airkorea_station.elevation_m

    expected_at_airkorea = expected_concentration_decay(
        source_concentration=tms_values,
        distance_km=distance,
        elevation_diff_m=elevation_diff,
        wind_speed_ms=wind_speed_ms,
    )

    # 2) 정규화 잔차 = (관측 - 기대) / 기대  (상대 편차)
    safe_expected = np.maximum(expected_at_airkorea, 1e-3)
    deviation = (airkorea_values - expected_at_airkorea) / safe_expected

    # 3) Page-Hinkley로 드리프트 알람
    detector = PageHinkleyDriftDetector(delta=0.005, threshold=drift_threshold)
    for i, d in enumerate(deviation):
        detector.update(float(d), i)

    # 4) 드리프트 점수 (0~1)
    drift_score = float(np.clip(np.std(deviation) / 0.2, 0.0, 1.0))

    # 5) 교정 권고 판정
    recommend = drift_score > 0.4 or len(detector.alarms) > 0
    if recommend:
        days_to_cal = max(1, int(days_calibration_cycle * (1.0 - drift_score)))
    else:
        days_to_cal = days_calibration_cycle

    return DriftReport(
        drift_score=drift_score,
        drift_alarms=detector.alarms,
        recommended_calibration=recommend,
        days_to_next_calibration=days_to_cal,
        deviation_mean=float(np.mean(deviation)),
        deviation_std=float(np.std(deviation)),
    )


# =============================================================================
# 4. 셀프테스트
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Cross-Source Calibration Drift Detection — Self-test")
    print("=" * 60)

    np.random.seed(42)
    n = 1000  # 약 84시간 (5분 간격)

    # 가상 TMS 측정 (50 ppm 기준 + 시간에 따라 점진 드리프트)
    base = 50.0
    drift = np.linspace(0, 5.0, n)  # 시간 따라 +5 ppm 드리프트
    noise = np.random.normal(0, 1.5, n)
    tms_values = base + drift + noise

    # 에어코리아 (drift 없음, 단순 노이즈)
    airkorea_values = base * 0.6 + np.random.normal(0, 1.0, n)  # 거리 감쇠로 60%

    # 측정소 위치 (예: 태안 화력)
    tms_st = StationGeometry(lat=36.91, lon=126.27, elevation_m=80, name="Taean TPP")
    airkorea_st = StationGeometry(lat=36.94, lon=126.30, elevation_m=10, name="Taean Air Quality")

    distance = haversine_distance_km(tms_st, airkorea_st)
    print(f"\n[측정소 정보]")
    print(f"  TMS:        {tms_st.name} ({tms_st.lat}, {tms_st.lon}) {tms_st.elevation_m}m")
    print(f"  Air Korea:  {airkorea_st.name} ({airkorea_st.lat}, {airkorea_st.lon}) {airkorea_st.elevation_m}m")
    print(f"  거리 = {distance:.2f} km")
    print(f"  고도차 = {tms_st.elevation_m - airkorea_st.elevation_m:.0f} m")

    wind = np.random.uniform(2, 6, n)
    timestamps = np.arange(n)

    report = detect_drift_cross_source(
        tms_values=tms_values,
        airkorea_values=airkorea_values,
        timestamps=timestamps,
        tms_station=tms_st,
        airkorea_station=airkorea_st,
        wind_speed_ms=wind,
        drift_threshold=30.0,
    )

    print(f"\n[Drift Report]")
    print(f"  drift_score              : {report.drift_score:.3f} (0~1)")
    print(f"  alarm 발생 횟수          : {len(report.drift_alarms)}")
    print(f"  교정 권고 여부           : {report.recommended_calibration}")
    print(f"  다음 교정 권고 시점      : {report.days_to_next_calibration}일 후")
    print(f"  편차 평균 (relative)     : {report.deviation_mean:+.4f}")
    print(f"  편차 표준편차 (relative) : {report.deviation_std:.4f}")

    print(f"\n[현행 정기 교정 vs 데이터 기반 교정]")
    cycle = 90
    if report.recommended_calibration:
        savings_days = cycle - report.days_to_next_calibration
        if savings_days > 0:
            print(f"  현행 90일 주기 → 데이터 기반 {report.days_to_next_calibration}일 주기")
            print(f"  → 추가 교정 필요: 정확도 우선 시점")
        else:
            extension = report.days_to_next_calibration - cycle
            print(f"  현행 90일 → 데이터 기반 {report.days_to_next_calibration}일")
            print(f"  → {extension}일 교정 연기 가능 → 비용 절감")
    else:
        print(f"  드리프트 미검출 → 90일 정기 주기 유지")
