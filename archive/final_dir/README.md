# Scheme Intelligence Engine

This project bootstraps a multi-source, requirement-driven dataset pipeline for Indian government schemes focused on startups and MSMEs.

## Quick start

```bash
python -m scheme_engine.scraper --seeds scheme_engine/config/portals_full.json --db data/schemes.db --limit 300 --depth 1
```

## What it does
- Discovers and fetches pages from seed portals
- Extracts scheme-like content using rule-based parsing
- Deduplicates and stores normalized scheme intelligence in SQLite

## Folder layout
- `scheme_engine/` core pipeline
- `scheme_engine/config/` portal seeds and settings
- `data/` local SQLite database

## Notes
- This is a v1 scaffold optimized for quick iteration.
- You can expand extractors and add API services later.

## Document Authenticity Verification Module

This repository now includes a production-oriented document verification API at `scheme_engine/doc_verify`.

### Run API

```bash
uvicorn scheme_engine.doc_verify_app:app --reload
```

### Auth headers

Send an `X-API-Key` header.

- Verifier: `verifier-local-key`
- Auditor: `auditor-local-key`
- Admin: `admin-local-key`

Override with `DOC_VERIFY_API_KEYS`, format:

```bash
DOC_VERIFY_API_KEYS="admin:...,verifier:...,auditor:..."
```

### Verify endpoint

`POST /v1/verify` with `multipart/form-data`:
- `file`: uploaded document
- `document_type`: e.g. `gst_certificate`
- `claimed_authority`: optional authority name
- `enterprise_profile_json`: JSON object
- `scheme_requirements_json`: JSON object

Strict enforcement:
- Uploaded content must match selected `document_type` (keyword + mandatory identifier checks)
- Mismatch is hard-failed as `Invalid`
- Allowed file types: `.pdf`, `.png`, `.jpg`, `.jpeg`, `.tif`, `.tiff`, `.bmp`, `.txt`

The response includes:
- Government-issued detection results
- Authority verification and domain checks
- Format and syntax checks (GSTIN/PAN/Udyam/CIN/date/turnover)
- Registry API checks (mock adapter ready for real APIs)
- Signature/QR consistency checks
- Fraud risk scoring with feature attributions
- Authenticity score and explainable root causes

### Data security

- Validation reports are encrypted at rest using AES-256 (`cryptography` AES-GCM).
- Role-based access control enforced via JWT bearer token (with API key fallback).
- Audit logs and authority registry are stored in SQLite.

### JWT auth

Issue token:

```bash
curl -X POST http://127.0.0.1:8000/v1/auth/token -F "api_key=verifier-local-key"
```

Use token:

```bash
Authorization: Bearer <access_token>
```

### App user auth (email/password)

Sign up:

```bash
curl -X POST http://127.0.0.1:8000/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d "{\"full_name\":\"Skathi\",\"email\":\"you@example.com\",\"password\":\"StrongPass@123\"}"
```

Login:

```bash
curl -X POST http://127.0.0.1:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"you@example.com\",\"password\":\"StrongPass@123\"}"
```

Both endpoints return a bearer token and user profile. Use:

```bash
Authorization: Bearer <access_token>
```

Error responses follow a standard shape:
- `request_id`
- `code`
- `message`
- `details`

### Live registry connectors

Registry checks now support live HTTP API adapters for GSTIN, PAN, CIN, and Udyam.

Set endpoints and headers with environment variables:

```bash
DOC_VERIFY_REGISTRY_ENDPOINTS="gstin:https://.../gst/verify,pan:https://.../pan/verify,cin:https://.../cin/verify,udyam:https://.../udyam/verify"
DOC_VERIFY_REGISTRY_HEADERS="Authorization:Bearer <token>,x-api-key:<key>"
```

Expected API response can include one of:
- boolean: `active`, `is_active`, `valid`, `is_valid`, `verified`
- string status: `ACTIVE`, `VALID`, `VERIFIED`, `INACTIVE`, `INVALID`, `CANCELLED`, etc.

If endpoints are not set, the module uses offline heuristics so the pipeline still runs.

### Scheme chat endpoint (LLM)

`POST /v1/chat` accepts:
- `query`
- `profile` (object)
- `schemes` (array of scheme rows)
- `history` (optional chat history)

By default it uses deterministic fallback RAG-style responses.

Enable OpenAI:

```bash
DOC_VERIFY_LLM_PROVIDER=openai
DOC_VERIFY_OPENAI_API_KEY=<key>
DOC_VERIFY_LLM_MODEL=gpt-4o-mini
DOC_VERIFY_OPENAI_BASE_URL=https://api.openai.com/v1
```

Enable Ollama (local live LLM):

```bash
DOC_VERIFY_LLM_PROVIDER=ollama
DOC_VERIFY_LLM_MODEL=llama3.1
DOC_VERIFY_OLLAMA_BASE_URL=http://127.0.0.1:11434
DOC_VERIFY_LLM_STRICT_LIVE=true
DOC_VERIFY_OLLAMA_MODELS=mistral:latest,vicuna:latest,tinyllama:latest
```

Advanced free local mode (recommended):
- Keeps everything free/local (no paid API required).
- Tries multiple Ollama models in order and uses the first valid structured response.
- Improves reliability for scheme Q&A and required-document extraction.

Enable Kimi (Moonshot) live LLM:

```bash
DOC_VERIFY_LLM_PROVIDER=kimi
DOC_VERIFY_KIMI_API_KEY=<kimi_key>
DOC_VERIFY_KIMI_BASE_URL=https://api.moonshot.ai/v1
DOC_VERIFY_KIMI_MODEL=moonshot-v1-8k
DOC_VERIFY_LLM_STRICT_LIVE=true
```

Enable DuckDuckAI live LLM:

```bash
DOC_VERIFY_LLM_PROVIDER=duckduckai
DOC_VERIFY_DUCKDUCKAI_MODEL=gpt-4o-mini
DOC_VERIFY_LLM_STRICT_LIVE=true
```

Enable HuggingFace Inference API (free tier):

```bash
DOC_VERIFY_LLM_PROVIDER=huggingface
DOC_VERIFY_HF_API_KEY=<hf_token>
DOC_VERIFY_HF_MODEL=mistralai/Mistral-7B-Instruct-v0.1
DOC_VERIFY_LLM_STRICT_LIVE=false
```

Important:
- Keep provider API keys only in backend `final/.env`.
- Do not place secret keys in frontend `.env` or any `VITE_*` variables.
