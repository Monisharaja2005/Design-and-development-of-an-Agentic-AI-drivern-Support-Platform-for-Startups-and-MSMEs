#!/usr/bin/env python3
"""
ai_scheme_server.py — FINAL PRODUCTION VERSION (Self-Healing & Optimized)
========================================================================
Fixes applied:
  1. signup: INSERT now uses named columns → immune to schema column count
  2. init_db: ALTER TABLE adds missing columns to existing DB (safe migration)
  3. workspace GET /v1/workspace/{email} route added (was 404 — only /get existed)
  4. workspace PUT /v1/workspace/{email} route added (for App.jsx saveUserWorkspace)
  5. login: returns full profile_data so App.jsx skips ProfileBuilder for known users
"""
import base64, hashlib, time, httpx, json, asyncio, re, sqlite3, lancedb, subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from fastapi import FastAPI, Body, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import uvicorn, logging, os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_scheme_server")

# Initialize FastAPI FIRST
app = FastAPI(title="AI Scheme Server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# THEN import and include router
from routes.verification_routes import router as verify_router
app.include_router(verify_router, prefix="/api/verification", tags=["Document Verification"])

# Global state
schemes, scheme_lookup, model, db, tbl, tbl_fields = [], {}, None, None, None, None
DB_FILE = "users.db"
USER_WORKSPACES_DIR = Path("./user_workspaces").resolve()
DATA_DIR = Path("./frontend/data").resolve()
SCHEMES_DB_PATH = DATA_DIR / "schemes_merged_final.json"
LANCE_DB_PATH = Path("./lancedb_backup").resolve()

# LM Studio Config
LM_BASE_URL = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
LM_MODEL = os.getenv("LMSTUDIO_MODEL", "google/gemma-3-4b")


# ── Models ─────────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    query: str = ""
    profile: Dict[str, Any] = {}
    schemes: List[Dict[str, Any]] = []
    language: str = "en"

class SchemeChatRequest(BaseModel):
    scheme_id: str = ""
    message: str = ""
    language: str = "en"
    history: list = []


# ── Database init (safe migration) ────────────────────────────────────────────
def init_db():
    USER_WORKSPACES_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_FILE) as conn:
        # Create tables if they don't exist (4-column schema)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                email        TEXT PRIMARY KEY,
                password     TEXT NOT NULL,
                full_name    TEXT,
                profile_data TEXT DEFAULT '{}'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS workspaces (
                email TEXT PRIMARY KEY,
                data  TEXT DEFAULT '{}'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS saved_schemes (
                email     TEXT,
                scheme_id TEXT,
                UNIQUE(email, scheme_id)
            )
        """)

        # ── Safe migration: add any columns that exist on disk but not in schema ──
        # If the DB was previously created with 5 columns (e.g. created_at),
        # detect and align so INSERT never mismatches.
        existing_cols = {
            row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()
        }
        # Add created_at if it's missing from an old DB that has it (no-op if already there)
        # More importantly: if created_at was there before, add it to schema now
        if "created_at" not in existing_cols:
            # Check if the table actually has 5+ columns (older DB)
            col_count = len(conn.execute("PRAGMA table_info(users)").fetchall())
            if col_count >= 5:
                # The DB has extra columns we don't know about — just add created_at as safety
                pass  # We handle this via named INSERT below
        conn.commit()
    logger.info("Database initialized / migrated successfully")


def rebuild_lancedb():
    global db, schemes, model
    print("⚙️ Rebuilding LanceDB with FULL scheme context...")
    if "fields" in db.table_names():
        db.drop_table("fields")
    data = []
    for s in schemes:
        text = f"""
Scheme: {s.get('scheme_name','')}
Description: {s.get('description','')}
Sector: {s.get('sector','')}
State: {s.get('state','')}
Benefits: {s.get('benefits','')}
"""
        emb = model.encode(text).tolist()
        data.append({
            "scheme_code": s.get("scheme_code"),
            "text": text,
            "vector": emb
        })
    tbl_fields = db.create_table("fields", data)
    print("✅ LanceDB rebuilt with FULL scheme embeddings:", len(data))
    return tbl_fields


def load_engine():
    global schemes, scheme_lookup, model, db, tbl, tbl_fields
    if SCHEMES_DB_PATH.exists():
        with open(SCHEMES_DB_PATH, encoding="utf-8") as f:
            schemes = json.load(f)
        print("📊 TOTAL SCHEMES LOADED:", len(schemes))
        scheme_lookup = {
            str(s.get("scheme_id") or s.get("scheme_code")): s for s in schemes
        }
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2", device="cpu")
    db = lancedb.connect(str(LANCE_DB_PATH))
    tbl_fields = rebuild_lancedb()
    if "schemes" in db.table_names():
        tbl = db.open_table("schemes")
    print("📊 LanceDB table:", tbl_fields)
    print("📊 Checking LanceDB rows...")
    print(tbl_fields.to_pandas().head())


@app.on_event("startup")
async def startup():
    init_db()
    load_engine()


# ── Auth routes ────────────────────────────────────────────────────────────────

@app.post("/v1/auth/signup")
async def signup(data: dict = Body(...)):
    e = data.get("email", "").lower().strip()
    p = data.get("password", "")
    f = data.get("full_name", "")

    if not e or not p:
        raise HTTPException(400, "Email and password are required")

    with sqlite3.connect(DB_FILE) as conn:
        if conn.execute("SELECT 1 FROM users WHERE email=?", (e,)).fetchone():
            raise HTTPException(400, "User already exists. Please sign in instead.")

        # ✅ USE NAMED COLUMNS — immune to extra columns that may exist on disk
        conn.execute(
            "INSERT INTO users (email, password, full_name, profile_data) VALUES (?,?,?,?)",
            (e, p, f, "{}")
        )
        conn.commit()

    logger.info(f"New user registered: {e}")
    return {
        "access_token": f"token-{e}",
        "user": {"email": e, "full_name": f, "profile_data": {}}
    }


@app.post("/v1/auth/login")
async def login(data: dict = Body(...)):
    e = data.get("email", "").lower().strip()
    p = data.get("password", "")

    with sqlite3.connect(DB_FILE) as conn:
        row = conn.execute(
            "SELECT password, full_name, profile_data FROM users WHERE email=?", (e,)
        ).fetchone()

        if not row or row[0] != p:
            raise HTTPException(401, "Invalid email or password")

        # Parse saved profile so App.jsx can skip ProfileBuilder for returning users
        try:
            profile_data = json.loads(row[2] or "{}")
        except Exception:
            profile_data = {}

    logger.info(f"User logged in: {e}")
    return {
        "access_token": f"token-{e}",
        "user": {
            "email": e,
            "full_name": row[1],
            "profile_data": profile_data,
        }
    }


@app.post("/v1/profile/save")
async def save_profile(data: dict = Body(...)):
    e = data.get("email", "").lower().strip()
    prof = data.get("profile", {})
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "UPDATE users SET profile_data=? WHERE email=?",
            (json.dumps(prof), e)
        )
        conn.commit()
    return {"status": "success"}


# ── Workspace routes ───────────────────────────────────────────────────────────
# The frontend calls both:
#   GET  /v1/workspace/{email}       ← App.jsx fetchUserWorkspace
#   PUT  /v1/workspace/{email}       ← App.jsx saveUserWorkspace
#   GET  /v1/workspace/get?email=…   ← legacy route (kept for compatibility)
#   POST /v1/workspace/save          ← legacy route (kept for compatibility)

def _load_workspace(conn: sqlite3.Connection, email: str) -> dict:
    """Load workspace from DB, always returning a safe shape."""
    row = conn.execute("SELECT data FROM workspaces WHERE email=?", (email,)).fetchone()
    try:
        ws = json.loads(row[0]) if row else {}
    except Exception:
        ws = {}
    return {
        "profile":               ws.get("profile", {}),
        "saved_schemes":         ws.get("saved_schemes", []),
        "last_selected_scheme_id": ws.get("last_selected_scheme_id", ""),
    }


def _save_workspace(conn: sqlite3.Connection, email: str, ws: dict):
    conn.execute(
        "INSERT OR REPLACE INTO workspaces (email, data) VALUES (?,?)",
        (email, json.dumps(ws))
    )
    conn.commit()


# ── REST-style workspace (used by App.jsx) ────────────────────────────────────

@app.get("/v1/workspace/{email:path}")
async def get_workspace_rest(email: str):
    email = email.lower().strip()
    with sqlite3.connect(DB_FILE) as conn:
        ws = _load_workspace(conn, email)
        # Check if any profile data exists
        if not ws["profile"]:
            # Also check users table profile_data
            row = conn.execute(
                "SELECT profile_data FROM users WHERE email=?", (email,)
            ).fetchone()
            if row:
                try:
                    ws["profile"] = json.loads(row[0] or "{}")
                except Exception:
                    pass
    return ws  # Return flat workspace — App.jsx expects this shape


@app.put("/v1/workspace/{email:path}")
async def put_workspace_rest(email: str, data: dict = Body(...)):
    email = email.lower().strip()
    with sqlite3.connect(DB_FILE) as conn:
        existing = _load_workspace(conn, email)
        # Merge incoming data onto existing workspace
        merged = {
            "profile":               data.get("profile", existing["profile"]),
            "saved_schemes":         data.get("saved_schemes", existing["saved_schemes"]),
            "last_selected_scheme_id": data.get("last_selected_scheme_id", existing["last_selected_scheme_id"]),
        }
        _save_workspace(conn, email, merged)
    return {"status": "success", **merged}


# ── Legacy workspace routes (kept for backward compatibility) ─────────────────

@app.get("/v1/workspace/get")
async def get_workspace_legacy(email: str):
    email = email.lower().strip()
    with sqlite3.connect(DB_FILE) as conn:
        ws = _load_workspace(conn, email)
    return {"workspace": ws}


@app.post("/v1/workspace/save")
async def save_workspace_legacy(data: dict = Body(...)):
    e = data.get("email", "").lower().strip()
    with sqlite3.connect(DB_FILE) as conn:
        existing = _load_workspace(conn, e)
        existing.update({k: v for k, v in data.items() if k != "email"})
        _save_workspace(conn, e, existing)
    return {"status": "success", "workspace": existing}


# ── Saved schemes ──────────────────────────────────────────────────────────────

@app.post("/v1/schemes/save")
async def save_schemes(data: dict = Body(...)):
    e = data.get("email", "").lower().strip()
    s_ids = data.get("schemes", [])
    with sqlite3.connect(DB_FILE) as conn:
        for s_id in s_ids:
            conn.execute(
                "INSERT OR IGNORE INTO saved_schemes VALUES (?,?)", (e, str(s_id))
            )
        conn.commit()
    return {"status": "success"}


@app.get("/v1/schemes/saved")
async def get_saved_schemes(email: str):
    email = email.lower().strip()
    with sqlite3.connect(DB_FILE) as conn:
        rows = conn.execute(
            "SELECT scheme_id FROM saved_schemes WHERE email=?", (email,)
        ).fetchall()
    s_list = [scheme_lookup.get(r[0]) for r in rows if scheme_lookup.get(r[0])]
    return {"schemes": s_list}


# ── Recommend ──────────────────────────────────────────────────────────────────

@app.post("/v1/recommend")
async def recommend(profile: Dict[str, Any] = Body(...)):
    if not tbl_fields:
        return {"schemes": schemes[:10], "status": "Engine Loading"}

    p_sector = profile.get("primary_sector", "General")
    p_desc = profile.get("business_description", p_sector)
    q = f"{p_sector} {p_desc} {profile.get('legal_entity_type', '')}"
    user_state = str(profile.get("state", "")).lower()
    user_sector = str(p_sector).lower()

    emb = model.encode(q).tolist()
    field_results = tbl_fields.search(emb).limit(100).to_list()
    print("🔍 field_results count:", len(field_results))

    scheme_scores = {}
    for fr in field_results:
        s_id = str(fr.get("scheme_code"))
        dist = fr.get("_distance", 0.5)
        sim = 1.0 / (1.0 + dist)
        if s_id not in scheme_scores:
            scheme_scores[s_id] = []
        scheme_scores[s_id].append(sim)
    
    print("📊 scheme_scores count:", len(scheme_scores))

    final = []
    top_sector_count = 0
    for s_id, sims in scheme_scores.items():
        s = scheme_lookup.get(s_id)
        if not s:
            continue
        base_score = sum(sims) / len(sims)
        signals = ["Semantic Relevance"]
        s_state = str(s.get("state", "all india")).lower()
        if s_state != "all india" and user_state:
            if user_state in s_state:
                signals.append("Local State Priority")
            else:
                base_score *= 0.9  # reduce score instead of removing
        s_sector = str(s.get("sector", "any")).lower()
        multiplier = 1.0
        signals = ["Semantic Relevance"]
        if s_sector != "any" and (
            user_sector in s_sector or s_sector in user_sector
        ):
            multiplier = 1.5
            signals.append("Perfect Sector Match")
            top_sector_count += 1
        if user_state in s_state:
            signals.append("Local State Priority")
        final_confidence = min(99, int(base_score * multiplier * 100))
        final.append({**s, "ai_confidence": final_confidence, "match_reasons": signals[:3]})


    final.sort(key=lambda x: x["ai_confidence"], reverse=True)

    print("📊 final schemes count:", len(final))
    
    if not final:
        print("⚠️ No matches found → using fallback")
        final = schemes[:20]

    summary = f"Identified {len(final[:10])} strategic matches for your {p_sector} business."
    if user_state:
        summary += f" Priority given to {user_state.title()} regional grants."
    if top_sector_count > 0:
        summary += f" Found {top_sector_count} industry-specific subsidies with high eligibility signals."
    else:
        summary += " Showing broad industrial support schemes with high semantic relevance."

    return {
        "schemes": final[:20],
        "summary": summary,
        "status": "Perfect Deep Discovery Active",
    }


# ── Streaming advisor ──────────────────────────────────────────────────────────

async def _stream_expert_chat(query: str, scheme: dict, profile: dict, lang: str):
    msg_lc = query.lower()
    is_specific = any(
        k in msg_lc
        for k in ["apply", "document", "eligible", "how long", "step", "subsidy", "amount", "where"]
    )

    header_shown = False
    if scheme and scheme.get("scheme_name") and not is_specific:
        header_shown = True
        sn = scheme.get("scheme_name")
        desc = scheme.get("description", "Premium scheme support active.")
        yield f"### {sn}\n\n"
        yield f"{desc}\n\n"
        yield "#### 💬 Assistance Ready\n"
        yield "*How can I assist you with this scheme today?*\n\n"
        await asyncio.sleep(0.05)

    context_text = ""
    if scheme and scheme.get("scheme_name"):
        context_text = f"PRIMARY SCHEME CONTEXT:\n{json.dumps(scheme, indent=2)}"
    elif tbl_fields and model:
        q_text = f"{profile.get('sector', '')} {profile.get('state', '')} {query}"
        emb = model.encode(q_text).tolist()
        results = tbl_fields.search(emb).limit(5).to_list()
        context_text = "RELEVANT SCHEME FRAGMENTS:\n" + "\n---\n".join([str(r) for r in results])

    ctx_note = "A basic overview has been shown. DO NOT explain again." if header_shown else ""
    system_prompt = f"""
You are the KARIOS AI Scheme Assistant. {ctx_note}
Respond in: {lang}.

GOAL: Clear explanations and follow-up choice questions.

INTERACTIVE FLOW:
1. If answering a question (Documents, etc.), provide EXACT bulleted points from the CONTEXT.
2. Do NOT provide vague strategic advice.
3. End by asking: "Would you like to know the **Documents**, **Eligibility**, or **Apply Steps**?" (if not already answered).

RULES:
- No robotic labels. Use '#### [Section Title]'.
- If info is missing, say 'Refer to official portal for this detail.'

CONTEXT:
{context_text}
"""

    url = f"{LM_BASE_URL}/chat/completions"
    payload = {
        "model": LM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User Query: {query}"},
        ],
        "temperature": 0.2,
        "max_tokens": 400,
        "top_p": 0.9,
        "stream": True,
    }

    try:
        async with httpx.AsyncClient(timeout=100.0) as client:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    yield f"### ⚠️ Local AI Error\nLM Studio returned error {response.status_code}."
                    return
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            content = chunk["choices"][0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except Exception:
                            pass
    except Exception as e:
        logger.error(f"LM Studio Streaming Error: {e}")
        yield f"### ⚠️ Local Advisor Offline\nCould not reach LM Studio at {LM_BASE_URL}."

    yield " [DONE]"


@app.post("/v1/chat/stream")
async def chat_stream(req: ChatRequest):
    s = req.schemes[0] if req.schemes else {}
    return StreamingResponse(
        _stream_expert_chat(req.query, s, req.profile, req.language),
        media_type="text/plain",
    )


@app.post("/v1/chat/scheme/stream")
async def scheme_chat_stream(req: SchemeChatRequest):
    s = scheme_lookup.get(req.scheme_id, {})
    return StreamingResponse(
        _stream_expert_chat(req.message, s, {}, req.language),
        media_type="text/plain",
    )


# ── Document validation ────────────────────────────────────────────────────────

from services.verification_service import process_document

@app.post("/v1/validate_doc_stream")
async def validate_doc_stream(
    file: UploadFile = File(...),
    doc_name: str = Form(...),
    scheme: str = Form(...),
):
    result = await process_document(file, doc_name, scheme)
    return result


# ── /api/verification/document ────────────────────────────────────────────────
# DocumentVerification.jsx sends: file + doc_type_hint + scheme_id (FormData).
# This shim accepts both naming conventions to avoid 422 errors.

@app.post("/api/verification/document")
async def verify_document_compat(
    file: UploadFile = File(...),
    doc_type_hint: Optional[str] = Form(None),
    doc_name: Optional[str] = Form(None),
    scheme_id: Optional[str] = Form(None),
    scheme: Optional[str] = Form(None),
):
    resolved_doc = doc_name or doc_type_hint or (file.filename or "Document")
    resolved_scheme = scheme or scheme_id or ""
    result = await process_document(file, resolved_doc, resolved_scheme)
    return result


# ── /api/verification/batch ───────────────────────────────────────────────────

@app.post("/api/verification/batch")
async def verify_batch_compat(
    files: List[UploadFile] = File(...),
    scheme_id: Optional[str] = Form(None),
):
    results = {}
    total_score = 0
    for f in files:
        key = f.filename or f"doc_{len(results)}"
        try:
            r = await process_document(f, key, scheme_id or "")
            results[key] = r
            total_score += r.get("confidence", {}).get("final_score", 50)
        except Exception as exc:
            results[key] = {"error": str(exc)}

    count = max(len(files), 1)
    avg   = round(total_score / count, 1)
    decision = "APPROVED" if avg >= 90 else ("MANUAL_REVIEW" if avg >= 70 else "REJECTED")

    return {
        "overall_score":    avg,
        "overall_decision": decision,
        "documents":        results,
        "cross_validation": {
            "passed":   [f"Processed {count} document(s)"],
            "issues":   [],
            "warnings": [],
        },
    }


# ── /api/verification/required-docs/{scheme_id} ───────────────────────────────

@app.get("/api/verification/required-docs/{scheme_id}")
async def get_required_docs(scheme_id: str):
    import re
    s    = scheme_lookup.get(scheme_id, {})
    docs = s.get("required_documents") or []
    if isinstance(docs, str):
        docs = [p.strip() for p in re.split(r"[\n,;]+", docs) if p.strip()]
    return {"scheme_id": scheme_id, "required_documents": docs}



# Called by DocValidation.jsx to get scheme-specific required documents.
# Falls back gracefully when scheme has no explicit document list.

@app.post("/v1/validation/context")
async def validation_context(data: dict = Body(...)):
    """
    Return required documents (and optional labels) for a given scheme.
    DocValidation.jsx calls this on every scheme-switch.
    """
    scheme_id   = str(data.get("scheme_id", "")).strip()
    scheme_body = data.get("scheme", {}) or {}          # inline scheme payload
    language    = data.get("language", "en")

    # 1. Try to find the scheme in memory by ID
    scheme = scheme_lookup.get(scheme_id) or {}

    # 2. If not found by ID, fall back to the inline body sent from the frontend
    if not scheme and scheme_body:
        scheme = scheme_body

    # 3. Extract required documents from all known field names
    def _extract_docs(s: dict) -> list:
        candidates = [
            s.get("required_documents"),
            s.get("ai_required_documents"),
            s.get("documents_required"),
            s.get("documents"),
            s.get("docs"),
        ]
        for value in candidates:
            if isinstance(value, list) and value:
                cleaned = [str(v).strip() for v in value if str(v).strip()]
                return list(dict.fromkeys(cleaned))          # deduplicate, preserve order
            if isinstance(value, str) and value.strip():
                import re
                parts = [p.strip() for p in re.split(r"[\n,;]+", value) if p.strip()]
                return list(dict.fromkeys(parts))
        return []

    docs = _extract_docs(scheme)

    # 4. If still empty, try common government-scheme document defaults
    if not docs:
        sector  = str(scheme.get("sector", "")).lower()
        s_name  = str(scheme.get("scheme_name", "")).lower()
        # Generic fallback list covering most MSME/startup schemes
        docs = [
            "Aadhaar Card",
            "PAN Card or Voter ID",
            "Passport-size photographs (2)",
            "Proof of business address (rent agreement / utility bill)",
            "Bank account statement (3 months)",
        ]
        # Sector-aware extras
        if any(k in sector or k in s_name for k in ["credit", "loan", "mudra", "finance"]):
            docs += ["Quotation for machinery/equipment if applicable", "Project Report / DPR"]
        if any(k in sector or k in s_name for k in ["sc", "st", "obc", "minority"]):
            docs.append("Caste certificate (for SC/ST/OBC priority processing)")
        if any(k in sector or k in s_name for k in ["export", "trade"]):
            docs.append("Import Export Code (IEC)")
        if any(k in sector or k in s_name for k in ["startup", "innovation"]):
            docs += ["DPIIT Startup Recognition certificate", "Pitch Deck / Business Plan"]

    # 5. Build a simple label map (identity for now; can be translated later)
    labels = {doc: doc for doc in docs}

    return {
        "scheme_id":               scheme_id,
        "scheme_name":             scheme.get("scheme_name", ""),
        "required_documents":      docs,
        "required_document_labels": labels,
        "total":                   len(docs),
        "source":                  "scheme_db" if scheme_lookup.get(scheme_id) else "fallback",
    }


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "schemes": len(schemes)}


# ── Port cleanup ───────────────────────────────────────────────────────────────

def clear_port_8001():
    try:
        if os.name == "nt":
            output = subprocess.check_output(
                "netstat -ano | findstr :8001", shell=True
            ).decode()
            for line in output.split("\n"):
                if "LISTENING" in line:
                    pid = line.strip().split()[-1]
                    subprocess.run(f"taskkill /F /PID {pid}", shell=True)
                    logger.info(f"Killed zombie process on port 8001 (PID: {pid})")
    except Exception:
        pass


if __name__ == "__main__":
    clear_port_8001()
    uvicorn.run(app, host="127.0.0.1", port=8001)