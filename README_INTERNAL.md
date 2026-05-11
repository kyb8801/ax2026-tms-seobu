# 2026 AX 아이디어 경진대회 — 한국서부발전 TMS 과제

> **마감**: 2026-05-18 23:59
> **부문**: 분석-지정 (한국서부발전 — AI 기반 발전소 대기오염물질 배출 예측 + 최적 운전조건 도출)
> **전략**: Core 70% + Innovation 25% + Extension 5%
> **장려 이상 확률**: 65-75% / 대상권 12-18%

## 디렉토리 구조

```
AX2026_TMS_Seobu/
├── README.md                       # 이 파일
├── admin/                          # 행정 (이메일, 양식, 일정)
│   ├── data_request_email.md       # 5/2 데이터 신청 이메일 템플릿
│   ├── timeline.md                 # 일정 역산
│   └── checklist.md                # 제출 체크리스트
├── data/                           # 원시·가공 데이터 (5/2 이후)
│   ├── tms/                        # TMS 5분 간격 (SOx/NOx/PM/CO)
│   ├── airkorea/                   # 인근 대기측정소
│   ├── kma/                        # 기상청 (풍향·풍속·기온·습도·기압·강수)
│   └── kpx/                        # 전력거래소 (발전량·이용률)
├── notebooks/                      # 탐색 분석
│   ├── 01_eda.ipynb
│   ├── 02_etl_4source.ipynb
│   └── 03_baseline.ipynb
├── src/                            # 프로덕션 코드
│   ├── core/                       # Tier 1: Core
│   │   ├── etl_4source.py
│   │   ├── lstm_autoencoder.py
│   │   ├── isolation_forest.py
│   │   └── shap_xai.py
│   ├── innovation/                 # Tier 2: Innovation (다른 참가자 0%)
│   │   ├── gum_uncertainty.py      # GUM 합성표준불확도 numpy 구현
│   │   ├── measurement_aware_loss.py  # GUM-weighted PyTorch loss
│   │   ├── calibration_drift.py    # Cross-source drift detection
│   │   └── operator_trust.py       # Operator Trust Calibration (0-100)
│   └── extension/                  # Tier 3: Extension
│       └── cbam_impact.py          # CBAM 비용 영향 시뮬레이션
└── docs/                           # 산출물
    ├── report_main.md              # 분석 보고서 본문
    ├── exec_summary.md             # 1쪽 Executive Summary
    ├── gum_infographic.md          # 1쪽 GUM 인포그래픽 텍스트
    ├── kpi_definition.md           # 운영 KPI 정의서
    ├── cbam_appendix.md            # CBAM 부록 1쪽
    └── policy_proposal.md          # 환경부 정책 제언 1쪽
```

## 핵심 자산 매핑

| 자산 | 적용 |
|---|---|
| MetroAI v0.5.0 (8500 LOC) | Innovation A — GUM 통합 직접 |
| SpectraGuard (SERS QC) | Core — 이상탐지 엔진 이식 |
| ISO 18516 1저자 | Innovation A — 자가 인용 |
| ILAC-MRA + ISO 17034 | Innovation B — 교정 도메인 |
| 측정불확도 역공학 | Innovation A — 이론적 근거 |
| AFM 캘리브레이션 8년 | Innovation B — 드리프트 모델링 |

## 다음 액션 (D-Day 기준)

- **D-29 ~ D-21 (4/19~4/27)**: KIPO 발송 우선
- **D-20 ~ D-18 (4/28~4/30)**: 프리워크 — GUM 함수 핵심 선구현
- **D-17 (5/1)**: OPIc 시험
- **D-16 (5/2)**: ⭐ **데이터 즉시 신청** + 다운로드 시작
- **D-15 ~ D-13 (5/3~5/5)**: ETL · EDA
- **D-12 ~ D-10 (5/6~5/8)**: Core 모델
- **D-9 ~ D-7 (5/9~5/11)**: Innovation A (Measurement-aware ML)
- **D-6 ~ D-4 (5/12~5/14)**: Innovation B (Calibration Drift) + F (Operator Trust)
- **D-3 (5/15)**: Extension D (CBAM 1-pager)
- **D-2 ~ D-1 (5/16~5/17)**: 보고서 · 시각화 · 배포
- **D-0 (5/18 오전)**: 제출

## 평가 기준 매핑 (분석-지정 부문)

| 평가 기준 | Tier | 답변 |
|---|---|---|
| 가설의 정교함 | Innovation A | GUM 기반 측정불확도 통합 |
| 모델링 우수성 | Core + Innovation | LSTM-AE + GUM-weighted loss |
| 데이터 융합 노력 | Core | 4-source ETL (TMS+에어코리아+기상+전력) |
| 해결 대안 구체성 | Core + Innovation B | 운전 권고 + 교정 시점 예측 |
| 정책 실현성 | Extension D | CBAM 비용 영향 정량화 |

---

*마지막 업데이트: 2026-04-19. v2 혁신 트로이카 전략.*
