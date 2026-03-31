from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from uuid import uuid4

from fastapi import Body, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .chat import SchemeChatService
from .engine import DocumentVerificationEngine
from .models import ApiError, EnterpriseProfile, SchemeRequirements, VerificationContext
from .registry import AuthorityRegistry
from .security import AuthManager
from .security import hash_password, verify_password
from .scheme_assistant import SchemeSemanticIndex, FaissRecommendation
from .settings import Settings
from .storage import VerificationStorage
from .validators import OfficialRegistryClient

ALLOWED_FILE_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".txt"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "text/plain",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/tiff",
    "image/bmp",
}


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1500)
    language: str = Field(default="English", max_length=64)
    profile: dict[str, object] = Field(default_factory=dict)
    schemes: list[dict[str, object]] = Field(default_factory=list)
    history: list[ChatMessage] = Field(default_factory=list)


class SchemeAuditEventRequest(BaseModel):
    scheme_id: str = Field(min_length=1, max_length=200)
    action: str = Field(min_length=1, max_length=120)
    detail: str = Field(min_length=1, max_length=2000)
    level: str = Field(default="info", max_length=32)


class SignUpRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=6, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class SignInRequest(BaseModel):
    email: str = Field(min_length=6, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class PanValidationRequest(BaseModel):
    pan: str = Field(min_length=10, max_length=10)


def create_app() -> FastAPI:
    settings = Settings.from_env()
    registry = AuthorityRegistry.from_file(settings.authority_registry_path)
    guard = AuthManager(
        key_to_role=settings.api_keys,
        jwt_secret=settings.jwt_secret,
        jwt_issuer=settings.jwt_issuer,
        jwt_ttl_minutes=settings.jwt_ttl_minutes,
    )
    storage = VerificationStorage(db_path=settings.db_path, encryption=_build_encryption(settings))
    storage.seed_authorities(registry)
    engine = DocumentVerificationEngine(
        registry=registry,
        weights=settings.score_weights,
        registry_endpoints=settings.registry_endpoints,
        registry_headers=settings.registry_headers,
    )
    chat_service = SchemeChatService(
        provider=settings.llm_provider,
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        karios_ai_api_key=settings.karios_ai_api_key,
        karios_ai_base_url=settings.karios_ai_base_url,
        karios_ai_model=settings.karios_ai_model,
        strict_live=settings.llm_strict_live,
        timeout_seconds=settings.llm_timeout_seconds,
        ollama_models=[],
    )
    local_index = SchemeSemanticIndex(
        csv_path=settings.schemes_csv_path,
        embedding_model=settings.embedding_model,
        cache_path=settings.db_path.parent / "scheme_embedding_cache.json",
    )
    faiss_recommender = FaissRecommendation(local_index)

    app = FastAPI(
        title="Government Document Authenticity Verification API",
        version="1.0.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def _soft_filter(scheme: dict, profile: dict) -> bool:
        """Soft filter: match state/sector/entity before ranking."""
        profile_state = (profile.get('state') or '').lower().strip()
        profile_sector = (profile.get('sector') or '').lower().strip()
        profile_entity = (profile.get('entityType') or '').lower().strip()
        
        scheme_state = (scheme.get('State_Applicable') or '').lower()
        scheme_sector = (scheme.get('Target_Sector') or '').lower()
        scheme_entities = (scheme.get('Entity_Types') or '').lower()
        
        # State match (all states or exact)
        state_match = 'all states' in scheme_state or profile_state in scheme_state
        
        # Sector match
        sector_match = not profile_sector or profile_sector in scheme_sector
        
        # Entity match
        entity_match = not profile_entity or profile_entity in scheme_entities
        
        return state_match and sector_match and entity_match

    @app.post("/v1/recommend")
    def recommend_profile_schemes(
        profile: dict[str, str],
        k: int = 20,
        auth=guard.require({"admin", "verifier", "auditor"})
    ):
        """Recommend schemes using profile: soft filter + BART/Faiss ranking."""
        if not local_index.rows:
            raise HTTPException(status_code=404, detail="No schemes loaded")
        
        # Build profile query for semantic matching (BART-like)
        profile_query = f"{profile.get('state', 'India')} {profile.get('sector', '')} {profile.get('entityType', '')} {profile.get('turnover', '')} {profile.get('businessDescription', 'business')}"
        
        # Faiss recommendation (semantic + schematic matching)
        candidates = faiss_recommender.recommend(profile_query, k=k)
        
        # Soft filter first
        filtered = [r for r in candidates if _soft_filter(r.scheme, profile)]
        
        # Top K ranked
        top_k = filtered[:min(k, len(filtered))]
        
        storage.log_audit(
            actor_role=auth.role,
            action="recommend_profile_schemes",
            resource_id=None,
            details={"profile_keys": list(profile.keys()), "candidate_count": len(candidates), "filtered_count": len(filtered)},
        )
        
        return {
            "profile_query": profile_query,
            "backend": local_index.backend,
            "total_candidates": len(candidates),
            "after_filter": len(filtered),
            "ranked_schemes": [{"score": item.score, "scheme": item.scheme} for item in top_k],
        }

    @app.middleware("http")
    async def attach_request_id(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.exception_handler(HTTPException)
    async def handle_http_exception(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=ApiError(
                request_id=getattr(request.state, "request_id", str(uuid4())),
                code=f"http_{exc.status_code}",
                message=str(exc.detail),
                details={},
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_exception(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=ApiError(
                request_id=getattr(request.state, "request_id", str(uuid4())),
                code="validation_error",
                message="Request validation failed",
                details={"errors": exc.errors()},
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=ApiError(
                request_id=getattr(request.state, "request_id", str(uuid4())),
                code="internal_error",
                message="Internal server error",
                details={"error": str(exc)},
            ).model_dump(),
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/v1/auth/token")
    def issue_token(
        api_key: str = Form(...),
    ):
        return guard.issue_token_from_api_key(api_key)

    @app.post("/v1/auth/signup")
    def sign_up(payload: SignUpRequest = Body(...)):
        email = payload.email.strip().lower()
        if "@" not in email:
            raise HTTPException(status_code=400, detail="Invalid email")
        try:
            user = storage.create_user(
                full_name=payload.full_name.strip(),
                email=email,
                password_hash=hash_password(payload.password),
                role="verifier",
            )
        except sqlite3.IntegrityError as exc:
            raise HTTPException(status_code=409, detail="Email already registered") from exc

        token_bundle = guard.issue_token(principal=user["user_id"], role=user["role"])
        return {
            **token_bundle,
            "user": {
                "user_id": user["user_id"],
                "full_name": user["full_name"],
                "email": user["email"],
                "role": user["role"],
            },
        }

    @app.post("/v1/auth/login")
    def sign_in(payload: SignInRequest = Body(...)):
        email = payload.email.strip().lower()
        user = storage.get_user_by_email(email)
        if not user or not user.get("is_active"):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if not verify_password(payload.password, str(user.get("password_hash", ""))):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        token_bundle = guard.issue_token(principal=str(user["user_id"]), role=str(user["role"]))
        return {
            **token_bundle,
            "user": {
                "user_id": user["user_id"],
                "full_name": user["full_name"],
                "email": user["email"],
                "role": user["role"],
            },
        }

    @app.post("/v1/profile/validate/pan")
    def validate_pan(payload: PanValidationRequest = Body(...), auth=guard.require({"admin", "verifier", "auditor"})):
        pan = payload.pan.strip().upper()
        format_valid = bool(re.fullmatch(r"[A-Z]{5}[0-9]{4}[A-Z]", pan))
        if not format_valid:
            return {
                "pan": pan,
                "format_valid": False,
                "exists": False,
                "verified": False,
                "source": "Local PAN format validator",
                "message": "PAN format is invalid. Expected pattern: AAAAA0000A.",
            }

        registry_client = OfficialRegistryClient(
            endpoints=settings.registry_endpoints,
            headers=settings.registry_headers,
        )
        exists, source = registry_client.verify_pan(pan)
        storage.log_audit(
            actor_role=auth.role,
            action="validate_pan",
            resource_id=None,
            details={"pan_tail": pan[-4:], "verified": exists, "source": source},
        )
        return {
            "pan": pan,
            "format_valid": True,
            "exists": bool(exists),
            "verified": bool(exists),
            "source": source,
            "message": "PAN validated successfully."
            if exists
            else "PAN could not be verified by the configured registry source.",
        }

    @app.post("/v1/chat")
    def chat_with_schemes(payload: ChatRequest = Body(...), auth=guard.require({"admin", "verifier", "auditor"})):
        answer = chat_service.answer(
            query=payload.query,
            language=payload.language,
            schemes=payload.schemes,
            profile=payload.profile,
            history=[item.model_dump() for item in payload.history],
        )
        if answer.get("mode") == "error":
            raise HTTPException(status_code=503, detail=answer.get("error", "Live LLM unavailable"))
        storage.log_audit(
            actor_role=auth.role,
            action="chat_with_schemes",
            resource_id=None,
            details={"query": payload.query[:120], "schemes_count": len(payload.schemes)},
        )
        return answer

    @app.get("/v1/schemes/retrieve")
    def retrieve_schemes(
        query: str,
        k: int = 8,
        auth=guard.require({"admin", "verifier", "auditor"}),
    ):
        results = local_index.search(query=query, k=k)
        storage.log_audit(
            actor_role=auth.role,
            action="retrieve_schemes",
            resource_id=None,
            details={"query": query[:120], "k": k, "count": len(results), "backend": local_index.backend},
        )
        return {
            "query": query,
            "backend": local_index.backend,
            "results": [{"score": item.score, "scheme": item.scheme} for item in results],
        }

    @app.post("/v1/chat/local")
    def chat_with_schemes_local(payload: ChatRequest = Body(...), auth=guard.require({"admin", "verifier", "auditor"})):
        retrieved = local_index.search(query=payload.query, k=8)
        candidate_schemes = [item.scheme for item in retrieved] or payload.schemes
        answer = chat_service.answer(
            query=payload.query,
            language=payload.language,
            schemes=candidate_schemes,
            profile=payload.profile,
            history=[item.model_dump() for item in payload.history],
        )
        if answer.get("mode") == "error":
            raise HTTPException(status_code=503, detail=answer.get("error", "Local LLM unavailable"))
        storage.log_audit(
            actor_role=auth.role,
            action="chat_with_schemes_local",
            resource_id=None,
            details={
                "query": payload.query[:120],
                "retrieved_count": len(candidate_schemes),
                "retrieval_backend": local_index.backend,
            },
        )
        answer["retrieval_backend"] = local_index.backend
        return answer

    @app.post("/v1/verify")
    async def verify_document(
        document_type: str = Form(...),
        claimed_authority: str = Form(default=""),
        enterprise_profile_json: str = Form(default="{}"),
        scheme_requirements_json: str = Form(default="{}"),
        file: UploadFile = File(...),
        auth=guard.require({"admin", "verifier"}),
    ):
        extension = Path(file.filename or "").suffix.lower()
        content_type = (file.content_type or "").lower().strip()
        if extension not in ALLOWED_FILE_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type '{extension or 'unknown'}'. Allowed: {', '.join(sorted(ALLOWED_FILE_EXTENSIONS))}",
            )
        if content_type and content_type not in ALLOWED_CONTENT_TYPES and not content_type.startswith(("image/", "text/")):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported content type '{content_type}'. Allowed PDF, text, and image documents only.",
            )

        try:
            profile = EnterpriseProfile.model_validate(json.loads(enterprise_profile_json))
            scheme = SchemeRequirements.model_validate(json.loads(scheme_requirements_json))
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid profile/scheme payload: {exc}") from exc

        payload = await file.read()
        context = VerificationContext(
            document_type=document_type,
            claimed_authority=claimed_authority or None,
            enterprise_profile=profile,
            scheme_requirements=scheme,
        )
        report = engine.verify_document(
            file_name=file.filename or "uploaded_document",
            content=payload,
            content_type=file.content_type,
            context=context,
        )
        storage.save_report(report)
        storage.log_audit(
            actor_role=auth.role,
            action="verify_document",
            resource_id=report.report_id,
            details={
                "document_type": document_type,
                "file_name": file.filename or "",
                "auth_type": auth.auth_type,
            },
        )
        return report

    @app.get("/v1/reports/{report_id}")
    def get_report(report_id: str, auth=guard.require({"admin", "auditor"})):
        report = storage.get_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        storage.log_audit(
            actor_role=auth.role,
            action="get_report",
            resource_id=report_id,
            details={},
        )
        return report

    @app.post("/v1/audit/event")
    def add_scheme_audit_event(
        payload: SchemeAuditEventRequest = Body(...),
        auth=guard.require({"admin", "verifier", "auditor"}),
    ):
        event = storage.add_scheme_audit_event(
            scheme_id=payload.scheme_id,
            actor_role=auth.role,
            action=payload.action,
            detail=payload.detail,
            level=payload.level,
        )
        storage.log_audit(
            actor_role=auth.role,
            action="add_scheme_audit_event",
            resource_id=payload.scheme_id,
            details={"event_id": event.event_id, "level": payload.level},
        )
        return event

    @app.get("/v1/audit")
    def list_scheme_audit_events(
        scheme_id: str,
        limit: int = 200,
        auth=guard.require({"admin", "verifier", "auditor"}),
    ):
        events = storage.list_scheme_audit_events(scheme_id=scheme_id, limit=limit)
        storage.log_audit(
            actor_role=auth.role,
            action="list_scheme_audit_events",
            resource_id=scheme_id,
            details={"limit": limit, "count": len(events)},
        )
        return {"scheme_id": scheme_id, "events": [event.model_dump(mode="json") for event in events]}

    return app


def _build_encryption(settings: Settings):
    from .security import EncryptionService

    return EncryptionService(settings.aes_key_b64)


app = create_app()
