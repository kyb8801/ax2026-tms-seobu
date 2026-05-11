FROM python:3.11-slim

LABEL maintainer="Kim Yong-Beom <kyb8801@gmail.com>"
LABEL description="2026 AX Idea Competition - Korea Western Power TMS"

# 시스템 의존성
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        git \
        curl \
        ca-certificates \
        make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# requirements 먼저 복사 (Docker 캐시)
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY src/ ./src/
COPY tests/ ./tests/
COPY streamlit_app.py ./
COPY Makefile ./
COPY docs/ ./docs/
COPY admin/ ./admin/
COPY README.md LICENSE ./

# Streamlit 포트 노출
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# 기본 실행: 데모
CMD ["make", "demo"]
