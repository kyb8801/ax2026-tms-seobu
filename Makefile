# Makefile — 2026 AX 한국서부발전 TMS
# 평가위원이 한 줄로 모든 결과를 재현할 수 있도록.
#
# 사용법:
#   make install            # 의존성 설치
#   make test               # 모든 모듈 셀프테스트
#   make e2e                # End-to-end 통합 테스트
#   make demo               # Streamlit 데모 실행
#   make reproduce          # 보고서의 모든 수치 재현
#   make all                # 위 4개 한 번에

.PHONY: install test e2e demo reproduce clean all docker docker-build docker-run

PYTHON := python3
PIP := pip3

# ============================================================================
# 1. 환경 설정
# ============================================================================

install:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "✅ 의존성 설치 완료"

# ============================================================================
# 2. 모듈 셀프테스트 (각 파일 단독 실행)
# ============================================================================

test:
	@echo "=== Module Self-Tests ==="
	$(PYTHON) src/innovation/gum_uncertainty.py
	$(PYTHON) src/innovation/measurement_aware_loss.py
	$(PYTHON) src/innovation/calibration_drift.py
	$(PYTHON) src/innovation/operator_trust.py
	$(PYTHON) src/core/lstm_autoencoder.py
	$(PYTHON) src/core/etl_4source.py
	$(PYTHON) src/core/isolation_forest_gum.py
	$(PYTHON) src/core/shap_xai.py
	$(PYTHON) src/extension/cbam_impact.py
	@echo "✅ 모든 모듈 self-test 통과"

# ============================================================================
# 3. End-to-end 통합 테스트
# ============================================================================

e2e:
	@echo "=== End-to-End Pipeline ==="
	$(PYTHON) tests/test_e2e_pipeline.py
	@echo "✅ E2E 통합 테스트 통과"

# ============================================================================
# 4. Streamlit 데모
# ============================================================================

demo:
	@echo "=== Streamlit Demo ==="
	@echo "브라우저가 자동 열립니다 — http://localhost:8501"
	streamlit run streamlit_app.py

# ============================================================================
# 5. 보고서 수치 전체 재현
# ============================================================================

reproduce: test e2e
	@echo "=== Reproducing Report Numbers ==="
	$(PYTHON) -m src.extension.cbam_impact   # CBAM 비용 시뮬
	@echo ""
	@echo "✅ 보고서의 모든 수치 재현 완료"
	@echo ""
	@echo "참고:"
	@echo "  - GUM SOx 50ppm → u_c = 1.007 ppm"
	@echo "  - Drift score 1.000 → 1일 후 교정 권고"
	@echo "  - PCA F1 = 0.635, IForest F1 = 0.264 (가상 데이터 기준)"
	@echo "  - OTS = 66.4/100 [REVIEW_REQUIRED]"
	@echo "  - CBAM 절감 = 261억원/년 (5호기 적용 시 5배)"

# ============================================================================
# 6. 통합 (전체 일괄)
# ============================================================================

all: install test e2e
	@echo ""
	@echo "═══════════════════════════════════════════════════════════"
	@echo "  ✅ 모든 검증 통과 — 평가위원 시연 가능"
	@echo "  데모 실행: make demo"
	@echo "  데이터 신청: admin/data_request_email.md 참조"
	@echo "═══════════════════════════════════════════════════════════"

# ============================================================================
# 7. 청소
# ============================================================================

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage htmlcov/
	@echo "✅ 캐시 청소 완료"

# ============================================================================
# 8. Docker (격리 환경에서 재현)
# ============================================================================

docker-build:
	docker build -t ax2026-tms-seobu:latest .

docker-run:
	docker run --rm -it -p 8501:8501 ax2026-tms-seobu:latest make demo

docker: docker-build docker-run
