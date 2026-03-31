#!/usr/bin/env python3
"""
ai_scheme_server.py  — FINAL PRODUCTION VERSION
================================================
Run:  python mainm.py
Port: http://127.0.0.1:8000

Bugs fixed vs the submitted version:
  1. ensure_youtube — always copies the dict before mutating (prevents
     shared-state corruption across requests).
  2. Priority engine — guards against empty results list (no IndexError).
  3. detect_timeline — try/except around int() cast (no crash on bad data).
  4. Auth endpoints — proper HTTP 400/401 status codes, not 200 + error body.
  5. ensure_youtube — strips empty name/state before building URLs.
  6. eligibility_score — guards against empty profile fields.
  7. app = FastAPI() moved above all route decorators — was defined AFTER
     routes tried to register on it, causing silent startup failure.
  8. Duplicate Profile class removed — the simple 6-field stub shadowed
     the full 30-field production model.
  9. SentenceTransformer + LanceDB double-init removed — model was loaded
     at module level AND again in load_engine(); now only in load_engine().
 10. uvicorn.run() rescued from orphaned docstring — server now actually
     starts when the script is run directly.
 11. @app.on_event("startup") replaced with modern lifespan handler.
 12. _try_lmstudio_vision added — was called by _run_vision_ai but never
     defined, causing NameError on every document-validation request.
 13. _run_vision_ai now uses the full provider fallback chain
     (LM Studio → Gemini → Groq → NVIDIA) instead of LM Studio only.
 14. Dead unreachable code removed after return in build_premium_fallback.
 15. Dead unreachable code removed after return in /v1/chat endpoint.
 16. StaticFiles mount added for the frontend directory.
"""
import base64
import time
import httpx
import json
import re
import sqlite3
import lancedb
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import quote_plus
from contextlib import asynccontextmanager
from fastapi import FastAPI, Body, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from doc_valid import layered_validate
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import uvicorn
import logging
import os
import openai
from dotenv import load_dotenv

load_dotenv()

# ─── IN-MEMORY WORKSPACE STORE ───────────────────────────────────────────────
_workspace_store: Dict[str, Any] = {}

# OpenAI Client
client_oa = None
if os.getenv("OPENAI_API_KEY"):
    client_oa = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Gemini Client (optional)
genai = None
genai_active = False
try:
    import google.generativeai as genai
    if os.getenv("GOOGLE_API_KEY"):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        genai_active = True
except ImportError:
    print("Note: google-generativeai not available (optional). Using OpenAI/rule-based fallback.")

# logging setup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AI-SCHEME")

LANGUAGE_REGISTRY = {
    "en": {"display": "English"},
    "hi": {"display": "Hindi (हिन्दी)"},
    "mr": {"display": "Marathi (मराठी)"},
    "kn": {"display": "Kannada (ಕನ್ನಡ)"},
    "ta": {"display": "Tamil (தமிழ்)"},
    "te": {"display": "Telugu (తెలుగు)"},
    "bn": {"display": "Bengali (বাংলা)"},
    "gu": {"display": "Gujarati (ગુજરાતી)"},
    "ml": {"display": "Malayalam (മലയാളം)"},
    "or": {"display": "Odia (ଓଡ଼ିଆ)"},
    "pa": {"display": "Punjabi (ਪੰਜਾਬੀ)"},
    "ur": {"display": "Urdu (اردو)"},
    "as": {"display": "Assamese (অসমীয়া)"},
    "sat": {"display": "Santali (ᱥᱟᱱᱛᱟᱲᱤ)"},
    "ks": {"display": "Kashmiri (कॉशुर)"},
    "ne": {"display": "Nepali (नेपाली)"},
}

LANGUAGE_ALIASES = {
    "english": "en",
    "en": "en",
    "hindi": "hi",
    "hi": "hi",
    "marathi": "mr",
    "mr": "mr",
    "kannada": "kn",
    "kn": "kn",
    "tamil": "ta",
    "ta": "ta",
    "telugu": "te",
    "te": "te",
    "bengali": "bn",
    "bn": "bn",
    "gujarati": "gu",
    "gu": "gu",
    "malayalam": "ml",
    "ml": "ml",
    "odia": "or",
    "oriya": "or",
    "or": "or",
    "punjabi": "pa",
    "pa": "pa",
    "urdu": "ur",
    "ur": "ur",
    "assamese": "as",
    "as": "as",
    "santali": "sat",
    "sat": "sat",
    "kashmiri": "ks",
    "ks": "ks",
    "nepali": "ne",
    "ne": "ne",
}


def normalize_language_code(value: Any) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return "en"
    compact = re.sub(r"\s+", " ", text)
    compact = compact.split("(", 1)[0].strip()
    return LANGUAGE_ALIASES.get(text, LANGUAGE_ALIASES.get(compact, "en"))


def language_display_name(value: Any) -> str:
    code = normalize_language_code(value)
    return LANGUAGE_REGISTRY.get(code, LANGUAGE_REGISTRY["en"])["display"]


def is_english_language(value: Any) -> bool:
    return normalize_language_code(value) == "en"


async def translate_text_block(text: str, target_lang: str) -> str:
    """Translate free-form text while preserving markdown structure when possible."""
    lang_code = normalize_language_code(target_lang)
    if not text or is_english_language(lang_code):
        return text

    target_display = language_display_name(lang_code)
    prompt = f"""
TASK: Translate the following content into {target_display}.

RULES:
1. Return ONLY the translated text.
2. Preserve Markdown structure, headings, bullet points, numbering, and links.
3. Do NOT make the output bilingual.
4. Keep official scheme names, acronyms, URLs, and legal identifiers unchanged unless a natural translation is standard.
5. Use only {target_display} for all explanatory text.

CONTENT:
{text}
""".strip()

    try:
        translated = await run_text_completion(
            prompt,
            system=(
                f"You are a professional localization engine. Translate only into {target_display}. "
                "Preserve markdown and never add bilingual text."
            ),
            temperature=0.2,
            max_tokens=2400,
        )
        if translated:
            return translated.strip()
    except Exception as e:
        logger.warning(f"Text translation failed for {target_display}: {e}")

    return text


async def translate_text_items(items: List[str], target_lang: str) -> List[str]:
    """Translate a list of short UI/content items and preserve the original ordering."""
    lang_code = normalize_language_code(target_lang)
    cleaned_items = [str(item or "").strip() for item in items if str(item or "").strip()]
    if not cleaned_items or is_english_language(lang_code):
        return cleaned_items

    target_display = language_display_name(lang_code)
    prompt = f"""
TASK: Translate the following JSON array of short text items into {target_display}.

JSON INPUT:
{json.dumps(cleaned_items, ensure_ascii=False)}

RULES:
1. Return ONLY a raw JSON array of strings.
2. Preserve ordering and array length.
3. Do NOT make the output bilingual.
4. Keep official names, acronyms, and URLs unchanged unless a natural translation is standard.
5. Use only {target_display} for explanatory text.
""".strip()

    try:
        translated_text = await run_text_completion(
            prompt,
            system=(
                f"You are a JSON localization engine. Translate only into {target_display}. "
                "Return raw JSON only."
            ),
            temperature=0.2,
            max_tokens=2400,
        )

        if translated_text:
            cleaned = translated_text
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            parsed = json.loads(cleaned.strip())
            if isinstance(parsed, dict):
                parsed = parsed.get("items", [])
            if isinstance(parsed, list):
                parsed_items = [str(item or "").strip() for item in parsed]
                if len(parsed_items) == len(cleaned_items):
                    return parsed_items
    except Exception as e:
        logger.warning(f"List translation failed for {target_display}: {e}")

    return cleaned_items


async def localize_validation_payload(payload: Dict[str, Any], target_lang: str) -> Dict[str, Any]:
    lang_code = normalize_language_code(target_lang)
    if is_english_language(lang_code):
        return payload

    messages: List[str] = []
    if payload.get("summary"):
        messages.append(str(payload["summary"]))
    errors = payload.get("errors") or []
    warnings = payload.get("warnings") or []
    messages.extend(str(item.get("message", "")).strip() for item in errors if item.get("message"))
    messages.extend(str(item.get("message", "")).strip() for item in warnings if item.get("message"))

    translated = await translate_text_items(messages, lang_code)
    if not translated:
        return payload

    pointer = 0
    localized = dict(payload)
    if localized.get("summary"):
        localized["summary"] = translated[pointer]
        pointer += 1

    localized_errors = []
    for item in errors:
        next_item = dict(item)
        if pointer < len(translated):
            next_item["message"] = translated[pointer]
            pointer += 1
        localized_errors.append(next_item)
    localized["errors"] = localized_errors

    localized_warnings = []
    for item in warnings:
        next_item = dict(item)
        if pointer < len(translated):
            next_item["message"] = translated[pointer]
            pointer += 1
        localized_warnings.append(next_item)
    localized["warnings"] = localized_warnings

    return localized


async def _try_lmstudio_text(prompt: str, system: str = "", temperature: float = 0.2, max_tokens: int = 2000) -> str:
    base_url = str(os.getenv("DOC_VERIFY_LMSTUDIO_BASE_URL", "") or "").strip().rstrip("/")
    model_name = str(os.getenv("DOC_VERIFY_LLM_MODEL", "") or "").strip()
    if not base_url or not model_name:
        raise Exception("LM Studio not configured")

    messages = []
    if system.strip():
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=90) as c:
        r = await c.post(
            f"{base_url}/chat/completions",
            headers={"Content-Type": "application/json"},
            json={
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


async def _try_gemini_text(prompt: str, system: str = "", temperature: float = 0.2, max_tokens: int = 2000) -> str:
    if not genai_active:
        raise Exception("Gemini not configured")
    full_prompt = f"{system}\n\n{prompt}".strip() if system else prompt
    model_gen = genai.GenerativeModel("gemini-2.0-flash")
    response = model_gen.generate_content(full_prompt)
    return response.text


async def _try_groq_text(prompt: str, system: str = "", temperature: float = 0.2, max_tokens: int = 2000) -> str:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise Exception("GROQ_API_KEY not set")
    messages = []
    if system.strip():
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    async with httpx.AsyncClient(timeout=90) as c:
        r = await c.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


async def _try_nvidia_text(prompt: str, system: str = "", temperature: float = 0.2, max_tokens: int = 2000) -> str:
    key = os.getenv("NVIDIA_API_KEY")
    if not key:
        raise Exception("NVIDIA_API_KEY not set")
    messages = []
    if system.strip():
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    async with httpx.AsyncClient(timeout=90) as c:
        r = await c.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "microsoft/phi-3-vision-128k-instruct",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


async def _try_openai_text(prompt: str, system: str = "", temperature: float = 0.2, max_tokens: int = 2000) -> str:
    if not client_oa:
        raise Exception("OpenAI not configured")
    messages = []
    if system.strip():
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    response = client_oa.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


async def run_text_completion(prompt: str, system: str = "", temperature: float = 0.2, max_tokens: int = 2000) -> str:
    providers = [
        ("LM Studio", _try_lmstudio_text, bool(os.getenv("DOC_VERIFY_LMSTUDIO_BASE_URL")) and bool(os.getenv("DOC_VERIFY_LLM_MODEL"))),
        ("Gemini", _try_gemini_text, genai_active),
        ("Groq", _try_groq_text, bool(os.getenv("GROQ_API_KEY"))),
        ("NVIDIA", _try_nvidia_text, bool(os.getenv("NVIDIA_API_KEY"))),
        ("OpenAI", _try_openai_text, bool(client_oa)),
    ]

    last_err = None
    for name, fn, available in providers:
        if not available:
            continue
        try:
            result = await fn(prompt, system=system, temperature=temperature, max_tokens=max_tokens)
            if result and str(result).strip():
                logger.info(f"Text completion served via {name}")
                return str(result).strip()
        except Exception as e:
            logger.warning(f"{name} text completion failed: {str(e)[:160]}")
            last_err = e

    raise Exception(f"All text completion providers failed: {last_err}")


async def translate_text_mapping(texts: List[str], target_lang: str) -> Dict[str, str]:
    lang_code = normalize_language_code(target_lang)
    cleaned_texts = dedupe_strings([str(text or "").strip() for text in texts if str(text or "").strip()])
    if not cleaned_texts or is_english_language(lang_code):
        return {text: text for text in cleaned_texts}

    mapping: Dict[str, str] = {}
    batch_size = 40
    for start in range(0, len(cleaned_texts), batch_size):
        batch = cleaned_texts[start:start + batch_size]
        translated_batch = await translate_text_items(batch, lang_code)
        for index, original in enumerate(batch):
            translated = translated_batch[index] if index < len(translated_batch) else original
            mapping[original] = translated or original

    return mapping

DATA_DIR = Path(os.getenv("DATA_DIR", "./frontend/data")).resolve()
SCHEMES_DB_PATH = DATA_DIR / "schemes_merged_final.json"
ENRICHED_PATH = DATA_DIR / "schemes_enriched_free.json"
LANCE_DB_PATH = Path(os.getenv("LANCE_DB_PATH", "./lancedb_backup")).resolve()

# ─── DEFERRED GLOBALS (populated in load_engine via lifespan) ────────────
# Declared here so the rest of the module can reference them;
# actual initialisation happens inside load_engine() at startup.
model: Any = None
db:    Any = None
tbl:   Any = None
tbl_fields: Any = None

# ─── CONSTANTS & CONFIG (from scoring engine) ──────────────────────────
STATE_POLICY_SCORE = {
    "andhra pradesh": 82, "arunachal pradesh": 70, "assam": 74, "bihar": 72,
    "chhattisgarh": 76, "goa": 80, "gujarat": 91, "haryana": 88,
    "himachal pradesh": 79, "jharkhand": 75, "karnataka": 92, "kerala": 86,
    "madhya pradesh": 83, "maharashtra": 94, "manipur": 68, "meghalaya": 67,
    "mizoram": 66, "nagaland": 65, "odisha": 81, "punjab": 85,
    "rajasthan": 84, "sikkim": 73, "tamil nadu": 93, "telangana": 90,
    "tripura": 69, "uttar pradesh": 82, "uttarakhand": 80, "west bengal": 83,
    "delhi": 95, "jammu and kashmir": 78, "ladakh": 72, "chandigarh": 88,
    "puducherry": 79, "andaman and nicobar": 68, "dadra and nagar haveli": 74,
    "daman and diu": 75, "central": 96, "india": 96, "all india": 96,
    "pan india": 96, "national": 96
}

# Anchor users.db to the script directory so it is always the same file
# regardless of which working directory the server is started from.
_SCRIPT_DIR = Path(__file__).resolve().parent
DB_FILE = str(Path(os.getenv("DB_FILE", str(_SCRIPT_DIR / "users.db"))))

# ─── LIFESPAN (replaces deprecated @app.on_event) ────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialise DB and load the ML engine. Shutdown: nothing needed."""
    init_db()
    load_engine()
    yield

# ─── APP INSTANCE (must be defined before any @app decorator) ────────────────
app = FastAPI(title="AI Scheme Recommendation Server", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── CHAT REQUEST MODEL ───────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    query: str
    schemes: List[Dict[str, Any]] = []
    profile: Dict[str, Any] = {}
    language: str = "en"


def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                full_name TEXT,
                profile_data TEXT,
                saved_schemes TEXT DEFAULT '[]'
            )
        ''')
        # Migrate existing databases — safe to run every startup:
        try:
            conn.execute("ALTER TABLE users ADD COLUMN saved_schemes TEXT DEFAULT '[]'")
        except sqlite3.OperationalError:
            pass  # Column already exists
        conn.commit()

@app.post("/v1/auth/signup")
async def signup(data: dict = Body(...)):
    email     = str(data.get("email",     "")).strip().lower()
    password  = str(data.get("password",  "")).strip()
    full_name = str(data.get("full_name", "")).strip()

    if not email or not password:
        raise HTTPException(status_code=400, detail="Missing email or password")

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # Use LOWER() so duplicate-check is case-insensitive
        cursor.execute("SELECT email FROM users WHERE LOWER(email) = ?", (email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="User already exists")
        
        cursor.execute(
            "INSERT INTO users (email, password, full_name, profile_data) VALUES (?, ?, ?, ?)",
            (email, password, full_name, "{}")
        )
        conn.commit()

    return {
        "access_token": f"demo-token-{email}",
        "token_type":   "bearer",
        "user":         {"email": email, "full_name": full_name, "profile_data": {}},
    }


@app.post("/v1/auth/login")
async def login(data: dict = Body(...)):
    email    = str(data.get("email",    "")).strip().lower()
    password = str(data.get("password", "")).strip()

    if not email or not password:
        raise HTTPException(status_code=400, detail="Missing email or password")

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # Search case-insensitively in case registration used mixed case
        cursor.execute(
            "SELECT password, full_name, profile_data FROM users WHERE LOWER(email) = ?",
            (email,)
        )
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="User not found. Please sign up first.")

        db_password, full_name, profile_data_str = row
        if db_password.strip() != password:
            raise HTTPException(status_code=401, detail="Incorrect password")

        try:
            profile_data = json.loads(profile_data_str) if profile_data_str else {}
        except json.JSONDecodeError:
            profile_data = {}

    with sqlite3.connect(DB_FILE) as conn2:
        cursor2 = conn2.cursor()
        cursor2.execute("SELECT saved_schemes FROM users WHERE LOWER(email) = ?", (email,))
        r2 = cursor2.fetchone()
        try:
            saved_schemes = json.loads(r2[0]) if r2 and r2[0] else []
        except Exception:
            saved_schemes = []

    last_id = saved_schemes[0].get("scheme_id", "") if saved_schemes else ""
    workspace_block = {
        "profile":                 profile_data,
        "saved_schemes":           saved_schemes,
        "last_selected_scheme_id": last_id,
    }
    return {
        "access_token": f"demo-token-{email}",
        "token_type":   "bearer",
        "user": {
            "email":                   email,
            "full_name":               full_name,
            "profile_data":            profile_data,
            "saved_schemes":           saved_schemes,
            "last_selected_scheme_id": last_id,
            "workspace":               workspace_block,
        },
    }


@app.post("/v1/profile/save")
async def save_profile(data: dict = Body(...)):
    email = str(data.get("email", "")).strip().lower()
    profile = data.get("profile", {})
    
    if not email:
        raise HTTPException(status_code=400, detail="Missing email")

    logger.info(f"Saving profile for {email}")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users WHERE LOWER(email) = ?", (email,))
        if not cursor.fetchone():
            logger.warning(f"User {email} not found during profile save, creating shadow record")
            cursor.execute("INSERT INTO users (email, password, full_name, profile_data) VALUES (?, ?, ?, ?)", (email, "p@ssword123", email.split('@')[0], "{}"))
            
        profile_json = json.dumps(profile)
        cursor.execute(
            "UPDATE users SET profile_data = ? WHERE LOWER(email) = ?",
            (profile_json, email)
        )
        conn.commit()

    logger.info(f"Profile saved successfully for {email}")
    return {"status": "success", "message": "Profile saved."}


@app.get("/v1/profile/get")
async def get_profile(email: str):
    if not email:
        raise HTTPException(status_code=400, detail="Missing email")

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT full_name, profile_data FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        
        full_name, profile_data_str = row
        try:
            profile_data = json.loads(profile_data_str) if profile_data_str else {}
        except json.JSONDecodeError:
            profile_data = {}

    return {"full_name": full_name, "profile": profile_data}


@app.post("/v1/schemes/save")
async def save_schemes(data: dict = Body(...)):
    """Persist a user's shortlisted/saved scheme list."""
    email          = str(data.get("email", "")).strip().lower()
    schemes_to_save = data.get("schemes", [])

    if not email:
        raise HTTPException(status_code=400, detail="Missing email")
    if not isinstance(schemes_to_save, list):
        raise HTTPException(status_code=400, detail="schemes must be a JSON array")

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users WHERE LOWER(email) = ?", (email,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
        cursor.execute(
            "UPDATE users SET saved_schemes = ? WHERE LOWER(email) = ?",
            (json.dumps(schemes_to_save), email)
        )
        conn.commit()

    logger.info(f"Saved {len(schemes_to_save)} scheme(s) for {email}")
    return {"status": "success", "saved_count": len(schemes_to_save)}


@app.get("/v1/schemes/saved")
async def get_saved_schemes(email: str):
    """Retrieve a user's previously saved schemes."""
    if not email:
        raise HTTPException(status_code=400, detail="Missing email")

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT saved_schemes FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        try:
            saved = json.loads(row[0]) if row[0] else []
        except json.JSONDecodeError:
            saved = []

    return {"schemes": saved, "count": len(saved)}

# ─── SCHEME ENGINE ────────────────────────────────────────────────────────────

schemes: List[Dict[str, Any]] = []


class Profile(BaseModel):
    # Core Identity (PII - Excluded from semantic match by default, except dob for age)
    email:               str = ""
    fullName:            str = ""
    dob:                 str = ""
    businessName:        str = ""
    brandName:           str = ""
    
    # Geographic & Sectoral (High Semantic Value)
    state:               str = ""
    district:            str = ""
    taluk:               str = ""
    pinCode:             str = ""
    locationType:        str = ""
    address:             str = ""
    sector:              str = ""
    subSector:           str = ""
    
    # Business Entity (High Semantic Value)
    entityType:          str = ""
    businessStage:       str = ""
    yearEstablished:     str = ""
    employees:           str = ""
    udyamRegistered:     str = ""
    gstRegistered:       str = ""
    techLevel:           str = ""
    exportIntention:     str = ""
    
    # Demographics (Incentive Matching)
    gender:              str = ""
    socialCategory:      str = ""
    womenEmployees:      str = ""
    
    # Financials (Eligibility Check)
    turnover:            str = ""
    projectCost:         str = ""
    fixedCapital:        str = ""
    financeMode:         str = ""
    ownContrib:          str = ""
    bank:                str = ""
    investmentReq:       str = ""
    hasLoans:            str = ""
    
    # Location Details
    premisesType:        str = ""
    
    # Narrative (Deep Semantic Discovery)
    businessDescription: str = ""
    goals:               str = ""
    
    # Localization
    language:            str = "en"


def load_engine():
    global schemes, model, db, tbl, tbl_fields
    try:
        # Use the configured backup path from .env when available.
        backup_path = str(LANCE_DB_PATH)
        
        path = ENRICHED_PATH if ENRICHED_PATH.exists() else SCHEMES_DB_PATH
        logger.info(f"Loading schemes from: {path}")

        with open(path, encoding="utf-8") as f:
            schemes = json.load(f)

        logger.info(f"Loaded {len(schemes)} schemes")

        model = SentenceTransformer("BAAI/bge-m3")
        
        db     = lancedb.connect(backup_path)
        tbl    = db.open_table("schemes")
        tbl_fields = db.open_table("fields")

        logger.info("Semantic Engine Ready (Backup Integrated)")
    except Exception as e:
        logger.error(f"Critical error in load_engine: {e}")
        raise e




# ─── HELPERS ─────────────────────────────────────────────────────────────────

def sector_matches(user_sector: str, scheme_sector: str) -> bool:
    if not user_sector or user_sector.lower() in ["all", "all sectors", "any", "general"]:
        return True
    
    sl = user_sector.lower().strip()
    ss = scheme_sector.lower().strip()
    
    # ── Agriculture vs Non-Agri Cross-Gate (HARD BLOCK) ──
    is_agri_user = any(k in sl for k in ["agri", "farm", "agro", "horticulture", "dairy", "fishery", "poultry", "agriculture", "kisan"])
    is_agri_scheme = any(k in ss for k in ["kisan", "agri", "farmer", "horticulture", "dairy", "fishery", "poultry", "agriculture"])
    
    if is_agri_scheme and not is_agri_user:
        return False # Absolute block for Agri schemes
    if is_agri_user and not is_agri_scheme and "multipurpose" not in ss:
        if any(k in ss for k in ["industrial", "manufacturing", "textile", "it ", "software"]):
            return False # Block high-tech/industrial for pure Agri users unless multipurpose
            
    # Standard matches
    basic_match = sl in ss or ss in sl or "all" in ss or "general" in ss
    
    # ── MSME Gate ──
    if "msme" in sl or "msme" in ss:
        # If it's a general MSME scheme, it matches most sectors
        if "general" in ss or "all" in ss or not ss:
            return True
        
    return basic_match


def detect_timeline(s: dict) -> int:
    raw = s.get("timeline_days") or s.get("Timeline_Days")
    if raw is not None:
        try:
            return int(raw)
        except (ValueError, TypeError):
            pass

    text = (
        str(s.get("description", "")) + " " +
        str(s.get("eligibility", ""))
    ).lower()

    if "cluster" in text or "infrastructure" in text: return 150
    if "capital subsidy" in text:                     return 120
    if "subsidy" in text:                             return 90
    if "loan" in text or "credit" in text:            return 60
    if "startup" in text or "seed" in text:           return 45
    return 75


def eligibility_score(profile: Profile, s: dict) -> int:
    score     = 0
    # Use the new eligibility_criteria list if available
    elig_text = " ".join(s.get("eligibility_criteria", [])) if isinstance(s.get("eligibility_criteria"), list) else str(s.get("eligibility", ""))
    elig_text = (elig_text + " " + str(s.get("description", "")) + " " + str(s.get("benefits_summary", ""))).lower()
    
    s_sector = str(s.get("sector", "")).lower()
    s_state  = str(s.get("state",  "")).lower()

    # 1. Hard Matches (Base 100)
    if profile.entityType and profile.entityType.lower() in elig_text: score += 40
    if profile.sector and sector_matches(profile.sector, s_sector):    score += 30
    if profile.state and (profile.state.lower() in s_state or any(k in s_state for k in ["central", "india", "pan india"])): score += 30

    # ── Industry-Sectors Gate ──
    s_name = s.get("scheme_name", "")
    p_sector = profile.sector or ""
    
    # 1. PLI/Manufacturing vs Service
    is_mfg_scheme = any(k in s_name.lower() or k in s_sector.lower() for k in ["pli", "production linked", "manufacturing"])
    is_service_user = any(k in p_sector.lower() for k in ["service", "design", "software", "it ", "consulting"])
    
    if is_mfg_scheme and is_service_user and "manufacturing" not in p_sector.lower():
        score -= 100 # Heavy penalty for PLI-Services mismatch

    # 2. Agriculture vs Non-Agri
    is_agri_scheme = any(k in s_name.lower() or k in s_sector.lower() for k in ["kisan", "agri", "farmer", "horti", "dairy", "fishery"])
    is_agri_user = any(k in p_sector.lower() for k in ["agri", "farm", "agro", "horti"])
    
    if is_agri_scheme and not is_agri_user:
        score -= 150 # Absolute block for Agri-schemes for non-agri users

    # 3. Demographic Boosts & Penalties (Net 40)
    # Strict Gender Filter: If scheme is clearly for women and user is not Female
    is_women_scheme = "women" in elig_text or "female" in elig_text or "lady" in elig_text
    if is_women_scheme:
        if profile.gender == "Female":
            score += 25
        elif profile.gender == "Male":
            score -= 50  # Significant penalty for gender-mismatch schemes

    if profile.socialCategory and profile.socialCategory.lower() in elig_text:
        score += 20
    if profile.businessStage and profile.businessStage.lower() in elig_text:
        score += 10

    return score


def ensure_youtube(s: dict) -> dict:
    """
    Returns a NEW dict copy — never mutates the global schemes[] element.
    Adds youtube_video_1/2 and youtube_label_1/2 if missing.
    """
    s = dict(s)   # copy FIRST — critical

    if s.get("youtube_video_1"):
        return s  # already enriched

    name  = str(s.get("scheme_name") or s.get("Scheme_Name") or "").strip()
    state = str(s.get("state") or s.get("State_Applicable") or "").strip()

    if not name:
        return s

    ctx = (
        state
        if state and state.lower() not in ("india", "all", "pan india", "")
        else "India"
    )

    s["youtube_video_1"] = (
        "https://www.youtube.com/results?search_query="
        + quote_plus(f"what is {name} scheme {ctx}")
    )
    s["youtube_label_1"] = f"What is {name}?"

    s["youtube_video_2"] = (
        "https://www.youtube.com/results?search_query="
        + quote_plus(f"how to apply {name} scheme {ctx}")
    )
    s["youtube_label_2"] = f"How to apply for {name}"

    return s

# ─── ADVANCED AI INTELLIGENCE ENGINES (PHASE 3-6) ─────────────────────────

class ProfileIntelligenceEngine:
    """Phase 3: Converts raw profile into a machine-understandable intelligence object."""
    @staticmethod
    def enrich(profile: Profile) -> dict:
        # ── Comprehensive "Meaning-Based" Context Engineering (PII-FREE) ──
        segments = []
        
        # 1. Entity & Identity
        entity_ctx = f"Business Entity: {profile.entityType or 'Enterprise'}."
        if profile.businessName: entity_ctx += f" Legal Name: {profile.businessName}."
        if profile.brandName: entity_ctx += f" Known as: {profile.brandName}."
        segments.append(entity_ctx)
        
        # 2. Stage & Scale
        scale_ctx = f"Operation Scale: {profile.businessStage or 'Development'} stage."
        if profile.yearEstablished: scale_ctx += f" Active since {profile.yearEstablished}."
        if profile.employees: scale_ctx += f" Workforce size: {profile.employees} employees."
        segments.append(scale_ctx)
        
        # 3. Sectoral Depth
        sector_ctx = f"Sectoral Focus: {profile.sector or 'General'}."
        if profile.subSector: sector_ctx += f" Specialized in {profile.subSector}."
        if profile.techLevel: sector_ctx += f" Technology Grade: {profile.techLevel}."
        if profile.exportIntention: sector_ctx += f" Global/Local Reach: {profile.exportIntention}."
        segments.append(sector_ctx)
        
        # 4. Geographic & Operational Details
        geo_ctx = f"Geography: {profile.state or 'India'}, {profile.district or 'Any District'}."
        if profile.taluk: geo_ctx += f" Area: {profile.taluk}."
        if profile.pinCode: geo_ctx += f" ZIP: {profile.pinCode}."
        if profile.locationType: geo_ctx += f" Density: {profile.locationType}."
        if profile.address: geo_ctx += f" Full Presence: {profile.address}."
        if profile.premisesType: geo_ctx += f" Facility: {profile.premisesType}."
        segments.append(geo_ctx)
        
        # 5. Socio-Demographics (Incentive Markers)
        socio = []
        if profile.gender: socio.append(f"Gender: {profile.gender}")
        if profile.socialCategory and profile.socialCategory != "General": socio.append(f"Social Category: {profile.socialCategory}")
        if profile.womenEmployees and profile.womenEmployees != "0": socio.append(f"Women workforce: {profile.womenEmployees}")
        if profile.dob: socio.append(f"Promoter Age/Context (DOB: {profile.dob})")
        if socio: segments.append(f"Socio-Demographics: {', '.join(socio)}.")
        
        # 6. Financial & Compliance Intelligence
        fin = []
        if profile.turnover: fin.append(f"Turnover: {profile.turnover}")
        if profile.projectCost: fin.append(f"Investment: {profile.projectCost}")
        if profile.fixedCapital: fin.append(f"Capital Investment: {profile.fixedCapital}")
        if profile.financeMode: fin.append(f"Funding Model: {profile.financeMode}")
        if profile.ownContrib: fin.append(f"Own contribution: {profile.ownContrib}")
        if profile.bank: fin.append(f"Preferred Banking: {profile.bank}")
        if profile.investmentReq: fin.append(f"Funds required: {profile.investmentReq}")
        if profile.hasLoans == "Yes": fin.append("Existing credit/loan history")
        if profile.udyamRegistered == "Yes": fin.append("Udyam MSME Registered")
        if profile.gstRegistered == "Yes": fin.append("GST Registered")
        if fin: segments.append(f"Financial Profile: {', '.join(fin)}.")
        
        # 7. Deep Narrative Focus
        if profile.businessDescription:
            segments.append(f"Core Mission: {profile.businessDescription}")
        if profile.goals:
            segments.append(f"Future State: {profile.goals}")

        full_context = " | ".join(segments)
        logger.info(f"Generated Deep Semantic Intelligence Context: {full_context[:150]}...")
        
        vector = model.encode(full_context).tolist()
        return {
            "intelligence_context": full_context,
            "profile_vector": vector,
            "enriched_tags": [profile.sector, profile.state, profile.entityType, profile.socialCategory, profile.gender]
        }

class MultiFactorRankingEngine:
    """Phase 6: Weighted scoring for premium decision support."""
    @staticmethod
    def rank(profile: Profile, schemes: List[dict]) -> List[dict]:
        user_state = (profile.state or "").lower()
        user_sector = (profile.sector or "").lower()
        
        for s in schemes:
            # 1. Base Eligibility Score
            elig_sc = eligibility_score(profile, s)
            
            # 2. State Policy Strength
            s_state = str(s.get("state", "")).lower()
            policy_strength = 75
            for key, val in STATE_POLICY_SCORE.items():
                if key in s_state:
                    policy_strength = val
                    break
            
            # 3. Sector Growth Intelligence
            s_sector = str(s.get("sector", "")).lower()
            if "manufacturing" in s_sector:   sector_growth = 88
            elif "it" in s_sector or "digital" in s_sector: sector_growth = 92
            elif "agriculture" in s_sector: sector_growth = 78
            elif "textile" in s_sector:     sector_growth = 81
            elif "export" in s_sector:      sector_growth = 85
            else:                           sector_growth = 72
            
            # 4. Funding Attractiveness
            desc = (str(s.get("description", "")) + " " + str(s.get("benefits_summary", ""))).lower()
            if "grant" in desc:      funding_score = 95
            elif "subsidy" in desc:  funding_score = 90
            elif "capital" in desc:  funding_score = 85
            elif "loan" in desc:     funding_score = 75
            else:                    funding_score = 65
            
            # 5. Success Probability (AI Heuristic)
            success_prob = min(98, int((elig_sc * 0.6 + policy_strength * 0.4)))
            
            # 6. Central/National Boost
            central_boost = 0
            if any(k in s_state for k in ["central", "india", "pan india", "national"]):
                central_boost = 20
            
            # 7. Final Weighted Formula
            final_score = (
                (elig_sc * 0.40) + 
                (success_prob * 0.20) + 
                (sector_growth * 0.15) + 
                (policy_strength * 0.15) + 
                (funding_score * 0.10) + 
                central_boost
            )
            
            # Phase 7: Explainable reasoning mapping
            reasons = []
            if profile.sector and profile.sector.lower() in s_sector:
                reasons.append(f"Sector Alignment: {profile.sector.title()}")
            elif "all" in s_sector or "general" in s_sector or not s_sector:
                reasons.append("Sector: Applicable to All Sectors")
                
            if profile.state and profile.state.lower() in s_state:
                reasons.append(f"Location Match: {profile.state.title()}")
            elif central_boost > 0:
                reasons.append("National Priority: Pan-India Availability")
                
            if profile.entityType and profile.entityType.lower() in (str(s.get("eligibility", "")) + s.get("description", "")).lower():
                reasons.append(f"Entity Suitability: {profile.entityType.title()}")
            
            if profile.gender == "Female" and ("women" in desc or "female" in desc):
                reasons.append("Exclusive Benefit: Women Entrepreneur Incentive")
            
            if funding_score >= 90:
                reasons.append("Funding Quality: High Grant/Subsidy Potential")

            s["match_reasons"] = reasons[:3]
            s["reasoning"] = f"Calculated match based on {len(reasons)} intelligence signals."
            s["ai_confidence"] = min(99, int(final_score))
            s["final_rank_score"] = final_score
            
            # Enrich scheme object for frontend metrics
            s["success_probability"] = success_prob
            s["policy_strength"] = policy_strength
            s["funding_quality"] = funding_score

        schemes.sort(key=lambda x: x["final_rank_score"], reverse=True)
        return schemes

class AgentOrchestrator:
    """Phase 4: The 'Decision Brain' that coordinates between modules."""
    @staticmethod
    async def orchestrate_discovery(profile: Profile):
        # STAGE 1: SOFT FILTERING (STRICT GEOGRAPHIC & TECHNICAL CONSTRAINTS)
        # ---------------------------------------------------------
        filtered = []
        for s in schemes:
            # 1. Sector Check
            if not sector_matches(profile.sector, str(s.get("sector", ""))):
                continue
            
            # 2. State Check (Hard Constraint - No Cross-Contamination)
            state_val = str(s.get("state", "")).lower()
            if profile.state and profile.state.lower() != "all india":
                state_match = (
                    profile.state.lower() in state_val
                    or "central" in state_val
                    or "india"   in state_val
                    or state_val == "all"
                )
            else:
                state_match = "central" in state_val or "india" in state_val or "all" in state_val
                
            if not state_match:
                continue

            # 3. Entity Type Keyword Check (Soft Filtering)
            entity_val = profile.entityType.lower()
            if entity_val and entity_val != "all entities":
                elig_text = " ".join(s.get("eligibility_criteria", [])).lower()
                combined = elig_text + " " + str(s.get("description", "")).lower()
                if entity_val == "proprietorship" and any(k in combined for k in ["private limited", "public limited", "incorporated entity"]):
                    if not any(k in combined for k in ["proprietor", "individual", "msme"]):
                        continue
                elif "limited" in entity_val and any(k in combined for k in ["street vendor", "individual only"]):
                    if not any(k in combined for k in ["company", "corporate", "msme"]):
                        continue

            filtered.append(s)

        # STAGE 2: SEMANTIC MATCHING (RANKING WITHIN FILTERED SUBSET)
        # ---------------------------------------------------------
        intel = ProfileIntelligenceEngine.enrich(profile)
        qvec = intel["profile_vector"]
        
        # We search the full table but then only take those that passed Stage 1
        vector_results = tbl.search(qvec).limit(100).to_pandas()
        vector_ids = set(vector_results["scheme_code"].tolist())
        
        # Discovery pool: Intersection of Stage 1 (Hard Filters) and Stage 2 (Top Semantic Hits)
        discovery_pool = [s for s in filtered if (s.get("scheme_code") in vector_ids or s.get("scheme_id") in vector_ids)]
        
        # If pool is too small, fill it up from 'filtered' list ordered by simple sector match
        if len(discovery_pool) < 20:
            already_ids = {s.get("scheme_code") for s in discovery_pool} | {s.get("scheme_id") for s in discovery_pool}
            # ONLY add from filtered list (which already passed hard constraints)
            for s in filtered:
                sid = s.get("scheme_code") or s.get("scheme_id")
                if sid not in already_ids:
                    discovery_pool.append(s)
                    already_ids.add(sid)
                if len(discovery_pool) >= 30: break

        if not discovery_pool: 
            discovery_pool = filtered[:25]

        # STAGE 3: MULTI-FACTOR RANKING (Phase 6)
        # ---------------------------------------------------------
        results = []
        for s in discovery_pool:
            r = ensure_youtube(s)
            r["timeline_days"] = detect_timeline(r)
            r["eligibility_score"] = eligibility_score(profile, r)
            r["priority_bucket"] = 3 if r["timeline_days"] < 60 else (2 if r["timeline_days"] < 120 else 1)
            results.append(r)
            
        ranked_results = MultiFactorRankingEngine.rank(profile, results)
        return ranked_results

# ─── RECOMMEND ENDPOINT ───────────────────────────────────────────────────────

@app.post("/v1/recommend")
async def recommend(profile: Profile):
    try:
        lang_code = normalize_language_code(profile.language)
        lang_display = language_display_name(lang_code)
        logger.info(f"Recommend request received. Language: {lang_code} ({lang_display})")
        results = await AgentOrchestrator.orchestrate_discovery(profile)
        
        # Phase 8: Dynamic Content Translation (Only for the top results to maintain speed)
        if not is_english_language(lang_code):
            top_results = results[:15]
            logger.info(f"Triggering dynamic translation for {len(top_results)} schemes into {lang_display}")
            translated_top = await translate_batch(top_results, lang_code)
            results = translated_top + results[15:]
        else:
            logger.info(f"Skipping dynamic translation (lang: {lang_code})")
            
        return {
            "schemes": results,
            "total_schemes": len(schemes),
            "matched_count": len(results),
            "intelligence_state": "Advanced Orchestration Active"
        }
    except Exception as e:
        logger.error(f"Orchestration failed: {e}")
        raise HTTPException(status_code=500, detail="Intelligence Engine Error")

async def translate_batch(items: List[dict], target_lang: str) -> List[dict]:
    """Translates a batch of scheme metadata using the AI core."""
    lang_code = normalize_language_code(target_lang)
    if not items or is_english_language(lang_code):
        return items

    target_display = language_display_name(lang_code)
    translated_items = [dict(item) for item in items]
    
    # 1. Prepare batch context
    batch_data = []
    for it in translated_items:
        batch_data.append({
            "id": it.get("scheme_id"),
            "name": it.get("scheme_name") or it.get("Scheme_Name"),
            "desc": it.get("description") or it.get("Scheme_Description")
        })
    
    prompt = f"""
    TASK: Translate the following Indian Government Scheme metadata into {target_display}.
    JSON INPUT: {json.dumps(batch_data, ensure_ascii=False)}
    
    RULES:
    1. Maintain the JSON structure.
    2. Translate 'name' and 'desc' accurately.
    3. Keep acronyms like (CGTMSE, MUDRA, PLI) in brackets if they exist.
    4. Do not make the output bilingual.
    5. Use only {target_display} for explanatory text.
    6. RETURN ONLY THE RAW JSON ARRAY. No preamble.
    """
    
    logger.info(f"AI Translation Request for {target_display}...")
    try:
        translated_text = await run_text_completion(
            prompt,
            system=(
                f"You are a JSON translation engine for Indian government scheme metadata. "
                f"Translate only into {target_display} and return raw JSON."
            ),
            temperature=0.2,
            max_tokens=3200,
        )
        
        if translated_text:
            # Clean possible markdown wrap
            cleaned = translated_text.strip()
            if cleaned.startswith("```json"): cleaned = cleaned[7:]
            if cleaned.startswith("```"): cleaned = cleaned[3:]
            if cleaned.endswith("```"): cleaned = cleaned[:-3]
            
            translated_list = json.loads(cleaned)
            if isinstance(translated_list, dict):
                translated_list = translated_list.get("items", [])
            mapping = {t["id"]: t for t in translated_list if "id" in t}
            
            # 2. Update the original items
            for it in translated_items:
                sid = it.get("scheme_id")
                if sid in mapping:
                    it["scheme_name"] = mapping[sid].get("name", it.get("scheme_name"))
                    it["description"] = mapping[sid].get("desc", it.get("description"))
    except Exception as e:
        logger.warning(f"Batch translation failed: {e}. Falling back to English.")
        
    return translated_items


class ChatSchemeRequest(BaseModel):
    scheme_id: str
    message: str
    language: str = "en"


class UITranslationRequest(BaseModel):
    texts: List[str] = []
    language: str = "en"


def _clean_scheme_item(value: Any) -> str:
    text = str(value or "").strip().strip("'\"[]")
    text = re.sub(r"^\s*(?:step\s*\d+[:.)-]*|\d+[:.)-]*|[-*•])\s*", "", text, flags=re.IGNORECASE)
    return text.strip()


def _list_from_value(value: Any) -> List[str]:
    if isinstance(value, list):
        raw_items = value
    elif isinstance(value, str):
        raw_items = re.split(r"[\n;|]+", value)
        if len(raw_items) <= 1 and "," in value:
            raw_items = value.split(",")
    else:
        raw_items = []
    return dedupe_strings([_clean_scheme_item(item) for item in raw_items if _clean_scheme_item(item)])


def _scheme_text(scheme: Dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = scheme.get(key)
        if isinstance(value, list):
            items = _list_from_value(value)
            if items:
                return "; ".join(items)
        else:
            text = str(value or "").strip()
            if text and text.lower() not in {"none", "null", "undefined", "nan"}:
                return text
    return ""


def _scheme_list(scheme: Dict[str, Any], *keys: str) -> List[str]:
    for key in keys:
        items = _list_from_value(scheme.get(key))
        if items:
            return items
    return []


def build_structured_scheme_brief(
    query: str,
    scheme: Dict[str, Any],
    rag_result: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    q = (query or "").lower().strip()
    rag_result = rag_result or {}

    def useful_text(value: Any) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        if text.lower() in {"none", "null", "undefined", "nan", "n/a", "na", "#"}:
            return ""
        return re.sub(r"\s+", " ", text).strip()

    name = _scheme_text(scheme, "scheme_name", "Scheme_Name", "name") or "Government Support Scheme"
    desc = _scheme_text(
        scheme,
        "detailed_description",
        "description",
        "Scheme_Description",
        "benefits_summary",
        "overview",
    )
    authority = _scheme_text(scheme, "authority", "ministry", "Ministry")
    funding = _scheme_text(scheme, "funding_type", "Funding_Type", "support_type")
    state = _scheme_text(scheme, "state", "State_Applicable")
    sector = _scheme_text(scheme, "sector", "Target_Sector", "target_sector")
    audience = _scheme_text(scheme, "target_audience", "Target_Audience", "beneficiaries")
    timeline = _scheme_text(scheme, "timeline_days", "Timeline_Days")
    link = _scheme_text(scheme, "official_link", "Website_URL", "website_url", "website") or "#"

    eligibility = _scheme_list(scheme, "eligibility_criteria", "Eligibility_Criteria")
    if not eligibility:
        eligibility = _list_from_value(_scheme_text(scheme, "eligibility"))

    docs = _scheme_list(
        scheme,
        "required_documents",
        "ai_required_documents",
        "documents_required",
        "documents",
        "docs",
    )
    if not docs:
        docs = _list_from_value(rag_result.get("required_documents"))

    steps = _scheme_list(
        scheme,
        "application_steps",
        "ai_application_steps",
        "procedure",
        "procedures",
        "Application_Process",
        "application_process",
    )
    if not steps:
        steps = _list_from_value(rag_result.get("application_steps"))

    desc = useful_text(desc)
    authority = useful_text(authority)
    funding = useful_text(funding)
    state = useful_text(state)
    sector = useful_text(sector)
    audience = useful_text(audience)
    timeline = useful_text(timeline)
    eligibility = dedupe_strings([useful_text(item) for item in eligibility if useful_text(item)])
    docs = dedupe_strings([useful_text(item) for item in docs if useful_text(item)])
    steps = dedupe_strings([useful_text(item) for item in steps if useful_text(item)])

    rag_note = useful_text(rag_result.get("answer", ""))
    rag_note = re.sub(r"^###.*?$", "", rag_note, flags=re.MULTILINE).strip()

    is_elig = any(word in q for word in ["eligib", "eligible", "criteria", "qualify", "qualification", "who can"])
    is_docs = any(word in q for word in ["document", "docs", "certificate", "proof", "upload", "required"])
    is_apply = any(word in q for word in ["apply", "application", "procedure", "process", "steps", "roadmap", "register"])
    is_benefit = any(word in q for word in ["benefit", "fund", "subsidy", "grant", "loan", "support", "equity", "amount"])
    is_overview = any(word in q for word in ["what is", "about", "overview", "summary", "details", "explain", "describe"])
    is_general = not any([is_elig, is_docs, is_apply, is_benefit, is_overview])

    title = name
    if authority and authority.lower() not in name.lower():
        title = f"{name} - {authority}"

    sections: List[str] = [f"### {title} - Strategic Intelligence"]

    if is_general or is_overview or is_benefit:
        if desc:
            sections.append(desc)
        else:
            sections.append(f"{name} is a government support scheme. Refer to the official portal for the most current operational details.")

        highlight_lines = []
        if funding:
            highlight_lines.append(f"- Funding type: {funding}")
        if authority:
            highlight_lines.append(f"- Implementing authority: {authority}")
        if state:
            highlight_lines.append(f"- Coverage: {state}")
        if sector:
            highlight_lines.append(f"- Sector focus: {sector}")
        if audience:
            highlight_lines.append(f"- Target beneficiaries: {audience}")
        if timeline:
            timeline_text = f"{timeline} days" if str(timeline).isdigit() else str(timeline)
            highlight_lines.append(f"- Typical timeline: {timeline_text}")
        if highlight_lines:
            sections.append("#### Key Highlights\n" + "\n".join(highlight_lines))

    if is_general or is_elig:
        if eligibility:
            sections.append("#### Strategic Eligibility\n" + "\n".join(f"- {item}" for item in eligibility[:8]))
        elif is_elig:
            sections.append("#### Strategic Eligibility\n- The current dataset does not specify detailed eligibility for this scheme. Please refer to the official portal.")

    if is_general or is_apply:
        if steps:
            split_at = (len(steps) + 1) // 2 if len(steps) > 4 else len(steps)
            roadmap_lines = ["#### Tactical Application Roadmap"]
            first_phase = steps[:split_at]
            second_phase = steps[split_at:]
            if len(steps) > 4:
                roadmap_lines.append("")
                roadmap_lines.append("**Phase 1: Registration**")
                roadmap_lines.extend(f"{idx}. {step}" for idx, step in enumerate(first_phase, start=1))
                if second_phase:
                    roadmap_lines.append("")
                    roadmap_lines.append("**Phase 2: Submission**")
                    roadmap_lines.extend(f"{idx}. {step}" for idx, step in enumerate(second_phase, start=1))
            else:
                roadmap_lines.extend(f"{idx}. {step}" for idx, step in enumerate(first_phase, start=1))
            sections.append("\n".join(roadmap_lines))
        elif is_apply:
            sections.append("#### Tactical Application Roadmap\n1. Visit the official portal.\n2. Confirm the current application route and registration requirements.\n3. Prepare your documents before submission.")

    if is_general or is_docs or is_apply:
        if docs:
            sections.append("#### Required Documentation\n" + "\n".join(f"- {item}" for item in docs[:10]))
        elif is_docs:
            sections.append("#### Required Documentation\n- The current dataset does not specify the exact document list. Please verify the official portal before applying.")

    if rag_note and (is_benefit or is_general) and normalize_phrase(rag_note) != normalize_phrase(desc):
        sections.append(f"#### Advisory Note\n{rag_note}")

    if link and link != "#":
        sections.append(f"#### Official Portal\nVisit Official Website: [Official Link]({link})")
    else:
        sections.append("#### Official Portal\nThe current dataset does not specify an official portal link.")

    return {
        "reply": "\n\n".join(section for section in sections if section.strip()),
        "required_documents": docs,
        "application_steps": steps,
    }

# ─── LLM ADVISOR CORE ──────────────────────────────────────────────────────────

async def get_llm_structured_response(query: str, context: str, lang: str = "en") -> str:
    """Uses the configured LLM fallback chain to generate a structured response."""
    lang_code = normalize_language_code(lang)
    lang_display = language_display_name(lang_code)
    
    prompt = f"""
    ROLE: You are the Senior KARIOS Strategic Advisor, a laser-focused AI similar to Gemini or Claude.
    
    CONTEXT DATA:
    {context}
    
    USER QUERY: {query}
    LANGUAGE: {lang_display}
    
    TASK: Answer the user's query using ONLY the provided context. 
    
    INSTRUCTIONS:
    1. RESPOND ONLY IN THE REQUESTED LANGUAGE ({lang_display}). This is a critical requirement.
    2. Do NOT mix English or any other language in the body of the answer.
    3. The only allowed exceptions are official scheme names, legal acronyms, portal names, URLs, and statutory identifiers.
    4. If a technical term has a natural translation, use it in {lang_display}.
    5. Be DIRECT. If the user asks a specific question (e.g. "What documents?"), provide ONLY that information.
    6. Use professional Markdown headers (###, ####) ONLY for the sections the user requested.
    7. TONE: Objective, expert, and conversational. No introductory filler.
    8. DATA INTEGRITY: If the context doesn't contain the specific answer, state that "The current dataset does not specify [X], please refer to the official portal." in {lang_display}.
    """

    try:
        return await run_text_completion(
            prompt,
            system=(
                f"Professional funding advisor. Respond only in {lang_display}. "
                "Do not output bilingual content unless an official acronym or proper noun must stay as-is."
            ),
            temperature=0.4,
            max_tokens=2200,
        )
    except Exception as e:
        logger.error(f"Structured advisor completion error: {e}")

    # Premium rule-based fallback when no provider is available
    return build_premium_fallback(query, context, lang_display)

def build_premium_fallback(query: str, context: str, lang: str) -> str:
    """A high-fidelity structured template that mirrors Gemini/Claude output with intent-filtering."""
    q = query.lower()
    lines = context.split("\n")
    data = {}
    for line in lines:
        if ":" in line:
            parts = line.split(":", 1)
            k = parts[0].strip().lower()
            v = parts[1].strip()
            if v.startswith("[") and v.endswith("]"):
                try: v = ", ".join(eval(v))
                except: pass
            data[k] = v

    name = data.get("scheme", data.get("scheme name", data.get("scheme_name", "Government Support Scheme")))
    link = data.get("official link", data.get("link", data.get("official_link", "#")))
    desc = data.get("summary", data.get("description", data.get("overview", "")))
    
    # Simple fallback localization for headers
    loc = {
        "English": {"briefing": "Strategic Intelligence", "elig": "⚖️ Strategic Eligibility", "roadmap": "⚙️ Tactical Application Roadmap", "docs": "📋 Required Documentation", "portal": "🌐 Official Portal", "phase1": "Phase 1: Registration", "phase2": "Phase 2: Submission", "visit": "Visit Official Website"},
        "Hindi (हिन्दी)": {"briefing": "रणनीतिक खुफिया", "elig": "⚖️ रणनीतिक पात्रता", "roadmap": "⚙️ सामरिक अनुप्रयोग रोडमैप", "docs": "📋 आवश्यक दस्तावेज", "portal": "🌐 आधिकारिक पोर्टल", "phase1": "चरण 1: पंजीकरण", "phase2": "चरण 2: सबमिशन", "visit": "आधिकारिक वेबसाइट पर जाएं"},
        "Marathi (मराठी)": {"briefing": "धोरणात्मक बुद्धिमत्ता", "elig": "⚖️ धोरणात्मक पात्रता", "roadmap": "⚙️ सामरिक अनुप्रयोग रोडमॅप", "docs": "📋 आवश्यक दस्तऐवज", "portal": "🌐 अधिकृत पोर्टल", "phase1": "टप्पा 1: नोंदणी", "phase2": "टप्पा 2: सबमिशन", "visit": "अधिकृत वेबसाइटला भेट द्या"},
        "Tamil (தமிழ்)": {"briefing": "மூலோபாய நுண்ணறிவு", "elig": "⚖️ மூலோபாய தகுதி", "roadmap": "⚙️ தந்திரோபாய விண்ணப்ப வரைபடம்", "docs": "📋 தேவையான ஆவணங்கள்", "portal": "🌐 அதிகாரப்பூர்வ போர்டல்", "phase1": "கட்டம் 1: பதிவு", "phase2": "கட்டம் 2: சமர்ப்பித்தல்", "visit": "அதிகாரப்பூர்வ வலைத்தளத்தைப் பார்வையிடவும்"},
        "Telugu (తెలుగు)": {"briefing": "వ్యూహాత్మక గూఢచారి", "elig": "⚖️ వ్యూహాత్మక అర్హత", "roadmap": "⚙️ వ్యూహాత్మక అప్లికేషన్ రోడ్‌మ్యాప్", "docs": "📋 అవసరమైన పత్రాలు", "portal": "🌐 అధికారిక పోర్టల్", "phase1": "దశ 1: నమోదు", "phase2": "దశ 2: సమర్పణ", "visit": "అధికారిక వెబ్‌సైట్‌ను సందర్శించండి"},
        "Kannada (ಕನ್ನಡ)": {"briefing": "ಕಾರ್ಯತಂತ್ರದ ಬುದ್ಧಿವಂತಿಕೆ", "elig": "⚖️ ಕಾರ್ಯತಂತ್ರದ ಅರ್ಹತೆ", "roadmap": "⚙️ ಯುದ್ಧತಂತ್ರದ ಅಪ್ಲಿಕೇಶನ್ ಮಾರ್ಗಸೂಚಿ", "docs": "📋 ಅಗತ್ಯ ದಾಖಲೆಗಳು", "portal": "🌐 ಅಧಿಕೃತ ಪೋರ್ಟಲ್", "phase1": "ಹಂತ 1: ನೋಂದಣಿ", "phase2": "ಹಂತ 2: ಸಲ್ಲಿಕೆ", "visit": "ಅಧಿಕೃತ ವೆಬ್‌ಸೈಟ್‌ಗೆ ಭೇಟಿ ನೀಡಿ"},
        "Malayalam (മലയാളം)": {"briefing": "തന്ത്രപരമായ ഇന്റലിജൻസ്", "elig": "⚖️ തന്ത്രപരമായ യോഗ്യത", "roadmap": "⚙️ തന്ത്രപരമായ ആപ്ലിക്കേഷൻ റോഡ്‌മാപ്പ്", "docs": "📋 ആവശ്യമായ രേഖകൾ", "portal": "🌐 ഔദ്യോഗിക പോർട്ടൽ", "phase1": "ഘട്ടം 1: രജിസ്ട്രേഷൻ", "phase2": "ഘട്ടം 2: സമർപ്പിക്കൽ", "visit": "ഔദ്യോഗിക വെബ്സൈറ്റ് സന്ദർശിക്കുക"}
    }
    
    # Default to English if lang not found
    l = loc.get(lang, loc["English"])

    # Intent detection
    is_elig   = any(w in q for w in ["eligib","eligible","who can","criteria","qualify"])
    is_docs   = any(w in q for w in ["document","doc","proof","required","upload"])
    is_apply  = any(w in q for w in ["apply","application","step","process","how to"])
    is_about  = any(w in q for w in ["what is","about","explain","details","describe","overview"])
    is_general = not (is_elig or is_docs or is_apply or is_about)

    resp = f"### {name} — {l['briefing']}\n\n"
    
    if is_about or is_general:
        if desc: resp += f"{desc}\n\n"
        
    if is_elig or is_general:
        elig_raw = data.get("eligibility", data.get("eligibility_criteria", ""))
        if elig_raw:
            resp += f"#### {l['elig']}\n"
            for item in elig_raw.replace(";", ",").split(","):
                item = item.strip().strip("'\"[]")
                if item: resp += f"- {item}\n"
            resp += "\n"

    if is_apply or is_general:
        resp += f"#### {l['roadmap']}\n"
        proc_raw = data.get("procedures", data.get("procedure", "Check official portal for registration details."))
        steps = proc_raw.replace(";", "|").split("|")
        clean_steps = [s.strip().strip("'\"[]") for s in steps if s.strip()]
        if len(clean_steps) > 1:
            mid = (len(clean_steps) + 1) // 2
            resp += f"**{l['phase1']}**\n"
            for s in clean_steps[:mid]: resp += f"- {s}\n"
            resp += f"\n**{l['phase2']}**\n"
            for s in clean_steps[mid:]: resp += f"- {s}\n"
        else:
            resp += f"- {clean_steps[0] if clean_steps else 'Access official portal.'}\n"
        
    if is_docs or is_general:
        resp += f"\n#### {l['docs']}\n"
        docs_raw = data.get("documents", data.get("documents_required", ""))
        if docs_raw:
            for d in docs_raw.replace(";", ",").split(","):
                d = d.strip().strip("'\"[]")
                if d: resp += f"- {d}\n"
        else:
            resp += "- Refer to official portal for documents.\n"

    resp += f"\n#### {l['portal']}\n{l['visit']}: [Official Link]({link})\n"
    return resp

@app.post("/v1/chat/scheme")
async def chat_scheme(req: ChatSchemeRequest):
    lang_code = normalize_language_code(req.language)
    s = next((x for x in schemes if x.get("scheme_id") == req.scheme_id or x.get("scheme_code") == req.scheme_id), None)
    if not s:
        raise HTTPException(status_code=404, detail="Scheme not found")
    
    rag_result: Dict[str, Any] = {}
    try:
        rag_result = await RAGIntelligence.get_grounded_answer(
            req.message,
            s,
            {},  # No profile for detail chat yet
            lang_code
        )
    except Exception as e:
        logger.warning(f"Scheme detail RAG fallback triggered: {e}")
    
    structured = build_structured_scheme_brief(req.message, s, rag_result)
    if not is_english_language(lang_code):
        structured["reply"] = await translate_text_block(structured["reply"], lang_code)
        structured["application_steps"] = await translate_text_items(structured.get("application_steps", []), lang_code)
        structured["required_documents"] = await translate_text_items(structured.get("required_documents", []), lang_code)
        
    return {
        "reply": structured["reply"],
        "official_link": s.get("official_link") or s.get("Website_URL"),
        "application_steps": structured.get("application_steps", []),
        "required_documents": structured.get("required_documents", [])
    }


@app.get("/health")
def health():
    return {"status": "ok", "schemes_loaded": len(schemes)}


@app.post("/v1/ui/translate")
async def ui_translate(req: UITranslationRequest):
    lang_code = normalize_language_code(req.language)
    translations = await translate_text_mapping(req.texts, lang_code)
    return {
        "language": lang_code,
        "translations": translations,
    }


@app.get("/v1/dashboard/stats")
async def dashboard_stats():
    # Phase 10: Aggregate system outputs into dashboard insights
    # In a real system, these would be user-specific from DB
    return {
        "schemes_indexed": len(schemes),
        "verified_docs": 0,  # Placeholder
        "funding_potential": "₹4.5Cr+",
        "readiness_index": 76,
        "recent_activity": [
            {"title": "Intelligence Enrichment", "status": "Active", "time": "Just now"},
            {"title": "Document Validation", "status": "Pending", "time": "2h ago"},
        ]
    }


@app.get("/v1/schemes/all")
async def all_schemes(limit: int = 50, offset: int = 0):
    # Paging support for standard browsing
    return {
        "schemes": schemes[offset : offset + limit],
        "total": len(schemes)
    }



# ─── CHAT ENDPOINT (FREE — no LLM API key needed) ────────────────────────────


def build_chat_answer(query: str, scheme: dict, profile: dict) -> dict:
    """
    Rule-based chatbot — answers questions about a scheme using its stored data.
    Zero external API calls. Works offline. Handles the 5 main intents.
    """
    q = query.lower().strip()

    # ── Field helpers ──────────────────────────────────────────────────────
    def f(*keys):
        for k in keys:
            v = str(scheme.get(k, "") or "").strip()
            if v and v not in ("none","null","undefined",""):
                return v
        return ""

    name     = f("scheme_name","Scheme_Name","name")
    desc     = f("detailed_description","description","Scheme_Description","benefits_summary")
    elig     = f("eligibility","Eligibility_Criteria")
    ministry = f("authority","Ministry","ministry")
    state    = f("state","State_Applicable")
    sector   = f("sector","Target_Sector","target_sector")
    audience = f("target_audience","Target_Audience")
    website  = f("Website_URL","website_url","website")
    process  = f("Application_Process","application_process")
    funding  = f("funding_type","Funding_Type")
    timeline = scheme.get("timeline_days") or scheme.get("Timeline_Days") or ""

    docs  = scheme.get("required_documents")  or scheme.get("ai_required_documents")  or []
    steps = scheme.get("application_steps")   or scheme.get("ai_application_steps")   or []

    if not isinstance(docs,  list): docs  = []
    if not isinstance(steps, list): steps = []

    # ── Intent detection ───────────────────────────────────────────────────
    is_elig   = any(w in q for w in ["eligib","eligible","who can","criteria","qualify","qualification"])
    is_docs   = any(w in q for w in ["document","docs","certificate","proof","required","need to submit","upload"])
    is_apply  = any(w in q for w in ["apply","application","how to","step","process","procedure","register","enroll"])
    is_benefit= any(w in q for w in ["benefit","amount","fund","subsidy","grant","loan","support","how much","₹","rs.","lakh","crore"])
    is_about  = any(w in q for w in ["what is","about","explain","tell me","describe","overview","summary"])

    # ── Build answer ───────────────────────────────────────────────────────

    if is_elig:
        if elig:
            lines = [l.strip() for l in elig.replace(";","\n").split("\n") if l.strip()]
            return {
                "answer": f"Eligibility criteria for {name}:",
                "application_steps": lines[:12],
                "required_documents": [],
                "suggested_actions": ["Check if you qualify", "Prepare required documents"],
            }
        return {
            "answer": f"Eligibility details for {name} are not available in our database yet. "
                      f"Please check the official portal{f': {website}' if website else ''}.",
            "suggested_actions": [f"Visit {website}" if website else "Check official government portal"],
        }

    if is_docs:
        if docs:
            return {
                "answer": f"Required documents for {name} ({len(docs)} total):",
                "required_documents": [str(d) for d in docs],
                "suggested_actions": ["Gather all documents", "Ensure copies are self-attested"],
            }
        # Generic Indian govt document set
        generic = [
            "Aadhaar Card of promoter(s)",
            "PAN Card of promoter and entity",
            "Udyam Registration Certificate",
            "Business constitution proof (MOA/AOA/Partnership deed)",
            "Bank account statement (last 6 months)",
            "Project Report / DPR",
            "GST Registration Certificate (if registered)",
            "Passport-size photographs",
        ]
        return {
            "answer": f"Standard documents typically required for {name}:",
            "required_documents": generic,
            "suggested_actions": [f"Verify exact list at official portal{': ' + website if website else ''}"],
        }

    if is_apply:
        if steps:
            return {
                "answer": f"Step-by-step application process for {name}:",
                "application_steps": [str(s) for s in steps],
                "required_documents": [],
                "suggested_actions": [f"Apply online: {website}" if website else "Visit official portal to apply"],
            }
        # Generic flow
        generic_steps = [
            f"Visit the official portal{': ' + website if website else ' for ' + (ministry or 'the implementing authority')}",
            "Register / create a new applicant account using your Aadhaar-linked mobile number",
            "Fill the online application form with business and promoter details",
            "Upload all required documents (Aadhaar, PAN, Udyam certificate, project report)",
            "Review the application and submit",
            "Note the application reference number for tracking",
            "Verification and site inspection may be conducted by the authority",
            "Approval / sanction letter will be sent to your registered email",
            "Post-approval: submit utilisation certificate and compliance reports as required",
        ]
        return {
            "answer": f"General application steps for {name}:",
            "application_steps": generic_steps,
            "suggested_actions": [f"Apply at: {website}" if website else "Search for official portal online"],
        }

    if is_benefit:
        benefit_parts = []
        if desc:    benefit_parts.append(desc)
        if funding: benefit_parts.append(f"Support type: {funding}.")
        if timeline:benefit_parts.append(f"Expected processing time: {timeline} days.")
        if benefit_parts:
            return {
                "answer": " ".join(benefit_parts),
                "suggested_actions": ["Check exact amounts on official portal"],
            }

    # Default — about / general
    about_parts = []
    if desc:     about_parts.append(desc)
    if ministry: about_parts.append(f"Implemented by: {ministry}.")
    if state and state.lower() not in ("india","all"):
        about_parts.append(f"Applicable in: {state}.")
    if audience: about_parts.append(f"Target beneficiaries: {audience}.")
    if timeline: about_parts.append(f"Processing time: {timeline} days.")

    return {
        "answer": " ".join(about_parts) if about_parts else f"{name} is a government support scheme. Please check the official portal for complete details.",
        "suggested_actions": [
            "Ask about eligibility",
            "Ask for required documents",
            "Ask how to apply",
        ],
    }


# ─── PHASE 9: RAG CONVERSATIONAL INTELLIGENCE ──────────────────────────

LOCALIZED_GREETINGS = {
    "Hindi (हिन्दी)": "नमस्ते! मैं कैरियोस इंटेलिजेंस हूँ। आपकी सहायता के लिए तैयार हूँ।",
    "Marathi (मराठी)": "नमस्कार! मी कॅरिओस इंटेलिजन्स आहे. तुम्हाला मदत करण्यास तयार आहे.",
    "Bengali (বাংলা)": "নমস্তে! আমি কারিওস ইন্টেলিজেন্স। আপনার সহায়তায় প্রস্তুত।",
    "Tamil (தமிழ்)": "வணக்கம்! நான் காரியோஸ் இன்டெலிஜென்ஸ். உங்களுக்கு உதவ தயார்.",
    "Telugu (తెలుగు)": "నమస్తే! నేను కారియోస్ ఇంటెలిజెన్స్. మీకు సహాయం చేయడానికి సిద్ధంగా ఉన్నాను."
}

class RAGIntelligence:
    """Phase 9: Pipeline for grounded Conversational Guidance using LanceDB fields."""
    @staticmethod
    async def get_grounded_answer(query: str, active_scheme: dict, profile: dict, language: str = "en") -> dict:
        lang_code = normalize_language_code(language)
        qvec = model.encode(query).tolist()
        s_code = active_scheme.get("scheme_code") or active_scheme.get("scheme_id")
        
        context_parts = []
        source = "KARIOS Knowledge Base"
        
        # 1. RETRIEVE RELEVANT DATA
        try:
            if s_code:
                # PRECISION LOOKUP: Fetch directly from the in-memory dataset first
                scheme_data = next((s for s in schemes if s.get("scheme_code") == s_code or s.get("scheme_id") == s_code), None)
                
                if scheme_data:
                    # Saturated full record from authoritative source
                    context_parts.append(
                        f"### AUTHORITATIVE SCHEME DATA\n"
                        f"Scheme Name: {scheme_data.get('scheme_name')}\n"
                        f"Authority: {scheme_data.get('authority', scheme_data.get('ministry', 'Unknown'))}\n"
                        f"Sector: {scheme_data.get('sector')}\n"
                        f"Funding Type: {scheme_data.get('funding_type')}\n"
                        f"Overview: {scheme_data.get('description')}\n"
                        f"Eligibility: {scheme_data.get('eligibility_criteria')}\n"
                        f"Procedure: {'; '.join(scheme_data.get('procedure')) if isinstance(scheme_data.get('procedure'), list) else scheme_data.get('procedure')}\n"
                        f"Documents: {', '.join(scheme_data.get('documents_required')) if isinstance(scheme_data.get('documents_required'), list) else scheme_data.get('documents_required')}\n"
                        f"Official Link: {scheme_data.get('official_link')}"
                    )
                
                # SUPPLEMENTAL Deep Dive: Search specialized fields for nuances
                res_fields = tbl_fields.search(qvec).where(f"scheme_code = '{s_code}'").limit(5).to_pandas()
                context_parts.extend([f"Nuance ({row.get('type','info')}): {row.get('text')}" for _, row in res_fields.iterrows()])
                
                source = active_scheme.get("scheme_name", s_code)
            else:
                # General Discovery: Search across ALL schemes in the dataset
                results = tbl.search(qvec).limit(3).to_pandas()
                for _, row in results.iterrows():
                    # Saturated Context for Gemini-style depth
                    context_parts.append(
                        f"Scheme Name: {row.get('scheme_name')}\n"
                        f"Authority: {row.get('authority', row.get('ministry', 'Unknown'))}\n"
                        f"Sector: {row.get('sector')}\n"
                        f"Funding Type: {row.get('funding_type')}\n"
                        f"Overview: {row.get('description')}\n"
                        f"Eligibility: {row.get('eligibility_criteria')}\n"
                        f"Procedure: {'; '.join(row.get('procedure')) if isinstance(row.get('procedure'), list) else row.get('procedure')}\n"
                        f"Documents: {', '.join(row.get('documents_required')) if isinstance(row.get('documents_required'), list) else row.get('documents_required')}\n"
                        f"Official Link: {row.get('official_link')}"
                    )
                if not results.empty:
                    source = f"Global Retrieval ({results.iloc[0]['scheme_name']})"
        except Exception as e:
            logger.error(f"RAG Retrieval Error: {e}")
            context_parts = ["Information grounded in standard MSME guidelines."]

        context = "\n---\n".join(context_parts)

        # 2. LLM GENERATION (Grounded in context)
        # We use the existing Advisor Core (Gemini/OpenAI/RuleFallback)
        answer = await get_llm_structured_response(query, context, lang_code)
        if "###" not in answer:
            heading = "### KARIOS Intelligence"
            if not is_english_language(lang_code):
                heading = await translate_text_block(heading, lang_code)
            answer = f"{heading}\n\n{answer}"

        # 3. STRUCTURED METADATA
        # If we have a specific scheme, extract its metadata for the UI
        top_meta = active_scheme if s_code else {}
        if not s_code and 'results' in locals() and not results.empty:
            top_meta = results.iloc[0].to_dict()

        required_documents = _scheme_list(
            top_meta,
            "required_documents",
            "documents_required",
            "documents",
            "docs",
        )[:5]
        if not required_documents:
            required_documents = [
                d.strip()
                for d in str(top_meta.get("documents", top_meta.get("required_documents", ""))).split(",")
                if d.strip()
            ][:5]

        application_steps = _scheme_list(
            top_meta,
            "application_steps",
            "procedure",
            "procedures",
            "Application_Process",
            "application_process",
        )[:5]
        if not application_steps:
            application_steps = [
                s.strip()
                for s in str(top_meta.get("procedure", "")).split(";")
                if s.strip()
            ][:5]

        suggested_actions = ["Verify Eligibility", "View Official Portal", "Expert Consultation"]
        ai_reasoning = f"Grounded in {len(context_parts)} specialized data points from your custom dataset."

        if not is_english_language(lang_code):
            required_documents = await translate_text_items(required_documents, lang_code)
            application_steps = await translate_text_items(application_steps, lang_code)
            suggested_actions = await translate_text_items(suggested_actions, lang_code)
            ai_reasoning = await translate_text_block(ai_reasoning, lang_code)

        return {
            "answer": answer,
            "grounding_source": [source],
            "required_documents": required_documents,
            "application_steps": application_steps,
            "suggested_actions": suggested_actions,
            "ai_reasoning": ai_reasoning,
        }

# ─── PHASE 10: SELECTIVE DOCUMENT INTELLIGENCE ─────────────────────────

COMMON_REQUIRED_DOCUMENTS = [
    "Aadhaar Card",
    "PAN Card",
    "Udyam Registration Certificate",
    "GST Certificate",
    "Bank Statement",
    "Project Report / DPR",
]

SUPPORTED_UPLOAD_CONTENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
}

SUPPORTED_UPLOAD_SUFFIXES = {
    ".pdf",
    ".doc",
    ".docx",
    ".jpeg",
    ".jpg",
    ".png",
    ".webp",
}

DOCUMENT_SYNONYMS = {
    "aadhaar card": ["aadhaar", "aadhar", "uidai"],
    "pan card": ["pan", "permanent account"],
    "udyam registration certificate": ["udyam", "udyog aadhaar", "udyog", "msme registration"],
    "gst certificate": ["gst", "gstin", "goods and services tax"],
    "bank statement": ["bank statement", "statement", "cancelled cheque", "bank passbook"],
    "project report / dpr": ["project report", "dpr", "detailed project report", "business plan"],
    "partnership deed / moa": ["partnership deed", "moa", "aoa", "incorporation certificate", "llp agreement"],
    "itr": ["itr", "income tax return"],
    "ca certificate": ["ca certificate", "chartered accountant", "net worth certificate"],
    "photograph": ["photograph", "photo", "passport size"],
    "business address proof": ["address proof", "utility bill", "rent agreement", "electricity bill"],
    "caste certificate": ["caste certificate", "sc certificate", "st certificate", "obc certificate"],
}

DOCUMENT_STOP_WORDS = {
    "and",
    "card",
    "certificate",
    "copy",
    "document",
    "for",
    "last",
    "months",
    "of",
    "proof",
    "registration",
    "size",
    "statement",
    "the",
    "years",
}


def normalize_phrase(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def canonical_document_name(value: Any) -> str:
    text = normalize_phrase(value)
    if not text:
        return ""

    for canonical, aliases in DOCUMENT_SYNONYMS.items():
        if text == canonical or any(alias in text for alias in aliases):
            return canonical

    return ""


def document_tokens(value: Any) -> set[str]:
    return {
        token
        for token in normalize_phrase(value).split()
        if token and token not in DOCUMENT_STOP_WORDS
    }


def documents_match(left: Any, right: Any) -> bool:
    left_text = normalize_phrase(left)
    right_text = normalize_phrase(right)
    if not left_text or not right_text:
        return False

    left_canonical = canonical_document_name(left_text)
    right_canonical = canonical_document_name(right_text)

    if left_canonical and right_canonical:
        return left_canonical == right_canonical

    if left_text == right_text:
        return True

    left_tokens = document_tokens(left_text)
    right_tokens = document_tokens(right_text)
    if left_tokens and right_tokens:
        overlap = len(left_tokens & right_tokens)
        min_size = min(len(left_tokens), len(right_tokens))
        if min_size and overlap / min_size >= 0.6:
            return True

    return SequenceMatcher(None, left_text, right_text).ratio() >= 0.74


def dedupe_strings(items: List[str]) -> List[str]:
    output: List[str] = []
    seen: set[str] = set()
    for item in items:
        cleaned = str(item or "").strip()
        if not cleaned:
            continue
        key = normalize_phrase(cleaned)
        if key in seen:
            continue
        seen.add(key)
        output.append(cleaned)
    return output


def coerce_document_list(value: Any) -> List[str]:
    if isinstance(value, list):
        raw_items = value
    elif isinstance(value, str):
        raw_items = re.split(r"[\n;,]+", value)
    else:
        raw_items = []
    return dedupe_strings([str(item or "").strip() for item in raw_items])


def scheme_required_documents(scheme: Dict[str, Any] | None) -> List[str]:
    if not scheme:
        return COMMON_REQUIRED_DOCUMENTS[:]

    for key in (
        "required_documents",
        "ai_required_documents",
        "documents_required",
        "documents",
        "docs",
    ):
        docs = coerce_document_list(scheme.get(key))
        if docs:
            return docs

    return COMMON_REQUIRED_DOCUMENTS[:]


def resolve_scheme_reference(raw_scheme: Any = None, scheme_id: str = "") -> Dict[str, Any] | None:
    payload: Dict[str, Any] = {}

    if isinstance(raw_scheme, dict):
        payload = dict(raw_scheme)
    elif isinstance(raw_scheme, str) and raw_scheme.strip():
        raw_stripped = raw_scheme.strip()
        # Try JSON parse first (full scheme object sent as string)
        try:
            parsed = json.loads(raw_stripped)
            if isinstance(parsed, dict):
                payload = parsed
            # else it parsed to a non-dict (e.g. a quoted string) — keep as name lookup below
        except (json.JSONDecodeError, ValueError):
            pass

        # If JSON parse failed or yielded nothing useful, treat the raw string
        # as a scheme name / scheme_id for direct lookup.
        if not payload:
            # Try exact scheme_id / scheme_code match first
            for s in schemes:
                if (
                    str(s.get("scheme_id", "")).strip() == raw_stripped
                    or str(s.get("scheme_code", "")).strip() == raw_stripped
                ):
                    return s
            # Then try case-insensitive scheme_name match
            raw_lower = raw_stripped.lower()
            for s in schemes:
                sname = str(s.get("scheme_name") or s.get("Scheme_Name") or "").strip().lower()
                if sname and (sname == raw_lower or raw_lower in sname or sname in raw_lower):
                    return s

    # Build lookup list from every identifier in the payload
    lookup_values = list({
        str(v).strip()
        for v in [
            scheme_id,
            payload.get("scheme_id"),
            payload.get("scheme_code"),
            payload.get("id"),
            payload.get("scheme_name"),
            payload.get("Scheme_Name"),
            payload.get("name"),
        ]
        if str(v or "").strip()
    })

    if lookup_values:
        # Exact match pass
        for s in schemes:
            if any(
                str(s.get(field, "")).strip() == value
                for value in lookup_values
                for field in ("scheme_id", "scheme_code", "scheme_name", "Scheme_Name")
            ):
                return s
        # Partial / substring match pass (handles truncated names)
        for s in schemes:
            sname = str(s.get("scheme_name") or s.get("Scheme_Name") or "").strip().lower()
            if sname and any(
                v.lower() in sname or sname in v.lower()
                for v in lookup_values
            ):
                return s

    if payload:
        payload.setdefault("scheme_name", payload.get("name", "Selected Scheme"))
        payload.setdefault("scheme_id", payload.get("id", payload.get("scheme_id", "")))
        return payload

    return None


def file_type_supported(file_name: str, content_type: str) -> bool:
    suffix = Path(file_name or "").suffix.lower()
    return content_type in SUPPORTED_UPLOAD_CONTENT_TYPES or suffix in SUPPORTED_UPLOAD_SUFFIXES


class DocumentIntelligence:
    """Validates uploaded documents against the actively selected scheme."""

    @staticmethod
    def validate_document(doc_name: str, scheme_requirements: List[str]) -> dict:
        matched_requirement = next(
            (req for req in scheme_requirements if documents_match(doc_name, req)),
            None,
        )
        is_verified = matched_requirement is not None
        return {
            "status": "Verified" if is_verified else "Needs Review",
            "trust_score": 96 if is_verified else 48,
            "validation_mode": "Scheme Requirement Matching",
            "matched_requirement": matched_requirement,
            "required_documents": scheme_requirements,
        }

    @staticmethod
    def validate_upload(
        *,
        file_name: str,
        file_size: int,
        content_type: str,
        selected_document: str,
        scheme: Dict[str, Any],
    ) -> dict:
        requirements = scheme_required_documents(scheme)
        matched_requirement = next(
            (req for req in requirements if documents_match(selected_document, req)),
            None,
        )
        file_doc_type = canonical_document_name(file_name)
        selected_doc_type = canonical_document_name(selected_document)

        errors: List[Dict[str, str]] = []
        warnings: List[Dict[str, str]] = []
        confidence = 62

        if not file_type_supported(file_name, content_type):
            errors.append({"message": f"Unsupported file type: {content_type or 'unknown'}", "source": "system"})

        if file_size and file_size < 5 * 1024:
            errors.append({"message": "File too small or blank.", "source": "system"})

        if matched_requirement:
            confidence += 18
        else:
            errors.append({"message": "Selected document is not required for this scheme.", "source": "scheme"})

        if file_doc_type and selected_doc_type:
            if file_doc_type == selected_doc_type:
                confidence += 16
            else:
                errors.append(
                    {
                        "message": f"Filename looks like {file_doc_type.title()}, not {selected_doc_type.title()}.",
                        "source": "filename",
                    }
                )
        else:
            warnings.append(
                {
                    "message": "Filename does not clearly identify the uploaded document type.",
                    "source": "filename",
                }
            )

        if content_type.startswith("image/"):
            confidence += 4
        elif Path(file_name).suffix.lower() == ".pdf":
            confidence += 8

        confidence = max(5, min(confidence, 99))

        if errors:
            verdict = "mismatch" if any(err["source"] == "filename" for err in errors) else "invalid"
            status = "error"
            is_valid = False
        elif warnings:
            verdict = "invalid"
            status = "warn"
            is_valid = False
        else:
            verdict = "valid"
            status = "valid"
            is_valid = True

        scheme_name = scheme.get("scheme_name") or scheme.get("Scheme_Name") or "Selected Scheme"
        summary = (
            f"{selected_document} matches {scheme_name} requirements."
            if is_valid
            else errors[0]["message"] if errors
            else warnings[0]["message"]
        )

        return {
            "success": True,
            "status": status,
            "isValid": is_valid,
            "verdict": verdict,
            "documentType": selected_document,
            "matchedRequirement": matched_requirement,
            "requiredDocuments": requirements,
            "confidenceScore": confidence,
            "summary": summary,
            "fileName": file_name,
            "fileSize": file_size,
            "errors": errors,
            "warnings": warnings,
            "validationMode": "KARIOS Scheme-Aware Validation",
            "scheme": {
                "scheme_id": scheme.get("scheme_id") or scheme.get("scheme_code") or "",
                "scheme_name": scheme_name,
            },
        }

@app.post("/v1/chat")
async def chat(req: ChatRequest):
    query = req.query.strip()
    if not query:
        return {"answer": "Please ask a question.", "application_steps": [], "required_documents": []}

    active_scheme = req.schemes[0] if req.schemes else {}
    lang = normalize_language_code(req.language)
    
    # ── ADVANCED RAG INTEL ENGINE (Multi-Lingual) ──
    result = await RAGIntelligence.get_grounded_answer(query, active_scheme, req.profile, lang)
    return result

@app.post("/v1/validation/context")
async def validation_context(data: dict = Body(...)):
    lang_code = normalize_language_code(data.get("language"))
    scheme = resolve_scheme_reference(
        raw_scheme=data.get("scheme"),
        scheme_id=str(data.get("scheme_id", "")).strip(),
    )
    if not scheme:
        raise HTTPException(status_code=404, detail="Selected scheme not found")

    required_documents = scheme_required_documents(scheme)
    localized_documents = required_documents
    if not is_english_language(lang_code):
        localized_documents = await translate_text_items(required_documents, lang_code)
    required_document_labels = {
        doc: localized_documents[idx] if idx < len(localized_documents) else doc
        for idx, doc in enumerate(required_documents)
    }

    return {
        "scheme_id": scheme.get("scheme_id") or scheme.get("scheme_code") or "",
        "scheme_name": scheme.get("scheme_name") or scheme.get("Scheme_Name") or "Selected Scheme",
        "required_documents": required_documents,
        "required_document_labels": required_document_labels,
        "state": scheme.get("state") or scheme.get("State_Applicable") or "",
        "sector": scheme.get("sector") or scheme.get("Target_Sector") or "",
    }

@app.post("/v1/validate_doc")
async def validate_doc(data: dict = Body(...)):
    doc_name = str(data.get("doc_name", "")).strip()
    scheme = resolve_scheme_reference(
        raw_scheme=data.get("scheme"),
        scheme_id=str(data.get("scheme_id", "")).strip(),
    )

    if not doc_name:
        raise HTTPException(status_code=400, detail="doc_name is required")
    if not scheme:
        raise HTTPException(status_code=404, detail="Selected scheme not found")

    requirements = scheme_required_documents(scheme)
    result = DocumentIntelligence.validate_document(doc_name, requirements)
    return {
        **result,
        "scheme_name": scheme.get("scheme_name") or scheme.get("Scheme_Name") or "Selected Scheme",
    }



# ═══════════════════════════════════════════════════════════════════════════════
# DOCUMENT VALIDATION — AI VISION ENGINE
# Priority: Gemini -> Groq -> NVIDIA -> rule-based fallback
# Ignores filename — judges document content only
# ═══════════════════════════════════════════════════════════════════════════════

def _pdf_to_image_b64(pdf_bytes: bytes):
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pix = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2), colorspace=fitz.csRGB)
        return base64.b64encode(pix.tobytes("jpeg")).decode()
    except ImportError:
        logger.warning("PyMuPDF not installed. Run: pip install pymupdf")
        return None
    except Exception as e:
        logger.warning(f"PDF to image failed: {e}")
        return None


def _vision_prompt(doc_name: str, scheme_name: str) -> str:
    return (
        "You are a strict Indian government document verification officer.\n\n"
        f"The applicant selected document type: \"{doc_name}\"\n"
        f"Scheme: \"{scheme_name}\"\n\n"
        "Look carefully at the document image.\n\n"
        "Choose ONE verdict:\n"
        f"- \"valid\"    = This IS a \"{doc_name}\", genuine, readable, no SAMPLE/SPECIMEN stamp\n"
        "- \"mismatch\" = This is a DIFFERENT document type\n"
        "- \"invalid\"  = Correct type but blurry/tampered/SAMPLE stamp/key info missing\n\n"
        "RULES:\n"
        "- Ignore the filename completely\n"
        "- If you see Aadhaar/UIDAI logo but selected doc is PAN Card -> mismatch\n"
        "- detectedType = what document you actually see\n\n"
        "Reply ONLY with this JSON (no markdown):\n"
        "{\n"
        "  \"verdict\": \"valid|mismatch|invalid\",\n"
        "  \"detectedType\": \"what you see\",\n"
        "  \"govBody\": \"issuing authority\",\n"
        "  \"extractedFields\": {\"name\": null, \"number\": null, \"dob\": null},\n"
        "  \"errors\": [],\n"
        "  \"warnings\": [],\n"
        "  \"confidenceScore\": 85,\n"
        "  \"summary\": \"max 8 words\"\n"
        "}"
    )


def _parse_vision_json(text) -> dict:
    """Parse JSON from AI response. Safely handles None, empty, or malformed input."""
    if not text or not isinstance(text, str):
        logger.error(f"_parse_vision_json received non-string: {type(text)} — {str(text)[:80]}")
        return {}
    try:
        s = text.find("{")
        e = text.rfind("}") + 1
        if s != -1 and e > s:
            parsed = json.loads(text[s:e])
            return parsed if isinstance(parsed, dict) else {}
        return {}
    except Exception:
        logger.error(f"JSON parse failed: {text[:200]}")
        return {}


async def _try_gemini(image_b64: str, mime: str, prompt: str) -> str:
    if not genai_active:
        raise Exception("Gemini not configured")
    m = genai.GenerativeModel("gemini-2.0-flash")
    parts = [{"inline_data": {"data": image_b64, "mime_type": mime}}, prompt]
    try:
        result = m.generate_content(parts)
        text = result.text if result and hasattr(result, "text") else None
        if not text:
            raise Exception("Gemini returned empty response")
        return text
    except Exception as e:
        if "429" in str(e) or "quota" in str(e).lower():
            # Rate limited — skip immediately, let next provider handle it
            raise Exception(f"Gemini rate limited — skipping to next provider")
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
                "max_tokens": 800,
                "temperature": 0.1,
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
                "model": "microsoft/phi-3-vision-128k-instruct",
                "max_tokens": 800,
                "temperature": 0.1,
                "messages": [{"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_b64}"}},
                    {"type": "text", "text": prompt},
                ]}],
            },
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


async def _try_lmstudio_vision(image_b64: str, mime: str, prompt: str) -> str:
    """Send an image + prompt to a locally running LM Studio vision model."""
    base_url  = str(os.getenv("DOC_VERIFY_LMSTUDIO_BASE_URL", "") or "").strip().rstrip("/")
    model_name = str(os.getenv("DOC_VERIFY_LLM_MODEL", "") or "").strip()
    if not base_url or not model_name:
        raise Exception("LM Studio not configured (DOC_VERIFY_LMSTUDIO_BASE_URL / DOC_VERIFY_LLM_MODEL not set)")

    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(
            f"{base_url}/chat/completions",
            headers={"Content-Type": "application/json"},
            json={
                "model": model_name,
                "max_tokens": 800,
                "temperature": 0.1,
                "messages": [{"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_b64}"}},
                    {"type": "text", "text": prompt},
                ]}],
            },
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


async def _run_vision_ai(image_b64: str, mime: str, prompt: str) -> str:
    """
    Vision AI fallback chain: LM Studio → Gemini → Groq → NVIDIA.
    Tries each provider in order; returns the first successful result.
    """
    providers = [
        ("LM Studio", _try_lmstudio_vision,
         bool(os.getenv("DOC_VERIFY_LMSTUDIO_BASE_URL")) and bool(os.getenv("DOC_VERIFY_LLM_MODEL"))),
        ("Gemini",    _try_gemini,    genai_active),
        ("Groq",      _try_groq,      bool(os.getenv("GROQ_API_KEY"))),
        ("NVIDIA",    _try_nvidia,    bool(os.getenv("NVIDIA_API_KEY"))),
    ]

    last_err = None
    for name, fn, available in providers:
        if not available:
            continue
        try:
            result = await fn(image_b64, mime, prompt)
            if result and str(result).strip():
                logger.info(f"Vision AI served via {name}")
                return str(result).strip()
        except Exception as e:
            logger.warning(f"{name} vision failed: {str(e)[:120]}")
            last_err = e

    raise Exception(f"All vision AI providers failed: {last_err}")


def _rule_fallback(doc_name, file_name, file_size, mime, scheme):
    if not file_type_supported(file_name, mime):
        return {
            "success": True, "status": "error", "isValid": False,
            "verdict": "invalid", "documentType": doc_name,
            "errors": [{"message": "Unsupported format. Upload PDF, JPG or PNG.", "source": "system"}],
            "warnings": [], "confidenceScore": 0, "summary": "Unsupported format.",
        }
    if file_size < 5 * 1024:
        return {
            "success": True, "status": "error", "isValid": False,
            "verdict": "invalid", "documentType": doc_name,
            "errors": [{"message": "File too small or blank. Upload a clear document.", "source": "system"}],
            "warnings": [], "confidenceScore": 0, "summary": "File too small.",
        }
    return {
        "success": True, "status": "valid", "isValid": True,
        "verdict": "valid", "documentType": doc_name,
        "govBody": "", "extractedFields": {}, "errors": [],
        "warnings": [{"message": "No AI key active - accepted on file format only.", "source": "system"}],
        "confidenceScore": 55, "summary": "Accepted (no AI key configured).",
    }



# ═══════════════════════════════════════════════════════════════════════════════
# REAL-TIME STREAMING VALIDATION  — SSE endpoint
# Frontend connects once, receives step-by-step JSON events as they happen
# ═══════════════════════════════════════════════════════════════════════════════

from fastapi.responses import StreamingResponse
import asyncio as _asyncio
import json as _json

@app.post("/v1/validate_doc_stream")
async def validate_doc_stream(
    file:     UploadFile = File(...),
    doc_name: str        = Form(...),
    scheme:   str        = Form(...),
    language: str        = Form("en"),
):
    """
    Server-Sent Events endpoint.
    Streams validation progress events as:
      data: {"type":"step","step":"file_sanity","label":"...","status":"running","detail":""}
      data: {"type":"step","step":"file_sanity","label":"...","status":"passed","detail":"JPEG | 142 KB"}
      data: {"type":"result","isValid":true,"verdict":"valid",...}
    """
    t0        = time.time()
    file_bytes = await file.read()

    async def event_stream():
        import asyncio

        def sse(payload: dict) -> str:
            return f"data: {_json.dumps(payload, ensure_ascii=False)}\n\n"

        def step_event(step, label, status, detail=""):
            return sse({"type": "step", "step": step, "label": label,
                        "status": status, "detail": detail})

        # ── Rebuild a fake UploadFile so layered_validate can read it ──────
        from fastapi import UploadFile as _UF
        from io import BytesIO as _BytesIO
        from starlette.datastructures import UploadFile as _SUF

        fake_file = _SUF(
            file=_BytesIO(file_bytes),
            size=len(file_bytes),
            filename=file.filename or "upload",
            headers=file.headers,
        )

        # We run layered_validate in a thread-safe way but also want to
        # stream steps.  The simplest approach: duplicate the pipeline here,
        # yielding steps as they complete, then yield the final result.

        import base64 as _b64, re as _re
        from doc_valid import (
            layer1_sanity, _resolve_profile, layer2_ocr_gate,
        )

        lang_code   = normalize_language_code(language)
        try:
            scheme_data = resolve_scheme_reference(raw_scheme=scheme) or {}
        except Exception:
            scheme_data = {}
        scheme_name = scheme_data.get("scheme_name", "Selected Scheme")
        mime_type   = (file.content_type or "application/octet-stream").lower()
        file_name   = file.filename or "upload"
        if mime_type == "image/jpg":
            mime_type = "image/jpeg"

        extracted_fields = {}
        ocr_score        = 0
        soft_warnings    = []

        # ── LAYER 1 ─────────────────────────────────────────────────────────
        yield step_event("file_sanity", "File Format & Quality Check", "running")
        await asyncio.sleep(0)   # flush to client

        l1_passed, l1_issues = layer1_sanity(file_name, mime_type, file_bytes)
        soft_warnings = [i for i in l1_issues if i.get("severity") == "warning"]
        hard_errors   = [i for i in l1_issues if i.get("severity") != "warning"]

        if not l1_passed:
            msg = (hard_errors[0] if hard_errors else l1_issues[0])["message"]
            yield step_event("file_sanity", "File Format & Quality Check", "failed", msg)
            yield sse({"type": "result", "isValid": False, "verdict": "invalid",
                       "errors": hard_errors, "warnings": soft_warnings,
                       "confidenceScore": 0, "summary": msg,
                       "documentType": doc_name, "extractedFields": {},
                       "processingMs": int((time.time()-t0)*1000)})
            return

        size_kb = len(file_bytes) // 1024
        yield step_event("file_sanity", "File Format & Quality Check", "passed",
                         f"{mime_type.split('/')[-1].upper()} | {size_kb} KB")
        await asyncio.sleep(0)

        # ── LAYER 2 ─────────────────────────────────────────────────────────
        profile = _resolve_profile(doc_name)

        if profile is None:
            yield step_event("ocr_extraction", "OCR Text Extraction", "skipped",
                             f"No profile for '{doc_name}' — AI will verify.")
            yield step_event("keyword_check", "Keyword & Pattern Verification", "skipped",
                             "No profile registered.")
            ocr_did_validate = False
        else:
            yield step_event("ocr_extraction", "OCR Text Extraction", "running")
            await asyncio.sleep(0)

            img_bytes_raw = file_bytes if mime_type.startswith("image/") else None

            # Run OCR in executor so it doesn't block event loop
            loop = asyncio.get_event_loop()
            l2_result = await loop.run_in_executor(
                None,
                lambda: layer2_ocr_gate(
                    image_bytes=img_bytes_raw,
                    file_bytes=file_bytes,
                    mime_type=mime_type,
                    file_name=file_name,
                    profile=profile,
                    doc_name=doc_name,
                )
            )
            l2_passed, l2_errors, extracted_fields, ocr_score, ocr_text_raw = l2_result

            ocr_unavailable  = (ocr_text_raw == "OCR_UNAVAILABLE")
            ocr_empty        = (not ocr_text_raw.strip() or ocr_unavailable)
            ocr_did_validate = (not ocr_empty and l2_passed and ocr_score > 0)

            if ocr_unavailable:
                yield step_event("ocr_extraction", "OCR Text Extraction", "skipped",
                                 "pytesseract not installed — skipping to AI")
                yield step_event("keyword_check", "Keyword & Pattern Verification", "skipped",
                                 "Skipped — OCR unavailable")
            elif not ocr_text_raw.strip():
                yield step_event("ocr_extraction", "OCR Text Extraction", "skipped",
                                 "No text found in document — skipping to AI")
                yield step_event("keyword_check", "Keyword & Pattern Verification", "skipped",
                                 "Skipped — no text extracted")
            else:
                wc = len(ocr_text_raw.split())
                yield step_event("ocr_extraction", "OCR Text Extraction", "passed",
                                 f"{wc} words extracted | score {ocr_score}/100")
            await asyncio.sleep(0)

            if not ocr_empty:
                if not l2_passed:
                    src = l2_errors[0].get("source", "") if l2_errors else ""
                    msg = l2_errors[0]["message"] if l2_errors else "Validation failed"

                    if "face" in src:
                        yield step_event("keyword_check", "Keyword & Pattern Verification", "passed", "Keywords matched")
                        yield step_event("face_detection", "Face Detection", "failed", msg)
                    elif "regex" in src:
                        yield step_event("keyword_check", "Keyword & Pattern Verification", "passed", "Keywords matched")
                        yield step_event("regex_check", "Field Pattern Validation", "failed", msg)
                    else:
                        yield step_event("keyword_check", "Keyword & Pattern Verification", "failed", msg)

                    yield sse({"type": "result", "isValid": False, "verdict": "invalid",
                               "errors": l2_errors, "warnings": soft_warnings,
                               "confidenceScore": 10, "summary": msg,
                               "documentType": doc_name,
                               "extractedFields": extracted_fields,
                               "ocrScore": ocr_score,
                               "processingMs": int((time.time()-t0)*1000)})
                    return

                fc = len([k for k in extracted_fields if not k.startswith("_")])
                yield step_event("keyword_check", "Keyword & Pattern Verification", "passed",
                                 f"Keywords confirmed | {fc} field(s) extracted")
                await asyncio.sleep(0)

        # ── Skip Layer 3 for lenient docs (passport photo, CV, etc.) ────────
        if profile and profile.get("lenient") or profile and profile.get("accept_image_always"):
            yield step_event("ai_vision", "AI Document Verification", "skipped",
                             "Accepted — no AI check needed for this document type.")
            await asyncio.sleep(0)
            fc_clean = {k:v for k,v in extracted_fields.items() if not k.startswith("_")}
            yield sse({"type":"result","isValid":True,"verdict":"valid",
                       "errors":[],"warnings":soft_warnings,
                       "confidenceScore":100,
                       "summary":f"{doc_name} accepted successfully.",
                       "documentType":doc_name,"extractedFields":fc_clean,
                       "ocrScore":ocr_score,"processingMs":int((time.time()-t0)*1000)})
            return

        # ── LAYER 3 — AI ────────────────────────────────────────────────────
        yield step_event("ai_vision", "AI Document Verification", "running")
        await asyncio.sleep(0)

        if mime_type.startswith("image/"):
            image_b64   = _b64.b64encode(file_bytes).decode()
            vision_mime = mime_type
        elif mime_type == "application/pdf" or file_name.lower().endswith(".pdf"):
            image_b64   = _pdf_to_image_b64(file_bytes)
            vision_mime = "image/jpeg"
        else:
            image_b64   = None
            vision_mime = "image/jpeg"

        if image_b64:
            try:
                prompt = _vision_prompt(doc_name, scheme_name)
                raw    = await _run_vision_ai(image_b64, vision_mime, prompt)
                ai     = _parse_vision_json(raw)

                if not ai or not isinstance(ai, dict):
                    raise ValueError(f"Empty AI response: {str(raw)[:80]}")

                verdict  = str(ai.get("verdict") or "invalid").lower().strip()
                detected = str(ai.get("detectedType") or ai.get("documentType") or doc_name).strip()
                conf     = min(99, int(ai.get("confidenceScore") or 75) + (ocr_score // 10))
                ai_errs  = [e for e in (ai.get("errors") or [])
                            if isinstance(e, str) and e.strip() and "filename" not in e.lower()]
                ai_warns = [w for w in (ai.get("warnings") or []) if isinstance(w, str) and w.strip()]
                summary  = str(ai.get("summary") or "").strip()

                ai_fields = ai.get("extractedFields") or {}
                if not isinstance(ai_fields, dict): ai_fields = {}
                merged = {**{k:v for k,v in extracted_fields.items() if not k.startswith("_")}, **ai_fields}

                if verdict == "mismatch":
                    msg = (f"Wrong document. You selected \'{doc_name}\' "
                           f"but uploaded \'{detected}\'. Please upload the correct document.")
                    yield step_event("ai_vision", "AI Document Verification", "failed", msg)
                    yield sse({"type":"result","isValid":False,"verdict":"mismatch",
                               "errors":[{"message":msg,"source":"ai"}],
                               "warnings":soft_warnings,"confidenceScore":conf,
                               "summary":f"Expected {doc_name}, got {detected}.",
                               "documentType":detected,"extractedFields":merged,
                               "govBody":ai.get("govBody",""),"ocrScore":ocr_score,
                               "processingMs":int((time.time()-t0)*1000)})
                elif verdict == "valid" and not ai_errs:
                    yield step_event("ai_vision", "AI Document Verification", "passed",
                                     f"Verified as \'{detected}\' — {conf}% confidence")
                    yield sse({"type":"result","isValid":True,"verdict":"valid",
                               "errors":[],"warnings":[{"message":w,"source":"ai"} for w in ai_warns]+soft_warnings,
                               "confidenceScore":conf,"summary":summary or f"{doc_name} verified successfully.",
                               "documentType":detected,"extractedFields":merged,
                               "govBody":ai.get("govBody",""),"ocrScore":ocr_score,
                               "processingMs":int((time.time()-t0)*1000)})
                else:
                    err_msgs = ai_errs or ["Could not verify. Upload a clearer copy."]
                    yield step_event("ai_vision", "AI Document Verification", "failed", err_msgs[0])
                    yield sse({"type":"result","isValid":False,"verdict":"invalid",
                               "errors":[{"message":e,"source":"ai"} for e in err_msgs],
                               "warnings":[{"message":w,"source":"ai"} for w in ai_warns]+soft_warnings,
                               "confidenceScore":conf,"summary":summary or err_msgs[0],
                               "documentType":detected,"extractedFields":merged,
                               "govBody":ai.get("govBody",""),"ocrScore":ocr_score,
                               "processingMs":int((time.time()-t0)*1000)})
                return

            except Exception as e:
                logger.error(f"AI Vision stream failed: {e}")
                yield step_event("ai_vision", "AI Document Verification", "skipped",
                                 f"AI failed: {str(e)[:60]}")

        # ── Fallback — Layer 1 passed, OCR unavailable, AI failed ──────────
        # If Layer 1 passed and doc type has no OCR profile or OCR unavailable,
        # accept the document — Layer 1 is sufficient proof of valid file format.
        fc_clean = {k:v for k,v in extracted_fields.items() if not k.startswith("_")}
        if ocr_did_validate:
            yield step_event("ai_vision", "AI Document Verification", "skipped",
                             "AI skipped — OCR already verified document.")
            yield sse({"type":"result","isValid":True,"verdict":"valid",
                       "errors":[],"warnings":[{"message":"Verified via OCR. Add AI key for deeper verification.","source":"system"}]+soft_warnings,
                       "confidenceScore":min(75, 50+ocr_score//2),
                       "summary":f"{doc_name} verified via document analysis.",
                       "documentType":doc_name,"extractedFields":fc_clean,
                       "ocrScore":ocr_score,"processingMs":int((time.time()-t0)*1000)})
        else:
            # Layer 1 passed — file is valid format/size. Accept with moderate confidence.
            yield step_event("ai_vision", "AI Document Verification", "skipped",
                             "AI unavailable — accepted based on file validation.")
            yield sse({"type":"result","isValid":True,"verdict":"valid",
                       "errors":[],
                       "warnings":[{"message":"AI verification unavailable. Document accepted based on file format check. Add a valid GROQ_API_KEY for full AI verification.","source":"system"}]+soft_warnings,
                       "confidenceScore":60,
                       "summary":f"{doc_name} accepted — file format verified.",
                       "documentType":doc_name,"extractedFields":fc_clean,
                       "ocrScore":ocr_score,"processingMs":int((time.time()-t0)*1000)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":    "no-cache",
            "X-Accel-Buffering": "no",
            "Connection":       "keep-alive",
        },
    )



@app.get("/v1/scheme/by-id")
async def get_scheme_by_id(scheme_id: str = "", name: str = ""):
    """
    Returns the full scheme object for a given scheme_id or name.
    DocValidation page calls this to get the complete scheme (with required_documents)
    before building its FormData for upload validation.
    """
    result = resolve_scheme_reference(raw_scheme=name or scheme_id, scheme_id=scheme_id)
    if not result:
        raise HTTPException(status_code=404, detail="Scheme not found")
    return result


@app.post("/v1/validate_doc_upload")
async def validate_doc_upload(
    file:     UploadFile = File(...),
    doc_name: str        = Form(...),
    scheme:   str        = Form(...),
    language: str        = Form("en"),
):
    t0 = time.time()

    # ── Fast path for lenient docs (passport photo, CV, signature) ──────────
    from doc_valid import _resolve_profile as _rp
    _profile = _rp(doc_name)
    if _profile and (_profile.get("lenient") or _profile.get("accept_image_always")):
        file_bytes = await file.read()
        size_kb = len(file_bytes) // 1024
        logger.info(f"Lenient fast-accept: {doc_name}")
        return {
            "success": True, "isValid": True, "verdict": "valid",
            "status": "valid", "documentType": doc_name,
            "confidenceScore": 100,
            "summary": f"{doc_name} accepted successfully.",
            "errors": [], "warnings": [],
            "extractedFields": {},
            "validationSteps": [
                {"step": "file_sanity",   "label": "File Format & Quality Check",    "status": "passed", "detail": f"{size_kb} KB — format accepted"},
                {"step": "ocr_extraction","label": "OCR Text Extraction",            "status": "skipped","detail": "Not required for this document type"},
                {"step": "keyword_check", "label": "Keyword & Pattern Verification", "status": "skipped","detail": "Not required for this document type"},
                {"step": "ai_vision",     "label": "AI Document Verification",       "status": "skipped","detail": "Auto-accepted — no AI check needed"},
            ],
            "processingMs": int((time.time()-t0)*1000),
        }

    return await layered_validate(
        file=file,
        doc_name=doc_name,
        scheme=scheme,
        language=language,
        t0=t0,
        _run_vision_ai=_run_vision_ai,
        _vision_prompt=_vision_prompt,
        _parse_vision_json=_parse_vision_json,
        _pdf_to_image_b64=_pdf_to_image_b64,
        localize_validation_payload=localize_validation_payload,
        normalize_language_code=normalize_language_code,
        resolve_scheme_reference=resolve_scheme_reference,
    )




@app.post("/v1/validate/document")
async def validate_document_alias(
    file:     UploadFile = File(...),
    docName:  str        = Form(...),
    scheme:   str        = Form(...),
    language: str        = Form("en"),
):
    return await validate_doc_upload(file=file, doc_name=docName, scheme=scheme, language=language)



# ─── WORKSPACE ENDPOINTS ─────────────────────────────────────────────────────

@app.get("/v1/workspace/get")
async def workspace_get(email: str = ""):
    """
    Load a user's full workspace (profile + saved_schemes) from SQLite.
    Called by fetchUserWorkspace() in userWorkspace.js on login/page load.
    """
    if not email:
        raise HTTPException(status_code=400, detail="email is required")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT full_name, profile_data, saved_schemes FROM users WHERE LOWER(email) = ?",
            (email.strip().lower(),)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        full_name, profile_data_str, saved_schemes_str = row
        try:
            profile_data = json.loads(profile_data_str) if profile_data_str else {}
        except json.JSONDecodeError:
            profile_data = {}
        try:
            saved_schemes = json.loads(saved_schemes_str) if saved_schemes_str else []
        except json.JSONDecodeError:
            saved_schemes = []
    last_id = saved_schemes[0].get("scheme_id", "") if saved_schemes else ""
    workspace_block = {
        "profile":                 profile_data,
        "saved_schemes":           saved_schemes,
        "last_selected_scheme_id": last_id,
    }
    return {
        "email":                   email,
        "full_name":               full_name,
        "profile_data":            profile_data,
        "profile":                 profile_data,
        "saved_schemes":           saved_schemes,
        "last_selected_scheme_id": last_id,
        "workspace":               workspace_block,
    }


@app.post("/v1/workspace/save")
async def workspace_save(data: dict = Body(default={})):
    """Persist workspace to SQLite so it survives server restarts."""
    email = str(data.get("email") or data.get("workspaceId") or "").strip().lower()
    # Also keep in-memory for backwards compat with /v1/workspace/load
    workspace_id = email or "default"
    _workspace_store[workspace_id] = {
        "workspaceId": workspace_id,
        "savedAt": time.time(),
        "data": data,
    }
    logger.info(f"[workspace/save] saved '{workspace_id}' ({len(str(data))} bytes)")

    if not email or "@" not in email:
        return {"success": True, "workspaceId": workspace_id}

    # Persist profile + saved_schemes to SQLite
    profile = data.get("profile") or {}
    saved_schemes = data.get("saved_schemes") or []
    last_id = data.get("last_selected_scheme_id") or (
        saved_schemes[0].get("scheme_id", "") if saved_schemes else ""
    )

    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM users WHERE LOWER(email) = ?", (email,))
            if cursor.fetchone():
                if profile:
                    cursor.execute(
                        "UPDATE users SET profile_data = ?, saved_schemes = ? WHERE LOWER(email) = ?",
                        (json.dumps(profile), json.dumps(saved_schemes), email)
                    )
                else:
                    # Profile is empty — only update saved_schemes, keep existing profile_data
                    cursor.execute(
                        "UPDATE users SET saved_schemes = ? WHERE LOWER(email) = ?",
                        (json.dumps(saved_schemes), email)
                    )
            else:
                cursor.execute(
                    "INSERT INTO users (email, password, full_name, profile_data, saved_schemes) VALUES (?,?,?,?,?)",
                    (email, "", email.split("@")[0], json.dumps(profile), json.dumps(saved_schemes))
                )
            conn.commit()
    except Exception as e:
        logger.warning(f"[workspace/save] SQLite persist failed: {e}")

    workspace_block = {
        "profile":                 profile,
        "saved_schemes":           saved_schemes,
        "last_selected_scheme_id": last_id,
    }
    return {
        "success":                 True,
        "workspaceId":             workspace_id,
        "email":                   email,
        "profile_data":            profile,
        "profile":                 profile,
        "saved_schemes":           saved_schemes,
        "last_selected_scheme_id": last_id,
        "workspace":               workspace_block,
    }


@app.get("/v1/workspace/load")
async def workspace_load(workspaceId: str = "default"):
    """Retrieve a previously saved workspace."""
    entry = _workspace_store.get(workspaceId)
    if not entry:
        return {"success": False, "workspaceId": workspaceId, "data": None}
    return {"success": True, **entry}


@app.delete("/v1/workspace/delete")
async def workspace_delete(workspaceId: str = "default"):
    """Delete a saved workspace."""
    existed = _workspace_store.pop(workspaceId, None) is not None
    return {"success": existed, "workspaceId": workspaceId}


# ─── STATIC FILES (frontend — must be mounted last so API routes take priority) ─
_frontend_dir = Path("./frontend").resolve()
if _frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")
else:
    logger.warning(f"Frontend directory not found at {_frontend_dir}. Static file serving disabled.")


# ─── ENTRY POINT ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Use reload=False when running via `python mainm.py`.
    # For hot-reload during development use: uvicorn mainm:app --reload
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)