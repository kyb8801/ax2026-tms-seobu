# GitHub Public 레포 셋업 가이드

> **목표**: 평가위원이 브라우저에서 코드 + Streamlit 데모를 직접 볼 수 있도록.
> **타이밍**: 5/2 데이터 받기 전 (4/30 직전 주말 추천)

## 1. 레포 생성

```bash
# 로컬에서 git 초기화
cd /path/to/AX2026_TMS_Seobu
git init -b main
git add .
git commit -m "Initial: AX 2026 — Korea Western Power TMS submission"

# README_PUBLIC.md를 README.md로 (내부 README는 README_INTERNAL.md로)
mv README.md README_INTERNAL.md
mv README_PUBLIC.md README.md
git add README*.md
git commit -m "Set public README as default"
```

## 2. GitHub 레포 만들기

1. https://github.com/new → 레포명: `ax2026-tms-seobu`
2. **Public** 선택
3. README/license/.gitignore — 모두 비활성 (이미 있음)
4. Create repository

```bash
git remote add origin https://github.com/kyb8801/ax2026-tms-seobu.git
git push -u origin main
```

## 3. Streamlit Cloud 배포 (무료)

1. https://share.streamlit.io 가입 (GitHub 연동)
2. New app → kyb8801/ax2026-tms-seobu → main → streamlit_app.py
3. Deploy! → URL 확보 (~5분)

배포 URL: `https://kyb8801-ax2026-tms-seobu.streamlit.app`

## 4. README 배지 추가 (선택)

```markdown
[![CI](https://github.com/kyb8801/ax2026-tms-seobu/actions/workflows/ci.yml/badge.svg)](https://github.com/kyb8801/ax2026-tms-seobu/actions)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://kyb8801-ax2026-tms-seobu.streamlit.app)
```

## 5. 발표 자료에 첨부

본 보고서 §1 Executive Summary에:
> **🌐 라이브 데모**: https://kyb8801-ax2026-tms-seobu.streamlit.app
> **📦 소스코드**: https://github.com/kyb8801/ax2026-tms-seobu

## 6. 5/16 마지막 점검

- [ ] CI 배지 녹색 (3개 Python 버전)
- [ ] Streamlit 데모 동작 확인
- [ ] LICENSE / README / 모든 모듈 self-test 통과
- [ ] 데이터 폴더가 `.gitignore`로 제외됐는지 확인 (TMS 원본 비공개)

## 7. 주의사항

- ❗ 한국서부발전 TMS 원본 데이터는 절대 commit 금지 (`.gitignore` 처리됨)
- ❗ API 키 / 토큰은 `.streamlit/secrets.toml` 에 (Public 제외)
- ❗ 분석 결과 시각화는 OK (가공된 비식별 데이터)
