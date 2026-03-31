# document_verification/face_matcher.py
# DeepFace face matching: Document ID photo vs Live Selfie
# Returns similarity score 0-1

from deepface import DeepFace
import cv2
import numpy as np
from typing import Dict, Tuple
from pathlib import Path

class FaceMatcher:
    def __init__(self, model: str = 'VGG-Face', detector_backend: str = 'opencv'):
        self.model = model
        self.detector_backend = detector_backend
    
    def extract_face_region(self, image_path: str) -> str:
        """Crop and save largest face region for better matching"""
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Cannot load image: {image_path}")
        
        # Detect faces
        faces = DeepFace.extract_faces(img_path=image_path, detector_backend='opencv', 
                                     enforce_detection=False)
        
        if not faces:
            raise ValueError("No face detected")
        
        # Use largest face (highest confidence)
        largest_face = max(faces['face'], key=lambda f: f.get('confidence', 0))
        
        # Save cropped face temp
        face_img = largest_face['face']
        temp_path = f"/tmp/matched_face_{Path(image_path).stem}.jpg"
        cv2.imwrite(temp_path, face_img)
        
        return temp_path
    
    def verify_faces(self, doc_image: str, selfie_image: str) -> Dict:
        """Compare document face vs selfie"""
        try:
            # Extract faces
            doc_face = self.extract_face_region(doc_image)
            selfie_face = self.extract_face_region(selfie_image)
            
            # DeepFace verify
            result = DeepFace.verify(
                doc_face, selfie_image,
                model_name=self.model,
                detector_backend=self.detector_backend,
                enforce_detection=False,
                distance_metric='cosine',
                threshold=0.40  # Adjustable
            )
            
            # Cleanup temps
            for path in [doc_face]:
                Path(path).unlink(missing_ok=True)
            
            return {
                'match': result['verified'],
                'distance': result['distance'],
                'similarity': 1 - result['distance'],  # 0-1 scale
                'model_used': self.model,
                'confidence': result.get('identity', 0.0)
            }
            
        except Exception as e:
            return {
                'match': False,
                'error': str(e),
                'similarity': 0.0,
                'confidence': 0.0
            }

def batch_face_match(pairs: List[Tuple[str, str]]) -> List[Dict]:
    """Batch verify multiple doc-selfie pairs"""
    matcher = FaceMatcher()
    results = []
    for doc, selfie in pairs:
        results.append(matcher.verify_faces(doc, selfie))
    return results

# Standalone usage
def match_doc_selfie(doc_path: str, selfie_path: str) -> Dict:
    """Simple wrapper"""
    matcher = FaceMatcher()
    return matcher.verify_faces(doc_path, selfie_path)

