# validators/udyam.py
import re

def validate_udyam(fields: dict, ocr_text: str) -> dict:
    issues = []
    warnings = []
    score = 100

    udyam_num = fields.get("udyam_number", "")
    
    # 1. Udyam number format: UDYAM-XX-00-0000000
    if not udyam_num:
        issues.append("Udyam registration number not detected")
        score -= 35
    elif not re.match(r'^UDYAM-[A-Z]{2}-\d{2}-\d{7}$', udyam_num, re.IGNORECASE):
        issues.append(f"Invalid Udyam number format: {udyam_num}")
        score -= 25

    # 2. Enterprise type
    enterprise_type = fields.get("enterprise_type", "")
    if enterprise_type not in ["MICRO", "SMALL", "MEDIUM"]:
        warnings.append("Enterprise type (Micro/Small/Medium) not clearly identified")
        score -= 10

    # 3. Enterprise name
    if not fields.get("enterprise_name"):
        warnings.append("Enterprise name not extracted")
        score -= 10

    # 4. MSME Ministry branding
    text_lower = ocr_text.lower()
    if "ministry of micro" not in text_lower and "msme" not in text_lower:
        warnings.append("MSME Ministry branding not detected")
        score -= 10

    # 5. NIC code check
    if "nic" not in text_lower:
        warnings.append("NIC activity code not found")
        score -= 5

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "score": max(score, 0),
        "fields_extracted": list(fields.keys())
    }