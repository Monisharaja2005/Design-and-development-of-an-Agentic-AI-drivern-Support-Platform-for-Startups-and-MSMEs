# validators/gst.py
import re

# Indian state codes for GST
STATE_CODES = {
    "01": "Jammu & Kashmir", "02": "Himachal Pradesh", "03": "Punjab",
    "04": "Chandigarh", "05": "Uttarakhand", "06": "Haryana",
    "07": "Delhi", "08": "Rajasthan", "09": "Uttar Pradesh",
    "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh",
    "13": "Nagaland", "14": "Manipur", "15": "Mizoram",
    "16": "Tripura", "17": "Meghalaya", "18": "Assam",
    "19": "West Bengal", "20": "Jharkhand", "21": "Odisha",
    "22": "Chhattisgarh", "23": "Madhya Pradesh", "24": "Gujarat",
    "27": "Maharashtra", "29": "Karnataka", "30": "Goa",
    "32": "Kerala", "33": "Tamil Nadu", "36": "Telangana",
    "37": "Andhra Pradesh"
}

def validate_gst(fields: dict, ocr_text: str) -> dict:
    issues = []
    warnings = []
    score = 100

    gstin = fields.get("gstin", "")
    
    # 1. GSTIN format: 15-char alphanumeric
    if not gstin:
        issues.append("GSTIN not detected")
        score -= 35
    elif not re.match(r'^\d{2}[A-Z]{5}\d{4}[A-Z]\d[Z][A-Z0-9]$', gstin):
        issues.append(f"Invalid GSTIN format: {gstin}")
        score -= 30
    else:
        # Validate state code
        state_code = gstin[:2]
        if state_code in STATE_CODES:
            fields["state"] = STATE_CODES[state_code]
        else:
            warnings.append(f"Unknown state code in GSTIN: {state_code}")
            score -= 5
        
        # 13th character must be Z
        if gstin[12] != 'Z':
            issues.append("Invalid GSTIN: 13th character must be Z")
            score -= 15

    # 2. Legal name check
    if not fields.get("legal_name"):
        warnings.append("Legal name not extracted")
        score -= 10

    # 3. GST-specific keywords
    text_lower = ocr_text.lower()
    required_keywords = ["gstin", "registration"]
    for kw in required_keywords:
        if kw not in text_lower:
            warnings.append(f"Expected keyword '{kw}' not found")
            score -= 5

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "score": max(score, 0),
        "fields_extracted": list(fields.keys())
    }