from __future__ import annotations

import re
from collections import Counter
from datetime import UTC, datetime

from .models import CheckState, ExtractedDocumentData, FraudResult, FraudRiskLevel, ValidationCheck


class FraudDetector:
    def evaluate(self, data: ExtractedDocumentData) -> FraudResult:
        signals: list[ValidationCheck] = []
        attributions: dict[str, float] = {}

        font_inconsistency = self._font_inconsistency_score(data.text)
        overlay_artifacts = self._overlay_artifact_score(data.text)
        altered_dates = self._conflicting_date_score(data.dates)
        metadata_mod = self._metadata_modification_score(data.metadata)

        features = {
            "font_inconsistency": font_inconsistency,
            "overlay_artifacts": overlay_artifacts,
            "altered_dates": altered_dates,
            "metadata_modification": metadata_mod,
        }
        weights = {
            "font_inconsistency": 0.22,
            "overlay_artifacts": 0.27,
            "altered_dates": 0.26,
            "metadata_modification": 0.25,
        }

        fraud_score = 0.0
        for feature, value in features.items():
            contribution = weights[feature] * value
            attributions[feature] = round(contribution, 4)
            fraud_score += contribution
            state = CheckState.FAIL if value > 0.6 else CheckState.WARN if value > 0.3 else CheckState.PASS
            signals.append(
                ValidationCheck(
                    check_id=f"fraud_{feature}",
                    name=feature.replace("_", " ").title(),
                    state=state,
                    message=f"{feature} score={value:.2f}",
                    score=max(0.0, 1 - value),
                )
            )

        fraud_score = max(0.0, min(1.0, fraud_score))
        if fraud_score >= 0.65:
            risk = FraudRiskLevel.HIGH
        elif fraud_score >= 0.35:
            risk = FraudRiskLevel.MEDIUM
        else:
            risk = FraudRiskLevel.LOW

        return FraudResult(
            score=round(fraud_score, 4),
            risk_level=risk,
            signals=signals,
            feature_attributions=attributions,
        )

    def _font_inconsistency_score(self, text: str) -> float:
        if not text:
            return 0.5
        chars = [c for c in text if c.isalpha()]
        if not chars:
            return 0.5
        upper_ratio = sum(1 for c in chars if c.isupper()) / len(chars)
        confusable_hits = sum(token in text for token in ("0O0O", "l1I", "rn", "m"))
        return min(1.0, (abs(upper_ratio - 0.35) * 1.2) + (confusable_hits * 0.06))

    def _overlay_artifact_score(self, text: str) -> float:
        if not text:
            return 0.5
        markers = ("photoshop", "edited", "corrected", "overwrite", "manual update", "reissued")
        hits = sum(marker in text.lower() for marker in markers)
        unusual_spaces = len(re.findall(r"[A-Za-z]\s{2,}[A-Za-z]", text))
        return min(1.0, hits * 0.25 + unusual_spaces * 0.03)

    def _conflicting_date_score(self, dates: list[str]) -> float:
        if len(dates) < 2:
            return 0.1
        parsed: list[datetime] = []
        for raw in dates:
            for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y"):
                try:
                    parsed.append(datetime.strptime(raw, fmt).replace(tzinfo=UTC))
                    break
                except ValueError:
                    continue
        if len(parsed) < 2:
            return 0.3
        years = [dt.year for dt in parsed]
        spread = max(years) - min(years)
        counts = Counter(years)
        dominant_ratio = max(counts.values()) / len(years)
        return min(1.0, (spread / 10.0) * 0.7 + (1 - dominant_ratio) * 0.4)

    def _metadata_modification_score(self, metadata: dict[str, object]) -> float:
        modified = metadata.get("modified_at")
        created = metadata.get("created_at")
        if not modified or not created:
            return 0.25
        try:
            created_dt = datetime.fromisoformat(str(created))
            modified_dt = datetime.fromisoformat(str(modified))
            delta_days = (modified_dt - created_dt).days
            if delta_days <= 0:
                return 0.1
            if delta_days <= 30:
                return 0.4
            return 0.75
        except Exception:
            return 0.45

