# document_verification/cross_validator.py
# Cross-validates extracted fields across multiple documents

from difflib import SequenceMatcher

def name_similarity(name1: str, name2: str) -> float:
    """Fuzzy name matching (handles initials, order differences)"""
    if not name1 or not name2:
        return 0.0
    n1 = name1.upper().strip()
    n2 = name2.upper().strip()
    return SequenceMatcher(None, n1, n2).ratio()

def cross_validate_documents(extracted_data: dict) -> dict:
    """
    Compare fields across all uploaded documents.
    extracted_data: {doc_type: {fields}}
    """
    issues = []
    warnings = []
    passed = []
    score = 100

    docs = extracted_data  # e.g., {"aadhaar": {...}, "pan": {...}, "gst": {...}}

    # 1. Name consistency across Aadhaar + PAN
    aadhaar_name = docs.get("aadhaar", {}).get("name", "")
    pan_name = docs.get("pan", {}).get("name", "")
    
    if aadhaar_name and pan_name:
        similarity = name_similarity(aadhaar_name, pan_name)
        if similarity < 0.6:
            issues.append(
                f"Name mismatch: Aadhaar='{aadhaar_name}' vs PAN='{pan_name}' "
                f"(similarity: {similarity:.0%})"
            )
            score -= 20
        elif similarity < 0.8:
            warnings.append(f"Name slightly different between Aadhaar and PAN ({similarity:.0%} match)")
            score -= 8
        else:
            passed.append(f"Name matches across Aadhaar & PAN ({similarity:.0%})")

    # 2. DOB consistency
    aadhaar_dob = docs.get("aadhaar", {}).get("dob", "")
    pan_dob = docs.get("pan", {}).get("dob", "")
    
    if aadhaar_dob and pan_dob:
        if aadhaar_dob != pan_dob:
            issues.append(f"DOB mismatch: Aadhaar={aadhaar_dob} vs PAN={pan_dob}")
            score -= 20
        else:
            passed.append("DOB matches across Aadhaar & PAN")

    # 3. GST — PAN embedded in GSTIN (chars 3-12)
    gstin = docs.get("gst", {}).get("gstin", "")
    pan_num = docs.get("pan", {}).get("pan_number", "")
    
    if gstin and pan_num:
        pan_in_gstin = gstin[2:12]
        if pan_in_gstin == pan_num:
            passed.append("PAN number embedded in GSTIN matches PAN card")
        else:
            issues.append(
                f"GSTIN-PAN mismatch: GSTIN contains '{pan_in_gstin}' but PAN card shows '{pan_num}'"
            )
            score -= 25

    # 4. Business name: GST legal name vs Udyam enterprise name
    gst_legal = docs.get("gst", {}).get("legal_name", "")
    udyam_name = docs.get("udyam", {}).get("enterprise_name", "")
    
    if gst_legal and udyam_name:
        sim = name_similarity(gst_legal, udyam_name)
        if sim < 0.5:
            warnings.append(
                f"Business name differs between GST ({gst_legal}) "
                f"and Udyam ({udyam_name})"
            )
            score -= 10
        else:
            passed.append("Business name consistent across GST & Udyam")

    return {
        "cross_valid_score": max(score, 0),
        "issues": issues,
        "warnings": warnings,
        "passed": passed,
        "documents_compared": list(docs.keys())
    }