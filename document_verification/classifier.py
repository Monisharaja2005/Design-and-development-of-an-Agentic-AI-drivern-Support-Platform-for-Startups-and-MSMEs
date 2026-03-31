# document_verification/classifier.py
# Classifies document type using keyword rules + ML confidence

import re
from typing import Tuple

# Rule-based keyword signatures per document type
DOCUMENT_SIGNATURES = {
    "aadhaar": {
        "keywords": [
            "aadhaar", "aadhar", "uid", "unique identification",
            "uidai", "government of india", "वर्ष", "आधार"
        ],
        "patterns": [
            r'\b\d{4}\s\d{4}\s\d{4}\b',   # 4-4-4 Aadhaar number
            r'dob|date of birth',
            r'male|female|transgender'
        ],
        "weight": 1.0
    },
    "pan": {
        "keywords": [
            "permanent account number", "pan", "income tax",
            "govt. of india", "income tax department"
        ],
        "patterns": [
            r'\b[A-Z]{5}[0-9]{4}[A-Z]\b',  # PAN format: ABCDE1234F
            r"father'?s? name",
            r"date of birth"
        ],
        "weight": 1.0
    },
    "gst": {
        "keywords": [
            "goods and services tax", "gst", "gstin",
            "registration certificate", "taxpayer"
        ],
        "patterns": [
            r'\b\d{2}[A-Z]{5}\d{4}[A-Z]\d[Z][A-Z0-9]\b',  # GSTIN format
            r"legal name",
            r"trade name",
            r"place of business"
        ],
        "weight": 1.0
    },
    "udyam": {
        "keywords": [
            "udyam", "udyog aadhaar", "msme", "ministry of micro",
            "udyam registration", "enterprise type"
        ],
        "patterns": [
            r'udyam-[a-z]{2}-\d{2}-\d{7}',  # UDYAM-XX-00-0000000
            r"major activity",
            r"nic code"
        ],
        "weight": 1.0
    },
    "bank_statement": {
        "keywords": [
            "bank statement", "account statement", "balance",
            "debit", "credit", "transaction", "ifsc"
        ],
        "patterns": [
            r'\b[A-Z]{4}0[A-Z0-9]{6}\b',  # IFSC code
            r"closing balance",
            r"opening balance"
        ],
        "weight": 0.9
    },
    "incorporation_certificate": {
        "keywords": [
            "certificate of incorporation", "company", "cin",
            "registrar of companies", "private limited", "llp"
        ],
        "patterns": [
            r'\b[LU]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}\b',  # CIN format
            r"incorporated",
            r"ministry of corporate affairs"
        ],
        "weight": 0.9
    },
    "business_address_proof": {
        "keywords": [
            "electricity bill", "property tax", "rent agreement",
            "lease deed", "municipal", "utility bill"
        ],
        "patterns": [
            r"consumer no|consumer number",
            r"premises",
            r"electricity|water|gas"
        ],
        "weight": 0.8
    }
}

def classify_document(ocr_text: str) -> Tuple[str, float, dict]:
    """
    Classify document type from OCR text.
    Returns: (doc_type, confidence, scores_dict)
    """
    text_lower = ocr_text.lower()
    scores = {}

    for doc_type, signature in DOCUMENT_SIGNATURES.items():
        score = 0.0
        matches = 0
        total_checks = len(signature["keywords"]) + len(signature["patterns"])

        # Keyword matching
        for keyword in signature["keywords"]:
            if keyword.lower() in text_lower:
                score += 1
                matches += 1

        # Pattern matching
        for pattern in signature["patterns"]:
            if re.search(pattern, text_lower, re.IGNORECASE):
                score += 1.5  # Patterns are stronger signals
                matches += 1

        normalized = (score / (total_checks * 1.5)) * signature["weight"]
        scores[doc_type] = round(normalized, 3)

    if not scores or max(scores.values()) == 0:
        return "unknown", 0.0, scores

    best_type = max(scores, key=scores.get)
    confidence = scores[best_type]

    # Require minimum confidence
    if confidence < 0.15:
        return "unknown", confidence, scores

    return best_type, confidence, scores