"""
apply_fix.py — Run this ONCE from D:\\demo\\final
Usage:  python apply_fix.py
It patches ai_scheme_server.py in place and restarts nothing — just restart manually after.
"""
import re, shutil, sys
from pathlib import Path

TARGET = Path(__file__).parent / "ai_scheme_server.py"
BACKUP = Path(__file__).parent / "ai_scheme_server.BAK.py"

if not TARGET.exists():
    sys.exit(f"ERROR: {TARGET} not found. Run this from D:\\demo\\final")

# ── backup ────────────────────────────────────────────────────────────────────
shutil.copy2(TARGET, BACKUP)
print(f"✅ Backup saved → {BACKUP}")

src = TARGET.read_text(encoding="utf-8")

# ── NEW VALIDATION BLOCK to inject ───────────────────────────────────────────
NEW_BLOCK = '''
# ═══════════════════════════════════════════════════════════════════════════════
# DOCUMENT VALIDATION — AI VISION ENGINE (patched by apply_fix.py)
# Priority: Gemini → Groq → NVIDIA → smart rule-based fallback
# Handles images AND PDFs (PDFs are rasterised for vision inspection)
# Ignores filename — judges document content only
# ═══════════════════════════════════════════════════════════════════════════════

def _pdf_to_image_b64(pdf_bytes: bytes):
    """Rasterise first page of PDF → JPEG base64 for vision models."""
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pix = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2), colorspace=fitz.csRGB)
        return base64.b64encode(pix.tobytes("jpeg")).decode()
    except ImportError:
        logger.warning("PyMuPDF not installed — install with: pip install pymupdf")
        return None
    except Exception as e:
        logger.warning(f"PDF→image failed: {e}")
        return None


def _vision_prompt(doc_name: str, scheme_name: str) -> str:
    return f"""You are a strict Indian government document verification officer.

The applicant selected document type: "{doc_name}"
Scheme: "{scheme_name}"

Look carefully at the document image.

Choose ONE verdict:
- "valid"    → This IS a "{doc_name}", genuine, readable, no SAMPLE/SPECIMEN stamp
- "mismatch" → This is a DIFFERENT document type (e.g. Aadhaar uploaded instead of PAN Card)
- "invalid"  → Correct type but blurry / tampered / SAMPLE stamp / key info missing

RULES:
- Ignore the filename completely — judge only what you see
- If you see Aadhaar/UIDAI but "{doc_name}" is "PAN Card" → verdict is "mismatch"
- detectedType = what document you actually see in the image
- errors = one plain human-readable sentence max

Reply ONLY with this JSON (no markdown):
{{
  "verdict": "valid|mismatch|invalid",
  "detectedType": "what you see",
  "govBody": "issuing authority",
  "extractedFields": {{"name": null, "number": null, "dob": null}},
  "errors": [],
  "warnings": [],
  "confidenceScore": 85,
  "summary": "max 8 words"
}}"""


def _parse_vision_json(text: str) -> dict:
    try:
        s = text.find("{"); e = text.rfind("}") + 1
        return json.loads(text[s:e]) if s != -1 and e > s else {}
    except Exception:
        logger.error(f"JSON parse failed: {text[:200]}")
        return {}


async def _try_gemini(image_b64: str, mime: str, prompt: str) -> str:
    if not genai_active:
        raise Exception("Gemini not configured")
    import asyncio
    m = genai.GenerativeModel("gemini-2.0-flash")
    parts = [{"inline_data": {"data": image_b64, "mime_type": mime}}, prompt]
    for attempt in range(3):
        try:
            return m.generate_content(parts).text
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                wait = (attempt + 1) * 20
                logger.warning(f"Gemini rate limited, waiting {wait}s")
                await asyncio.sleep(wait)
            else:
                raise


async def _try_groq(image_b64: str, mime: str, prompt: str) -> str:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise Exception("GROQ_API_KEY not set")
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                "max_tokens": 800, "temperature": 0.1,
                "messages": [{"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_b64}"}},
                    {"type": "text", "text": prompt},
                ]}],
            },
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


async def _try_nvidia(image_b64: str, mime: str, prompt: str) -> str:
    key = os.getenv("NVIDIA_API_KEY")
    if not key:
        raise Exception("NVIDIA_API_KEY not set")
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "meta/llama-4-scout-17b-16e-instruct",
                "max_tokens": 800, "temperature": 0.1,
                "messages": [{"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_b64}"}},
                    {"type": "text", "text": prompt},
                ]}],
            },
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


async def _run_vision_ai(image_b64: str, mime: str, prompt: str) -> str:
    """Try Gemini → Groq → NVIDIA in order."""
    providers = [
        ("Gemini", _try_gemini, genai_active),
        ("Groq",   _try_groq,   bool(os.getenv("GROQ_API_KEY"))),
        ("NVIDIA", _try_nvidia, bool(os.getenv("NVIDIA_API_KEY"))),
    ]
    last_err = None
    for name, fn, available in providers:
        if not available:
            logger.info(f"⏭  {name} skipped (no key)")
            continue
        try:
            result = await fn(image_b64, mime, prompt)
            logger.info(f"✅ Document validated via {name}")
            return result
        except Exception as e:
            logger.warning(f"⚠️  {name} failed: {str(e)[:120]}")
            last_err = e
    raise Exception(f"All AI providers failed: {last_err}")


def _rule_fallback(doc_name, file_name, file_size, mime, scheme):
    scheme_name = scheme.get("scheme_name") or "Selected Scheme"
    if not file_type_supported(file_name, mime):
        return {"success": True, "status": "error", "isValid": False,
                "verdict": "invalid", "documentType": doc_name,
                "errors": [{"message": "Unsupported file format. Please upload PDF, JPG or PNG.", "source": "system"}],
                "warnings": [], "confidenceScore": 0, "summary": "Unsupported file format."}
    if file_size < 5 * 1024:
        return {"success": True, "status": "error", "isValid": False,
                "verdict": "invalid", "documentType": doc_name,
                "errors": [{"message": "File too small or blank. Upload a clear complete document.", "source": "system"}],
                "warnings": [], "confidenceScore": 0, "summary": "File too small."}
    return {"success": True, "status": "valid", "isValid": True,
            "verdict": "valid", "documentType": doc_name, "govBody": "",
            "extractedFields": {}, "errors": [],
            "warnings": [{"message": "No AI key available — accepted on file format only. Add GROQ_API_KEY for full visual verification.", "source": "system"}],
            "confidenceScore": 55, "summary": f"{doc_name} accepted (no AI)."}


@app.post("/v1/validate_doc_upload")
async def validate_doc_upload(
    file:     UploadFile = File(...),
    doc_name: str        = Form(...),
    scheme:   str        = Form(...),
    language: str        = Form("en"),
):
    t0 = time.time()
    scheme_payload = resolve_scheme_reference(raw_scheme=scheme)
    if not scheme_payload:
        raise HTTPException(status_code=404, detail="Selected scheme not found")

    file_bytes  = await file.read()
    file_size   = len(file_bytes)
    mime_type   = (file.content_type or "application/octet-stream").lower()
    file_name   = file.filename or "uploaded-file"
    scheme_name = scheme_payload.get("scheme_name") or "Selected Scheme"

    if mime_type == "image/jpg":
        mime_type = "image/jpeg"

    # Basic checks
    if not file_type_supported(file_name, mime_type):
        return {"success": True, "status": "error", "isValid": False, "verdict": "invalid",
                "documentType": doc_name,
                "errors": [{"message": "Unsupported format. Upload PDF, JPG, or PNG.", "source": "system"}],
                "warnings": [], "confidenceScore": 0, "summary": "Unsupported format.",
                "processingMs": int((time.time()-t0)*1000)}

    if file_size < 5 * 1024:
        return {"success": True, "status": "error", "isValid": False, "verdict": "invalid",
                "documentType": doc_name,
                "errors": [{"message": "File too small or blank. Upload a clear complete document.", "source": "system"}],
                "warnings": [], "confidenceScore": 0, "summary": "File too small.",
                "processingMs": int((time.time()-t0)*1000)}

    # Prepare image for vision
    if mime_type.startswith("image/"):
        image_b64   = base64.b64encode(file_bytes).decode()
        vision_mime = mime_type
    elif mime_type == "application/pdf" or file_name.lower().endswith(".pdf"):
        image_b64   = _pdf_to_image_b64(file_bytes)
        vision_mime = "image/jpeg"
    else:
        image_b64   = None
        vision_mime = "image/jpeg"

    # AI Vision
    if image_b64:
        prompt = _vision_prompt(doc_name, scheme_name)
        try:
            raw  = await _run_vision_ai(image_b64, vision_mime, prompt)
            ai   = _parse_vision_json(raw)
            if not ai:
                raise ValueError("Empty AI response")

            verdict  = ai.get("verdict", "invalid").lower().strip()
            detected = ai.get("detectedType") or doc_name
            conf     = int(ai.get("confidenceScore", 75))
            ai_errs  = [e for e in (ai.get("errors") or [])
                        if isinstance(e, str) and e.strip() and "filename" not in e.lower()]
            ai_warns = [w for w in (ai.get("warnings") or []) if isinstance(w, str) and w.strip()]
            summary  = (ai.get("summary") or "").strip()

            if verdict == "mismatch":
                msg     = f"Wrong document uploaded. You selected '{doc_name}' but uploaded '{detected}'. Please upload the correct document."
                errors  = [{"message": msg, "source": "ai"}]
                warns   = []
                valid   = False
                status  = "error"
                summary = f"Expected {doc_name}, got {detected}."
            elif verdict == "valid" and not ai_errs:
                errors  = []
                warns   = [{"message": w, "source": "ai"} for w in ai_warns]
                valid   = True
                status  = "valid"
                summary = summary or f"{doc_name} verified successfully."
            else:
                errors  = [{"message": e, "source": "ai"} for e in ai_errs] or \
                          [{"message": "Could not verify document. Upload a clearer copy.", "source": "ai"}]
                warns   = [{"message": w, "source": "ai"} for w in ai_warns]
                valid   = False
                status  = "error"
                summary = summary or errors[0]["message"]

            ms = int((time.time()-t0)*1000)
            logger.info(f"[validate] \'{doc_name}\' → {verdict} | detected=\'{detected}\' | conf={conf} | {ms}ms")
            return {"success": True, "status": status, "isValid": valid,
                    "verdict": verdict, "documentType": detected,
                    "govBody": ai.get("govBody", ""),
                    "extractedFields": ai.get("extractedFields", {}),
                    "errors": errors, "warnings": warns,
                    "confidenceScore": conf, "summary": summary,
                    "fileName": file_name, "processingMs": ms}

        except Exception as e:
            logger.error(f"All AI providers failed: {e}")

    # Rule-based fallback
    result = _rule_fallback(doc_name, file_name, file_size, mime_type, scheme_payload)
    result["processingMs"] = int((time.time()-t0)*1000)
    return result


@app.post("/v1/validate/document")
async def validate_document_alias(
    file:    UploadFile = File(...),
    docName: str        = Form(...),
    scheme:  str        = Form(...),
    language: str       = Form("en"),
):
    return await validate_doc_upload(file=file, doc_name=docName, scheme=scheme, language=language)
'''

# ── Find and replace everything from first validate_doc_upload to end ────────
# Pattern: from the old duplicate endpoint OR the patch comment all the way to if __name__
pattern = re.compile(
    r'(@app\.post\("/v1/validate_doc_upload"\).*?)'
    r'(if __name__\s*==\s*["\']__main__["\"])',
    re.DOTALL
)

if not pattern.search(src):
    sys.exit("ERROR: Could not find the section to replace. Is this the right file?")

new_src = pattern.sub(NEW_BLOCK + '\n\nif __name__ == "__main__":', src)

TARGET.write_text(new_src, encoding="utf-8")
print(f"✅ Patched {TARGET}")

# ── Verify ────────────────────────────────────────────────────────────────────
import ast
try:
    ast.parse(new_src)
    print("✅ Syntax check passed")
except SyntaxError as e:
    print(f"❌ Syntax error: {e}")
    shutil.copy2(BACKUP, TARGET)
    sys.exit("Restored backup. Please report this error.")

checks = [
    ("validate_doc_upload endpoint", "@app.post(\"/v1/validate_doc_upload\")"),
    ("PDF conversion",               "_pdf_to_image_b64"),
    ("Groq vision",                  "_try_groq"),
    ("Gemini vision",                "_try_gemini"),
    ("rule fallback",                "_rule_fallback"),
]
all_ok = True
for label, needle in checks:
    found = needle in new_src
    print(f"{'✅' if found else '❌'} {label}")
    if not found:
        all_ok = False

if all_ok:
    print("\n🎉 All checks passed! Now restart your server:")
    print("   python ai_scheme_server.py")
else:
    print("\n❌ Some checks failed — restoring backup")
    shutil.copy2(BACKUP, TARGET)
