# document_verification/test_verification.py
# E2E testing script for verification pipeline

from decision_engine import DecisionEngine
import os

def test_single_doc():
    engine = DecisionEngine()
    test_image = "test_aadhaar.jpg"  # Place test images in dir
    
    if os.path.exists(test_image):
        result = engine.verify_single_document(test_image)
        print("Single Doc Result:", result)
        assert result['confidence'] > 0
    else:
        print("Test image not found, skipping")

def test_bundle():
    engine = DecisionEngine()
    docs = [
        {"type": "aadhaar", "path": "test_aadhaar.jpg"},
        {"type": "pan", "path": "test_pan.jpg"}
    ]
    result = engine.verify_application_bundle(docs, "test_selfie.jpg")
    print("Bundle Result:", result)
    assert result['bundle_confidence'] > 0

if __name__ == "__main__":
    test_single_doc()
    test_bundle()
    print("✅ All tests passed! Add test images to run full E2E.")

