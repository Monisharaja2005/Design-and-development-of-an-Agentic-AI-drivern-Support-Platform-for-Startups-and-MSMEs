# validators/aadhaar.py
import re
from datetime import datetime

def validate_aadhaar(fields: dict, ocr_text: str) -> dict:
    """
    Validate Aadhaar card fields.
    Returns: {valid, issues, warnings, score}
    """
    issues = []
    warnings = []
    score = 100

    # 1. Aadhaar number format check
    aadhaar_num = fields.get("aadhaar_number", "")
    if not aadhaar_num:
        issues.append("Aadhaar number not detected")
        score -= 30
    elif not re.match(r'^\d{12}$', aadhaar_num):
        issues.append(f"Invalid Aadhaar format: {aadhaar_num}")
        score -= 25
    else:
        # Aadhaar cannot start with 0 or 1
        if aadhaar_num[0] in ['0', '1']:
            issues.append("Aadhaar number starts with invalid digit")
            score -= 20

    # 2. Name check
    if not fields.get("name"):
        warnings.append("Name not extracted clearly")
        score -= 10

    # 3. DOB format check
    dob = fields.get("dob", "")
    if dob:
        try:
            dob_date = datetime.strptime(dob, "%d/%m/%Y")
            age = (datetime.now() - dob_date).days // 365
            if age < 0 or age > 120:
                issues.append(f"Invalid age derived from DOB: {age}")
                score -= 15
        except ValueError:
            warnings.append(f"DOB format unclear: {dob}")
            score -= 5
    else:
        warnings.append("Date of birth not found")
        score -= 10

    # 4. UIDAI branding check
    text_lower = ocr_text.lower()
    if "uidai" not in text_lower and "unique identification" not in text_lower:
        warnings.append("UIDAI branding not detected — may be unofficial copy")
        score -= 10

    # 5. Gender check
    if not fields.get("gender"):
        warnings.append("Gender field not found")
        score -= 5

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "score": max(score, 0),
        "fields_extracted": list(fields.keys())
    }