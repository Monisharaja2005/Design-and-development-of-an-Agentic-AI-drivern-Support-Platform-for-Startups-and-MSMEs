from document_verification.ocr_engine import run_ocr
from document_verification.classifier import classify_document
from document_verification.extractor import extract_fields
from document_verification.validators.aadhaar import validate_aadhaar
from document_verification.validators.pan import validate_pan
from document_verification.validators.gst import validate_gst
from document_verification.validators.udyam import validate_udyam
import os
import uuid
from pathlib import Path
from typing import Dict, Any

VALIDATORS = {
    "aadhaar": validate_aadhaar,
    "pan": validate_pan,
    "gst": validate_gst,
    "udyam": validate_udyam,
}

async def process_document(file: Any, doc_name: str, scheme: str = "") -> Dict[str, Any]:
    """
    Full AI pipeline for Task 2:
    UploadFile → OCR → Classify → Extract → Validate → Confidence → Standard Format
    """
    # 1. Save temp file
    temp_dir = Path("tmp")
    temp_dir.mkdir(exist_ok=True)
    temp_path = temp_dir / f"temp_{uuid.uuid4().hex}_{file.filename}"
    
    with open(temp_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    try:
        # 2. OCR
        ocr_result = run_ocr(str(temp_path))
        text = ocr_result.get("text", "")
        
        if not text.strip():
            return {
                "status": "rejected",
                "document_type": "unknown",
                "confidence": 0.0,
                "extracted_data": {},
                "validation": {"is_valid": False, "errors": ["No text extracted"]}
            }
        
        # 3. Classify
        doc_type, class_conf, _ = classify_document(text)
        
        # 4. Extract
        fields = extract_fields(doc_type, text)
        
        # 5. Validate
        validator = VALIDATORS.get(doc_type)
        if validator:
            validation = validator(fields, text)
        else:
            validation = {"is_valid": False, "errors": ["No validator"], "score": 0}
        
        # 6. Confidence (0-1.0)
        confidence = min(1.0, (class_conf + validation.get("score", 0) / 100) / 2)
        
        # 7. Task 5 Format
        status = "verified" if validation.get("is_valid", False) and confidence > 0.7 else "rejected"
        
        return {
            "status": status,
            "document_type": doc_type,
            "confidence": round(confidence, 2),
            "extracted_data": fields,
            "validation": {
                "is_valid": validation.get("valid", validation.get("is_valid", False)),
                "errors": validation.get("issues", validation.get("errors", []))
            }
        }
    
    finally:
        if temp_path.exists():
            temp_path.unlink()
