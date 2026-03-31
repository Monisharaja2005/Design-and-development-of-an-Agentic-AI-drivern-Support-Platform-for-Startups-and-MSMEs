# Document Verification + Scheme Assistant Integration

This project supports:
1. Government document verification (authenticity, format, authority checks)
2. Scheme assistant chat (live provider: local/puter/backend)
3. Pipeline-level auto-verification for downloaded scheme files

## Architecture

1. `scheme_collector` calls verifier APIs via `engine/document_verifier.py`
2. Verifier backend runs in `final/scheme_engine/doc_verify`
3. Frontend (`frontend`) consumes chat + verification endpoints

## Supported document types

Use these strict types where possible:
1. `gst_certificate`
2. `pan_card`
3. `udyam_certificate`
4. `cin_certificate`
5. `generic_certificate` (fallback/general)

If selected document type and extracted content mismatch, status becomes `Invalid`.

## Start backend verifier service

From `d:\final\final`:

```bash
python -m uvicorn scheme_engine.doc_verify_app:app --app-dir d:\final\final --host 127.0.0.1 --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Expected:

```json
{"status":"ok"}
```

## Manual file verification

From `d:\final\scheme_collector`:

```bash
python verify_document.py --file documents/files/PMEGP_Guidelines.pdf --document-type generic_certificate --claimed-authority "Government of India"
```

Optional payloads:
1. `--enterprise-profile-json`
2. `--scheme-requirements-json`

Example with profile + requirements:

```bash
python verify_document.py ^
  --file documents/files/sample_gst_certificate.txt ^
  --document-type gst_certificate ^
  --claimed-authority "Goods and Services Tax Network" ^
  --enterprise-profile-json "{\"enterprise_name\":\"Skathi\",\"state\":\"Tamil Nadu\"}" ^
  --scheme-requirements-json "{\"required_document_types\":[\"gst_certificate\",\"pan_card\"]}"
```

## Auto-verify in scheme pipeline

Set env before `python run_engine.py`:

```bash
ENABLE_DOC_VERIFY=true
DOC_VERIFY_BASE_URL=http://127.0.0.1:8000
DOC_VERIFY_API_KEY=verifier-local-key
DOC_VERIFY_DEFAULT_TYPE=generic_certificate
DOC_VERIFY_DEFAULT_AUTHORITY="Government of India"
```

Output verification summaries are stored in MongoDB collection `doc_verifications`.

## JWT auth (optional)

Mint bearer token from API key:

```bash
python -c "from engine.document_verifier import DocumentVerificationClient as C; c=C(); print(c.mint_bearer_token())"
```

Then set:

```bash
DOC_VERIFY_BEARER_TOKEN=<token>
```

## Scheme assistant chat providers

Set frontend provider via:

```bash
VITE_SCHEME_CHAT_PROVIDER=...
```

Values:
1. `puter-web` -> Puter live chat
2. `local` -> local retrieval + `/v1/chat/local` (Ollama-backed)
3. `backend` -> `/v1/chat`

## Local assistant mode (recommended no API cost)

Backend env:

```bash
DOC_VERIFY_LLM_PROVIDER=ollama
DOC_VERIFY_LOCAL_CHAT_MODEL=mistral:latest
DOC_VERIFY_OLLAMA_BASE_URL=http://127.0.0.1:11434
DOC_VERIFY_SCHEMES_CSV=d:\final\frontend\dist\schemes.csv
DOC_VERIFY_EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

Frontend env:

```bash
VITE_SCHEME_CHAT_PROVIDER=local
VITE_DOC_VERIFY_BASE_URL=http://127.0.0.1:8000
```

## Retrieval API (local semantic index)

Endpoint:

```bash
GET /v1/schemes/retrieve?query=<text>&k=8
```

Use this to inspect top matched schemes and retrieval backend (`sentence-transformers` or `lexical`).

## Common issues and fixes

1. `Live Failed: Failed to fetch`
- Backend not reachable / wrong base URL / CORS mismatch.
- Check `http://127.0.0.1:8000/health`.

2. `provider is not supported`
- Set `DOC_VERIFY_LLM_PROVIDER` correctly (`ollama`, `openai`, `kimi`, or use non-strict fallback).

3. `No module named fastapi`
- Install backend deps:

```bash
pip install -r d:\final\final\requirements.txt
```

4. `Document not found`
- Use correct absolute/relative path from current working directory.

5. `strict mode` failures with paid APIs
- Quota/billing/API key issues; switch to local `ollama` mode.

## Expected verification output fields

1. `status`: `Valid | Invalid | Suspicious`
2. `authenticity_score`
3. `fraud_risk`
4. `authority_verification`
5. `breakdown` (layer-wise checks)
6. `extracted_data`

Use these fields to drive approval/rejection in downstream workflow.
