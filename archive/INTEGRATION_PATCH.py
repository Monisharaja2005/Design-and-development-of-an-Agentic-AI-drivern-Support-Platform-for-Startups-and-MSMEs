"""
INTEGRATION PATCH  —  ai_scheme_server.py
==========================================
Apply these 3 surgical changes.  Nothing else needs to change.

──────────────────────────────────────────────────────────────────────────────
CHANGE 1  (top of file, after existing imports)
──────────────────────────────────────────────────────────────────────────────
Add this import right after:
    from fastapi.staticfiles import StaticFiles
"""

# ── ADD THIS BLOCK ──────────────────────────────────────────────────────────
from doc_validation_layer import layered_validate

# ──────────────────────────────────────────────────────────────────────────────
# CHANGE 2  — Replace validate_doc_upload() entirely
# (Keep the @app.post decorator and function signature unchanged)
# ──────────────────────────────────────────────────────────────────────────────

"""
@app.post("/v1/validate_doc_upload")
async def validate_doc_upload(
    file:     UploadFile = File(...),
    doc_name: str        = Form(...),
    scheme:   str        = Form(...),
    language: str        = Form("en"),
):
    t0 = time.time()
    # ── DELEGATE TO THREE-LAYER PIPELINE ─────────────────────────────────────
    return await layered_validate(
        file=file,
        doc_name=doc_name,
        scheme=scheme,
        language=language,
        t0=t0,
        # Pass the existing helpers from this module
        _run_vision_ai=_run_vision_ai,
        _vision_prompt=_vision_prompt,
        _parse_vision_json=_parse_vision_json,
        _pdf_to_image_b64=_pdf_to_image_b64,
        localize_validation_payload=localize_validation_payload,
        normalize_language_code=normalize_language_code,
        resolve_scheme_reference=resolve_scheme_reference,
    )
"""

# ──────────────────────────────────────────────────────────────────────────────
# CHANGE 3  — validate_document_alias is already fine (calls validate_doc_upload)
#             No change needed there.
# ──────────────────────────────────────────────────────────────────────────────

"""
That's all.  The response from layered_validate() now includes a new field:

  "validationSteps": [
    {"step": "file_sanity",    "label": "File Format & Size Check",        "status": "passed",  "detail": "image/jpeg | 142 KB"},
    {"step": "ocr_extraction", "label": "OCR Text Extraction",             "status": "passed",  "detail": "312 words extracted"},
    {"step": "keyword_check",  "label": "Document Keyword Verification",   "status": "passed",  "detail": "Keywords present for 'PAN Card'"},
    {"step": "regex_check",    "label": "Pattern & Field Validation",      "status": "passed",  "detail": "1 field(s) extracted"},
    {"step": "ai_vision",      "label": "AI Document Verification",        "status": "passed",  "detail": "Verified as 'PAN Card' with 92% confidence"}
  ]

The frontend ValidationPopup.jsx reads this array and renders each step
as a live progress stepper.
"""
