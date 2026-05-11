# 운영 KPI 정의서

> **목적**: 평가 항목 "정책 실현성" 직접 답변. 평가위원이 "운영 가능한가" 의심을 한 페이지로 해소.
> **분량**: 보고서 별첨 1쪽.

---

## KPI 매트릭스

| 분류 | KPI | 정의 | 목표값 | 측정 주기 |
|---|---|---|---|---|
| **검출 성능** | Detection Latency | 이상 발생 ~ 알람 시간 | ≤ 5분 | 실시간 |
| | Recall (오염물질별) | 실제 이상 중 탐지 비율 | SOx ≥ 95%, NOx ≥ 95%, PM ≥ 90% | 일간 |
| | Precision (오염물질별) | 알람 중 실제 이상 비율 | ≥ 80% (false alarm 20% 이하) | 일간 |
| | F1 Score | 2 × P × R / (P + R) | ≥ 0.85 | 일간 |
| **신뢰성** | Confidence Calibration (Brier Score) | (예측확률 - 실제)² 평균 | ≤ 0.10 | 주간 |
| | Coverage Rate (95%) | 실측이 예측 ±2u 안에 있는 비율 | 0.93 ≤ x ≤ 0.97 | 주간 |
| | RMS z-score | √mean(((y-ŷ)/u)²) | ≤ 1.0 | 주간 |
| **운영 효율** | Operator Trust Index | 평균 OTS (전체 알람) | ≥ 70/100 | 주간 |
| | Auto-Execute Ratio | OTS ≥ 80 비율 | ≥ 60% (운영자 부담 ↓) | 주간 |
| | Calibration Cost Reduction | 정기 교정 대비 절감 | 30~50% | 분기 |
| **정책 부합** | ISO 17025 부합 | 검·교정 추적성 보고 | 연 1회 외부 인증 | 연간 |
| | CBAM 보고 정확도 | 보수 마진 축소율 | 1~3%p 개선 | 분기 |
| | 운전 권고 채택률 | 알람 → 실 운전 조정 | ≥ 50% (현장 신뢰 지표) | 월간 |

---

## KPI 산출 코드 위치

- `src/innovation/measurement_aware_loss.py` — Coverage, Brier, RMS z
- `src/innovation/operator_trust.py` — OTS, Auto-Execute Ratio
- `src/innovation/calibration_drift.py` — Calibration Cost Reduction
- `src/extension/cbam_impact.py` — CBAM 보고 정확도, 비용 절감
- `src/core/lstm_autoencoder.py` — Detection Latency, F1
- `src/core/shap_xai.py` — XAI 일관성

---

## 보고 자동화

```
[일간 리포트]   매일 09:00 자동 메일 — Recall/Precision/F1, Auto-Execute Ratio
[주간 리포트]   월요일 09:00 — Coverage, Brier, OTS 분포, 알람 통계
[월간 리포트]   1일 09:00 — 운전 권고 채택률, 운영자 피드백 통계
[분기 리포트]   분기 첫째 주 — Calibration cost, CBAM 보고 정확도, 정책 부합
[연간 리포트]   1월 둘째 주 — ISO 17025 외부 인증, KPI 종합, 다음 해 목표 갱신
```

---

## 임계 발생 시 자동 대응

| 조건 | 자동 대응 |
|---|---|
| Recall < 90% (3일 연속) | 모델 재학습 트리거 |
| Coverage < 0.90 | OTS 알람 임계 보정 + 운영자 통보 |
| OTS 평균 < 60 | XAI 일관성 점검 + SHAP 베이스라인 갱신 |
| Calibration drift score > 0.7 (24시간) | 측정기 점검 자동 신청서 발송 |
| Auto-Execute Ratio < 30% | 시스템 운영 일시 정지 + 본부 알림 |

---

## 외부 인증·심사 일정 권고

- **연 1회 KOLAS / ILAC-MRA 외부 평가** — TMS 측정 추적성 + AI 시스템 ISO 17025 부합 확인
- **분기별 환경부 자체 점검** — 보고 데이터 품질·AI 알람 통계
- **반기별 CBAM EU 보고 검증** — 측정 불확도 마진 적정성

---

*작성: 김용범 — 2026 AX 아이디어 경진대회. ISO/IEC 17025·GUM 기반.*
