# validators/pan.py
import re

def validate_pan(fields: dict, ocr_text: str) -> dict:
    issues = []
    warnings = []
    score = 100

    pan_num = fields.get("pan_number", "")
    
    # 1. PAN format: ABCDE1234F
    if not pan_num:
        issues.append("PAN number not detected")
        score -= 35
    elif not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', pan_num):
        issues.append(f"Invalid PAN format: {pan_num}")
        score -= 30
    else:
        # 4th character indicates taxpayer type
        taxpayer_types = {
            'P': 'Individual', 'C': 'Company', 'H': 'HUF',
            'F': 'Firm', 'A': 'AOP', 'T': 'Trust', 'B': 'BOI',
            'L': 'Local Authority', 'J': 'Artificial Juridical Person',
            'G': 'Government'
        }
        fourth_char = pan_num[3]
        if fourth_char not in taxpayer_types:
            warnings.append(f"Unusual taxpayer type code: {fourth_char}")
            score -= 5
        else:
            fields["taxpayer_type"] = taxpayer_types[fourth_char]

    # 2. Name check
    if not fields.get("name"):
        warnings.append("Name not clearly extracted")
        score -= 10

    # 3. Income Tax Dept branding
    text_lower = ocr_text.lower()
    if "income tax" not in text_lower:
        warnings.append("Income Tax Dept branding not found")
        score -= 10

    # 4. Father's name (required for individuals)
    if not fields.get("father_name"):
        warnings.append("Father's name not extracted")
        score -= 5

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "score": max(score, 0),
        "fields_extracted": list(fields.keys())
    }