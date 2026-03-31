# document_verification/extractor.py
# Extracts structured fields from OCR text using spaCy + regex

import re
import spacy
from typing import Optional

# Load spaCy model (download: python -m spacy download en_core_web_sm)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = None

# ─── AADHAAR EXTRACTION ───────────────────────────────────────
def extract_aadhaar_fields(text: str) -> dict:
    fields = {}
    
    # Aadhaar number: 4-4-4 digits (masked or full)
    aadhaar_match = re.search(r'\b(\d{4}[\s-]?\d{4}[\s-]?\d{4})\b', text)
    if aadhaar_match:
        fields["aadhaar_number"] = aadhaar_match.group(1).replace(" ", "").replace("-", "")
    
    # Name: Usually first line with capital words
    name_match = re.search(
        r'(?:name[:\s]*)?([A-Z][a-z]+ (?:[A-Z][a-z]+ )?[A-Z][a-z]+)', text
    )
    if name_match:
        fields["name"] = name_match.group(1).strip()
    
    # DOB
    dob_match = re.search(
        r'(?:dob|date of birth|जन्म तिथि)[:\s]*(\d{2}[/-]\d{2}[/-]\d{4})', 
        text, re.IGNORECASE
    )
    if dob_match:
        fields["dob"] = dob_match.group(1)
    
    # Gender
    gender_match = re.search(r'\b(male|female|transgender)\b', text, re.IGNORECASE)
    if gender_match:
        fields["gender"] = gender_match.group(1).upper()
    
    # Address - everything after "Address" keyword
    addr_match = re.search(r'(?:address|पता)[:\s]*(.{10,150})', text, re.IGNORECASE | re.DOTALL)
    if addr_match:
        fields["address"] = addr_match.group(1).strip()[:200]
    
    return fields

# ─── PAN EXTRACTION ───────────────────────────────────────────
def extract_pan_fields(text: str) -> dict:
    fields = {}
    
    # PAN number: ABCDE1234F
    pan_match = re.search(r'\b([A-Z]{5}[0-9]{4}[A-Z])\b', text)
    if pan_match:
        fields["pan_number"] = pan_match.group(1)
    
    # Name (usually bold line before Father's name)
    name_match = re.search(r'name[:\s]*([A-Z\s]+?)(?:\n|father)', text, re.IGNORECASE)
    if name_match:
        fields["name"] = name_match.group(1).strip().title()
    
    # Father's name
    father_match = re.search(r"father'?s?\s*name[:\s]*([A-Z\s]+?)(?:\n|dob|date)", text, re.IGNORECASE)
    if father_match:
        fields["father_name"] = father_match.group(1).strip().title()
    
    # DOB
    dob_match = re.search(r'(?:dob|date of birth)[:\s]*(\d{2}[/-]\d{2}[/-]\d{4})', text, re.IGNORECASE)
    if dob_match:
        fields["dob"] = dob_match.group(1)
    
    return fields

# ─── GST EXTRACTION ───────────────────────────────────────────
def extract_gst_fields(text: str) -> dict:
    fields = {}
    
    # GSTIN: 15-char alphanumeric
    gstin_match = re.search(r'\b(\d{2}[A-Z]{5}\d{4}[A-Z]\d[Z][A-Z0-9])\b', text)
    if gstin_match:
        fields["gstin"] = gstin_match.group(1)
        # State code is first 2 digits
        fields["state_code"] = gstin_match.group(1)[:2]
    
    # Legal/Trade name
    legal_match = re.search(r'legal name[:\s]*([A-Za-z0-9\s&.,\-]+?)(?:\n|trade)', text, re.IGNORECASE)
    if legal_match:
        fields["legal_name"] = legal_match.group(1).strip()
    
    trade_match = re.search(r'trade name[:\s]*([A-Za-z0-9\s&.,\-]+?)(?:\n)', text, re.IGNORECASE)
    if trade_match:
        fields["trade_name"] = trade_match.group(1).strip()
    
    # Registration date
    date_match = re.search(r'(?:registration date|effective date)[:\s]*(\d{2}[/-]\d{2}[/-]\d{4})', text, re.IGNORECASE)
    if date_match:
        fields["registration_date"] = date_match.group(1)
    
    # Business type
    biz_match = re.search(r'constitution[:\s]*([A-Za-z\s]+?)(?:\n)', text, re.IGNORECASE)
    if biz_match:
        fields["business_type"] = biz_match.group(1).strip()
    
    return fields

# ─── UDYAM EXTRACTION ─────────────────────────────────────────
def extract_udyam_fields(text: str) -> dict:
    fields = {}
    
    # Udyam registration number
    udyam_match = re.search(r'(UDYAM-[A-Z]{2}-\d{2}-\d{7})', text, re.IGNORECASE)
    if udyam_match:
        fields["udyam_number"] = udyam_match.group(1).upper()
    
    # Enterprise name
    name_match = re.search(r'name of enterprise[:\s]*([A-Za-z0-9\s&.,\-]+?)(?:\n)', text, re.IGNORECASE)
    if name_match:
        fields["enterprise_name"] = name_match.group(1).strip()
    
    # Type: Micro/Small/Medium
    type_match = re.search(r'\b(micro|small|medium)\b', text, re.IGNORECASE)
    if type_match:
        fields["enterprise_type"] = type_match.group(1).upper()
    
    # Major activity
    activity_match = re.search(r'major activity[:\s]*([A-Za-z\s]+?)(?:\n)', text, re.IGNORECASE)
    if activity_match:
        fields["major_activity"] = activity_match.group(1).strip()
    
    return fields

# ─── MAIN DISPATCHER ──────────────────────────────────────────
def extract_fields(doc_type: str, ocr_text: str) -> dict:
    """Extract structured fields based on document type"""
    extractors = {
        "aadhaar": extract_aadhaar_fields,
        "pan": extract_pan_fields,
        "gst": extract_gst_fields,
        "udyam": extract_udyam_fields,
    }
    
    extractor = extractors.get(doc_type)
    if extractor:
        fields = extractor(ocr_text)
        # Use spaCy for any remaining name/org entities if available
        if nlp and "name" not in fields:
            doc = nlp(ocr_text[:500])
            for ent in doc.ents:
                if ent.label_ == "PERSON" and "name" not in fields:
                    fields["name"] = ent.text
                elif ent.label_ == "ORG" and "org_name" not in fields:
                    fields["org_name"] = ent.text
        return fields
    
    return {}