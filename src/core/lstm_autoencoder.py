"""
LSTM-Autoencoder for TMS Anomaly Detection (Core)
==================================================

시계열 재구성 오차 기반 이상탐지.
Innovation A (Measurement-aware Loss)와 호환되는 인터페이스 제공.

PyTorch는 5/2 환경 구축 시 import. 본 파일은 NumPy 베이스라인 + 인터페이스 정의.

작성: 김용범 — 2026 AX 아이디어 경진대회
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass

try:
    import torch
    import torch.nn as nn
    _HAS_TORCH = True
except ImportError:
    _HAS_TORCH = False


# =============================================================================
# 1. 모델 설정 dataclass
# =============================================================================

@dataclass
class LSTMAEConfig:
    sequence_length: int = 24       # 24 step (5분 × 24 = 2시간 윈도우)
    input_dim: int = 4              # SOx, NOx, PM, CO
    hidden_dim: int = 64
    num_layers: int = 2
    latent_dim: int = 16
    dropout: float = 0.1


# =============================================================================
# 2. NumPy 베이스라인 — 단순 PCA 기반 재구성 (PyTorch 없을 때 검증용)
# =============================================================================

class PCAAutoencoderBaseline:
    """단순 PCA 재구성 — LSTM-AE 도입 전 베이스라인."""

    def __init__(self, n_components: int = 8):
        self.n_components = n_components
        self.mean_ = None
        self.components_ = None

    def fit(self, X: np.ndarray) -> "PCAAutoencoderBaseline":
        """X shape: (n_samples, n_features) — 평탄화된 시퀀스."""
        self.mean_ = X.mean(axis=0)
        X_centered = X - self.mean_
        # SVD
        _, _, Vt = np.linalg.svd(X_centered, full_matrices=False)
        self.components_ = Vt[: self.n_components]
        return self

    def reconstruct(self, X: np.ndarray) -> np.ndarray:
        X_centered = X - self.mean_
        latent = X_centered @ self.components_.T
        return latent @ self.components_ + self.mean_

    def reconstruction_error(self, X: np.ndarray) -> np.ndarray:
        recon = self.reconstruct(X)
        return np.sqrt(np.mean((X - recon) ** 2, axis=1))


# =============================================================================
# 3. PyTorch LSTM-Autoencoder (5/2 활성)
# =============================================================================

if _HAS_TORCH:

    class LSTMAutoencoder(nn.Module):
        def __init__(self, cfg: LSTMAEConfig):
            super().__init__()
            self.cfg = cfg
            # Encoder: input → latent
            self.encoder = nn.LSTM(
                input_size=cfg.input_dim,
                hidden_size=cfg.hidden_dim,
                num_layers=cfg.num_layers,
                batch_first=True,
                dropout=cfg.dropout if cfg.num_layers > 1 else 0,
            )
            self.encoder_fc = nn.Linear(cfg.hidden_dim, cfg.latent_dim)
            # Decoder: latent → output
            self.decoder_fc = nn.Linear(cfg.latent_dim, cfg.hidden_dim)
            self.decoder = nn.LSTM(
                input_size=cfg.hidden_dim,
                hidden_size=cfg.hidden_dim,
                num_layers=cfg.num_layers,
                batch_first=True,
                dropout=cfg.dropout if cfg.num_layers > 1 else 0,
            )
            self.output_fc = nn.Linear(cfg.hidden_dim, cfg.input_dim)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            # x: (batch, seq, input_dim)
            _, (h, _) = self.encoder(x)
            latent = self.encoder_fc(h[-1])              # (batch, latent_dim)
            decoded = self.decoder_fc(latent)            # (batch, hidden_dim)
            decoded = decoded.unsqueeze(1).repeat(1, self.cfg.sequence_length, 1)
            decoded, _ = self.decoder(decoded)
            recon = self.output_fc(decoded)
            return recon

        def reconstruction_error(self, x: torch.Tensor) -> torch.Tensor:
            recon = self.forward(x)
            return ((x - recon) ** 2).mean(dim=(1, 2))


    class GUMWeightedReconstructionLoss(nn.Module):
        """
        Innovation A 통합용 — 재구성 손실에 GUM 가중치 적용.
        Measurement-aware Loss와 동일한 철학.
        """
        def forward(
            self,
            x: torch.Tensor,
            x_recon: torch.Tensor,
            u_c: torch.Tensor,
        ) -> torch.Tensor:
            weights = 1.0 / (u_c ** 2 + 1e-6)
            weights = weights / weights.mean()
            sq_err = (x - x_recon) ** 2
            return (weights * sq_err).mean()


# =============================================================================
# 4. 셀프테스트
# =============================================================================

def make_synthetic_tms(n_samples: int = 1000, n_features: int = 4, anomaly_ratio: float = 0.05):
    """가상 TMS 데이터 생성 — 5/2 데이터 도착 전 모의."""
    np.random.seed(42)
    base = np.random.normal(50, 5, (n_samples, n_features))
    # 이상 패턴 주입
    n_anomaly = int(n_samples * anomaly_ratio)
    anomaly_idx = np.random.choice(n_samples, n_anomaly, replace=False)
    base[anomaly_idx] += np.random.uniform(20, 50, (n_anomaly, n_features))
    labels = np.zeros(n_samples, dtype=int)
    labels[anomaly_idx] = 1
    return base, labels


if __name__ == "__main__":
    print("=" * 60)
    print("LSTM-Autoencoder Core — Self-test (PCA baseline)")
    print("=" * 60)

    X, labels = make_synthetic_tms(1000, 4, 0.05)
    print(f"  데이터 shape : {X.shape}, 이상 비율: {labels.mean()*100:.1f}%")

    # PCA 베이스라인 fit
    pca_ae = PCAAutoencoderBaseline(n_components=2)
    pca_ae.fit(X[labels == 0])  # 정상 데이터로만 학습

    errors = pca_ae.reconstruction_error(X)
    threshold = np.percentile(errors[labels == 0], 95)
    predictions = (errors > threshold).astype(int)

    tp = int(((predictions == 1) & (labels == 1)).sum())
    fp = int(((predictions == 1) & (labels == 0)).sum())
    fn = int(((predictions == 0) & (labels == 1)).sum())
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-9)

    print(f"\n[PCA 베이스라인 결과]")
    print(f"  Threshold (95% normal) : {threshold:.4f}")
    print(f"  Precision = {precision:.3f}, Recall = {recall:.3f}, F1 = {f1:.3f}")
    print(f"  (LSTM-AE 도입 시 일반적으로 Recall +10-20%p 기대)")

    if _HAS_TORCH:
        print("\n[PyTorch LSTM-AE 가용 — 5/2 본격 학습]")
    else:
        print("\n[PyTorch 미설치 — 5/2 환경 구축 시 LSTM-AE 활성화]")
