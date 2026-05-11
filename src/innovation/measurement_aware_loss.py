"""
Measurement-aware ML — GUM-Weighted Loss for PyTorch
======================================================

핵심 혁신: 기존 ML은 모든 측정 데이터를 동등하게 취급.
본 모듈은 GUM 합성표준불확도(u_c)의 역수 제곱(1/u²)을 가중치로 사용 →
정밀하게 측정된 데이터가 학습에 더 큰 영향을 주도록.

이론적 근거:
  - Maximum Likelihood Estimation under Gaussian noise with heteroscedastic σ_i:
      L = Σ_i (y_i - ŷ_i)² / σ_i²  + const.
  - GUM 합성표준불확도 u_c가 1-sigma 등가 → σ_i = u_c,i 직접 대입.

다른 참가자가 못 하는 이유:
  - GUM 적용에는 ISO 17025/17034 운영 실무 + 측정과학 학위급 이해 필요.
  - 환경공학·데이터사이언스 출신 일반 ML 엔지니어 영역 외.

작성: 김용범 — 2026 AX 아이디어 경진대회
"""

from __future__ import annotations

import numpy as np

# PyTorch는 5/2 환경 구축 시 import. 본 파일은 사전 설계로 수치 검증만.
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    _HAS_TORCH = True
except ImportError:
    _HAS_TORCH = False


# =============================================================================
# 1. NumPy 베이스라인 — PyTorch 없는 환경에서도 검증 가능
# =============================================================================

def gum_weighted_mse_numpy(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    u_c: np.ndarray,
    epsilon: float = 1e-6,
) -> float:
    """
    GUM-weighted Mean Squared Error (numpy).

    L = mean( w_i × (y_i - ŷ_i)² ),  w_i = 1 / (u_c,i² + ε)

    epsilon은 u_c → 0 시 무한 가중치 방지용 (수치 안정성).
    """
    weights = 1.0 / (u_c ** 2 + epsilon)
    weights = weights / weights.mean()  # 평균 1로 정규화 (학습률 호환성)
    sq_err = (y_true - y_pred) ** 2
    return float(np.mean(weights * sq_err))


def measurement_consistency_score(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    u_c: np.ndarray,
    coverage_factor: float = 2.0,
) -> dict:
    """
    측정 일관성 점수 — 예측값이 측정 신뢰구간 [y - U, y + U] 안에 들어가는 비율.

    GUM 관점에서 "예측이 측정과 통계적으로 일치하는가"를 정량화.
    XAI에서 모델 신뢰도 보고 시 사용.
    """
    U = coverage_factor * u_c  # 95% 확장불확도
    within_band = np.abs(y_true - y_pred) <= U
    coverage_rate = float(within_band.mean())

    # 정규화 잔차 (z-score)
    z = (y_pred - y_true) / (u_c + 1e-12)
    return {
        "coverage_rate_95": coverage_rate,
        "expected_coverage_95": 0.95,
        "calibration_error": coverage_rate - 0.95,
        "mean_z_score": float(np.mean(z)),
        "rms_z_score": float(np.sqrt(np.mean(z ** 2))),
    }


# =============================================================================
# 2. PyTorch 버전 — 학습 시 본격 사용
# =============================================================================

if _HAS_TORCH:

    class GUMWeightedMSELoss(nn.Module):
        """PyTorch loss module — GUM-weighted MSE.

        사용 예:
            loss_fn = GUMWeightedMSELoss()
            for x, y, u in loader:    # u = GUM 합성표준불확도
                pred = model(x)
                loss = loss_fn(pred, y, u)
        """

        def __init__(self, epsilon: float = 1e-6, normalize: bool = True):
            super().__init__()
            self.epsilon = epsilon
            self.normalize = normalize

        def forward(
            self,
            pred: torch.Tensor,
            target: torch.Tensor,
            u_c: torch.Tensor,
        ) -> torch.Tensor:
            weights = 1.0 / (u_c ** 2 + self.epsilon)
            if self.normalize:
                weights = weights / weights.mean()
            sq_err = (pred - target) ** 2
            return (weights * sq_err).mean()


    class HeteroscedasticGaussianNLL(nn.Module):
        """
        모델이 평균과 분산을 동시에 예측 → Negative Log Likelihood loss.

        L = 0.5 × log(σ_pred² + u_c²) + 0.5 × (y - μ_pred)² / (σ_pred² + u_c²)

        GUM 측정불확도(u_c)와 모델 인식론적 불확도(σ_pred²)를 합산 →
        예측 신뢰구간 자동 전파. PINN 같은 최신 트렌드와도 호환.
        """

        def forward(
            self,
            mu_pred: torch.Tensor,
            log_var_pred: torch.Tensor,
            target: torch.Tensor,
            u_c: torch.Tensor,
        ) -> torch.Tensor:
            sigma2_total = torch.exp(log_var_pred) + u_c ** 2
            return 0.5 * (torch.log(sigma2_total) + (target - mu_pred) ** 2 / sigma2_total).mean()


    def predict_with_uncertainty_propagation(
        model: nn.Module,
        x: torch.Tensor,
        u_x: torch.Tensor,
        n_mc: int = 100,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Monte Carlo uncertainty propagation:
        입력 x의 측정 불확도 u_x를 출력으로 전파.

        GUM Section 8 — Type B uncertainty propagation을 비선형 모델에 적용.
        """
        model.eval()
        x_samples = x.unsqueeze(0).repeat(n_mc, 1, 1)
        noise = torch.randn_like(x_samples) * u_x.unsqueeze(0)
        x_perturbed = x_samples + noise

        with torch.no_grad():
            preds = torch.stack([model(x_perturbed[i]) for i in range(n_mc)])

        mu = preds.mean(dim=0)
        u_y = preds.std(dim=0)
        return mu, u_y


# =============================================================================
# 3. NumPy 셀프테스트 (사전 검증)
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Measurement-aware Loss — NumPy Self-test")
    print("=" * 60)

    np.random.seed(42)
    n = 100
    y_true = np.random.uniform(20, 80, n)
    # 예측: 정답 + 작은 노이즈
    y_pred = y_true + np.random.normal(0, 1.5, n)
    # 측정 불확도: 측정값에 비례 (5%)
    u_c = y_true * 0.04

    # 비교
    plain_mse = float(np.mean((y_true - y_pred) ** 2))
    gum_loss = gum_weighted_mse_numpy(y_true, y_pred, u_c)

    print(f"\n[Loss 비교]")
    print(f"  Plain MSE         : {plain_mse:.4f}")
    print(f"  GUM-weighted MSE  : {gum_loss:.4f}")
    print(f"  Ratio              : {gum_loss / plain_mse:.4f}")

    # 일관성 점수
    cons = measurement_consistency_score(y_true, y_pred, u_c)
    print(f"\n[측정 일관성 점수]")
    for k, v in cons.items():
        print(f"  {k:30s}: {v:+.4f}")

    print("\n[해석]")
    print("  - coverage_rate_95: 예측이 95% 신뢰구간 안에 들어가는 비율")
    print("  - 0.95에 가까울수록 모델이 측정과 통계적으로 일치")
    print("  - rms_z_score < 1.0이면 모델 신뢰성 양호")

    if _HAS_TORCH:
        print("\n[PyTorch 버전 가용 — 5/2 본격 사용]")
    else:
        print("\n[PyTorch 미설치 — 5/2 환경 구축 시 활성화]")
