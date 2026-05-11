"""
4-Source ETL Pipeline (Core)
==============================

TMS + 에어코리아 + 기상청 + 전력거래소 — 4개 데이터 소스 결합.

평가 항목 "데이터 융합 노력" 직격.
5/2 데이터 도착 즉시 가동.

작성: 김용범 — 2026 AX 아이디어 경진대회
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


# =============================================================================
# 1. 데이터 소스 메타데이터
# =============================================================================

@dataclass
class DataSourceSpec:
    name: str
    sampling_interval_minutes: int   # 5(TMS), 60(AirKorea), 60(KMA), 60(KPX)
    columns: list[str] = field(default_factory=list)
    quality_flags: list[str] = field(default_factory=list)


TMS_SPEC = DataSourceSpec(
    name="TMS",
    sampling_interval_minutes=5,
    columns=["timestamp", "plant_id", "unit_id", "SOx_ppm", "NOx_ppm", "PM_mgm3", "CO_ppm", "stack_temp", "flow_rate"],
    quality_flags=["calibration_status", "data_quality_code"],
)
AIRKOREA_SPEC = DataSourceSpec(
    name="AirKorea",
    sampling_interval_minutes=60,
    columns=["timestamp", "station_id", "lat", "lon", "PM10", "PM25", "SO2_ppm", "NO2_ppm", "CO_ppm", "O3_ppm"],
    quality_flags=["data_grade"],
)
KMA_SPEC = DataSourceSpec(
    name="KMA_ASOS",
    sampling_interval_minutes=60,
    columns=["timestamp", "station_id", "lat", "lon", "elevation", "temperature_c", "humidity_pct", "wind_speed_ms", "wind_direction_deg", "pressure_hpa", "rainfall_mm"],
    quality_flags=["qc_flag"],
)
KPX_SPEC = DataSourceSpec(
    name="KPX_EPSIS",
    sampling_interval_minutes=60,
    columns=["timestamp", "plant_id", "unit_id", "generation_mwh", "utilization_pct", "fuel_type", "thermal_efficiency"],
    quality_flags=[],
)


# =============================================================================
# 2. ETL 단계
# =============================================================================

@dataclass
class ETLConfig:
    target_resolution_minutes: int = 60     # 시간 단위 정합
    aggregation: str = "mean"                # mean / median / max
    interpolation: str = "linear"            # linear / nearest / spline
    max_gap_hours: int = 6                   # 6시간 이상 결측은 NaN 유지
    align_method: str = "asof"               # asof / merge_close


def parse_timestamp_safe(ts) -> Optional[datetime]:
    """타임존·포맷 변형 허용 파서. 실데이터 도착 후 정밀화."""
    if isinstance(ts, datetime):
        return ts
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except Exception:
        try:
            return datetime.strptime(str(ts), "%Y-%m-%d %H:%M:%S")
        except Exception:
            return None


def resample_to_hourly(
    timestamps: np.ndarray,
    values: np.ndarray,
    target_minutes: int = 60,
    method: str = "mean",
) -> tuple[np.ndarray, np.ndarray]:
    """5분 → 60분 리샘플링.
    실데이터에서는 pandas resample으로 대체. 본 함수는 사전 검증용."""
    timestamps_sorted_idx = np.argsort(timestamps)
    ts_sorted = timestamps[timestamps_sorted_idx]
    val_sorted = values[timestamps_sorted_idx]

    if len(ts_sorted) == 0:
        return ts_sorted, val_sorted

    bin_size_seconds = target_minutes * 60
    t_min = ts_sorted[0]
    bins = np.arange(0, (ts_sorted[-1] - t_min) + bin_size_seconds, bin_size_seconds)

    relative_seconds = ts_sorted - t_min
    bin_indices = np.digitize(relative_seconds, bins) - 1

    aggregated_ts = []
    aggregated_val = []
    for b in range(len(bins) - 1):
        mask = bin_indices == b
        if mask.sum() == 0:
            continue
        if method == "mean":
            v = np.nanmean(val_sorted[mask])
        elif method == "median":
            v = np.nanmedian(val_sorted[mask])
        else:
            v = np.nanmax(val_sorted[mask])
        aggregated_ts.append(t_min + bins[b])
        aggregated_val.append(v)
    return np.array(aggregated_ts), np.array(aggregated_val)


def fill_missing_linear(values: np.ndarray, max_gap: int = 6) -> np.ndarray:
    """선형 보간 — 연속 결측 max_gap 이하만."""
    out = values.copy()
    nan_mask = np.isnan(out)
    if not nan_mask.any():
        return out

    n = len(out)
    i = 0
    while i < n:
        if not nan_mask[i]:
            i += 1
            continue
        j = i
        while j < n and nan_mask[j]:
            j += 1
        gap = j - i
        # 양 끝 보간 가능 + gap 한도 이내
        if 0 < i and j < n and gap <= max_gap:
            left, right = out[i - 1], out[j]
            out[i:j] = np.linspace(left, right, gap + 2)[1:-1]
        i = j
    return out


# =============================================================================
# 3. 메인 통합 함수
# =============================================================================

@dataclass
class FusedDataset:
    """4-source 결합 결과."""
    timestamps: np.ndarray
    tms: dict          # {pollutant: array}
    airkorea: dict     # {pollutant: array}
    kma: dict          # {variable: array}
    kpx: dict          # {variable: array}
    geometry: dict = field(default_factory=dict)  # {plant_id: StationGeometry}

    def n_samples(self) -> int:
        return len(self.timestamps)

    def feature_matrix(self, pollutant: str = "SOx") -> np.ndarray:
        """ML 입력용 피처 매트릭스 — TMS + 외부 변수 결합."""
        cols = []
        if pollutant in self.tms:
            cols.append(self.tms[pollutant])
        # 외부
        for k in ["PM25", "NO2_ppm"]:
            if k in self.airkorea:
                cols.append(self.airkorea[k])
        for k in ["temperature_c", "humidity_pct", "wind_speed_ms"]:
            if k in self.kma:
                cols.append(self.kma[k])
        for k in ["utilization_pct", "thermal_efficiency"]:
            if k in self.kpx:
                cols.append(self.kpx[k])
        return np.column_stack(cols)


def fuse_datasets(
    tms_data: dict,
    airkorea_data: dict,
    kma_data: dict,
    kpx_data: dict,
    config: ETLConfig | None = None,
) -> FusedDataset:
    """
    4-source 결합 — 5/2 도착 후 실 데이터로 호출.

    각 입력 dict는 {column: np.ndarray} 형식 가정.
    """
    if config is None:
        config = ETLConfig()

    # 1) 모든 소스의 timestamps를 60분 격자로 정렬
    # 2) 시간 정합 후 union timestamps 추출
    # 3) 각 변수 보간

    # 사전 검증용 — 첫 소스의 timestamps 사용
    ref_timestamps = tms_data.get("timestamp", np.array([]))

    fused = FusedDataset(
        timestamps=ref_timestamps,
        tms={k: v for k, v in tms_data.items() if k != "timestamp"},
        airkorea={k: v for k, v in airkorea_data.items() if k != "timestamp"},
        kma={k: v for k, v in kma_data.items() if k != "timestamp"},
        kpx={k: v for k, v in kpx_data.items() if k != "timestamp"},
    )
    return fused


# =============================================================================
# 4. 데이터 품질 리포트
# =============================================================================

@dataclass
class DataQualityReport:
    n_samples: int
    n_missing: dict
    n_outliers: dict
    sampling_continuity_pct: float
    cross_source_alignment_pct: float


def quality_report(dataset: FusedDataset, outlier_z: float = 3.5) -> DataQualityReport:
    n = dataset.n_samples()
    n_missing = {}
    n_outliers = {}
    for source_name, source_dict in [("tms", dataset.tms), ("airkorea", dataset.airkorea),
                                       ("kma", dataset.kma), ("kpx", dataset.kpx)]:
        for k, v in source_dict.items():
            v_arr = np.asarray(v, dtype=float)
            n_missing[f"{source_name}.{k}"] = int(np.isnan(v_arr).sum())
            if v_arr.size > 5:
                z = np.abs((v_arr - np.nanmean(v_arr)) / (np.nanstd(v_arr) + 1e-9))
                n_outliers[f"{source_name}.{k}"] = int((z > outlier_z).sum())
    return DataQualityReport(
        n_samples=n,
        n_missing=n_missing,
        n_outliers=n_outliers,
        sampling_continuity_pct=100.0,  # 실데이터에서 계산
        cross_source_alignment_pct=100.0,
    )


# =============================================================================
# 5. 셀프테스트
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("4-Source ETL Pipeline — Self-test")
    print("=" * 60)

    np.random.seed(42)
    n = 720  # 30일 × 24시간

    # 각 소스 가상 데이터
    timestamps = np.arange(n).astype(float) * 3600  # 1시간 간격 (초 단위)
    tms_data = {
        "timestamp": timestamps,
        "SOx_ppm": np.random.normal(50, 5, n),
        "NOx_ppm": np.random.normal(120, 15, n),
        "PM_mgm3": np.random.normal(15, 3, n),
        "CO_ppm": np.random.normal(8, 2, n),
    }
    airkorea_data = {
        "timestamp": timestamps,
        "PM25": np.random.normal(20, 7, n),
        "NO2_ppm": np.random.normal(0.03, 0.01, n),
    }
    kma_data = {
        "timestamp": timestamps,
        "temperature_c": 15 + 10 * np.sin(np.arange(n) * 2 * np.pi / 24) + np.random.normal(0, 1, n),
        "humidity_pct": np.random.uniform(40, 80, n),
        "wind_speed_ms": np.random.uniform(2, 6, n),
    }
    kpx_data = {
        "timestamp": timestamps,
        "utilization_pct": np.random.uniform(60, 95, n),
        "thermal_efficiency": np.random.uniform(0.40, 0.46, n),
    }

    # 일부 결측 주입
    nan_idx = np.random.choice(n, 30, replace=False)
    for k in ["SOx_ppm", "NOx_ppm"]:
        tms_data[k][nan_idx] = np.nan

    fused = fuse_datasets(tms_data, airkorea_data, kma_data, kpx_data)

    print(f"\n[Fused Dataset]")
    print(f"  샘플 수            : {fused.n_samples()}")
    print(f"  TMS 변수            : {list(fused.tms.keys())}")
    print(f"  AirKorea 변수       : {list(fused.airkorea.keys())}")
    print(f"  KMA 변수            : {list(fused.kma.keys())}")
    print(f"  KPX 변수            : {list(fused.kpx.keys())}")

    # 피처 매트릭스
    X = fused.feature_matrix(pollutant="SOx_ppm")
    print(f"\n[ML 입력 피처 매트릭스]")
    print(f"  shape = {X.shape}  (TMS-SOx + 6 외부 변수)")

    # 품질 리포트
    report = quality_report(fused)
    print(f"\n[데이터 품질 리포트]")
    print(f"  샘플 수            : {report.n_samples}")
    print(f"  결측치             :")
    for k, v in report.n_missing.items():
        if v > 0:
            print(f"    {k}: {v} ({v/report.n_samples*100:.1f}%)")
    print(f"  이상치 (|z| > 3.5)  :")
    for k, v in report.n_outliers.items():
        if v > 0:
            print(f"    {k}: {v}")

    # 보간 테스트
    sox_filled = fill_missing_linear(tms_data["SOx_ppm"], max_gap=6)
    n_filled = int(np.isnan(tms_data["SOx_ppm"]).sum() - np.isnan(sox_filled).sum())
    print(f"\n[선형 보간]")
    print(f"  결측 → 보간: {n_filled}개 (max_gap=6시간)")
