# Streamlit Cloud 배포 가이드 (5/16 ~ 5/17)

> **목적**: 평가위원이 브라우저에서 직접 시연 가능한 라이브 URL 확보
> **무료**: Streamlit Community Cloud (Public 레포 기반)
> **소요 시간**: 30분 (첫 배포)
> **타이밍**: 5/16 (보고서 v2 완성 후) ~ 5/17

---

## 사전 준비 체크리스트

- [x] `requirements.txt` 완비
- [x] `streamlit_app.py` 완비 (4-탭 데모: GUM·Drift·OTS·CBAM)
- [x] 셀프테스트 9개 모두 통과
- [ ] GitHub Public 레포 변환 (4/30 권장)
- [ ] Streamlit Community Cloud 가입

---

## Step 1 — GitHub Public 레포 생성 (10분)

### 1.1 GitHub 계정 준비
- 계정: kyb8801 (사용자 기존)
- 레포명: `ax2026-tms-seobu`

### 1.2 로컬에서 git 초기화
```bash
cd /path/to/MetroAI/AX2026_TMS_Seobu

# README 정리 (Public용 + Internal용 분리)
mv README.md README_INTERNAL.md
mv README_PUBLIC.md README.md

# git 초기화
git init -b main
git add .gitignore LICENSE README.md README_INTERNAL.md \
  requirements.txt Makefile Dockerfile streamlit_app.py \
  src/ tests/ docs/ admin/ .github/

git commit -m "Initial: 2026 AX 한국서부발전 TMS submission

- 9 Python modules (Innovation A·B·F + Core 4 + Extension 2)
- Streamlit demo (4 tabs)
- E2E integration test
- Documentation (report + KPI + policy + ISO 18516 attachment)
- ISO 18516:2019 contributing author"
```

### 1.3 GitHub 레포 생성 + push
```bash
# https://github.com/new 에서 ax2026-tms-seobu 레포 생성 (Public, 비어있는 상태)
git remote add origin https://github.com/kyb8801/ax2026-tms-seobu.git
git branch -M main
git push -u origin main
```

### 1.4 GitHub Actions CI 자동 가동 확인
- 레포 → Actions 탭 → CI 실행 확인 (3분 소요)
- 녹색 체크 ✓ → 셀프테스트 모두 통과 증명

---

## Step 2 — Streamlit Community Cloud 가입 + 배포 (15분)

### 2.1 Streamlit Cloud 가입
1. https://share.streamlit.io 접속
2. **Sign up with GitHub** → kyb8801 계정 연동
3. Workspace permissions 승인

### 2.2 New App 배포
1. Streamlit Cloud 대시보드 → **New app** 클릭
2. 설정:
   ```
   Repository:      kyb8801/ax2026-tms-seobu
   Branch:          main
   Main file path:  streamlit_app.py
   App URL:         kyb8801-ax2026-tms-seobu  (subdomain 자유)
   ```
3. **Advanced settings**:
   ```
   Python version: 3.11
   Secrets:        (비워둠 — 본 앱은 secrets 불요)
   ```
4. **Deploy!** 클릭 → 5~10분 빌드 대기

### 2.3 빌드 로그 확인
- 의존성 설치 로그 모니터링
- 에러 발생 시 `requirements.txt` 핀 버전 확인

### 2.4 배포 완료 URL
```
https://kyb8801-ax2026-tms-seobu.streamlit.app
```

---

## Step 3 — 배포 검증 (5분)

### 3.1 기능 테스트
- [ ] GUM 패널: SOx 50ppm 입력 → u_c=1.007 자동 계산
- [ ] Drift 패널: 가상 드리프트 폭 변경 → drift_score 갱신
- [ ] OTS 패널: 모델 분산 슬라이더 변경 → 등급 변화
- [ ] CBAM 패널: 가격·정확도 변경 → 절감액 갱신

### 3.2 모바일 호환성
- 평가위원이 폰으로 볼 가능성 → 반응형 OK 확인

### 3.3 로딩 시간
- 첫 로딩 5초 이내 (Streamlit Cloud 무료 티어 한계)

---

## Step 4 — 보고서·발표 자료에 URL 첨부 (5분)

### 4.1 보고서 본문 (`report_main_v1.md`)
이미 다음 위치에 URL 명시됨:
- Executive Summary 끝부분 — "리소스" 섹션
- §10 결론 직후 — "코드 가용성" 섹션

### 4.2 발표 슬라이드 (`presentation_15slides.md`)
- 슬라이드 10: "Live Demo" 페이지 URL 추가
- 슬라이드 15: "마무리" 페이지 URL 추가

### 4.3 시연 영상 (`demo_video_script.md`)
- 영상 마지막 5초: URL 화면 텍스트
- YouTube 영상 설명에 URL 추가

### 4.4 GitHub README
이미 README_PUBLIC.md에 [![Streamlit App]] 배지 명시됨.

---

## Step 5 — Streamlit Cloud 한계 + 대비책

### 한계
| 한계 | 영향 | 대비책 |
|---|---|---|
| 1GB RAM (무료 티어) | LSTM-AE 학습 어려움 | 사전 학습 모델 .pkl 로드 |
| 빌드 5분+ | 첫 배포 대기 | 5/16에 미리 배포 |
| 동시 사용자 ~수십 명 | 평가위원 동시 접속 시 느림 | OK (보통 1~2명) |
| 데이터 영속성 X | 세션 종료 시 사라짐 | 가상 데이터만 사용 |
| 외부 데이터 다운 | Streamlit Cloud → API 호출 가능 | 미리 .csv 로드 |

### 대안
- **Hugging Face Spaces** (Gradio/Streamlit) — 무료 + GPU 옵션 있음
- **Replit Deploy** — 간편 배포
- **Vercel** — Next.js 기반 (변경 부담 큼)
- **로컬 시연 영상 백업** — 만일 Streamlit Cloud 다운 시

---

## Step 6 — 최종 점검 (5/17 저녁)

### URL 살아 있는지 마지막 점검
- [ ] https://kyb8801-ax2026-tms-seobu.streamlit.app 접속 OK
- [ ] 4 탭 모두 정상 작동
- [ ] 로딩 5초 이내
- [ ] 모바일 호환

### 백업 자료
- [ ] Streamlit GIF 녹화 (1분, OBS) → 보고서·발표에 첨부
- [ ] 로컬 실행 명령어 문서화 (`streamlit run streamlit_app.py`)

---

## 🚨 만약 배포 실패 시

### Plan B: 로컬 실행 가이드
보고서·발표에 다음 문구 추가:
> "본 데모는 GitHub repo (https://github.com/kyb8801/ax2026-tms-seobu)에서 `make demo` 한 줄로 로컬 실행 가능합니다. 또는 평가위원 요청 시 본 연구자가 1:1 화면 공유 시연 가능."

### Plan C: GIF 영상으로 대체
- OBS Studio로 데모 화면 녹화 (1분)
- GIF 변환 (giphy.com 또는 ffmpeg)
- 보고서·발표·GitHub README에 첨부

---

## 비용 정리

| 항목 | 비용 |
|---|---|
| GitHub Public 레포 | **$0** |
| Streamlit Community Cloud | **$0** (무료 티어 충분) |
| 도메인 | **$0** (subdomain 무료) |
| **총 비용** | **0원** |

---

## 🎯 즉시 액션 우선순위

```
[지금~4/30]
1. (사용자) GitHub 레포 생성 + 첫 push (10분)
2. (사용자) Streamlit Cloud 가입 (5분)

[5/2~5/16]
3. AX 메인 작업 진행

[5/16 저녁]
4. (사용자) Streamlit Cloud 배포 클릭 (5분 + 빌드 10분)
5. (사용자) 4 탭 기능 테스트 (5분)
6. (사용자) URL을 보고서·발표·영상에 삽입

[5/17 저녁]
7. 최종 URL 살아 있는지 마지막 점검
```

---

## 명령어 요약 (사용자가 PC에서 실행)

```bash
# 1. git 초기화 (1회)
cd /path/to/AX2026_TMS_Seobu
mv README.md README_INTERNAL.md
mv README_PUBLIC.md README.md
git init -b main
git add .
git commit -m "Initial: AX 2026 한국서부발전 TMS"

# 2. GitHub 연결 (https://github.com/new 에서 레포 생성 후)
git remote add origin https://github.com/kyb8801/ax2026-tms-seobu.git
git push -u origin main

# 3. 변경사항 commit (보고서 v2 작업할 때)
git add docs/report_main_v2.md
git commit -m "Update: report v2 with real KOWEPO data"
git push

# 4. Streamlit 자동 재배포 (push마다 자동 트리거)
```

---

*작성: 2026-04-27. 5/16 배포 예정.*
