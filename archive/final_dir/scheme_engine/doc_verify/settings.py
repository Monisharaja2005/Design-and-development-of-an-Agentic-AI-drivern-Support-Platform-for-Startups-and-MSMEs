from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ScoreWeights:
    govt_issuer: float = 0.25
    authority_check: float = 0.20
    format_check: float = 0.20
    api_check: float = 0.20
    fraud_inverse: float = 0.15


@dataclass(frozen=True)
class Settings:
    db_path: Path
    authority_registry_path: Path
    aes_key_b64: str
    score_weights: ScoreWeights
    api_keys: dict[str, str]
    registry_endpoints: dict[str, str]
    registry_headers: dict[str, str]
    cors_origins: list[str]
    jwt_secret: str
    jwt_issuer: str
    jwt_ttl_minutes: int
    llm_provider: str
    llm_model: str
    llm_api_key: str
    llm_base_url: str
    karios_ai_api_key: str
    karios_ai_base_url: str
    karios_ai_model: str
    llm_strict_live: bool
    llm_timeout_seconds: float | None
    ollama_base_url: str
    ollama_models: list[str]
    kimi_api_key: str
    kimi_base_url: str
    kimi_model: str
    duckduckai_model: str
    hf_api_key: str
    hf_model: str
    schemes_csv_path: Path
    embedding_model: str
    local_chat_model: str

    @classmethod
    def from_env(cls) -> "Settings":
        base_dir = Path(__file__).resolve().parent
        _load_env_files(base_dir)
        db_path = Path(os.getenv("DOC_VERIFY_DB_PATH", str(base_dir / "data" / "doc_verify.db")))
        authority_registry_path = Path(
            os.getenv(
                "DOC_VERIFY_AUTHORITY_REGISTRY",
                str(base_dir / "data" / "government_authorities.json"),
            )
        )

        key = os.getenv("DOC_VERIFY_AES_KEY", "")
        if not key:
            key = base64.b64encode(os.urandom(32)).decode("ascii")

        api_keys = _parse_api_keys(
            os.getenv(
                "DOC_VERIFY_API_KEYS",
                "admin:admin-local-key,verifier:verifier-local-key,auditor:auditor-local-key",
            )
        )
        registry_endpoints = _parse_mapping(
            os.getenv(
                "DOC_VERIFY_REGISTRY_ENDPOINTS",
                (
                    "gstin:,"
                    "pan:,"
                    "cin:,"
                    "udyam:"
                ),
            )
        )
        registry_headers = _parse_mapping(os.getenv("DOC_VERIFY_REGISTRY_HEADERS", ""))
        cors_origins = _parse_list(
            os.getenv(
                "DOC_VERIFY_CORS_ORIGINS",
                (
                    "http://localhost:5173,http://127.0.0.1:5173,"
                    "http://localhost:5174,http://127.0.0.1:5174,"
                    "http://localhost:5175,http://127.0.0.1:5175,"
                    "http://localhost:5176,http://127.0.0.1:5176"
                ),
            )
        )
        jwt_secret = os.getenv("DOC_VERIFY_JWT_SECRET", "")
        if not jwt_secret:
            jwt_secret = base64.b64encode(os.urandom(32)).decode("ascii")
        jwt_issuer = os.getenv("DOC_VERIFY_JWT_ISSUER", "doc-verify-service")
        jwt_ttl_minutes = int(os.getenv("DOC_VERIFY_JWT_TTL_MINUTES", "120"))
        llm_provider = os.getenv("DOC_VERIFY_LLM_PROVIDER", "lmstudio")
        llm_model = os.getenv("DOC_VERIFY_LLM_MODEL", "local-model")
        llm_api_key = os.getenv("GEMINI_API_KEY", "") or os.getenv("DOC_VERIFY_GEMINI_API_KEY", "")
        llm_base_url = os.getenv("DOC_VERIFY_LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
        gemini_api_key = os.getenv("GEMINI_API_KEY", "") or os.getenv("DOC_VERIFY_GEMINI_API_KEY", "")
        gemini_base_url = os.getenv("DOC_VERIFY_GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")
        gemini_model = os.getenv("DOC_VERIFY_GEMINI_MODEL", "gemini-1.5-flash")
        llm_strict_live = _parse_bool(os.getenv("DOC_VERIFY_LLM_STRICT_LIVE", "false"))
        llm_timeout_seconds = _parse_timeout_seconds(os.getenv("DOC_VERIFY_LLM_TIMEOUT_SECONDS", "120"))
        ollama_base_url = os.getenv("DOC_VERIFY_OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        ollama_models = _parse_list(os.getenv("DOC_VERIFY_OLLAMA_MODELS", ""))
        kimi_api_key = os.getenv("DOC_VERIFY_KIMI_API_KEY", "")
        kimi_base_url = os.getenv("DOC_VERIFY_KIMI_BASE_URL", "https://api.moonshot.ai/v1")
        kimi_model = os.getenv("DOC_VERIFY_KIMI_MODEL", "moonshot-v1-8k")
        duckduckai_model = os.getenv("DOC_VERIFY_DUCKDUCKAI_MODEL", "gpt-4o-mini")
        hf_api_key = os.getenv("DOC_VERIFY_HF_API_KEY", "")
        hf_model = os.getenv("DOC_VERIFY_HF_MODEL", "Qwen/Qwen3-14B")
        schemes_csv_path = Path(os.getenv("DOC_VERIFY_SCHEMES_CSV", str(Path("d:/final/frontend/data/schemes_correct_383.json"))))
        embedding_model = os.getenv("DOC_VERIFY_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        local_chat_model = os.getenv("DOC_VERIFY_LOCAL_CHAT_MODEL", "mistral:latest")
        return cls(
            db_path=db_path,
            authority_registry_path=authority_registry_path,
            aes_key_b64=key,
            score_weights=ScoreWeights(),
            api_keys=api_keys,
            registry_endpoints=registry_endpoints,
            registry_headers=registry_headers,
            cors_origins=cors_origins,
            jwt_secret=jwt_secret,
            jwt_issuer=jwt_issuer,
            jwt_ttl_minutes=jwt_ttl_minutes,
            llm_provider=llm_provider,
            llm_model=llm_model,
            llm_api_key=llm_api_key,
            llm_base_url=llm_base_url,
            karios_ai_api_key=gemini_api_key,
            karios_ai_base_url=gemini_base_url,
            karios_ai_model=gemini_model,
            llm_strict_live=llm_strict_live,
            llm_timeout_seconds=llm_timeout_seconds,
            ollama_base_url=ollama_base_url,
            ollama_models=ollama_models,
            kimi_api_key=kimi_api_key,
            kimi_base_url=kimi_base_url,
            kimi_model=kimi_model,
            duckduckai_model=duckduckai_model,
            hf_api_key=hf_api_key,
            hf_model=hf_model,
            schemes_csv_path=schemes_csv_path,
            embedding_model=embedding_model,
            local_chat_model=local_chat_model,
        )


def _parse_api_keys(raw: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for token in (part.strip() for part in raw.split(",")):
        if not token or ":" not in token:
            continue
        role, key = token.split(":", 1)
        role_clean = role.strip().lower()
        key_clean = key.strip()
        if role_clean and key_clean:
            mapping[key_clean] = role_clean
    return mapping


def _parse_mapping(raw: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for token in (part.strip() for part in raw.split(",")):
        if not token or ":" not in token:
            continue
        key, value = token.split(":", 1)
        key_clean = key.strip().lower()
        value_clean = value.strip()
        if key_clean and value_clean:
            mapping[key_clean] = value_clean
    return mapping


def _parse_list(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_timeout_seconds(value: str) -> float | None:
    raw = value.strip().lower()
    if not raw or raw in {"0", "none", "null", "off", "false"}:
        return None
    return float(raw)


def _default_schemes_csv(base_dir: Path) -> Path:
    # base_dir: .../scheme_engine/doc_verify
    repo_root = base_dir.parents[2]
    candidates = [
        repo_root / "frontend" / "dist" / "schemes.csv",
        repo_root / "frontend" / "public" / "schemes.csv",
        repo_root / "frontend" / "schemes.csv",
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


def _load_env_files(base_dir: Path) -> None:
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        return
    project_root = base_dir.parents[2]
    app_root = base_dir.parents[1]
    # Load both repo-level and app-level env files so local runs from d:\final\final
    # still pick up d:\final\final\.env without requiring shell exports.
    load_dotenv(project_root / ".env", override=False)
    load_dotenv(project_root / ".env.local", override=False)
    load_dotenv(app_root / ".env", override=False)
    load_dotenv(app_root / ".env.local", override=False)
