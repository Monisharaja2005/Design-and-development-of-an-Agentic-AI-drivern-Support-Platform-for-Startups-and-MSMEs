from pathlib import Path

from scheme_engine.doc_verify.engine import DocumentVerificationEngine
from scheme_engine.doc_verify.models import EnterpriseProfile, SchemeRequirements, VerificationContext
from scheme_engine.doc_verify.registry import AuthorityRegistry
from scheme_engine.doc_verify.settings import ScoreWeights


def _engine() -> DocumentVerificationEngine:
    registry_path = Path(__file__).resolve().parents[1] / "doc_verify" / "data" / "government_authorities.json"
    registry = AuthorityRegistry.from_file(registry_path)
    return DocumentVerificationEngine(registry=registry, weights=ScoreWeights())


def test_valid_gst_certificate_scores_high():
    engine = _engine()
    text = """
    Government of India
    Goods and Services Tax
    Name of Enterprise: Acme Industries Private Limited
    GSTIN: 27ABCDE1234F1Z5
    PAN: ABCDE1234F
    Certificate No: GST/2025/000123
    Date: 13/02/2025
    Digital Signature: Valid
    https://services.gst.gov.in
    """
    ctx = VerificationContext(
        document_type="gst_certificate",
        claimed_authority="Goods and Services Tax Network",
        enterprise_profile=EnterpriseProfile(
            enterprise_name="Acme Industries Private Limited",
            gstin="27ABCDE1234F1Z5",
            pan="ABCDE1234F",
        ),
        scheme_requirements=SchemeRequirements(required_document_types=["gst_certificate"], require_gstin=True),
    )
    report = engine.verify_text(text, ctx)
    assert report.authenticity_score >= 70
    assert report.authority_verification == "Verified"


def test_inactive_gstin_causes_invalid():
    engine = _engine()
    text = """
    Government of India
    Goods and Services Tax
    GSTIN: 27ABCDE1234F1Z9
    Date: 13/02/2025
    https://fake-gst.example.com
    """
    ctx = VerificationContext(
        document_type="gst_certificate",
        claimed_authority="GSTN",
        enterprise_profile=EnterpriseProfile(gstin="27ABCDE1234F1Z9"),
    )
    report = engine.verify_text(text, ctx)
    assert report.status.value in {"Invalid", "Suspicious"}
    assert any("GSTIN Registry Status" in cause for cause in report.root_causes)

