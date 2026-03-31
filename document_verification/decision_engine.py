# document_verification/decision_engine.py
# Orchestrates full verification pipeline + final decision

from typing import Dict, List, Any, Optional
from pathlib import Path
import json
from .ocr_engine import run_ocr
from .classifier import classify_document
from .confidence_scorer import calculate_confidence
from .fraud_detector import run_fraud_detection
from .validators.aadhaar import validate_aadhaar
from .validators.pan import validate_pan
from .validators.gst import validate_gst
from .validators.udyam import validate_udyam
from .cross_validator import cross_validate_documents
from .extractor import extract_fields
from .classifier import classify_document

class DecisionEngine:
    VALIDATORS = {
        "aadhaar": validate_aadhaar,
        "pan": validate_pan,
        "gst": validate_gst,
        "udyam": validate_udyam,
    }
    
    def verify_single_document(self, image_path: str, options: Dict = None) -> Dict:
        """
        Complete single document verification:
        OCR → Classify → Extract → Validate → Fraud → Score → Decide
        """
        options = options or {}
        
        # Step 1: OCR
        print(f"🔍 Running OCR on {image_path}")
        ocr_result = run_ocr(image_path)
        
        if not ocr_result['success']:
            return {
                'status': 'ERROR',
                'reason': f"OCR failed: {ocr_result.get('error', 'Unknown')}",
                'confidence': 0.0
            }
        
        ocr_text = ocr_result['text']
        
        # Step 2: Classify
        doc_type, class_conf, class_scores = classify_document(ocr_text)
        
        # Step 3: Extract
        extracted_fields = extract_fields(doc_type, ocr_text)
        
        # Step 4: Validate
        validator = self.VALIDATORS.get(doc_type)
        validation_result = validator(extracted_fields, ocr_text) if validator else {"score": 50, "valid": False, "issues": ["No validator"]}
        
        # Step 5: Fraud check
        fraud_result = run_fraud_detection(image_path)
        
        # Step 6: Cross placeholder + confidence
        cross_placeholder = {"cross_valid_score": 100}
        score_result = calculate_confidence(
            ocr_result, class_conf, validation_result, fraud_result, cross_placeholder
        )
        
        return {
            'status': 'COMPLETED',
            'doc_type': doc_type,
            'confidence': score_result['overall_confidence'],
            'decision': score_result['recommended_action'],
            'risk_score': 100 - score_result['overall_confidence'],
            'details': score_result['details'],
            'class_scores': class_scores,
            'action_items': self._get_action_items(score_result)
        }
    
    def verify_application_bundle(self, 
                                documents: List[Dict[str, str]],  # [{'type': 'aadhaar', 'path': '...'}, ...]
                                selfie_path: Optional[str] = None) -> Dict:
        """
        Verify complete KYC bundle (Aadhaar + PAN + Address + Selfie)
        """
        if len(documents) == 0:
            return {'status': 'ERROR', 'reason': 'No documents provided'}
        
        ocr_results = []
        for doc in documents:
            path = doc['path']
            ocr_result = run_ocr(path)
            if ocr_result['success']:
                doc['ocr'] = ocr_result
                ocr_results.append(doc)
        
        # Score individuals + cross-validate
        # Simple bundle scoring (TODO: enhance)
        cross_result = cross_validate_documents({doc['type']: doc.get('extracted', {}) for doc in ocr_results})
        avg_conf = sum(ocr_result.get('confidence', 0.5) for ocr_result in ocr_results) / len(ocr_results)
        bundle_result = {
            'bundle_confidence': avg_conf * 100,
            'recommended_action': 'APPROVED' if avg_conf > 0.7 else 'MANUAL_REVIEW',
            'individual_scores': [r for r in ocr_results],
            'cross_validation': cross_result,
            'face_match': {'match': True},  # TODO: integrate face_matcher
        }
        
        return {
            'status': 'COMPLETED',
            'bundle_confidence': bundle_result['bundle_confidence'],
            'decision': bundle_result['recommended_action'],
            'individual_results': bundle_result['individual_scores'],
            'cross_validation': bundle_result['cross_validation'],
            'face_match': bundle_result['face_match'],
            'action_items': self._get_bundle_actions(bundle_result)
        }
    
    def _get_action_items(self, result: dict) -> list[str]:
        """Generate human-readable action items"""
        final_score = result.get('final_score', 50)
        items = []
        
        if final_score < 50:
            items.append("❌ Low confidence - Manual review required")
        elif final_score < 75:
            items.append("⚠️ Medium confidence - Check details")
        else:
            items.append("✅ High confidence - Auto-approved")
        
        # Fraud flag
        if result.get('breakdown', {}).get('fraud_check', 100) < 80:
            items.append("🚨 Potential tampering detected")
        
        return items
        items = []
        
        if confidence < 70:
            items.append("❌ Low confidence - Manual review required")
        elif confidence < 90:
            items.append("⚠️  Medium confidence - Check details")
        else:
            items.append("✅ High confidence - Auto-approved")
        
        # Specific flags
        details = result['details']
        if details['fraud_result']['fraud_likely']:
            items.append("🚨 Potential tampering detected")
        
        if 'issues' in details.get('cross_validation', {}):
            items.extend([f"📋 {issue}" for issue in details['cross_validation']['issues']])
        
        return items
    
    def _get_bundle_actions(self, bundle_result: dict) -> list[str]:
        items = [f"📊 Bundle score: {bundle_result['bundle_confidence']:.1f}%"]
        
        cross = bundle_result['cross_validation']
        if cross.get('issues'):
            items.append("🔍 Cross-doc inconsistencies found")
        
        return items
        
        if bundle_result['face_match'] and not bundle_result['face_match']['match']:
            items.append("👤 Selfie mismatch - Recapture required")
        
        cross = bundle_result['cross_validation']
        if not cross['consistent']:
            items.append("🔍 Cross-doc inconsistencies found")
        
        return items

# CLI Interface
def main():
    """Example usage"""
    engine = DecisionEngine()
    
    # Single doc
    result = engine.verify_single_document("sample_aadhaar.jpg")
    print(json.dumps(result, indent=2, default=str))
    
    # Bundle example
    docs = [
        {'type': 'aadhaar', 'path': 'aadhaar.jpg'},
        {'type': 'pan', 'path': 'pan.jpg'}
    ]
    bundle_result = engine.verify_application_bundle(docs, 'selfie.jpg')
    print(json.dumps(bundle_result, indent=2, default=str))

if __name__ == "__main__":
    main()

