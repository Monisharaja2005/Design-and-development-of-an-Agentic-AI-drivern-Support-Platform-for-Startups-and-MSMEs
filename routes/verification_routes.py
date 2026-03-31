# routes/verification_routes.py
import os
import uuid
import shutil
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse

from document_verification.ocr_engine import run_ocr
from document_verification.classifier import classify_document
from document_verification.extractor import extract_fields
from document_verification.fraud_detector import run_fraud_detection
from document_verification.cross_validator import cross_validate_documents
from document_verification.confidence_scorer import calculate_confidence
from document_verification.validators.aadhaar import validate_aadhaar
from document_verification.validators.pan import validate_pan
from document_verification.validators.gst import validate_gst
from document_verification.validators.udyam import validate_udyam

router = APIRouter()

UPLOAD_DIR = Path("tmp/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

VALIDATORS = {
    "aadhaar": validate_aadhaar,
    "pan": validate_pan,
    "gst": validate_gst,
    "udyam": validate_udyam,
}

@router.post("/document")
async def verify_single_document(
    file: UploadFile = File(...),
    doc_type_hint: Optional[str] = Form(None),
    scheme_id: Optional[str] = Form(None)
):
    """
    Verify a single document.
    Steps: Upload → OCR → Classify → Extract → Validate → Fraud Check → Score
    """
    # Save uploaded file
    file_id = str(uuid.uuid4())
    ext = Path(file.filename).suffix.lower()
    file_path = UPLOAD_DIR / f"{file_id}{ext}"
    
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    try:
        # Step 1: OCR
        ocr_result = run_ocr(str(file_path))
        if not ocr_result["success"] or not ocr_result.get("text"):
            raise HTTPException(status_code=422, detail="OCR failed — cannot read document")
        
        ocr_text = ocr_result["text"]
        
        # Step 2: Classify
        if doc_type_hint and doc_type_hint in VALIDATORS:
            doc_type = doc_type_hint
            class_confidence = 0.9  # User-provided hint
            class_scores = {}
        else:
            doc_type, class_confidence, class_scores = classify_document(ocr_text)
        
        # Step 3: Extract fields
        fields = extract_fields(doc_type, ocr_text)
        
        # Step 4: Validate
        validator = VALIDATORS.get(doc_type)
        if validator:
            validation_result = validator(fields, ocr_text)
        else:
            validation_result = {
                "valid": True, "issues": [], "warnings": ["No validator for this document type"],
                "score": 60
            }
        
        # Step 5: Fraud detection (images only)
        if ext in ['.jpg', '.jpeg', '.png']:
            fraud_result = run_fraud_detection(str(file_path))
        else:
            fraud_result = {"fraud_detected": False, "fraud_score": 0, "risk_level": "LOW"}
        
        # Step 6: Single-doc confidence (no cross-doc yet)
        cross_placeholder = {"cross_valid_score": 100}
        confidence = calculate_confidence(
            ocr_result, class_confidence, validation_result,
            fraud_result, cross_placeholder
        )
        
        return JSONResponse({
            "file_id": file_id,
            "filename": file.filename,
            "doc_type": doc_type,
            "classification_confidence": round(class_confidence * 100, 1),
            "extracted_fields": fields,
            "validation": validation_result,
            "fraud_detection": fraud_result,
            "confidence": confidence,
            "ocr_text_preview": ocr_text[:300] + "..." if len(ocr_text) > 300 else ocr_text
        })
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup
        if file_path.exists():
            file_path.unlink()


@router.post("/batch")
async def verify_batch_documents(
    files: List[UploadFile] = File(...),
    scheme_id: Optional[str] = Form(None)
):
    """
    Verify multiple documents + cross-validate between them.
    """
    results = {}
    extracted_all = {}
    
    for uploaded_file in files:
        file_id = str(uuid.uuid4())
        ext = Path(uploaded_file.filename).suffix.lower()
        file_path = UPLOAD_DIR / f"{file_id}{ext}"
        
        with open(file_path, "wb") as f:
            shutil.copyfileobj(uploaded_file.file, f)
        
        try:
            ocr_result = run_ocr(str(file_path))
            ocr_text = ocr_result.get("text", "")
            
            doc_type, class_conf, _ = classify_document(ocr_text)
            fields = extract_fields(doc_type, ocr_text)
            
            validator = VALIDATORS.get(doc_type)
            val_result = validator(fields, ocr_text) if validator else {"score": 60, "issues": [], "warnings": []}
            
            fraud_result = {"fraud_detected": False, "fraud_score": 0, "risk_level": "LOW"}
            if ext in ['.jpg', '.jpeg', '.png']:
                fraud_result = run_fraud_detection(str(file_path))
            
            results[doc_type] = {
                "filename": uploaded_file.filename,
                "doc_type": doc_type,
                "fields": fields,
                "validation": val_result,
                "fraud": fraud_result,
                "ocr_success": ocr_result["success"]
            }
            extracted_all[doc_type] = fields
        
        except Exception as e:
            results[uploaded_file.filename] = {"error": str(e)}
        finally:
            if file_path.exists():
                file_path.unlink()
    
    # Cross-document validation
    cross_result = cross_validate_documents(extracted_all)
    
    # Overall batch decision
    all_scores = []
    for doc_type, res in results.items():
        if "validation" in res:
            val = res["validation"]
            fraud = res.get("fraud", {})
            conf = calculate_confidence(
                {"blocks": []}, 0.8, val, fraud, cross_result
            )
            res["confidence"] = conf
            all_scores.append(conf["final_score"])
    
    overall_score = sum(all_scores) / len(all_scores) if all_scores else 0
    
    if overall_score >= 75:
        overall_decision = "APPROVED"
    elif overall_score >= 50:
        overall_decision = "MANUAL_REVIEW"
    else:
        overall_decision = "REJECTED"
    
    return JSONResponse({
        "overall_score": round(overall_score, 1),
        "overall_decision": overall_decision,
        "documents": results,
        "cross_validation": cross_result,
        "total_documents": len(files)
    })


@router.get("/required-docs/{scheme_id}")
async def get_required_documents(scheme_id: str):
    """Return list of documents required for a given scheme"""
    # Load from your schemes JSON
    import json
    schemes_path = Path("schemes_lancedb") / "schemes.json"
    
    if not schemes_path.exists():
        raise HTTPException(status_code=404, detail="Schemes data not found")
    
    with open(schemes_path) as f:
        schemes = json.load(f)
    
    scheme = next((s for s in schemes if str(s.get("scheme_id")) == scheme_id), None)
    
    if not scheme:
        raise HTTPException(status_code=404, detail=f"Scheme {scheme_id} not found")
    
    return {
        "scheme_id": scheme_id,
        "scheme_name": scheme.get("scheme_name"),
        "documents_required": scheme.get("documents_required", []),
        "procedure": scheme.get("procedure", [])
    }