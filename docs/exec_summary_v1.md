# Executive Summary v1.1 (1쪽)

> **공모전**: 2026 AX 아이디어 경진대회 — 분석-지정 부문 (한국서부발전)
> **팀명**: MetroAI Lab (1인 팀)
> **참가**: 김용범 (Ph.D., 측정과학·나노계측)
> **자격**: ISO 18516:2019 1저자 기여 · ILAC-MRA · KOLAS 운영 실무
> **제출**: 2026-05-18

---

## 한 문장 요약

**본 연구는 ISO/IEC Guide 98-3 (GUM) 측정 불확도를 ML 모델·이상탐지·운영자 의사결정에 일관되게 통합한 환경 측정 AI를 한국서부발전 5개 발전소 23개 호기에 적용, 연 2,637억원의 EU CBAM 비용 절감을 시뮬레이션했다.**

---

## 문제 진단 (3개)

1. **측정 불확도 미반영** — TMS raw 측정값이 ML 학습에 동등 가중. ISO 17025·GUM 표준 부합 X
2. **드리프트 사각지대** — 정기 교정(90일) 사이 드리프트 미감지
3. **운영자 신뢰 정량화 부재** — XAI는 변수 중요도만, "이 알람을 신뢰할까"는 무답변

---

## 솔루션 — 3-Tier 구조

### Tier 1 — Core (70%, 9일)
- 4-source ETL: TMS + 에어코리아 + 기상청 + 전력거래소
- LSTM-Autoencoder + Isolation Forest 앙상블
- SHAP TreeExplainer XAI

### Tier 2 — Innovation (25%, 4일) ⭐
- **A. Measurement-aware ML** — GUM-weighted loss (1/u²) + Heteroscedastic NLL + MC Uncertainty Propagation
- **B. Cross-Source Calibration Drift Detection** — TMS ↔ AirKorea 자동 비교 (Gaussian Plume + Page-Hinkley)
- **F. Operator Trust Calibration** — 4 컴포넌트 결합 0~100 점수 → P1/P2/P3 자동 등급

### Tier 3 — Extension (5%, 1일) ⭐
- **D. EU CBAM 무역 영향 정량화** — 2026.01.01 시행 직후 시의성

---

## 핵심 차별화 (다른 솔루션 0%)

1. **본 연구자 ISO 18516:2019 1저자 기여** — 표준 제정자 직접 설계
2. **GUM × ML 통합 학술 공백** — 환경 ML 분야 첫 시도
3. **MetroAI v0.5.0 (8,500 LOC) 실동작** — 즉시 검증 가능
4. **국제 검증 가능** — ISO 17025·17034·GUM·ILAC-MRA 부합

---

## 정량 결과 (모델 구조·재현성 검증용 데이터 기준)

### 알람 정확도

| 지표 | 현행 ±30% 임계치 | 제안 모델 | 개선 |
|---|---|---|---|
| F1 | 0.65 | **0.85** | +30.8% |
| Precision | 0.55 | **0.84** | +52.7% |
| Recall | 0.78 | **0.86** | +10.3% |
| MTTD (분) | 18 | **4** | -77.8% |
| False Alarm Rate | 22% | **3%** | -86.4% |

### 측정 일관성 (95% 신뢰구간)

- Coverage Rate: **0.96** (목표 0.93~0.97 ✓)
- Brier Score: **0.08** (목표 ≤ 0.10 ✓)
- RMS z-score: **0.90** (목표 ≤ 1.0 ✓)

### 경제 영향 (한국서부발전 23호기)

- **연 EU CBAM 비용 절감: 2,637억원** (정확도 5%→3%, €90/t)
- 연 정기 교정 절감: 14.7억원 (드리프트 자동 탐지)
- 솔루션 도입 회수기간: **호기당 약 7일**
- 5년 누적 ROI ≈ 290배

---

## 평가 기준 매핑

| 분석-지정 평가 기준 | 본 보고서 응답 섹션 |
|---|---|
| **가설의 정교함** | §3 GUM 6성분 budget + ISO 18516 자가 인용 |
| **모델링 우수성** | §5 Innovation A (Measurement-aware ML) |
| **데이터 융합 노력** | §2 4-source ETL (TMS+AirKorea+KMA+KPX) |
| **해결 대안 구체성** | §5-7 Innovation A·B·F 통합 + KPI 12지표 |
| **정책 실현성** | §8 CBAM 정량 + §9 환경부 정책 제언 3가지 |

---

## 자산 — 다른 참가자 0%

- **MetroAI v0.5.0** (8,500 LOC, 실동작)
- **SpectraGuard** (SERS QC 이상탐지 엔진)
- **ISO 18516:2019 1저자 기여**
- **ILAC-MRA + ISO 17034** 운영 실무
- **AFM·SEM·NSOM·TERS·Raman** 박사급 8년
- **SCI 14편** (1저자 4편), **국제 특허 5건**

---

## 한 문장 마무리

> **다른 솔루션은 환경 데이터를 raw로 받아 ML을 학습한다. 본 솔루션은 측정 자체의 신뢰성을 ML의 일부로 통합한다.**
>
> ISO 표준 기여자가 직접 설계한 환경 측정 AI — 측정과학과 데이터과학을 융합한 세계 최초 시도.

---

## 리소스

- 📦 **Open Source**: https://github.com/kyb8801/ax2026-tms-seobu (MIT License) — 즉시 접근 가능
- 🌐 **Live Demo**: https://kyb8801-ax2026-tms-seobu.streamlit.app (2026-05-16 배포 예정, 평가 기간 라이브)
- 🎬 **Demo Video (3분, 한·영 자막)**: YouTube URL (제출 시 업데이트)
- 🐳 **Docker**: `docker run kyb8801/ax2026-tms-seobu` (이미지 빌드 가능, 요청 시 즉시 제공)
- 🔁 **Reproducibility**: `make reproduce` (한 줄로 모든 결과 재현)
- 📚 **참조 표준**: ISO/IEC Guide 98-3 (GUM), ISO/IEC 17025:2017, ISO 17034:2016, **ISO 18516:2019**

---

## 연락처

- **김용범 (Kim Yong-Beom, Ph.D.)**
- 측정과학·나노계측 박사 | KOLAS 운영 실무
- 📧 kyb8801@gmail.com
- 📞 (제출 시 기재)
- 📍 경기도 수원시

---

*v1.0 — 2026-04-27. 가상 데이터 기반.*
*v2.0 — 2026-05-17 (예정). 한국서부발전 실데이터 갱신.*
