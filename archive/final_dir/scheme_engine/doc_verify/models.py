from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CheckState(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"


class DocumentStatus(str, Enum):
    VALID = "Valid"
    INVALID = "Invalid"
    SUSPICIOUS = "Suspicious"


class FraudRiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class ValidationCheck(BaseModel):
    check_id: str
    name: str
    state: CheckState
    message: str
    evidence: list[str] = Field(default_factory=list)
    score: float = 0.0


class LayerResult(BaseModel):
    passed: bool
    score: float = 0.0
    hard_fail: bool = False
    checks: list[ValidationCheck] = Field(default_factory=list)


class EnterpriseProfile(BaseModel):
    enterprise_name: str | None = None
    gstin: str | None = None
    pan: str | None = None
    udyam_id: str | None = None
    cin: str | None = None
    address: str | None = None
    turnover: float | None = None


class SchemeRequirements(BaseModel):
    required_document_types: list[str] = Field(default_factory=list)
    require_active_registration: bool = True
    require_gstin: bool = False
    require_pan: bool = False
    require_udyam: bool = False
    require_cin: bool = False
    min_turnover: float | None = None
    max_turnover: float | None = None


class VerificationContext(BaseModel):
    document_type: str
    claimed_authority: str | None = None
    enterprise_profile: EnterpriseProfile = Field(default_factory=EnterpriseProfile)
    scheme_requirements: SchemeRequirements = Field(default_factory=SchemeRequirements)


class ExtractedDocumentData(BaseModel):
    text: str
    business_name: str | None = None
    gstin: str | None = None
    pan: str | None = None
    udyam_id: str | None = None
    cin: str | None = None
    certificate_number: str | None = None
    serial_number: str | None = None
    authority_name: str | None = None
    urls: list[str] = Field(default_factory=list)
    dates: list[str] = Field(default_factory=list)
    turnover: float | None = None
    has_government_header: bool = False
    has_signature_block: bool = False
    signature_verified: bool = False
    signature_verification_detail: str | None = None
    qr_payload: dict[str, Any] | None = None
    qr_verified: bool = False
    qr_verification_detail: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class FraudResult(BaseModel):
    score: float
    risk_level: FraudRiskLevel
    signals: list[ValidationCheck] = Field(default_factory=list)
    feature_attributions: dict[str, float] = Field(default_factory=dict)


class ReportBreakdown(BaseModel):
    document_class: LayerResult
    govt_issuer: LayerResult
    authority_check: LayerResult
    format_syntax: LayerResult
    registry_api: LayerResult
    signature_qr: LayerResult
    profile_scheme: LayerResult
    fraud: FraudResult


class VerificationReport(BaseModel):
    report_id: str
    generated_at: datetime
    document_type: str
    status: DocumentStatus
    authenticity_score: float
    fraud_risk: FraudRiskLevel
    authority_verification: str
    root_causes: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    breakdown: ReportBreakdown
    extracted_data: ExtractedDocumentData
    version: int = 1


class ApiError(BaseModel):
    request_id: str
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class SchemeAuditEvent(BaseModel):
    event_id: str
    scheme_id: str
    created_at: datetime
    actor_role: str
    action: str
    detail: str
    level: str = "info"
