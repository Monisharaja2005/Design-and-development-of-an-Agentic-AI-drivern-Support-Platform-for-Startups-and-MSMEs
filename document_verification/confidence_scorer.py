# document_verification/confidence_scorer.py

def calculate_confidence(
    ocr_result: dict,
    classification_confidence: float,
    validation_result: dict,
    fraud_result: dict,
    cross_validation_result: dict
) -> dict:
    """
    Weighted confidence score combining all signals.
    
    Weights:
    - OCR quality:         15%
    - Classification:      10%
    - Field validation:    35%
    - Fraud detection:     25%
    - Cross-document:      15%
    """
    
    # 1. OCR quality score (0-100)
    ocr_blocks = ocr_result.get("blocks", [])
    if ocr_blocks:
        avg_conf = sum(b.get("confidence", 0.5) for b in ocr_blocks) / len(ocr_blocks)
        ocr_score = avg_conf * 100
    else:
        ocr_score = 40  # Default if no block data
    
    # 2. Classification score
    class_score = classification_confidence * 100
    
    # 3. Validation score (from validators)
    val_score = validation_result.get("score", 50)
    
    # 4. Fraud score (invert — higher fraud = lower confidence)
    fraud_score_raw = fraud_result.get("fraud_score", 0)
    fraud_confidence = max(0, 100 - fraud_score_raw)
    
    # 5. Cross-document score
    cross_score = cross_validation_result.get("cross_valid_score", 100)
    
    # Weighted final score
    final_score = (
        (ocr_score * 0.15) +
        (class_score * 0.10) +
        (val_score * 0.35) +
        (fraud_confidence * 0.25) +
        (cross_score * 0.15)
    )
    
    # Decision thresholds
    if final_score >= 75:
        decision = "APPROVED"
        decision_color = "green"
    elif final_score >= 50:
        decision = "MANUAL_REVIEW"
        decision_color = "yellow"
    else:
        decision = "REJECTED"
        decision_color = "red"
    
    return {
        "final_score": round(final_score, 1),
        "decision": decision,
        "decision_color": decision_color,
        "breakdown": {
            "ocr_quality": round(ocr_score, 1),
            "classification": round(class_score, 1),
            "validation": round(val_score, 1),
            "fraud_check": round(fraud_confidence, 1),
            "cross_document": round(cross_score, 1)
        }
    }