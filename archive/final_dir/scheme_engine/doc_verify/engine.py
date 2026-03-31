from __future__ import annotations

import uuid
from datetime import UTC, datetime

from .extraction import DocumentExtractor
from .fraud import FraudDetector
from .models import ReportBreakdown, VerificationContext, VerificationReport
from .registry import AuthorityRegistry
from .scoring import compute_authenticity_score, resolve_status
from .settings import ScoreWeights
from .validators import (
    AuthorityVerificationValidator,
    DocumentClassValidator,
    FormatSyntaxValidator,
    GovernmentIssuedValidator,
    OfficialRegistryClient,
    ProfileSchemeValidator,
    RegistryAPIVerifier,
    SignatureQrValidator,
)


class DocumentVerificationEngine:
    def __init__(
        self,
        registry: AuthorityRegistry,
        weights: ScoreWeights,
        registry_endpoints: dict[str, str] | None = None,
        registry_headers: dict[str, str] | None = None,
    ):
        self.registry = registry
        self.weights = weights
        self.extractor = DocumentExtractor()
        self.document_class_validator = DocumentClassValidator()
        self.gov_validator = GovernmentIssuedValidator()
        self.authority_validator = AuthorityVerificationValidator()
        self.format_validator = FormatSyntaxValidator()
        self.api_validator = RegistryAPIVerifier(
            client=OfficialRegistryClient(endpoints=registry_endpoints, headers=registry_headers)
        )
        self.sig_qr_validator = SignatureQrValidator()
        self.profile_validator = ProfileSchemeValidator()
        self.fraud_detector = FraudDetector()

    def verify_document(
        self,
        *,
        file_name: str,
        content: bytes,
        content_type: str | None,
        context: VerificationContext,
    ) -> VerificationReport:
        extracted = self.extractor.extract(file_name=file_name, content=content, content_type=content_type)
        return self._run_pipeline(extracted, context)

    def verify_text(self, text: str, context: VerificationContext) -> VerificationReport:
        extracted = self.extractor.extract_from_text(text=text)
        return self._run_pipeline(extracted, context)

    def _run_pipeline(self, extracted, context: VerificationContext) -> VerificationReport:
        doc_class = self.document_class_validator.validate(extracted, context)
        govt = self.gov_validator.validate(extracted, self.registry)
        authority = self.authority_validator.validate(extracted, context, self.registry)
        fmt = self.format_validator.validate(extracted, context)
        api = self.api_validator.validate(extracted, context)
        sig_qr = self.sig_qr_validator.validate(extracted)
        profile = self.profile_validator.validate(extracted, context)
        fraud = self.fraud_detector.evaluate(extracted)

        authenticity = compute_authenticity_score(
            govt_issuer=govt,
            authority_check=authority,
            format_check=fmt,
            api_check=api,
            fraud_score=fraud.score,
            weights=self.weights,
        )

        hard_fail = any(
            (
                doc_class.hard_fail,
                govt.hard_fail,
                authority.hard_fail,
                fmt.hard_fail,
                api.hard_fail,
                sig_qr.hard_fail,
            )
        )
        status = resolve_status(
            authenticity_score=authenticity,
            fraud_risk=fraud.risk_level,
            hard_fail=hard_fail,
        )

        root_causes = _collect_root_causes([doc_class, govt, authority, fmt, api, sig_qr, profile], fraud.score)
        actions = _recommend_actions(root_causes)

        authority_status = "Verified" if authority.passed else "Unverified Issuing Authority"
        breakdown = ReportBreakdown(
            document_class=doc_class,
            govt_issuer=govt,
            authority_check=authority,
            format_syntax=fmt,
            registry_api=api,
            signature_qr=sig_qr,
            profile_scheme=profile,
            fraud=fraud,
        )

        return VerificationReport(
            report_id=str(uuid.uuid4()),
            generated_at=datetime.now(tz=UTC),
            document_type=context.document_type,
            status=status,
            authenticity_score=authenticity,
            fraud_risk=fraud.risk_level,
            authority_verification=authority_status,
            root_causes=root_causes,
            recommended_actions=actions,
            breakdown=breakdown,
            extracted_data=extracted,
            version=1,
        )


def _collect_root_causes(layer_results, fraud_score: float) -> list[str]:
    causes: list[str] = []
    for layer in layer_results:
        for check in layer.checks:
            if check.state.value == "fail":
                causes.append(f"{check.name}: {check.message}")
    if fraud_score >= 0.65:
        causes.append("High fraud probability from tamper signals")
    return causes[:8]


def _recommend_actions(root_causes: list[str]) -> list[str]:
    if not root_causes:
        return ["Proceed with application workflow and archive verification artifacts."]
    actions = [
        "Re-upload original document downloaded from official government portal.",
        "Provide document with valid digital signature or verifiable QR code.",
        "Cross-check applicant profile identifiers (GSTIN/PAN/Udyam/CIN) before resubmission.",
    ]
    if any("Registry Status" in cause for cause in root_causes):
        actions.insert(0, "Validate registration status directly on respective official registry portal.")
    return actions[:4]
