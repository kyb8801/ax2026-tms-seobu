# AX 2026 분석-지정 부문 제출 가이드 (참가신청서 + 5/18 패키지)

> **마감**: 2026-05-18 (월) 23:59
> **제출**: konetic.or.kr/ecothon → 온라인 접수
> **부문**: 분석-지정 (한국서부발전)

---

## 📋 제출 5종 체크리스트

| # | 서류 | 형식 | 본 솔루션 위치 | 상태 |
|---|---|---|---|---|
| 1 | **참가 신청서** | HWPX | konetic.or.kr 다운로드 후 작성 | ⬜ 양식 다운로드 필요 |
| 2 | **분석 보고서** | HWPX/PDF | `docs/report_main_v1.md` → PDF 변환 | 🟡 v1 완성, v2 5/17 |
| 3 | **분석 코드** | Python .zip | `src/` 폴더 + README + requirements.txt | ✅ 완성 |
| 4 | **근거 데이터** | CSV .zip | 5/2 실데이터 도착 후 | ⬜ 5/2 후 |
| 5 | **결과 데이터셋·시각화** | CSV·PNG·HTML | Streamlit 대시보드 캡처 + 결과 표 | ⬜ 5/15 후 |

---

## Step 1 — 참가신청서 양식 다운로드 (즉시)

1. https://konetic.or.kr/ecothon/content/guide.do 접속
2. **공모요강** 페이지 하단의 **신청 서류** 섹션 확인
3. **자유분석·지정 분석(12개 과제) : 참가 신청서, 분석 보고서** 양식 다운로드
4. ⚠️ **iOS에서는 다운로드 불가** → PC 또는 Android 사용
5. 다운로드한 HWPX 파일 → `admin/` 폴더에 저장

**대안**: 운영사무국 메일 요청
- ✉ 2026axidea@gmail.com
- ☎ 043-254-7942

---

## Step 2 — 참가신청서 작성 (4/27 ~ 5/2)

### 작성 항목 (예상)

| 항목 | 내용 |
|---|---|
| 부문 | 분석-지정 |
| 지정과제 | 한국서부발전 — AI 기반 발전소 대기오염물질 배출 예측 및 최적 운전조건 도출 |
| 참가 형태 | 개인 |
| 성명 | 김용범 |
| 생년월일 | (개인정보) |
| 연락처 | (개인정보) |
| 이메일 | kyb8801@gmail.com |
| 주소 | 경기도 수원시 |
| 학력·경력 | Ph.D. 측정과학 / KOLAS 시험기관 (킴스레퍼런스) 재직 / ISO 18516 1저자 |
| 작품명 | Measurement-aware AI for Korea Western Power TMS |
| 작품 요약 (200자) | (아래 템플릿 참조) |

### 작품 요약 템플릿 (200자 이내)

> ISO/IEC Guide 98-3 (GUM) 측정 불확도를 ML 모델·이상탐지·운영자 의사결정에 통합한 환경 측정 AI. ISO 18516 1저자 기여자가 설계. 한국서부발전 5개 발전소 23호기 적용 시 연 2,637억원 EU CBAM 비용 절감 추정. MetroAI v0.5.0 (8,500 LOC) 실동작 + GitHub Open Source.

---

## Step 3 — 분석 보고서 PDF 변환 (5/15 ~ 5/17)

### 옵션 A — Markdown → HWPX (한컴)
1. report_main_v1.md (또는 v2) → HWPX 변환
2. 한컴 오피스에서 양식 적용
3. 표·그림 정렬 점검
4. PDF 출력

### 옵션 B — Markdown → PDF 직접 (권장)
1. Pandoc 사용:
   ```bash
   pandoc docs/report_main_v1.md \
     --pdf-engine=xelatex \
     -V CJKmainfont="Noto Sans KR" \
     -V mainfont="Noto Sans KR" \
     --toc \
     -o submission/02_분석보고서.pdf
   ```
2. 또는 VS Code "Markdown PDF" 익스텐션
3. 또는 GitHub README 렌더링 → 브라우저 PDF 저장

### 옵션 C — Streamlit으로 동적 렌더링
- Streamlit Cloud 배포 후 URL을 보고서 별첨에 첨부
- PDF는 압축 버전만 제출

---

## Step 4 — 분석 코드 .zip 패키지 (5/16)

```bash
cd /path/to/AX2026_TMS_Seobu

# 캐시 청소
make clean

# 제출용 zip 생성 (data 폴더 제외)
zip -r submission/03_분석코드.zip \
  src/ tests/ \
  README.md README_PUBLIC.md LICENSE \
  requirements.txt Makefile Dockerfile \
  streamlit_app.py \
  -x "*.pyc" "*__pycache__*" "data/raw/*" ".git/*"
```

확인:
- README.md (한국어 + 영어)
- requirements.txt (Python 3.10+ 호환)
- Makefile (`make install`, `make test`, `make reproduce`)
- 셀프테스트 9개 모두 통과 가능
- 시드 고정 (`np.random.seed(42)`, `torch.manual_seed(42)`)

---

## Step 5 — 근거 데이터 .zip (5/16, 실데이터 도착 후)

```
04_근거데이터/
├── tms_processed.csv          # 한국서부발전 TMS 가공
├── airkorea_sample.csv         # 인근 측정소
├── kma_asos_sample.csv         # 기상청 ASOS
├── kpx_epsis_sample.csv        # 전력거래소
├── README.md                   # 데이터 출처 명시
└── data_dictionary.md          # 변수 설명
```

⚠️ **출처 명시 필수**:
- TMS: 한국서부발전 (AX 경진대회 제공)
- AirKorea: airkorea.or.kr (환경부 한국환경공단)
- KMA: data.kma.go.kr (기상청 공공데이터)
- KPX: epsis.kpx.or.kr (한국전력거래소)

---

## Step 6 — 결과 데이터셋·시각화 (5/17)

```
05_결과데이터셋_시각화/
├── results_table.csv           # 5호기 적용 결과 표
├── alarm_predictions.csv       # 가상/실제 알람 예측 결과
├── dashboard_screenshot_1.png  # Streamlit GUM 패널
├── dashboard_screenshot_2.png  # Drift Detection 패널
├── dashboard_screenshot_3.png  # Operator Trust 패널
├── dashboard_screenshot_4.png  # CBAM 시뮬레이션
├── shap_plot.html              # 인터랙티브 SHAP 시각화
├── plotly_dashboard.html       # 종합 대시보드
└── README.md
```

---

## Step 7 — 추가 첨부 (차별화 가산)

| 파일 | 위치 | 효과 |
|---|---|---|
| GUM 1쪽 인포그래픽 | docs/gum_infographic.md → PDF | 평가위원 직관 이해 |
| ISO 18516 1저자 증명 | docs/iso_18516_attachment.md → PDF | 학계 신뢰 |
| 국제 비교 표 | docs/international_comparison.md → PDF | 글로벌 위치 |
| 운영 매뉴얼·ROI | docs/operations_manual.md → PDF | 정책 실현성 |
| KPI 정의서 | docs/kpi_definition.md → PDF | "운영 가능한가" 답변 |
| 정책 제언 | docs/policy_proposal.md → PDF | 환경부 채택 가능성 |
| GitHub URL | github.com/kyb8801/ax2026-tms-seobu | 코드 검증 |
| Streamlit URL | kyb8801-ax2026-tms-seobu.streamlit.app | 라이브 시연 |
| YouTube URL | (시연 영상 3분, 한·영 자막) | 1차 서류 가산 |

---

## 📅 5/17 ~ 5/18 최종 제출 체크리스트

### 5/17 오후
- [ ] report_main_v2.md 완성 (실데이터 수치 반영)
- [ ] PDF 변환 (한국어 + 영어 옵션)
- [ ] Streamlit Cloud 배포 + URL 확보
- [ ] GitHub Public 변환 + 최종 commit
- [ ] YouTube 영상 업로드 + URL
- [ ] 모든 첨부 PDF 변환

### 5/17 저녁
- [ ] 5개 .zip 파일 최종 검토
- [ ] 백업: 외장하드 + 클라우드 (Google Drive)
- [ ] 알람: 5/18 09:00

### 5/18 오전 09:00 ~ 12:00
- [ ] konetic.or.kr/ecothon → 온라인 접수
- [ ] 5개 서류 업로드
- [ ] 추가 첨부 URL 입력란
- [ ] 제출 확인 메일 수신
- [ ] 접수번호 보관

⚠️ **5/18 마감 직전 제출 회피** — 시스템 폭주 가능성

---

## 위험 분석

| 위험 | 확률 | 완화 |
|---|---|---|
| 양식 다운로드 실패 (iOS) | 30% | PC/Android 사용 |
| HWPX 변환 시 표 깨짐 | 40% | PDF 직접 변환 |
| 코드 .zip 사이즈 초과 (보통 100MB) | 20% | data/ 폴더 제외 + git LFS |
| 실데이터 5/2 지연 | 30% | 가상 v1 우선 + v2 마이너 갱신 |
| 5/18 시스템 폭주 | 50% | 5/18 오전 제출 |

---

## 🎯 즉시 액션

오늘~내일 (4/27 ~ 4/28):
- [ ] konetic.or.kr/ecothon 사이트 접속 → 양식 다운로드
- [ ] 양식 받으면 본 폴더 admin/forms/ 저장
- [ ] 참가신청서 항목 미리 채우기 (보고서 v2 시 최종 확정)

5/2 (D-Day):
- [ ] 한국서부발전 데이터 신청 메일 발송
- [ ] 외부 3-source (AirKorea·KMA·KPX) API 키 확보
- [ ] ETL 가동

---

*작성: 2026-04-27. v1.*
