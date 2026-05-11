# 시연 영상 3분 — 스크립트 + 자막 (한·영)

> **목적**: 1차 서류 심사 첨부 + 발표심사 백업.
> **분량**: 정확히 3:00 (180초)
> **제작 도구**: OBS Studio (화면 녹화) + Audacity (음성)
> **업로드**: YouTube Public + 보고서·발표 자료에 URL 첨부
> **언어**: 한국어 음성 + 영어 자막 (글로벌 어필)

---

## 영상 구조 (총 180초)

```
0:00 ~ 0:30  [도입] 문제 정의 + 본 연구자 소개  (30초)
0:30 ~ 2:00  [솔루션 시연] 3개 Innovation 시연   (90초)
2:00 ~ 2:45  [정량 결과] 5개 발전소 + CBAM       (45초)
2:45 ~ 3:00  [마무리] 한 줄 + 콜투액션            (15초)
```

---

## Section 1 — 도입 (0:00~0:30, 30초)

### 화면
- 0:00~0:10: 한국서부발전 발전소 항공사진 (공개 자료)
- 0:10~0:20: TMS 측정기 클로즈업 + 그래프 (Streamlit 화면)
- 0:20~0:30: 본 연구자 프로필 슬라이드 (ISO 18516 강조)

### 한국어 음성
> "한국서부발전 5개 발전소의 굴뚝 원격감시체계, TMS는 매 5분마다 대기오염물질을 측정합니다. 그러나 측정 자체의 신뢰도가 ML 모델에 반영되지 않고, 정기 교정 사이의 드리프트는 보이지 않습니다. ISO 18516 국제표준 1저자 기여자가 직접 설계한 측정과학 기반 AI를 소개합니다."

### English Subtitle
> "Korea Western Power's TMS measures air pollutants every 5 minutes across 5 power plants. But sensor uncertainty doesn't reach the ML model, and calibration drift between scheduled inspections stays hidden. As a contributing author of ISO 18516, I built measurement-science-grounded AI to fix this."

---

## Section 2 — 솔루션 시연 (0:30~2:00, 90초)

### 2-A. Innovation A: Measurement-aware ML (30초)

**화면**: Streamlit 데모 — 사이드바에서 SOx 50ppm, 교정 30일 설정 → GUM 불확도 자동 계산 → 6성분 차트 등장

**한국어 음성**:
> "Innovation A — Measurement-aware ML. SOx 50ppm 측정에 ISO/IEC Guide 98-3, GUM의 6개 불확도 성분을 적용하면 합성표준불확도 1.0ppm이 자동 산출됩니다. 이 신뢰도가 ML loss의 가중치(1/u²)로 직접 들어갑니다. 정밀한 측정이 더 큰 학습 영향을 가집니다."

**English Subtitle**:
> "Innovation A — Measurement-aware ML. For a SOx reading of 50 ppm, applying GUM's six uncertainty components yields a combined standard uncertainty of 1.0 ppm automatically. This becomes the inverse-variance weight in the ML loss — precise measurements get more learning weight."

### 2-B. Innovation B: Calibration Drift (30초)

**화면**: Streamlit 데모 — 가상 드리프트 폭 3 ppm 설정 → TMS vs 에어코리아 시계열 → drift_score 0.857, 12일 후 교정 권고

**한국어 음성**:
> "Innovation B — Cross-Source Calibration Drift Detection. 발전소 TMS와 인근 에어코리아 측정소를 거리, 고도, 풍속으로 보정해 자동 비교합니다. 드리프트 점수 0.857에서 Page-Hinkley test가 12일 후 교정 권고로 응답합니다. 정기 90일 교정 대비 정확도 우선 시점을 데이터가 결정합니다."

**English Subtitle**:
> "Innovation B — Cross-Source Calibration Drift Detection. The plant's TMS is auto-compared with nearby AirKorea stations using distance, elevation, and wind corrections. A Page-Hinkley test responds in 12 days at drift score 0.857. Data, not the calendar, decides when calibration matters."

### 2-C. Innovation F: Operator Trust (30초)

**화면**: Streamlit 데모 — 모델 예측 표준편차 슬라이더 변경 → OTS 점수 변화 → P1/P2/P3 등급 변화

**한국어 음성**:
> "Innovation F — Operator Trust Calibration. 측정·모델·XAI·이력 4개 컴포넌트를 결합한 0~100 점수입니다. 80 이상이면 자동 실행, 60~80은 운영자 검토, 40~60은 승인 필요. 발전사 운영자의 책임 범위가 명확해지고, 환경부 감독도 정량 지표로 가능해집니다."

**English Subtitle**:
> "Innovation F — Operator Trust Calibration. A 0-100 score combining measurement, model, XAI, and history. 80+ auto-executes, 60-80 needs review, 40-60 needs approval. Operator accountability becomes quantified, and so does ministry supervision."

---

## Section 3 — 정량 결과 (2:00~2:45, 45초)

### 화면
- 2:00~2:25: 5개 발전소 시뮬레이션 결과 표 (Streamlit 또는 슬라이드)
- 2:25~2:45: CBAM 영향 차트 (Streamlit 동적 — €60→€150 슬라이더)

### 한국어 음성
> "한국서부발전 5개 발전소 23기에 가상 적용 시 연 CBAM 절감 2,637억, 정기 교정 절감 14.7억. EU CBAM이 €120 도달하면 호기당 절감 522억까지 확장됩니다. 측정 정확도 1퍼센트포인트 개선이 호기당 연 87억 단위 효과를 만듭니다."

### English Subtitle
> "Across 23 units in 5 plants: ₩263.7B in annual CBAM savings, ₩1.47B in calibration cost savings. At a CBAM price of €120/t, savings scale to ₩52.2B per unit. A single percentage point improvement in measurement accuracy moves the needle by ₩8.7B per unit annually."

---

## Section 4 — 마무리 (2:45~3:00, 15초)

### 화면
- 텍스트 오버레이: "측정 신뢰도와 예측 신뢰도를 분리하지 않는다"
- URL 표시: github.com/kyb8801/ax2026-tms-seobu
- streamlit URL: kyb8801-ax2026-tms-seobu.streamlit.app

### 한국어 음성
> "측정 신뢰도와 예측 신뢰도를 분리하지 않는다. 코드와 데모는 깃허브에 공개되어 있습니다. 감사합니다."

### English Subtitle
> "Do not separate measurement trust from prediction trust. Code and demo are public on GitHub. Thank you."

---

## 제작 절차 (5/16~5/17, 1.5일)

### 5/16 오전 — 음성 녹음 (1시간)
- Audacity로 4개 섹션 음성 녹음
- 노이즈 제거, 볼륨 정규화
- 4개 mp3 파일

### 5/16 오후 — 화면 녹화 (2시간)
- OBS Studio로 Streamlit 데모 녹화
- 4개 섹션별 컷 분리
- 1080p, 30fps

### 5/17 오전 — 편집 (3시간)
- DaVinci Resolve (무료) 또는 iMovie 사용
- 음성 + 화면 정확히 맞추기
- 영어 자막 SRT 파일 import
- 트랜지션·텍스트 오버레이 추가

### 5/17 오후 — 업로드 + 첨부 (1시간)
- YouTube Public 업로드
- 영상 설명에 GitHub·Streamlit URL
- 보고서 §1 Executive Summary에 URL 첨부
- 발표 슬라이드 #1·#10에도 URL 추가

---

## 자막 파일 (subtitles_en.srt — 영어 자막)

```
1
00:00:00,000 --> 00:00:30,000
Korea Western Power's TMS measures air pollutants every 5 minutes across 5 power plants. But sensor uncertainty doesn't reach the ML model, and calibration drift between scheduled inspections stays hidden. As a contributing author of ISO 18516, I built measurement-science-grounded AI to fix this.

2
00:00:30,000 --> 00:01:00,000
Innovation A — Measurement-aware ML. For a SOx reading of 50 ppm, applying GUM's six uncertainty components yields a combined standard uncertainty of 1.0 ppm automatically. This becomes the inverse-variance weight in the ML loss — precise measurements get more learning weight.

3
00:01:00,000 --> 00:01:30,000
Innovation B — Cross-Source Calibration Drift Detection. The plant's TMS is auto-compared with nearby AirKorea stations using distance, elevation, and wind corrections. A Page-Hinkley test responds in 12 days at drift score 0.857. Data, not the calendar, decides when calibration matters.

4
00:01:30,000 --> 00:02:00,000
Innovation F — Operator Trust Calibration. A 0-100 score combining measurement, model, XAI, and history. 80+ auto-executes, 60-80 needs review, 40-60 needs approval. Operator accountability becomes quantified, and so does ministry supervision.

5
00:02:00,000 --> 00:02:45,000
Across 23 units in 5 plants: ₩263.7B in annual CBAM savings, ₩1.47B in calibration cost savings. At a CBAM price of €120/t, savings scale to ₩52.2B per unit. A single percentage point improvement in measurement accuracy moves the needle by ₩8.7B per unit annually.

6
00:02:45,000 --> 00:03:00,000
Do not separate measurement trust from prediction trust. Code and demo are public on GitHub. Thank you.
```

---

## 한국어 자막 (subtitles_ko.srt)

```
1
00:00:00,000 --> 00:00:30,000
한국서부발전 5개 발전소의 굴뚝 원격감시체계, TMS는 매 5분마다 대기오염물질을 측정합니다. 그러나 측정 자체의 신뢰도가 ML 모델에 반영되지 않고, 정기 교정 사이의 드리프트는 보이지 않습니다. ISO 18516 국제표준 1저자 기여자가 직접 설계한 측정과학 기반 AI를 소개합니다.

2
00:00:30,000 --> 00:01:00,000
Innovation A — Measurement-aware ML. SOx 50ppm 측정에 ISO/IEC Guide 98-3, GUM의 6개 불확도 성분을 적용하면 합성표준불확도 1.0ppm이 자동 산출됩니다. 이 신뢰도가 ML loss의 가중치로 직접 들어갑니다. 정밀한 측정이 더 큰 학습 영향을 가집니다.

3
00:01:00,000 --> 00:01:30,000
Innovation B — Cross-Source Calibration Drift Detection. 발전소 TMS와 인근 에어코리아 측정소를 거리, 고도, 풍속으로 보정해 자동 비교합니다. 드리프트 점수 0.857에서 Page-Hinkley test가 12일 후 교정 권고로 응답합니다. 정기 90일 교정 대비 정확도 우선 시점을 데이터가 결정합니다.

4
00:01:30,000 --> 00:02:00,000
Innovation F — Operator Trust Calibration. 측정·모델·XAI·이력 4개 컴포넌트를 결합한 0~100 점수입니다. 80 이상이면 자동 실행, 60~80은 운영자 검토, 40~60은 승인 필요. 발전사 운영자의 책임 범위가 명확해지고, 환경부 감독도 정량 지표로 가능해집니다.

5
00:02:00,000 --> 00:02:45,000
한국서부발전 5개 발전소 23기에 가상 적용 시 연 CBAM 절감 2,637억, 정기 교정 절감 14.7억. EU CBAM이 €120 도달하면 호기당 절감 522억까지 확장됩니다. 측정 정확도 1퍼센트포인트 개선이 호기당 연 87억 단위 효과를 만듭니다.

6
00:02:45,000 --> 00:03:00,000
측정 신뢰도와 예측 신뢰도를 분리하지 않는다. 코드와 데모는 깃허브에 공개되어 있습니다. 감사합니다.
```

---

## 영상 메타데이터 (YouTube 업로드용)

**제목**: Measurement-aware AI for Power Plant TMS — 2026 AX 아이디어 경진대회 (Korea Western Power)

**설명**:
```
2026 AX Idea Competition — Designated Analysis Track
Korea Western Power TMS Project

Author: Kim Yong-Beom (Ph.D., Measurement Science)
ISO 18516:2019 1st-author contribution

This 3-minute demo shows three innovations that no other contestant
will build:

1. Measurement-aware ML — GUM uncertainty integrated into PyTorch loss
2. Cross-Source Calibration Drift Detection — TMS ↔ AirKorea auto-comparison
3. Operator Trust Calibration — 0-100 trust score with P1/P2/P3 alarm tiering

Plus EU CBAM 2026 trade impact simulation showing per-unit annual savings
of ₩52.2 billion at €120/t.

📦 GitHub: https://github.com/kyb8801/ax2026-tms-seobu
🌐 Live demo: https://kyb8801-ax2026-tms-seobu.streamlit.app
📚 ISO/IEC Guide 98-3 (GUM) · ISO 17025 · ISO 17034 · ISO 18516
```

**태그**: 2026 AX, 한국서부발전, TMS, GUM, ISO 17025, CBAM, 측정과학, environmental AI, climate-energy, KOWEPO

---

*작성: 김용범 — 2026 AX 아이디어 경진대회. 5/16~5/17 OBS Studio + DaVinci Resolve 제작.*
