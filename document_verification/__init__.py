"""
Document Verification Engine - Fixed Imports for KARIOS
"""
__version__ = "1.0.0"

# Core pipeline functions matching verification_routes.py
from .ocr_engine import run_ocr
from .classifier import classify_document  
from .extractor import extract_fields
from .fraud_detector import run_fraud_detection
from .cross_validator import cross_validate_documents
from .confidence_scorer import calculate_confidence

# Validators
from .validators.aadhaar import validate_aadhaar
from .validators.pan import validate_pan
from .validators.gst import validate_gst
from .validators.udyam import validate_udyam

__all__ = [
    "run_ocr", "classify_document", "extract_fields",
    "run_fraud_detection", "cross_validate_documents", 
    "calculate_confidence",
    "validate_aadhaar", "validate_pan", "validate_gst", "validate_udyam"
]
