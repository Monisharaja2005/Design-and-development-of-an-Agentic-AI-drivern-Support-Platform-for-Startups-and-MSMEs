#!/usr/bin/env python3
"""
doc_validation_layer.py  — PRODUCTION v3
=========================================
THREE-LAYER VALIDATION PIPELINE:
  Layer 1 — Deep File Sanity  : magic bytes, resolution, blur, aspect ratio  (~5 ms)
  Layer 2 — OCR + Smart Gate  : multi-pass OCR, banned keywords, keyword
                                 scoring, regex extraction, face detection   (~400 ms)
  Layer 3 — AI Vision API     : Gemini / Groq / NVIDIA                      (API call)

Only documents that PASS all layers reach the AI API.
Wrong / blank / irrelevant files are rejected at Layer 1 or 2 — zero API tokens.

INSTALL:
  pip install pytesseract Pillow pymupdf opencv-python-headless
"""

from __future__ import annotations

import base64
import io
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── Auto-configure Tesseract path from .env (Windows) ─────────────────────
def _setup_tesseract():
    try:
        import pytesseract
        # Try env var first
        tess = os.getenv("TESSERACT_CMD", "").strip()
        if tess and Path(tess).exists():
            pytesseract.pytesseract.tesseract_cmd = tess
            return True
        # Auto-discover on Windows common paths
        common = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"C:\Users\{}\AppData\Local\Tesseract-OCR\tesseract.exe".format(os.getenv("USERNAME","user")),
        ]
        for p in common:
            if Path(p).exists():
                pytesseract.pytesseract.tesseract_cmd = p
                return True
        return True  # installed, path will be auto-found on Linux/Mac
    except ImportError:
        return False

_TESSERACT_READY = _setup_tesseract()

logger = logging.getLogger("DOC-LAYER")


# ═══════════════════════════════════════════════════════════════════════════════
#  DOCUMENT PROFILES
# ═══════════════════════════════════════════════════════════════════════════════

DOCUMENT_PROFILES: Dict[str, Dict[str, Any]] = {

    "aadhaar card": {
        "aliases": ["aadhaar", "aadhar", "uid card", "uidai", "unique identification authority"],
        "required_keywords": ["aadhaar", "uidai", "unique identification authority"],
        "any_of_keywords": [],
        "banned_keywords": [
            "permanent account", "income tax department", "passport", "election commission",
            "driving licence", "voter", "gstin", "udyam", "goods and services",
        ],
        "scoring_keywords": [
            "government of india", "enrollment", "date of birth", "address",
            "male", "female", "xxxx", "dob",
        ],
        "regex_patterns": {
            "aadhaar_number":    r"\b\d{4}\s?\d{4}\s?\d{4}\b",
            "enrollment_number": r"\b\d{4}/\d{5}/\d{5}\b",
            "vid_number":        r"\bVID\s*:?\s*\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b",
        },
        "min_regex_hits": 1,
        "face_required": True,
        "doc_type": "identity",
    },

    "pan card": {
        "aliases": ["pan card", "pan", "permanent account number", "income tax pan"],
        "required_keywords": ["permanent account number", "income tax"],
        "any_of_keywords": [],
        "banned_keywords": [
            "aadhaar", "uidai", "election commission", "driving licence",
            "passport", "udyam", "gstin", "goods and services",
        ],
        "scoring_keywords": [
            "govt of india", "father", "date of birth",
            "signature", "income tax department",
        ],
        "regex_patterns": {
            "pan_number": r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
        },
        "min_regex_hits": 1,
        "face_required": True,
        "doc_type": "identity",
    },

    "passport": {
        "aliases": ["passport", "republic of india", "travel document", "indian passport"],
        "required_keywords": ["passport", "republic of india"],
        "any_of_keywords": [],
        "banned_keywords": [
            "aadhaar", "uidai", "pan card", "permanent account",
            "election commission", "driving licence", "udyam", "gstin",
        ],
        "scoring_keywords": [
            "surname", "nationality", "place of birth", "date of issue",
            "date of expiry", "personal no", "given name",
        ],
        "regex_patterns": {
            "passport_number": r"\b[A-Z][0-9]{7}\b",
            "mrz_line":        r"P<IND[A-Z<]{39}",
        },
        "min_regex_hits": 1,
        "face_required": True,
        "doc_type": "identity",
    },

    "driving license": {
        "aliases": [
            "driving licence", "driving license", "dl", "motor vehicle",
            "transport department", "rto",
        ],
        "required_keywords": ["driving", "licence", "license", "transport", "motor vehicles"],
        "any_of_keywords": [],
        "banned_keywords": [
            "aadhaar", "uidai", "permanent account", "election commission",
            "passport", "gstin", "udyam",
        ],
        "scoring_keywords": [
            "blood group", "class of vehicle", "validity", "badge no",
            "rto", "date of birth", "cov",
        ],
        "regex_patterns": {
            "dl_number":    r"\b[A-Z]{2}[-\s]?\d{2}[-\s]?\d{4}[-\s]?\d{7}\b",
            "dl_number_v2": r"\b[A-Z]{2}\d{13}\b",
        },
        "min_regex_hits": 0,
        "face_required": True,
        "doc_type": "identity",
    },

    "voter id": {
        "aliases": [
            "voter id", "voter card", "epic", "election commission",
            "electors photo identity card", "electoral photo",
        ],
        "required_keywords": ["election commission", "elector", "voter"],
        "any_of_keywords": [],
        "banned_keywords": [
            "aadhaar", "uidai", "permanent account", "passport",
            "driving licence", "gstin", "udyam",
        ],
        "scoring_keywords": [
            "constituency", "assembly", "part no", "serial no",
            "polling station", "state",
        ],
        "regex_patterns": {
            "epic_number": r"\b[A-Z]{3}[0-9]{7}\b",
        },
        "min_regex_hits": 1,
        "face_required": True,
        "doc_type": "identity",
    },

    "udyam registration certificate": {
        "aliases": [
            "udyam", "udyog aadhaar", "msme registration",
            "msme certificate", "udyam certificate",
        ],
        "required_keywords": ["udyam"],
        "any_of_keywords": [
            ["ministry", "micro", "msme", "enterprise", "udyam registration"],
        ],
        "banned_keywords": [
            "aadhaar", "uidai", "permanent account", "election commission",
            "passport", "driving licence",
        ],
        "scoring_keywords": [
            "udyam registration number", "enterprise name",
            "major activity", "nic code", "investment", "turnover",
        ],
        "regex_patterns": {
            "udyam_number": r"\bUDYAM-[A-Z]{2}-\d{2}-\d{7}\b",
        },
        "min_regex_hits": 1,
        "face_required": False,
        "doc_type": "certificate",
    },

    "dpiit startup recognition certificate": {
        "aliases": [
            "dpiit", "startup india", "startup recognition",
            "department for promotion", "startup certificate",
        ],
        "required_keywords": ["startup india", "dpiit", "department for promotion"],
        "any_of_keywords": [],
        "banned_keywords": [
            "aadhaar", "permanent account", "election commission",
            "passport", "gstin", "udyam", "driving licence",
        ],
        "scoring_keywords": [
            "certificate of recognition", "recognised startup",
            "industry and internal trade", "date of recognition",
        ],
        "regex_patterns": {
            "dpiit_number": r"\bDIPP\d+\b",
            "startup_id":   r"\bSTARTUP[-_]\d+\b",
        },
        "min_regex_hits": 0,
        "face_required": False,
        "doc_type": "certificate",
    },

    "gst certificate": {
        "aliases": [
            "gst", "gstin", "goods and services tax",
            "gst registration certificate", "gst reg",
        ],
        "required_keywords": ["goods and services tax", "gstin"],
        "any_of_keywords": [
            ["registration", "certificate", "taxpayer"],
        ],
        "banned_keywords": [
            "aadhaar", "uidai", "permanent account", "election commission",
            "passport", "udyam", "driving licence",
        ],
        "scoring_keywords": [
            "central tax", "state tax", "trade name",
            "constitution of business", "date of liability",
            "type of registration", "principal place",
        ],
        "regex_patterns": {
            "gstin": r"\b\d{2}[A-Z]{5}\d{4}[A-Z][A-Z0-9]Z[A-Z0-9]\b",
        },
        "min_regex_hits": 1,
        "face_required": False,
        "doc_type": "certificate",
    },

    "company incorporation certificate": {
        "aliases": [
            "certificate of incorporation", "incorporation certificate",
            "mca", "registrar of companies", "cin certificate",
        ],
        "required_keywords": ["certificate of incorporation", "registrar of companies"],
        "any_of_keywords": [],
        "banned_keywords": [
            "aadhaar", "permanent account", "election commission",
            "passport", "gstin", "udyam",
        ],
        "scoring_keywords": [
            "companies act", "cin", "corporate identity number",
            "date of incorporation", "type of company",
        ],
        "regex_patterns": {
            "cin": r"\b[LUO]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}\b",
        },
        "min_regex_hits": 0,
        "face_required": False,
        "doc_type": "certificate",
    },

    "partnership deed": {
        "aliases": ["partnership deed", "deed of partnership", "llp agreement"],
        "required_keywords": ["partnership", "deed"],
        "any_of_keywords": [["partners", "firm", "business"]],
        "banned_keywords": [
            "aadhaar", "uidai", "permanent account", "election commission",
            "passport", "gstin", "udyam",
        ],
        "scoring_keywords": [
            "profit sharing", "capital contribution", "dissolution",
            "working partner", "firm name",
        ],
        "regex_patterns": {},
        "min_regex_hits": 0,
        "face_required": False,
        "doc_type": "certificate",
    },

    "memorandum of association": {
        "aliases": ["memorandum of association", "moa"],
        "required_keywords": ["memorandum of association"],
        "any_of_keywords": [],
        "banned_keywords": [
            "aadhaar", "permanent account", "election commission",
            "passport", "gstin", "articles of association",
        ],
        "scoring_keywords": [
            "objects clause", "liability", "capital clause",
            "subscribers", "name clause", "registered office",
        ],
        "regex_patterns": {},
        "min_regex_hits": 0,
        "face_required": False,
        "doc_type": "certificate",
    },

    "articles of association": {
        "aliases": ["articles of association", "aoa"],
        "required_keywords": ["articles of association"],
        "any_of_keywords": [],
        "banned_keywords": [
            "aadhaar", "permanent account", "election commission",
            "passport", "gstin", "memorandum of association",
        ],
        "scoring_keywords": [
            "directors", "shares", "meetings", "regulations",
            "board", "transfer of shares",
        ],
        "regex_patterns": {},
        "min_regex_hits": 0,
        "face_required": False,
        "doc_type": "certificate",
    },

    "bank statement": {
        "aliases": [
            "bank statement", "account statement", "passbook",
            "transaction statement", "bank account statement",
            "bank account details", "cancelled cheque", "cheque",
        ],
        "required_keywords": [],
        "any_of_keywords": [["account", "bank", "ifsc", "balance", "transaction", "debit", "credit", "cheque"]],
        "banned_keywords": [
            "aadhaar", "uidai", "permanent account number", "election commission",
            "passport", "udyam", "gstin", "driving licence",
        ],
        "scoring_keywords": [
            "opening balance", "closing balance", "statement period",
            "branch", "account holder", "cheque no",
        ],
        "regex_patterns": {
            "account_number": r"(?:A/?c\.?\s*No\.?|Account\s*No\.?)\s*[:\-]?\s*(\d{9,18})",
            "ifsc_code":      r"\b[A-Z]{4}0[A-Z0-9]{6}\b",
        },
        "min_regex_hits": 1,
        "face_required": False,
        "doc_type": "financial",
    },

    "cancelled cheque": {
        "aliases": [
            "cancelled cheque", "canceled cheque", "void cheque",
            "cheque leaf", "blank cheque",
        ],
        "required_keywords": ["cancelled", "cheque"],
        "any_of_keywords": [],
        "banned_keywords": [
            "aadhaar", "uidai", "permanent account number",
            "election commission", "passport", "udyam",
        ],
        "scoring_keywords": ["account no", "ifsc", "micr", "bank", "branch"],
        "regex_patterns": {
            "ifsc_code": r"\b[A-Z]{4}0[A-Z0-9]{6}\b",
            "micr_code": r"\b\d{9}\b",
            "cheque_no": r"\b\d{6}\b",
        },
        "min_regex_hits": 0,
        "face_required": False,
        "doc_type": "financial",
    },

    "income tax return": {
        "aliases": [
            "itr", "income tax return", "itr acknowledgement",
            "form itr", "income tax filing",
        ],
        "required_keywords": ["income tax"],
        "any_of_keywords": [["return", "itr", "acknowledgement", "assessment"]],
        "banned_keywords": [
            "aadhaar", "uidai", "election commission", "passport",
            "udyam", "gstin", "driving licence",
        ],
        "scoring_keywords": [
            "assessment year", "acknowledgement number",
            "total income", "tax payable", "refund", "filing date",
        ],
        "regex_patterns": {
            "pan_number":         r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
            "assessment_year":    r"\b20\d{2}[-\u2013]\d{2}\b",
            "acknowledgement_no": r"\b\d{15}\b",
        },
        "min_regex_hits": 1,
        "face_required": False,
        "doc_type": "financial",
    },

    "balance sheet": {
        "aliases": ["balance sheet", "statement of financial position"],
        "required_keywords": ["balance sheet"],
        "any_of_keywords": [["assets", "liabilities", "equity", "capital"]],
        "banned_keywords": [
            "aadhaar", "permanent account", "election commission",
            "passport", "udyam", "gstin", "driving licence",
        ],
        "scoring_keywords": [
            "fixed assets", "current assets", "reserves", "surplus",
            "borrowings", "trade payables", "shareholders",
        ],
        "regex_patterns": {
            "amount": r"(?:Rs\.?|\u20b9)\s*[\d,]+(?:\.\d{2})?",
        },
        "min_regex_hits": 0,
        "face_required": False,
        "doc_type": "financial",
    },

    "profit and loss statement": {
        "aliases": [
            "profit and loss", "p&l", "income statement",
            "statement of profit and loss", "p l account",
        ],
        "required_keywords": ["profit", "loss"],
        "any_of_keywords": [["revenue", "income", "expenses", "turnover"]],
        "banned_keywords": [
            "aadhaar", "permanent account", "election commission",
            "passport", "udyam", "gstin", "driving licence", "balance sheet",
        ],
        "scoring_keywords": [
            "gross profit", "net profit", "operating expenses",
            "depreciation", "ebitda", "tax", "revenue from operations",
        ],
        "regex_patterns": {
            "amount": r"(?:Rs\.?|\u20b9)\s*[\d,]+(?:\.\d{2})?",
        },
        "min_regex_hits": 0,
        "face_required": False,
        "doc_type": "financial",
    },

    "electricity bill": {
        "aliases": [
            "electricity bill", "power bill", "eb bill", "bescom", "tneb",
            "msedcl", "energy bill", "electricity charges",
        ],
        "required_keywords": ["electricity"],
        "any_of_keywords": [["consumer", "bill", "meter", "units", "kwh", "board"]],
        "banned_keywords": [
            "aadhaar", "permanent account", "election commission",
            "passport", "udyam", "gstin", "driving licence",
        ],
        "scoring_keywords": [
            "kwh", "units consumed", "meter reading", "due date",
            "billing period", "connected load", "tariff",
        ],
        "regex_patterns": {
            "consumer_number": r"(?:Consumer|Account|CA)\s*(?:No\.?|Number)\s*[:\-]?\s*([\dA-Z\/]+)",
            "bill_amount":     r"(?:Rs\.?|\u20b9)\s*[\d,]+(?:\.\d{2})?",
            "meter_number":    r"(?:Meter\s*No\.?|Meter\s*Number)\s*[:\-]?\s*([\dA-Z]+)",
        },
        "min_regex_hits": 0,
        "face_required": False,
        "doc_type": "address",
    },

    "water bill": {
        "aliases": ["water bill", "water charges", "municipal water", "water tax"],
        "required_keywords": ["water"],
        "any_of_keywords": [["consumer", "municipal", "corporation", "supply", "charges", "board"]],
        "banned_keywords": [
            "aadhaar", "permanent account", "election commission",
            "passport", "udyam", "gstin", "electricity",
        ],
        "scoring_keywords": [
            "connection no", "ward", "water meter", "usage", "monthly charges",
        ],
        "regex_patterns": {},
        "min_regex_hits": 0,
        "face_required": False,
        "doc_type": "address",
    },

    "gas bill": {
        "aliases": [
            "gas bill", "lpg bill", "png bill", "piped natural gas",
            "indane", "bharat gas", "hp gas", "mgl",
        ],
        "required_keywords": ["gas"],
        "any_of_keywords": [["cylinder", "consumer", "connection", "lpg", "png", "bill"]],
        "banned_keywords": [
            "aadhaar", "permanent account", "election commission",
            "passport", "udyam", "electricity", "water",
        ],
        "scoring_keywords": [
            "subsidy", "distributor", "connection number",
            "bp number", "invoice", "delivery",
        ],
        "regex_patterns": {},
        "min_regex_hits": 0,
        "face_required": False,
        "doc_type": "address",
    },

    "rental agreement": {
        "aliases": [
            "rental agreement", "rent agreement", "lease deed",
            "tenancy agreement", "leave and licence",
        ],
        "required_keywords": ["rent", "agreement"],
        "any_of_keywords": [["tenant", "lessor", "lessee", "landlord", "licensee"]],
        "banned_keywords": [
            "aadhaar", "permanent account", "election commission",
            "passport", "udyam", "gstin",
        ],
        "scoring_keywords": [
            "monthly rent", "security deposit", "tenure",
            "premises", "notice period", "stamp duty",
        ],
        "regex_patterns": {
            "rent_amount":     r"(?:Rs\.?|\u20b9)\s*[\d,]+(?:\.\d{2})?",
            "duration_months": r"\b(?:11|12|24|36)\s*months\b",
        },
        "min_regex_hits": 0,
        "face_required": False,
        "doc_type": "address",
    },

    "property tax receipt": {
        "aliases": [
            "property tax", "house tax", "municipal tax",
            "property tax receipt", "property tax bill",
        ],
        "required_keywords": ["property tax"],
        "any_of_keywords": [["receipt", "municipal", "corporation", "assessment", "ward"]],
        "banned_keywords": [
            "aadhaar", "permanent account", "election commission",
            "passport", "udyam", "gstin", "electricity", "water",
        ],
        "scoring_keywords": [
            "property id", "demand", "zone", "plot no",
            "owner name", "tax period", "assessment no",
        ],
        "regex_patterns": {},
        "min_regex_hits": 0,
        "face_required": False,
        "doc_type": "address",
    },

    "telephone bill": {
        "aliases": [
            "telephone bill", "mobile bill", "broadband bill",
            "jio bill", "airtel bill", "bsnl bill", "vi bill",
        ],
        "required_keywords": ["bill"],
        "any_of_keywords": [["mobile", "telephone", "broadband", "postpaid", "telecom", "data"]],
        "banned_keywords": [
            "aadhaar", "permanent account", "election commission",
            "passport", "udyam", "electricity", "water", "gas",
        ],
        "scoring_keywords": [
            "plan", "usage", "data", "voice", "recharge",
            "billing cycle", "subscriber", "invoice",
        ],
        "regex_patterns": {
            "mobile_number": r"\b[6-9]\d{9}\b",
            "bill_amount":   r"(?:Rs\.?|\u20b9)\s*[\d,]+(?:\.\d{2})?",
        },
        "min_regex_hits": 0,
        "face_required": False,
        "doc_type": "address",
    },

    "passport photo": {
        "aliases": [
            "passport photo", "passport size photo", "photograph", "photo",
            "passport-size photographs", "photographs",
        ],
        "required_keywords": [],
        "any_of_keywords": [],
        "banned_keywords": [],
        "scoring_keywords": [],
        "regex_patterns": {},
        "min_regex_hits": 0,
        "face_required": False,
        "doc_type": "other",
        "lenient": True,
        "accept_image_always": True,
    },

    "signature image": {
        "aliases": ["signature", "sign", "wet signature"],
        "required_keywords": [],
        "any_of_keywords": [],
        "banned_keywords": [],
        "scoring_keywords": [],
        "regex_patterns": {},
        "min_regex_hits": 0,
        "face_required": False,
        "doc_type": "other",
    },

    "founders cv": {
        "aliases": [
            "cv", "resume", "curriculum vitae", "biodata", "founder cv",
            "founders cv", "co-founder cv", "director cv", "profile",
        ],
        "required_keywords": [],
        "any_of_keywords": [
            ["experience", "education", "skills", "work", "employment",
             "qualification", "objective", "summary", "profile", "career"],
        ],
        "banned_keywords": [
            "aadhaar", "uidai", "gstin", "udyam", "election commission",
        ],
        "scoring_keywords": [
            "years of experience", "bachelor", "master", "degree",
            "university", "college", "email", "phone", "linkedin",
        ],
        "regex_patterns": {
            "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "phone": r"[\+]?[0-9]{10,13}",
        },
        "min_regex_hits": 0,
        "face_required": False,
        "doc_type": "other",
        "lenient": True,
    },

    "board resolution": {
        "aliases": ["board resolution", "resolution passed", "board meeting resolution"],
        "required_keywords": ["board", "resolution"],
        "any_of_keywords": [["directors", "resolved", "meeting", "company"]],
        "banned_keywords": [
            "aadhaar", "permanent account", "election commission",
            "passport", "gstin", "udyam",
        ],
        "scoring_keywords": [
            "authorized", "signatory", "seal", "director",
            "chairman", "secretary", "date of meeting",
        ],
        "regex_patterns": {},
        "min_regex_hits": 0,
        "face_required": False,
        "doc_type": "certificate",
    },

    "government approval certificate": {
        "aliases": [
            "government approval", "approval certificate",
            "no objection certificate", "noc", "clearance certificate",
        ],
        "required_keywords": ["certificate"],
        "any_of_keywords": [["approval", "government", "authority", "granted", "noc", "clearance"]],
        "banned_keywords": [
            "aadhaar", "permanent account", "election commission",
            "passport", "gstin", "udyam",
        ],
        "scoring_keywords": [
            "reference no", "valid upto", "issued by",
            "granted to", "conditions",
        ],
        "regex_patterns": {
            "ref_number": r"\b[A-Z]{2,5}[-/]\d{4,8}\b",
        },
        "min_regex_hits": 0,
        "face_required": False,
        "doc_type": "certificate",
    },
}


def _resolve_profile(doc_name: str) -> Optional[Dict[str, Any]]:
    norm = re.sub(r"[^a-z0-9 ]", " ", doc_name.lower()).strip()
    norm = re.sub(r"\s+", " ", norm)

    if norm in DOCUMENT_PROFILES:
        return DOCUMENT_PROFILES[norm]

    best, best_len = None, 0
    for profile in DOCUMENT_PROFILES.values():
        for alias in profile.get("aliases", []):
            if alias in norm and len(alias) > best_len:
                best, best_len = profile, len(alias)
    if best:
        return best

    norm_words = set(norm.split())
    for key, profile in DOCUMENT_PROFILES.items():
        key_words = set(key.split())
        if key_words and len(key_words & norm_words) / len(key_words) >= 0.6:
            return profile

    return None


# ═══════════════════════════════════════════════════════════════════════════════
#  LAYER 1 — Deep File Sanity
# ═══════════════════════════════════════════════════════════════════════════════

SUPPORTED_MIME_TYPES = {
    "application/pdf", "image/jpeg", "image/jpg",
    "image/png", "image/webp",
}
SUPPORTED_SUFFIXES = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}
MIN_FILE_BYTES     = 5 * 1024
MAX_FILE_BYTES     = 25 * 1024 * 1024

MAGIC_BYTES = {
    "jpeg": b"\xff\xd8\xff",
    "png":  b"\x89PNG\r\n\x1a\n",
    "pdf":  b"%PDF-",
}


def _check_magic_bytes(data: bytes, suffix: str) -> Optional[str]:
    s = suffix.lstrip(".")
    if s in ("jpg", "jpeg"):
        if not data.startswith(MAGIC_BYTES["jpeg"]):
            return "File is not a valid JPEG. It may be renamed or corrupted."
    elif s == "png":
        if not data.startswith(MAGIC_BYTES["png"]):
            return "File is not a valid PNG. It may be renamed or corrupted."
    elif s == "pdf":
        if not data.startswith(MAGIC_BYTES["pdf"]):
            return "File is not a valid PDF. It may be renamed or corrupted."
    elif s == "webp":
        if not (data.startswith(b"RIFF") and data[8:12] == b"WEBP"):
            return "File is not a valid WebP. It may be renamed or corrupted."
    return None


def _check_image_quality(data: bytes) -> Tuple[List[Dict], List[Dict]]:
    """Returns (hard_errors, warnings) from image analysis."""
    errors, warnings = [], []
    try:
        from PIL import Image, ImageStat
        img    = Image.open(io.BytesIO(data))
        w, h   = img.size
        gray   = img.convert("L")
        stat   = ImageStat.Stat(gray)
        mean   = stat.mean[0]
        stddev = stat.stddev[0]
        ratio  = w / h if h > 0 else 0

        # Resolution too low
        if w < 150 or h < 150:
            errors.append({
                "message": f"Image resolution too low ({w}x{h} px). "
                           "Upload a clear scan of at least 300x300 px.",
                "source": "layer1_resolution", "layer": "1",
            })

        # Extreme aspect ratio — not a document
        if ratio > 8 or (ratio < 0.1 and ratio > 0):
            errors.append({
                "message": f"Image shape is unusual (ratio {ratio:.1f}:1). "
                           "This does not look like a document page.",
                "source": "layer1_aspect", "layer": "1",
            })

        # Blank image (nearly uniform — no content)
        if stddev < 8:
            errors.append({
                "message": "The uploaded image appears blank or empty. "
                           "Please upload a clear document photo.",
                "source": "layer1_blank", "layer": "1",
            })

        # Too dark
        elif mean < 20:
            errors.append({
                "message": "The image is too dark to read. "
                           "Please upload a well-lit document photo.",
                "source": "layer1_dark", "layer": "1",
            })

        # Too bright / overexposed
        elif mean > 248 and stddev < 15:
            warnings.append({
                "message": "Image appears overexposed. Text may be hard to read.",
                "source": "layer1_bright", "layer": "1", "severity": "warning",
            })

        # Thumbnail-sized
        if 150 <= w < 350 and 150 <= h < 350:
            warnings.append({
                "message": f"Image appears small ({w}x{h} px). "
                           "A higher-resolution scan will improve verification accuracy.",
                "source": "layer1_small", "layer": "1", "severity": "warning",
            })

    except Exception as e:
        logger.warning(f"Image quality check failed: {e}")

    return errors, warnings


def _check_pdf_sanity(data: bytes) -> Tuple[List[Dict], List[Dict]]:
    errors, warnings = [], []
    try:
        import fitz
        doc = fitz.open(stream=data, filetype="pdf")
        if doc.page_count == 0:
            errors.append({
                "message": "PDF has no pages. Please upload a valid document.",
                "source": "layer1_pdf_empty", "layer": "1",
            })
        if doc.is_encrypted:
            errors.append({
                "message": "PDF is password-protected. Please upload an unlocked PDF.",
                "source": "layer1_pdf_encrypted", "layer": "1",
            })
    except Exception as e:
        logger.warning(f"PDF sanity check failed: {e}")
    return errors, warnings


def layer1_sanity(
    file_name: str,
    mime_type: str,
    file_bytes: bytes,
) -> Tuple[bool, List[Dict]]:
    errors   = []
    warnings = []
    suffix   = Path(file_name or "").suffix.lower()
    mt       = mime_type.lower().replace("image/jpg", "image/jpeg")
    size     = len(file_bytes)

    # 1. Format
    if mt not in SUPPORTED_MIME_TYPES and suffix not in SUPPORTED_SUFFIXES:
        errors.append({
            "message": f"'{suffix or mt}' is not supported. "
                       "Please upload PDF, JPG, PNG, or WebP.",
            "source": "layer1_format", "layer": "1",
        })
        return False, errors

    # 2. Size
    if size < MIN_FILE_BYTES:
        errors.append({
            "message": f"File too small ({size // 1024} KB). "
                       "Please upload a clear, complete document (min 5 KB).",
            "source": "layer1_size_min", "layer": "1",
        })
        return False, errors

    if size > MAX_FILE_BYTES:
        errors.append({
            "message": f"File too large ({size // (1024*1024)} MB). Maximum is 25 MB.",
            "source": "layer1_size_max", "layer": "1",
        })
        return False, errors

    # 3. Magic bytes
    magic_err = _check_magic_bytes(file_bytes, suffix)
    if magic_err:
        errors.append({"message": magic_err, "source": "layer1_magic", "layer": "1"})
        return False, errors

    # 4. Image quality checks
    if suffix in (".jpg", ".jpeg", ".png", ".webp"):
        img_errors, img_warnings = _check_image_quality(file_bytes)
        errors.extend(img_errors)
        warnings.extend(img_warnings)

    # 5. PDF sanity
    if suffix == ".pdf" or mt == "application/pdf":
        pdf_errors, pdf_warnings = _check_pdf_sanity(file_bytes)
        errors.extend(pdf_errors)
        warnings.extend(pdf_warnings)

    passed = len(errors) == 0
    return passed, errors + warnings


# ═══════════════════════════════════════════════════════════════════════════════
#  LAYER 2 — OCR + Smart Gate
# ═══════════════════════════════════════════════════════════════════════════════

def _pdf_to_image_bytes(file_bytes: bytes) -> Optional[bytes]:
    try:
        import fitz
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        if doc.page_count == 0:
            return None
        pix = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2), colorspace=fitz.csRGB)
        return pix.tobytes("jpeg")
    except ImportError:
        logger.warning("PyMuPDF not installed — pip install pymupdf")
        return None
    except Exception as e:
        logger.warning(f"PDF to image failed: {e}")
        return None


def _ocr_cv2(image_bytes: bytes) -> Optional[str]:
    """Full preprocessing pipeline with cv2 + dual-pass Tesseract."""
    try:
        import cv2
        import numpy as np
        import pytesseract
        from PIL import Image as PILImage

        nparr = np.frombuffer(image_bytes, np.uint8)
        img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            pil = PILImage.open(io.BytesIO(image_bytes)).convert("RGB")
            img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

        # Upscale if small — boosts OCR word count dramatically
        h, w = img.shape[:2]
        if max(h, w) < 1200:
            scale = 1600 / max(h, w)
            img = cv2.resize(img, (int(w * scale), int(h * scale)),
                             interpolation=cv2.INTER_CUBIC)

        gray     = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray, h=10)

        # Adaptive threshold — handles uneven lighting / phone photos
        thresh = cv2.adaptiveThreshold(
            denoised, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 31, 10,
        )

        # Deskew up to 30°
        coords = np.column_stack(np.where(thresh < 200))
        if len(coords) > 100:
            angle = cv2.minAreaRect(coords)[-1]
            angle = -(90 + angle) if angle < -45 else -angle
            if 0.5 < abs(angle) < 30:
                Mh, Mw = thresh.shape
                M = cv2.getRotationMatrix2D((Mw // 2, Mh // 2), angle, 1.0)
                thresh = cv2.warpAffine(thresh, M, (Mw, Mh),
                                        flags=cv2.INTER_CUBIC,
                                        borderMode=cv2.BORDER_REPLICATE)

        # Morphological closing — joins broken characters
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        pil_final = PILImage.fromarray(thresh)

        # Two passes: auto-layout + single uniform block — take the richer one
        t1 = pytesseract.image_to_string(pil_final, config="--psm 3 --oem 3")
        t2 = pytesseract.image_to_string(pil_final, config="--psm 6 --oem 3")
        text = t1 if len(t1.split()) >= len(t2.split()) else t2

        logger.info(f"OCR [cv2]: {len(text.split())} words")
        return text.lower()

    except ImportError:
        return None
    except Exception as e:
        logger.warning(f"cv2 OCR error: {e}")
        return None


def _ocr_pil(image_bytes: bytes) -> Optional[str]:
    """PIL-only OCR — no cv2 needed."""
    try:
        import pytesseract
        from PIL import Image, ImageEnhance, ImageFilter, ImageOps

        img = Image.open(io.BytesIO(image_bytes))
        w, h = img.size
        if max(w, h) < 1200:
            scale = 1600 / max(w, h)
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        img = img.convert("L")
        img = ImageOps.autocontrast(img, cutoff=2)
        img = ImageEnhance.Sharpness(img).enhance(2.0)
        img = img.filter(ImageFilter.MedianFilter(3))

        text = pytesseract.image_to_string(img, config="--psm 3 --oem 3")
        logger.info(f"OCR [PIL]: {len(text.split())} words")
        return text.lower()

    except ImportError:
        import sys
        logger.warning(
            f"pytesseract not found in current Python ({sys.executable}). "
            f"Run: {sys.executable} -m pip install pytesseract  "
            f"(make sure you use the same Python your server runs with)"
        )
        return "OCR_UNAVAILABLE"
    except Exception as e:
        logger.warning(f"PIL OCR error: {e}")
        return None


def run_ocr(image_bytes: bytes) -> str:
    """Best-available OCR. Returns lowercase text, '' on failure, 'OCR_UNAVAILABLE' if no engine."""
    result = _ocr_cv2(image_bytes)
    if result is not None:
        return result
    result = _ocr_pil(image_bytes)
    if result is not None:
        return result
    return ""


def _detect_faces(image_bytes: bytes) -> int:
    """Returns face count, or -1 if cv2 unavailable."""
    try:
        import cv2
        import numpy as np
        nparr = np.frombuffer(image_bytes, np.uint8)
        img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return -1
        h, w = img.shape[:2]
        if max(h, w) < 500:
            scale = 700 / max(h, w)
            img = cv2.resize(img, (int(w * scale), int(h * scale)))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        cas  = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        faces = cas.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=4,
            minSize=(25, 25), flags=cv2.CASCADE_SCALE_IMAGE,
        )
        count = len(faces) if hasattr(faces, "__len__") else 0
        logger.info(f"Face detection: {count} face(s)")
        return count
    except ImportError:
        return -1
    except Exception as e:
        logger.warning(f"Face detection failed: {e}")
        return -1


def _score_ocr(ocr_text: str, profile: Dict, doc_name: str) -> Tuple[bool, List[Dict], Dict, int]:
    """
    Smart scoring of OCR text against profile.
    Returns: (passed, errors, extracted_fields, score_0_to_100)
    """
    errors    = []
    extracted = {}
    score     = 0

    # ── Banned keywords — fast-fail (wrong document type detected) ───────────
    for bkw in profile.get("banned_keywords", []):
        if bkw.lower() in ocr_text:
            errors.append({
                "message": (
                    f"The uploaded file appears to be a different type of document "
                    f"(found '{bkw}'). You selected '{doc_name}'. "
                    "Please upload the correct document."
                ),
                "source": "layer2_banned_keyword", "layer": "2",
            })
            return False, errors, {}, 0

    # ── Required keywords — at least one must match ───────────────────────────
    required = profile.get("required_keywords", [])
    if required:
        found = [kw for kw in required if kw.lower() in ocr_text]
        if not found:
            errors.append({
                "message": (
                    f"This does not appear to be a '{doc_name}'. "
                    f"None of the expected identifiers found "
                    f"({', '.join(required[:3])}). "
                    "Please upload the correct document."
                ),
                "source": "layer2_required_keyword", "layer": "2",
            })
            return False, errors, {}, 0
        score += min(40, 12 * len(found))

    # ── any_of groups — each group: at least 1 word must match ───────────────
    for group in profile.get("any_of_keywords", []):
        if not group:
            continue
        found_in_group = [kw for kw in group if kw.lower() in ocr_text]
        if not found_in_group:
            errors.append({
                "message": (
                    f"Missing expected content for '{doc_name}'. "
                    f"Could not find any of: {', '.join(group[:4])}."
                ),
                "source": "layer2_any_of_keyword", "layer": "2",
            })
            return False, errors, {}, 0
        score += 10

    # ── Scoring keywords — boost confidence ───────────────────────────────────
    bonus = sum(5 for kw in profile.get("scoring_keywords", []) if kw.lower() in ocr_text)
    score += min(20, bonus)

    # ── Regex field extraction ────────────────────────────────────────────────
    hit_count = 0
    for field_name, pattern in profile.get("regex_patterns", {}).items():
        m = re.search(pattern, ocr_text, re.IGNORECASE)
        if m:
            hit_count += 1
            score     += 8
            val = m.group(1) if (m.lastindex and m.lastindex >= 1) else m.group(0)
            extracted[field_name] = val.strip()

    min_hits = profile.get("min_regex_hits", 0)
    if min_hits > 0 and hit_count < min_hits:
        missing = [k for k in profile.get("regex_patterns", {}) if k not in extracted]
        errors.append({
            "message": (
                f"Could not find required document identifiers "
                f"({', '.join(missing[:2])}) in the uploaded file. "
                "Ensure the full document is visible and image is clear."
            ),
            "source": "layer2_regex", "layer": "2",
        })
        return False, errors, extracted, score

    # ── Watermark / Specimen detection ───────────────────────────────────────
    wm = re.search(
        r"\b(specimen|sample|void|dummy|test document|not valid|for demo|sample only)\b",
        ocr_text, re.IGNORECASE,
    )
    if wm:
        errors.append({
            "message": (
                f"Document has a '{wm.group(0).upper()}' watermark. "
                "Please upload an original valid document."
            ),
            "source": "layer2_watermark", "layer": "2",
        })
        return False, errors, extracted, 0

    return True, [], extracted, min(score, 100)


def layer2_ocr_gate(
    image_bytes: Optional[bytes],
    file_bytes:  bytes,
    mime_type:   str,
    file_name:   str,
    profile:     Dict,
    doc_name:    str,
) -> Tuple[bool, List[Dict], Dict, int, str]:
    """
    Returns: (passed, errors, extracted_fields, ocr_score, ocr_text)
    """
    # Prepare OCR image
    if mime_type == "application/pdf" or file_name.lower().endswith(".pdf"):
        ocr_img = _pdf_to_image_bytes(file_bytes)
    else:
        ocr_img = image_bytes or file_bytes

    ocr_text = run_ocr(ocr_img) if ocr_img else ""

    if ocr_text == "OCR_UNAVAILABLE":
        logger.warning("pytesseract not installed — Layer 2 skipped")
        return True, [], {}, 0, "OCR_UNAVAILABLE"

    # Lenient mode — accept any valid image immediately (passport photo etc.)
    if profile.get("accept_image_always") and ocr_img:
        logger.info(f"Lenient mode: accepting {doc_name} as image upload")
        return True, [], {"_accepted": "image_upload"}, 80, ocr_text or ""

    if not ocr_text.strip():
        logger.info("OCR returned empty — deferring to AI")
        # For lenient docs, accept even without OCR text
        if profile.get("lenient"):
            return True, [], {}, 60, ""
        return True, [], {}, 0, ""

    # Score and validate
    passed, errors, extracted, score = _score_ocr(ocr_text, profile, doc_name)
    if not passed:
        # For lenient docs, downgrade to warning instead of hard fail
        if profile.get("lenient"):
            logger.info(f"Lenient mode: accepting {doc_name} despite OCR mismatch")
            return True, [], extracted, 55, ocr_text
        return False, errors, extracted, score, ocr_text

    # Face detection — only for strict identity docs, skip for scanned PDFs
    if profile.get("face_required") and ocr_img and not profile.get("lenient"):
        face_count = _detect_faces(ocr_img)
        if face_count > 1:
            extracted["_face_count_warning"] = f"{face_count} faces detected"

    return True, [], extracted, score, ocr_text


# ═══════════════════════════════════════════════════════════════════════════════
#  VALIDATION STEP (popup progress)
# ═══════════════════════════════════════════════════════════════════════════════

class ValidationStep:
    def __init__(self, step: str, label: str, status: str, detail: str = ""):
        self.step   = step
        self.label  = label
        self.status = status
        self.detail = detail

    def to_dict(self) -> Dict:
        return {"step": self.step, "label": self.label,
                "status": self.status, "detail": self.detail}


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN ENTRY — layered_validate()
# ═══════════════════════════════════════════════════════════════════════════════

async def layered_validate(
    file,
    doc_name:  str,
    scheme:    Any,
    language:  str,
    t0:        float,
    _run_vision_ai=None,
    _vision_prompt=None,
    _parse_vision_json=None,
    _pdf_to_image_b64=None,
    localize_validation_payload=None,
    normalize_language_code=None,
    resolve_scheme_reference=None,
) -> Dict[str, Any]:

    steps: List[ValidationStep] = []

    def add_step(step, label, status, detail=""):
        for s in steps:
            if s.step == step:
                s.label  = label
                s.status = status
                s.detail = detail
                return
        steps.append(ValidationStep(step, label, status, detail))

    def build_response(*, is_valid, verdict, errors, warnings,
                       confidence, summary, detected_type="",
                       extracted_fields=None, gov_body="", ocr_score=0) -> Dict:
        return {
            "success":         True,
            "status":          "valid" if is_valid else "error",
            "isValid":         is_valid,
            "verdict":         verdict,
            "documentType":    detected_type or doc_name,
            "govBody":         gov_body,
            "extractedFields": extracted_fields or {},
            "errors":          errors,
            "warnings":        warnings,
            "confidenceScore": confidence,
            "summary":         summary,
            "ocrScore":        ocr_score,
            "validationSteps": [s.to_dict() for s in steps],
            "processingMs":    int((time.time() - t0) * 1000),
        }

    # ── Read file ──────────────────────────────────────────────────────────────
    file_bytes = await file.read()
    mime_type  = (file.content_type or "application/octet-stream").lower()
    file_name  = file.filename or "uploaded-file"
    file_size  = len(file_bytes)
    if mime_type == "image/jpg":
        mime_type = "image/jpeg"

    lang_code   = normalize_language_code(language) if normalize_language_code else "en"
    scheme_data = resolve_scheme_reference(raw_scheme=scheme) if resolve_scheme_reference else {}
    scheme_name = (scheme_data or {}).get("scheme_name", "Selected Scheme")

    extracted_fields: Dict = {}
    ocr_score: int         = 0
    soft_warnings: List    = []

    # ══════════════════════════════════════════════════════════════════════════
    #  LAYER 1
    # ══════════════════════════════════════════════════════════════════════════
    add_step("file_sanity", "File Format & Quality Check", "running")
    l1_passed, l1_issues = layer1_sanity(file_name, mime_type, file_bytes)

    soft_warnings = [i for i in l1_issues if i.get("severity") == "warning"]
    hard_errors   = [i for i in l1_issues if i.get("severity") != "warning"]

    if not l1_passed:
        first = hard_errors[0] if hard_errors else l1_issues[0]
        add_step("file_sanity", "File Format & Quality Check", "failed", first["message"])
        result = build_response(
            is_valid=False, verdict="invalid",
            errors=hard_errors, warnings=soft_warnings,
            confidence=0, summary=first["message"],
        )
        return await localize_validation_payload(result, lang_code) if localize_validation_payload else result

    size_kb = file_size // 1024
    warn_note = f" | {len(soft_warnings)} quality warning(s)" if soft_warnings else ""
    add_step("file_sanity", "File Format & Quality Check", "passed",
             f"{mime_type.split('/')[-1].upper()} | {size_kb} KB{warn_note}")

    # ══════════════════════════════════════════════════════════════════════════
    #  LAYER 2
    # ══════════════════════════════════════════════════════════════════════════
    profile          = _resolve_profile(doc_name)
    ocr_did_validate = False

    if profile is None:
        add_step("ocr_extraction",  "OCR Text Extraction",          "skipped",
                 f"No validation profile for '{doc_name}' — delegating to AI.")
        add_step("keyword_check",   "Keyword & Pattern Verification", "skipped",
                 "No profile registered.")
    else:
        add_step("ocr_extraction", "OCR Text Extraction", "running")
        img_bytes_raw = file_bytes if mime_type.startswith("image/") else None

        l2_passed, l2_errors, extracted_fields, ocr_score, ocr_text_raw = layer2_ocr_gate(
            image_bytes=img_bytes_raw,
            file_bytes=file_bytes,
            mime_type=mime_type,
            file_name=file_name,
            profile=profile,
            doc_name=doc_name,
        )

        ocr_unavailable  = (ocr_text_raw == "OCR_UNAVAILABLE")
        ocr_empty        = (not ocr_text_raw.strip() or ocr_unavailable)
        ocr_did_validate = (not ocr_empty and l2_passed and ocr_score > 0)

        # OCR step status
        if ocr_unavailable:
            add_step("ocr_extraction", "OCR Text Extraction", "skipped",
                     "pytesseract not installed — run: pip install pytesseract")
        elif not ocr_text_raw.strip():
            add_step("ocr_extraction", "OCR Text Extraction", "skipped",
                     "No text found in image — AI will verify.")
        else:
            wc = len(ocr_text_raw.split())
            add_step("ocr_extraction", "OCR Text Extraction", "passed",
                     f"{wc} words extracted | score {ocr_score}/100")

        # Keyword / pattern check status
        if not ocr_empty:
            if not l2_passed:
                src   = l2_errors[0].get("source", "") if l2_errors else ""
                msg   = l2_errors[0]["message"] if l2_errors else "Validation failed"
                label = "Keyword & Pattern Verification"

                if "face" in src:
                    add_step("keyword_check", label, "passed", "Keywords matched")
                    add_step("face_detection", "Face Detection", "failed", msg)
                elif "regex" in src:
                    add_step("keyword_check", label, "passed", "Keywords matched")
                    add_step("regex_check", "Field Pattern Validation", "failed", msg)
                else:
                    add_step("keyword_check", label, "failed", msg)

                result = build_response(
                    is_valid=False, verdict="invalid",
                    errors=l2_errors, warnings=soft_warnings,
                    confidence=10, summary=msg,
                    extracted_fields=extracted_fields, ocr_score=ocr_score,
                )
                return await localize_validation_payload(result, lang_code) if localize_validation_payload else result
            else:
                fc = len([k for k in extracted_fields if not k.startswith("_")])
                add_step("keyword_check", "Keyword & Pattern Verification", "passed",
                         f"Document keywords confirmed | {fc} field(s) extracted")

    # ══════════════════════════════════════════════════════════════════════════
    #  LAYER 3 — AI Vision
    # ══════════════════════════════════════════════════════════════════════════
    add_step("ai_vision", "AI Document Verification", "running")

    if mime_type.startswith("image/"):
        image_b64   = base64.b64encode(file_bytes).decode()
        vision_mime = mime_type
    elif mime_type == "application/pdf" or file_name.lower().endswith(".pdf"):
        image_b64   = _pdf_to_image_b64(file_bytes) if _pdf_to_image_b64 else None
        vision_mime = "image/jpeg"
    else:
        image_b64   = None
        vision_mime = "image/jpeg"

    if image_b64 and _run_vision_ai and _vision_prompt and _parse_vision_json:
        try:
            prompt = _vision_prompt(doc_name, scheme_name)
            raw    = await _run_vision_ai(image_b64, vision_mime, prompt)
            ai     = _parse_vision_json(raw)

            if not ai or not isinstance(ai, dict):
                raise ValueError(f"Unparseable AI response: {str(raw)[:120]}")

            verdict  = str(ai.get("verdict") or "invalid").lower().strip()
            detected = str(ai.get("detectedType") or ai.get("documentType") or doc_name).strip()
            conf     = int(ai.get("confidenceScore") or 75)
            ai_errs  = [e for e in (ai.get("errors") or [])
                        if isinstance(e, str) and e.strip() and "filename" not in e.lower()]
            ai_warns = [w for w in (ai.get("warnings") or []) if isinstance(w, str) and w.strip()]
            summary  = str(ai.get("summary") or "").strip()

            ai_fields = ai.get("extractedFields") or {}
            if not isinstance(ai_fields, dict):
                ai_fields = {}

            merged = {
                **{k: v for k, v in extracted_fields.items() if not k.startswith("_")},
                **ai_fields,
            }
            # OCR score boosts final confidence
            conf = min(99, conf + (ocr_score // 10))

            if verdict == "mismatch":
                msg = (
                    f"Wrong document. You selected '{doc_name}' "
                    f"but uploaded '{detected}'. "
                    "Please upload the correct document."
                )
                add_step("ai_vision", "AI Document Verification", "failed", msg)
                result = build_response(
                    is_valid=False, verdict="mismatch",
                    errors=[{"message": msg, "source": "ai"}],
                    warnings=soft_warnings, confidence=conf,
                    summary=f"Expected {doc_name}, got {detected}.",
                    detected_type=detected, extracted_fields=merged,
                    gov_body=ai.get("govBody", ""), ocr_score=ocr_score,
                )
            elif verdict == "valid" and not ai_errs:
                add_step("ai_vision", "AI Document Verification", "passed",
                         f"Verified as '{detected}' — {conf}% confidence")
                result = build_response(
                    is_valid=True, verdict="valid", errors=[],
                    warnings=[{"message": w, "source": "ai"} for w in ai_warns] + soft_warnings,
                    confidence=conf,
                    summary=summary or f"{doc_name} verified successfully.",
                    detected_type=detected, extracted_fields=merged,
                    gov_body=ai.get("govBody", ""), ocr_score=ocr_score,
                )
            else:
                err_msgs = ai_errs or ["Could not verify. Upload a clearer copy."]
                add_step("ai_vision", "AI Document Verification", "failed", err_msgs[0])
                result = build_response(
                    is_valid=False, verdict="invalid",
                    errors=[{"message": e, "source": "ai"} for e in err_msgs],
                    warnings=[{"message": w, "source": "ai"} for w in ai_warns] + soft_warnings,
                    confidence=conf, summary=summary or err_msgs[0],
                    detected_type=detected, extracted_fields=merged,
                    gov_body=ai.get("govBody", ""), ocr_score=ocr_score,
                )

            logger.info(
                f"[validate] '{doc_name}' → {verdict} | detected='{detected}' | "
                f"conf={conf} | ocr={ocr_score} | {int((time.time()-t0)*1000)}ms"
            )
            return await localize_validation_payload(result, lang_code) if localize_validation_payload else result

        except Exception as e:
            logger.error(f"AI Vision failed: {e}")
            add_step("ai_vision", "AI Document Verification", "skipped",
                     f"AI check failed: {str(e)[:80]}")

    # ── Fallback ──────────────────────────────────────────────────────────────
    if ocr_did_validate:
        add_step("ai_vision", "AI Document Verification", "skipped",
                 "No AI key — accepted via OCR + keyword validation.")
        result = build_response(
            is_valid=True, verdict="valid", errors=[],
            warnings=[{
                "message": "No AI key configured. Accepted via OCR + regex validation only.",
                "source": "system",
            }] + soft_warnings,
            confidence=min(70, 40 + ocr_score // 2),
            summary=f"{doc_name} accepted via OCR validation.",
            extracted_fields={k: v for k, v in extracted_fields.items() if not k.startswith("_")},
            ocr_score=ocr_score,
        )
    else:
        add_step("ai_vision", "AI Document Verification", "failed",
                 "Cannot verify — OCR unavailable and AI check failed.")
        result = build_response(
            is_valid=False, verdict="invalid",
            errors=[{
                "message": (
                    "Document could not be verified. "
                    "Install pytesseract (pip install pytesseract) for offline OCR, "
                    "or add a Gemini/Groq/NVIDIA key to your .env file."
                ),
                "source": "system",
            }],
            warnings=soft_warnings, confidence=0,
            summary="Verification failed — no OCR or AI available.",
        )

    return await localize_validation_payload(result, lang_code) if localize_validation_payload else result