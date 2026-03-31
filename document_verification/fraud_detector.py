# document_verification/fraud_detector.py
# OpenCV-based tampering / fraud detection

import cv2
import numpy as np
from pathlib import Path

def detect_copy_move_forgery(image: np.ndarray) -> dict:
    """Detect copy-move forgery using SIFT feature matching"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    try:
        sift = cv2.SIFT_create()
        kp, desc = sift.detectAndCompute(gray, None)
        
        if desc is None or len(kp) < 10:
            return {"detected": False, "confidence": 0, "reason": "insufficient features"}
        
        # Self-matching to find duplicated regions
        bf = cv2.BFMatcher()
        matches = bf.knnMatch(desc, desc, k=3)
        
        suspicious = 0
        for m in matches:
            if len(m) >= 2:
                # Skip self-match (distance = 0)
                non_self = [x for x in m if x.distance > 0.01]
                if len(non_self) >= 2 and non_self[0].distance < 0.75 * non_self[1].distance:
                    suspicious += 1
        
        ratio = suspicious / max(len(kp), 1)
        detected = ratio > 0.3
        
        return {
            "detected": detected,
            "confidence": round(ratio, 3),
            "suspicious_features": suspicious,
            "total_features": len(kp)
        }
    except Exception as e:
        return {"detected": False, "confidence": 0, "error": str(e)}

def detect_noise_inconsistency(image: np.ndarray) -> dict:
    """Detect unnatural noise patterns indicating digital editing"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float64)
    
    # ELA-like analysis: compress and compare
    # Divide into blocks and check noise variance
    h, w = gray.shape
    block_size = 16
    variances = []
    
    for y in range(0, h - block_size, block_size):
        for x in range(0, w - block_size, block_size):
            block = gray[y:y+block_size, x:x+block_size]
            variances.append(np.var(block))
    
    if not variances:
        return {"detected": False, "confidence": 0}
    
    var_array = np.array(variances)
    mean_var = np.mean(var_array)
    std_var = np.std(var_array)
    
    # Suspicious if some blocks have very different noise (edited patches)
    outliers = np.sum(np.abs(var_array - mean_var) > 3 * std_var)
    outlier_ratio = outliers / len(variances)
    
    detected = outlier_ratio > 0.1
    
    return {
        "detected": detected,
        "confidence": round(outlier_ratio, 3),
        "outlier_blocks": int(outliers),
        "total_blocks": len(variances)
    }

def detect_ela(image_path: str) -> dict:
    """Error Level Analysis for JPEG tampering"""
    try:
        import io
        from PIL import Image, ImageChops, ImageEnhance
        
        original = Image.open(image_path).convert('RGB')
        
        # Save at lower quality and compare
        buffer = io.BytesIO()
        original.save(buffer, 'JPEG', quality=75)
        buffer.seek(0)
        compressed = Image.open(buffer).convert('RGB')
        
        # ELA difference
        ela = ImageChops.difference(original, compressed)
        ela = ImageEnhance.Brightness(ela).enhance(20)
        
        ela_array = np.array(ela)
        ela_mean = np.mean(ela_array)
        ela_max = np.max(ela_array)
        
        # High ELA values in certain regions indicate tampering
        tampered = ela_mean > 15 or ela_max > 180
        
        return {
            "detected": bool(tampered),
            "confidence": round(min(ela_mean / 30, 1.0), 3),
            "ela_mean": round(float(ela_mean), 2),
            "ela_max": round(float(ela_max), 2)
        }
    except Exception as e:
        return {"detected": False, "confidence": 0, "error": str(e)}

def check_metadata(image_path: str) -> dict:
    """Check EXIF metadata for inconsistencies"""
    try:
        from PIL import Image
        import piexif
        
        img = Image.open(image_path)
        exif_data = img._getexif()
        
        if exif_data is None:
            return {
                "suspicious": True,
                "reason": "No EXIF data — may be screenshot or edited",
                "confidence": 0.3
            }
        
        # Check for editing software tags
        software_tag = 305  # EXIF tag for Software
        software = exif_data.get(software_tag, "")
        
        editing_software = ["photoshop", "gimp", "paint", "editor", "lightroom"]
        if any(sw in str(software).lower() for sw in editing_software):
            return {
                "suspicious": True,
                "reason": f"Editing software detected: {software}",
                "confidence": 0.8
            }
        
        return {"suspicious": False, "reason": "Metadata looks clean", "confidence": 0.1}
    
    except Exception as e:
        return {"suspicious": False, "reason": "Could not read metadata", "confidence": 0.1}

def run_fraud_detection(image_path: str) -> dict:
    """
    Run all fraud detection checks.
    Returns combined fraud score and individual results.
    """
    results = {}
    
    try:
        image = cv2.imread(image_path)
        if image is None:
            return {"fraud_detected": False, "fraud_score": 0, "error": "Cannot read image"}
        
        # Run all checks
        results["copy_move"] = detect_copy_move_forgery(image)
        results["noise"] = detect_noise_inconsistency(image)
        results["ela"] = detect_ela(image_path)
        results["metadata"] = check_metadata(image_path)
        
        # Aggregate fraud score (0-100, higher = more suspicious)
        fraud_indicators = []
        
        if results["copy_move"].get("detected"):
            fraud_indicators.append(results["copy_move"]["confidence"] * 40)
        
        if results["noise"].get("detected"):
            fraud_indicators.append(results["noise"]["confidence"] * 30)
        
        if results["ela"].get("detected"):
            fraud_indicators.append(results["ela"]["confidence"] * 20)
        
        if results["metadata"].get("suspicious"):
            fraud_indicators.append(results["metadata"]["confidence"] * 10)
        
        fraud_score = min(sum(fraud_indicators), 100)
        fraud_detected = fraud_score > 30
        
        return {
            "fraud_detected": fraud_detected,
            "fraud_score": round(fraud_score, 1),
            "risk_level": (
                "HIGH" if fraud_score > 60
                else "MEDIUM" if fraud_score > 30
                else "LOW"
            ),
            "checks": results
        }
    
    except Exception as e:
        return {"fraud_detected": False, "fraud_score": 0, "error": str(e)}