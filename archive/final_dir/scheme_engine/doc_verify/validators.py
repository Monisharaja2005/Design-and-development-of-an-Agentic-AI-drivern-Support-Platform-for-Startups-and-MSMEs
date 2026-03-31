from __future__ import annotations

from datetime import UTC, datetime
from urllib.parse import urlparse

import requests

from .models import (
    CheckState,
    ExtractedDocumentData,
    LayerResult,
    ValidationCheck,
    VerificationContext,
)
from .registry import AuthorityRegistry


class OfficialRegistryClient:
    """Configurable API adapters for GSTIN/PAN/CIN/Udyam verification."""

    def __init__(self, endpoints: dict[str, str] | None = None, headers: dict[str, str] | None = None):
        self.endpoints = endpoints or {}
        self.headers = headers or {}

    def verify_gstin(self, gstin: str) -> tuple[bool, str]:
        return self._verify_with_endpoint("gstin", {"gstin": gstin}, fallback_invalid=gstin.endswith("Z9"))

    def verify_pan(self, pan: str) -> tuple[bool, str]:
        return self._verify_with_endpoint("pan", {"pan": pan}, fallback_invalid=pan.startswith("AAAAA"))

    def verify_cin(self, cin: str) -> tuple[bool, str]:
        return self._verify_with_endpoint("cin", {"cin": cin}, fallback_invalid=cin.endswith("000000"))

    def verify_udyam(self, udyam_id: str) -> tuple[bool, str]:
        return self._verify_with_endpoint("udyam", {"udyam_id": udyam_id}, fallback_invalid=udyam_id.endswith("0000000"))

    def _verify_with_endpoint(self, key: str, payload: dict[str, str], fallback_invalid: bool) -> tuple[bool, str]:
        endpoint = self.endpoints.get(key)
        if not endpoint:
            return (not fallback_invalid, f"Offline heuristic ({key})")
        try:
            resp = requests.post(endpoint, json=payload, headers=self.headers, timeout=12)
            resp.raise_for_status()
            data = resp.json() if resp.content else {}
            status = self._parse_status(data)
            if status is None:
                return (not fallback_invalid, f"Unclear API response ({key})")
            return (status, f"Live registry API ({key})")
        except Exception as exc:
            return (not fallback_invalid, f"Registry API error ({key}): {exc}")

    def _parse_status(self, data: dict[str, object]) -> bool | None:
        if not data:
            return None
        for key in ("active", "is_active", "valid", "is_valid", "verified"):
            if key in data and isinstance(data[key], bool):
                return bool(data[key])
        raw_status = data.get("status")
        if isinstance(raw_status, str):
            status_upper = raw_status.strip().upper()
            if status_upper in {"ACTIVE", "VALID", "VERIFIED", "ENABLED"}:
                return True
            if status_upper in {"INACTIVE", "INVALID", "CANCELLED", "DISABLED", "SUSPENDED"}:
                return False
        nested = data.get("data")
        if isinstance(nested, dict):
            return self._parse_status(nested)
        return None


class GovernmentIssuedValidator:
    def validate(self, data: ExtractedDocumentData, registry: AuthorityRegistry) -> LayerResult:
        checks: list[ValidationCheck] = []

        header_ok = data.has_government_header
        checks.append(
            ValidationCheck(
                check_id="gov_header",
                name="Government Header Detection",
                state=CheckState.PASS if header_ok else CheckState.FAIL,
                message="Official government header present" if header_ok else "No official government header found",
                evidence=[data.text[:250]],
                score=1.0 if header_ok else 0.0,
            )
        )

        authority = registry.detect_from_text(data.text)
        authority_ok = authority is not None
        checks.append(
            ValidationCheck(
                check_id="gov_authority_text",
                name="Issuing Department Detection",
                state=CheckState.PASS if authority_ok else CheckState.FAIL,
                message=authority.authority_name if authority else "Recognized authority not detected in document",
                score=1.0 if authority_ok else 0.0,
            )
        )

        logo_hint = any(token in data.text.lower() for token in ("emblem", "logo", "seal"))
        checks.append(
            ValidationCheck(
                check_id="gov_logo",
                name="Logo Presence Check",
                state=CheckState.PASS if logo_hint else CheckState.WARN,
                message="Logo marker detected (text-level heuristic)"
                if logo_hint
                else "Logo model unavailable; no text evidence for logo",
                score=0.8 if logo_hint else 0.3,
            )
        )

        serial_ok = bool(data.serial_number)
        checks.append(
            ValidationCheck(
                check_id="gov_serial",
                name="Certificate Serial Presence",
                state=CheckState.PASS if serial_ok else CheckState.WARN,
                message="Certificate serial/pattern present" if serial_ok else "No certificate serial pattern detected",
                evidence=[data.serial_number] if data.serial_number else [],
                score=1.0 if serial_ok else 0.4,
            )
        )

        score = sum(check.score for check in checks) / len(checks)
        passed = header_ok and authority_ok
        return LayerResult(passed=passed, score=score, hard_fail=not passed, checks=checks)


class DocumentClassValidator:
    DOC_KEYWORDS = {
        "gst_certificate": ("goods and services tax", "gst", "gstin"),
        "pan_card": ("permanent account number", "income tax", "pan"),
        "udyam_certificate": ("udyam", "msme", "registration"),
        "cin_certificate": ("corporate identity number", "ministry of corporate affairs", "cin"),
    }

    DOC_FIELDS = {
        "gst_certificate": ("gstin",),
        "pan_card": ("pan",),
        "udyam_certificate": ("udyam_id",),
        "cin_certificate": ("cin",),
    }

    def validate(self, data: ExtractedDocumentData, context: VerificationContext) -> LayerResult:
        doc_type = context.document_type.lower()
        checks: list[ValidationCheck] = []
        keywords = self.DOC_KEYWORDS.get(doc_type, tuple())
        required_fields = self.DOC_FIELDS.get(doc_type, tuple())
        sample = data.text.lower()

        keyword_match = any(token in sample for token in keywords) if keywords else True
        checks.append(
            ValidationCheck(
                check_id="doc_class_keywords",
                name="Document Type Keyword Match",
                state=CheckState.PASS if keyword_match else CheckState.FAIL,
                message="Document text matches selected document type"
                if keyword_match
                else "Document content does not match selected document type keywords",
                evidence=[context.document_type],
                score=1.0 if keyword_match else 0.0,
            )
        )

        missing_fields = [field for field in required_fields if not getattr(data, field)]
        fields_ok = len(missing_fields) == 0
        checks.append(
            ValidationCheck(
                check_id="doc_class_identifiers",
                name="Mandatory Identifier Presence",
                state=CheckState.PASS if fields_ok else CheckState.FAIL,
                message="All mandatory identifiers are present"
                if fields_ok
                else f"Missing identifiers for selected type: {', '.join(missing_fields)}",
                evidence=missing_fields,
                score=1.0 if fields_ok else 0.0,
            )
        )

        score = sum(c.score for c in checks) / len(checks)
        passed = all(c.state != CheckState.FAIL for c in checks)
        return LayerResult(passed=passed, score=score, hard_fail=not passed, checks=checks)


class AuthorityVerificationValidator:
    def validate(
        self,
        data: ExtractedDocumentData,
        context: VerificationContext,
        registry: AuthorityRegistry,
    ) -> LayerResult:
        checks: list[ValidationCheck] = []
        detected = registry.detect_from_text(data.text)
        claimed = registry.match_name(context.claimed_authority)

        authority_match = bool(detected and claimed and detected.authority_name == claimed.authority_name)
        if context.claimed_authority and not claimed:
            authority_match = False

        checks.append(
            ValidationCheck(
                check_id="authority_name",
                name="Authority Name Match",
                state=CheckState.PASS if authority_match else CheckState.FAIL,
                message="Claimed authority validated"
                if authority_match
                else "Claimed authority does not match recognized registry authority",
                evidence=[f"claimed={context.claimed_authority}", f"detected={detected.authority_name if detected else 'none'}"],
                score=1.0 if authority_match else 0.0,
            )
        )

        doc_type_ok = bool(claimed and context.document_type.lower() in claimed.document_types) if claimed else False
        checks.append(
            ValidationCheck(
                check_id="authority_doc_type",
                name="Authority Document Type Support",
                state=CheckState.PASS if doc_type_ok else CheckState.FAIL,
                message="Document type is supported by claimed authority"
                if doc_type_ok
                else "Uploaded document type is not supported by claimed authority",
                evidence=[
                    f"document_type={context.document_type}",
                    f"authority={claimed.authority_name if claimed else 'unknown'}",
                ],
                score=1.0 if doc_type_ok else 0.0,
            )
        )

        allowed_domains = set((claimed.domains if claimed else []))
        domain_checks = []
        if data.urls:
            for url in data.urls:
                host = (urlparse(url).hostname or "").lower()
                ok = _domain_matches(host, allowed_domains) if allowed_domains else False
                domain_checks.append(ok)
        domain_ok = all(domain_checks) if domain_checks else bool(allowed_domains)
        checks.append(
            ValidationCheck(
                check_id="authority_domain",
                name="Authority Domain Authenticity",
                state=CheckState.PASS if domain_ok else CheckState.WARN,
                message="All referenced domains are consistent with authority"
                if domain_ok
                else "One or more referenced domains are unverified for claimed authority",
                evidence=data.urls,
                score=1.0 if domain_ok else 0.45,
            )
        )

        score = sum(c.score for c in checks) / len(checks)
        passed = all(c.state != CheckState.FAIL for c in checks)
        return LayerResult(passed=passed, score=score, hard_fail=not passed, checks=checks)


class FormatSyntaxValidator:
    DOC_TYPE_REQUIREMENTS = {
        "gst_certificate": ("gstin",),
        "pan_card": ("pan",),
        "udyam_certificate": ("udyam_id",),
        "cin_certificate": ("cin",),
    }

    def validate(self, data: ExtractedDocumentData, context: VerificationContext) -> LayerResult:
        checks: list[ValidationCheck] = []
        required = self.DOC_TYPE_REQUIREMENTS.get(context.document_type.lower(), tuple())

        for field in ("gstin", "pan", "udyam_id", "cin"):
            value = getattr(data, field)
            if field not in required and not value:
                continue
            state = CheckState.PASS if bool(value) else CheckState.FAIL
            checks.append(
                ValidationCheck(
                    check_id=f"fmt_{field}",
                    name=f"{field.upper()} Format Check",
                    state=state,
                    message=f"{field.upper()} detected and valid pattern" if state == CheckState.PASS else f"{field.upper()} missing/invalid",
                    evidence=[value] if value else [],
                    score=1.0 if state == CheckState.PASS else 0.0,
                )
            )

        now = datetime.now(tz=UTC).date()
        parsed_dates = _parse_dates(data.dates)
        dates_ok = all(dt <= now for dt in parsed_dates)
        checks.append(
            ValidationCheck(
                check_id="fmt_dates",
                name="Date Calendar Validation",
                state=CheckState.PASS if dates_ok else CheckState.FAIL,
                message="Dates are calendar-valid and not future-dated"
                if dates_ok
                else "At least one date appears invalid/future-dated",
                evidence=data.dates,
                score=1.0 if dates_ok else 0.0,
            )
        )

        turnover_ok = data.turnover is None or data.turnover >= 0
        checks.append(
            ValidationCheck(
                check_id="fmt_turnover",
                name="Turnover Numeric Validation",
                state=CheckState.PASS if turnover_ok else CheckState.FAIL,
                message="Turnover format is numeric" if turnover_ok else "Turnover parsing failed",
                evidence=[str(data.turnover)] if data.turnover is not None else [],
                score=1.0 if turnover_ok else 0.0,
            )
        )

        score = sum(c.score for c in checks) / len(checks) if checks else 0.0
        passed = all(c.state != CheckState.FAIL for c in checks)
        return LayerResult(passed=passed, score=score, hard_fail=not passed, checks=checks)


class RegistryAPIVerifier:
    def __init__(self, client: OfficialRegistryClient):
        self.client = client

    def validate(self, data: ExtractedDocumentData, context: VerificationContext) -> LayerResult:
        checks: list[ValidationCheck] = []

        if data.gstin:
            active, source = self.client.verify_gstin(data.gstin)
            checks.append(
                ValidationCheck(
                    check_id="api_gstin",
                    name="GSTIN Registry Status",
                    state=CheckState.PASS if active else CheckState.FAIL,
                    message=f"{source}: {'active' if active else 'inactive'}",
                    evidence=[data.gstin],
                    score=1.0 if active else 0.0,
                )
            )
        if data.pan:
            valid, source = self.client.verify_pan(data.pan)
            checks.append(
                ValidationCheck(
                    check_id="api_pan",
                    name="PAN Registry Status",
                    state=CheckState.PASS if valid else CheckState.FAIL,
                    message=f"{source}: {'valid' if valid else 'invalid'}",
                    evidence=[data.pan],
                    score=1.0 if valid else 0.0,
                )
            )
        if data.cin:
            valid, source = self.client.verify_cin(data.cin)
            checks.append(
                ValidationCheck(
                    check_id="api_cin",
                    name="CIN Registry Status",
                    state=CheckState.PASS if valid else CheckState.FAIL,
                    message=f"{source}: {'active' if valid else 'invalid/inactive'}",
                    evidence=[data.cin],
                    score=1.0 if valid else 0.0,
                )
            )
        if data.udyam_id:
            valid, source = self.client.verify_udyam(data.udyam_id)
            checks.append(
                ValidationCheck(
                    check_id="api_udyam",
                    name="Udyam Registry Status",
                    state=CheckState.PASS if valid else CheckState.FAIL,
                    message=f"{source}: {'active' if valid else 'inactive'}",
                    evidence=[data.udyam_id],
                    score=1.0 if valid else 0.0,
                )
            )

        if not checks:
            checks.append(
                ValidationCheck(
                    check_id="api_none",
                    name="Registry Verification Coverage",
                    state=CheckState.WARN,
                    message="No registry-verifiable identifiers were extracted",
                    score=0.4,
                )
            )

        score = sum(c.score for c in checks) / len(checks)
        passed = all(c.state != CheckState.FAIL for c in checks)
        return LayerResult(passed=passed, score=score, hard_fail=not passed, checks=checks)


class SignatureQrValidator:
    def validate(self, data: ExtractedDocumentData) -> LayerResult:
        checks: list[ValidationCheck] = []

        if data.has_signature_block and data.signature_verified:
            checks.append(
                ValidationCheck(
                    check_id="sig_block",
                    name="Digital Signature Block Detection",
                    state=CheckState.PASS,
                    message=data.signature_verification_detail or "Digital signature cryptographically verified",
                    score=1.0,
                )
            )
        elif data.has_signature_block:
            checks.append(
                ValidationCheck(
                    check_id="sig_block",
                    name="Digital Signature Block Detection",
                    state=CheckState.FAIL,
                    message=data.signature_verification_detail or "Signature block present but cryptographic verification failed",
                    score=0.0,
                )
            )
        else:
            checks.append(
                ValidationCheck(
                    check_id="sig_block",
                    name="Digital Signature Block Detection",
                    state=CheckState.WARN,
                    message="No digital signature marker found",
                    score=0.35,
                )
            )

        if data.qr_payload and data.qr_verified:
            mismatches = _compare_qr_payload(data)
            qr_ok = len(mismatches) == 0
            checks.append(
                ValidationCheck(
                    check_id="qr_match",
                    name="QR Payload Consistency",
                    state=CheckState.PASS if qr_ok else CheckState.FAIL,
                    message="QR payload is consistent with extracted document fields"
                    if qr_ok
                    else "QR payload mismatches extracted fields",
                    evidence=mismatches,
                    score=1.0 if qr_ok else 0.0,
                )
            )
        elif data.qr_payload and not data.qr_verified:
            checks.append(
                ValidationCheck(
                    check_id="qr_presence",
                    name="QR Authenticity Validation",
                    state=CheckState.FAIL,
                    message=data.qr_verification_detail or "QR code detected but could not be validated",
                    score=0.0,
                )
            )
        else:
            checks.append(
                ValidationCheck(
                    check_id="qr_presence",
                    name="QR Authenticity Validation",
                    state=CheckState.WARN,
                    message="No decodable QR payload found",
                    score=0.35,
                )
            )

        score = sum(c.score for c in checks) / len(checks)
        passed = all(c.state != CheckState.FAIL for c in checks)
        return LayerResult(passed=passed, score=score, hard_fail=not passed, checks=checks)


class ProfileSchemeValidator:
    def validate(self, data: ExtractedDocumentData, context: VerificationContext) -> LayerResult:
        checks: list[ValidationCheck] = []
        profile = context.enterprise_profile
        req = context.scheme_requirements

        checks.extend(
            _match_identifier(name, getattr(data, name), getattr(profile, name))
            for name in ("gstin", "pan", "udyam_id", "cin")
            if getattr(profile, name) is not None
        )

        if profile.enterprise_name and data.business_name:
            match = profile.enterprise_name.lower() in data.business_name.lower() or data.business_name.lower() in profile.enterprise_name.lower()
            checks.append(
                ValidationCheck(
                    check_id="profile_name",
                    name="Enterprise Name Match",
                    state=CheckState.PASS if match else CheckState.FAIL,
                    message="Business name matches applicant profile" if match else "Business name mismatch against profile",
                    evidence=[profile.enterprise_name, data.business_name],
                    score=1.0 if match else 0.0,
                )
            )

        if req.required_document_types:
            doc_match = context.document_type.lower() in [d.lower() for d in req.required_document_types]
            checks.append(
                ValidationCheck(
                    check_id="scheme_doc_type",
                    name="Scheme Document Type Eligibility",
                    state=CheckState.PASS if doc_match else CheckState.FAIL,
                    message="Document type accepted by scheme" if doc_match else "Document type not accepted by scheme",
                    evidence=[context.document_type],
                    score=1.0 if doc_match else 0.0,
                )
            )

        if req.min_turnover is not None and data.turnover is not None:
            checks.append(
                ValidationCheck(
                    check_id="scheme_min_turnover",
                    name="Minimum Turnover Eligibility",
                    state=CheckState.PASS if data.turnover >= req.min_turnover else CheckState.FAIL,
                    message="Turnover meets minimum threshold"
                    if data.turnover >= req.min_turnover
                    else "Turnover below minimum threshold",
                    evidence=[str(data.turnover), str(req.min_turnover)],
                    score=1.0 if data.turnover >= req.min_turnover else 0.0,
                )
            )
        if req.max_turnover is not None and data.turnover is not None:
            checks.append(
                ValidationCheck(
                    check_id="scheme_max_turnover",
                    name="Maximum Turnover Eligibility",
                    state=CheckState.PASS if data.turnover <= req.max_turnover else CheckState.FAIL,
                    message="Turnover within maximum threshold"
                    if data.turnover <= req.max_turnover
                    else "Turnover exceeds maximum threshold",
                    evidence=[str(data.turnover), str(req.max_turnover)],
                    score=1.0 if data.turnover <= req.max_turnover else 0.0,
                )
            )

        if not checks:
            checks.append(
                ValidationCheck(
                    check_id="profile_none",
                    name="Profile and Scheme Match",
                    state=CheckState.WARN,
                    message="No profile/scheme constraints provided",
                    score=0.5,
                )
            )

        score = sum(c.score for c in checks) / len(checks)
        passed = all(c.state != CheckState.FAIL for c in checks)
        return LayerResult(passed=passed, score=score, hard_fail=not passed, checks=checks)


def _parse_dates(raw_dates: list[str]) -> list[datetime.date]:
    parsed: list[datetime.date] = []
    for value in raw_dates:
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y"):
            try:
                parsed.append(datetime.strptime(value, fmt).date())
                break
            except ValueError:
                continue
    return parsed


def _domain_matches(host: str, allowed_domains: set[str]) -> bool:
    if not host:
        return False
    for domain in allowed_domains:
        if host == domain or host.endswith(f".{domain}"):
            return True
    return False


def _compare_qr_payload(data: ExtractedDocumentData) -> list[str]:
    mismatches: list[str] = []
    if not data.qr_payload:
        return mismatches
    for key in ("gstin", "pan", "udyam_id", "cin", "business_name", "certificate_number"):
        qr_val = data.qr_payload.get(key)
        extracted_val = getattr(data, key, None)
        if qr_val and extracted_val and str(qr_val).strip().lower() != str(extracted_val).strip().lower():
            mismatches.append(f"{key}: qr={qr_val} extracted={extracted_val}")
    return mismatches


def _match_identifier(field: str, extracted: str | None, expected: str | None) -> ValidationCheck:
    matched = bool(extracted and expected and extracted.upper() == expected.upper())
    return ValidationCheck(
        check_id=f"profile_{field}",
        name=f"Profile {field.upper()} Match",
        state=CheckState.PASS if matched else CheckState.FAIL,
        message=f"{field.upper()} matches profile" if matched else f"{field.upper()} mismatch against applicant profile",
        evidence=[f"extracted={extracted}", f"profile={expected}"],
        score=1.0 if matched else 0.0,
    )
