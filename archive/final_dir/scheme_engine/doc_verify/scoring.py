from __future__ import annotations

from .models import DocumentStatus, FraudRiskLevel, LayerResult
from .settings import ScoreWeights


def compute_authenticity_score(
    govt_issuer: LayerResult,
    authority_check: LayerResult,
    format_check: LayerResult,
    api_check: LayerResult,
    fraud_score: float,
    weights: ScoreWeights,
) -> float:
    score_0_1 = (
        weights.govt_issuer * govt_issuer.score
        + weights.authority_check * authority_check.score
        + weights.format_check * format_check.score
        + weights.api_check * api_check.score
        + weights.fraud_inverse * (1 - fraud_score)
    )
    return round(max(0.0, min(1.0, score_0_1)) * 100, 2)


def resolve_status(
    authenticity_score: float,
    fraud_risk: FraudRiskLevel,
    hard_fail: bool,
) -> DocumentStatus:
    if hard_fail or authenticity_score < 60:
        return DocumentStatus.INVALID
    if fraud_risk == FraudRiskLevel.HIGH or authenticity_score < 80:
        return DocumentStatus.SUSPICIOUS
    return DocumentStatus.VALID

