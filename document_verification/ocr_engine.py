# document_verification/ocr_engine.py
# OCR Engine: PaddleOCR (primary) + Tesseract (fallback)
# Supports PDF, JPG, PNG

import os
import cv2
import numpy as np
from PIL import Image
import pytesseract
from pathlib import Path

# PaddleOCR - lazy load to avoid startup cost
_paddle_ocr = None

def get_paddle_ocr():
    global _paddle_ocr
    if _paddle_ocr is None:
        try:
            from paddleocr import PaddleOCR
            _paddle_ocr = PaddleOCR(
                use_angle_cls=True,
                lang='en',
                show_log=False,
                use_gpu=False  # CPU mode - free
            )
        except ImportError:
            _paddle_ocr = None
    return _paddle_ocr

def preprocess_image(image_path: str) -> np.ndarray:
    """
    Preprocess image for better OCR accuracy:
    - Grayscale
    - Denoise
    - Adaptive threshold
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot read image: {image_path}")
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    # Adaptive threshold for uneven lighting
    thresh = cv2.adaptiveThreshold(
        denoised, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
    return thresh

def extract_text_paddle(image_path: str) -> dict:
    """Primary OCR using PaddleOCR with bounding boxes"""
    ocr = get_paddle_ocr()
    if ocr is None:
        return {"success": False, "text": "", "blocks": []}
    
    try:
        result = ocr.ocr(image_path, cls=True)
        full_text = ""
        blocks = []
        
        if result and result[0]:
            for line in result[0]:
                bbox, (text, confidence) = line
                full_text += text + "\n"
                blocks.append({
                    "text": text,
                    "confidence": round(confidence, 3),
                    "bbox": bbox
                })
        
        return {
            "success": True,
            "text": full_text.strip(),
            "blocks": blocks,
            "engine": "paddleocr"
        }
    except Exception as e:
        return {"success": False, "text": "", "blocks": [], "error": str(e)}

def extract_text_tesseract(image_path: str) -> dict:
    """Fallback OCR using Tesseract"""
    try:
        preprocessed = preprocess_image(image_path)
        pil_img = Image.fromarray(preprocessed)
        
        # PSM 6 = uniform block of text, good for documents
        config = '--psm 6 --oem 3'
        text = pytesseract.image_to_string(pil_img, config=config, lang='eng')
        
        # Also get word-level data for confidence
        data = pytesseract.image_to_data(
            pil_img, config=config,
            output_type=pytesseract.Output.DICT
        )
        
        blocks = []
        for i, word in enumerate(data['text']):
            if word.strip() and int(data['conf'][i]) > 30:
                blocks.append({
                    "text": word,
                    "confidence": int(data['conf'][i]) / 100,
                    "bbox": [
                        data['left'][i], data['top'][i],
                        data['width'][i], data['height'][i]
                    ]
                })
        
        return {
            "success": True,
            "text": text.strip(),
            "blocks": blocks,
            "engine": "tesseract"
        }
    except Exception as e:
        return {"success": False, "text": "", "blocks": [], "error": str(e)}

def extract_text_from_pdf(pdf_path: str) -> dict:
    """Extract text from PDF - try direct text first, then OCR each page"""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        full_text = ""
        
        for page in doc:
            text = page.get_text()
            if text.strip():
                full_text += text
            else:
                # Scanned PDF - render and OCR
                pix = page.get_pixmap(dpi=200)
                img_array = np.frombuffer(pix.samples, dtype=np.uint8)
                img_array = img_array.reshape(pix.height, pix.width, pix.n)
                
                # Save temp and OCR
                temp_path = f"/tmp/page_{page.number}.png"
                cv2.imwrite(temp_path, img_array)
                result = run_ocr(temp_path)
                full_text += result.get("text", "")
        
        doc.close()
        return {"success": True, "text": full_text.strip(), "engine": "pymupdf+ocr"}
    except Exception as e:
        return {"success": False, "text": "", "error": str(e)}

def run_ocr(file_path: str) -> dict:
    """
    Main OCR dispatcher:
    1. Try PaddleOCR
    2. Fallback to Tesseract
    3. Handle PDF separately
    """
    ext = Path(file_path).suffix.lower()
    
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    
    # Try PaddleOCR first
    result = extract_text_paddle(file_path)
    
    if not result["success"] or len(result.get("text", "")) < 20:
        # Fallback to Tesseract
        result = extract_text_tesseract(file_path)
    
    return result