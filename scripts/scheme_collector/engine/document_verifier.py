import json
import os
from pathlib import Path
from typing import Any

import requests


class DocumentVerificationClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout_seconds: int = 45,
    ):
        self.base_url = (base_url or os.getenv("DOC_VERIFY_BASE_URL", "http://127.0.0.1:8000")).rstrip("/")
        self.api_key = api_key or os.getenv("DOC_VERIFY_API_KEY", "verifier-local-key")
        self.bearer_token = os.getenv("DOC_VERIFY_BEARER_TOKEN", "")
        self.timeout_seconds = timeout_seconds

    def _auth_headers(self) -> dict[str, str]:
        if self.bearer_token:
            return {"Authorization": f"Bearer {self.bearer_token}"}
        return {"X-API-Key": self.api_key}

    def verify_file(
        self,
        *,
        file_path: str | Path,
        document_type: str,
        claimed_authority: str = "",
        enterprise_profile: dict[str, Any] | None = None,
        scheme_requirements: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")

        with file_path.open("rb") as handle:
            files = {"file": (file_path.name, handle, "application/octet-stream")}
            data = {
                "document_type": document_type,
                "claimed_authority": claimed_authority,
                "enterprise_profile_json": json.dumps(enterprise_profile or {}),
                "scheme_requirements_json": json.dumps(scheme_requirements or {}),
            }
            resp = requests.post(
                f"{self.base_url}/v1/verify",
                headers=self._auth_headers(),
                data=data,
                files=files,
                timeout=self.timeout_seconds,
            )
            resp.raise_for_status()
            return resp.json()

    def fetch_report(self, report_id: str) -> dict[str, Any]:
        resp = requests.get(
            f"{self.base_url}/v1/reports/{report_id}",
            headers=self._auth_headers(),
            timeout=self.timeout_seconds,
        )
        resp.raise_for_status()
        return resp.json()

    def mint_bearer_token(self) -> dict[str, Any]:
        resp = requests.post(
            f"{self.base_url}/v1/auth/token",
            data={"api_key": self.api_key},
            timeout=self.timeout_seconds,
        )
        resp.raise_for_status()
        token_payload = resp.json()
        token = token_payload.get("access_token", "")
        if token:
            self.bearer_token = token
        return token_payload
