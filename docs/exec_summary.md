# Executive Summary — 1쪽 요약

> 본 보고서를 처음 보는 평가위원이 5분 안에 핵심을 파악하기 위한 1쪽 요약.

---

## 한 줄 결론

**한국서부발전 TMS에 ISO/IEC Guide 98-3 (GUM) 측정 불확도를 ML 모델·이상탐지·운영 의사결정에 일관되게 통합하여, 측정 신뢰도와 예측 신뢰도를 분리하지 않는 통합적 환경 측정 AI 시스템을 제안한다.**

---

## 문제 진단 (3개)

1. **측정 불확도 미반영** — TMS 측정 데이터가 ML 학습에 동등 가중. 신뢰도 낮은 측정도 모델에 영향
2. **드리프트 사각지대** — 정기 교정(90일) 사이 측정기 드리프트 미감지
3. **운영자 신뢰 정량화 부재** — XAI는 변수 중요도만 보여줌. "이 알람을 얼마나 신뢰할까"는 미답변

---

## 솔루션 (Tier 3 구조)

### Tier 1 — Core (기본기, 70% 시간)
- 4-source ETL: TMS + 에어코리아 + 기상청 + 전력거래소
- LSTM-Autoencoder + Isolation Forest 앙상블 이상탐지
- SHAP XAI 변수 중요도

### Tier 2 — Innovation (다른 참가자 0%, 25% 시간)
- **A. Measurement-aware ML** — GUM 가중 손실 + Heteroscedastic NLL + MC uncertainty propagation
- **B. Cross-Source Calibration Drift Detection** — TMS ↔ 에어코리아 자동 비교 + Page-Hinkley + 거리·고도·풍속 보정
- **F. Operator Trust Calibration** — 0~100 OTS + P1/P2/P3 자동 등급

### Tier 3 — Extension (시의성, 5% 시간)
- **D. CBAM 무역 영향** — 측정 정확도 1%p 개선 → 호기당 연 ~억원 단위 절감

---

## 자산 매핑 (왜 본 연구자만 가능한가)

| 자산 | 본 보고서 적용 |
|---|---|
| MetroAI v0.5.0 (8500 LOC, GUM 자동화) | Innovation A 직접 통합 |
| SpectraGuard (SERS QC 이상탐지) | Core Isolation Forest 이식 |
| **ISO 18516:2019 1저자 기여** | Innovation A 자가 인용 |
| **ILAC-MRA + ISO 17034 운영** | Innovation B 교정 도메인 |
| AFM 캘리브레이션 8년 | Innovation B 드리프트 모델링 |
| 측정불확도 역공학 | 본 연구의 이론적 토대 |

---

## 평가 기준 매핑

| 기준 | 본 보고서 답변 |
|---|---|
| 가설의 정교함 | GUM 합성표준불확도 + 6개 성분 budget (§3) |
| 모델링 우수성 | Measurement-aware ML + Heteroscedastic NLL (§5) |
| 데이터 융합 노력 | 4-source ETL + Cross-Source Calibration (§2, §6) |
| 해결 대안 구체성 | Innovation A·B·F 통합 + 운영 KPI (§5-7, §9) |
| 정책 실현성 | CBAM 정량 영향 + 환경부 정책 제언 (§8, §9) |

---

## 기대 성과 (5/2 데이터 도착 후 정량 확정)

- F1 알람 정확도 향상 (현행 임계치 대비)
- 측정 일관성 점수 95% coverage rate 달성
- Calibration cost 30~50% 절감 추정
- CBAM 보고 비용 호기당 연 ~억원 단위 절감 (시뮬레이션)
- ISO 17025·17034·18516 표준 부합 → 국제 검증 가능

---

## 본 보고서의 차별점 한 문장

> **다른 솔루션은 환경 데이터를 raw로 받아 ML 모델을 학습한다. 본 솔루션은 측정 자체의 신뢰성을 ML의 일부로 통합한다.**

ISO 표준 기여자가 직접 설계한 환경 측정 AI — 측정과학과 데이터과학을 융합한 **세계 최초 시도**.
