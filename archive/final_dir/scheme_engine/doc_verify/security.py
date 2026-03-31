from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import Depends, Header, HTTPException, status


@dataclass(frozen=True)
class AuthContext:
    principal: str
    role: str
    auth_type: str


class AuthManager:
    def __init__(self, key_to_role: dict[str, str], jwt_secret: str, jwt_issuer: str, jwt_ttl_minutes: int):
        self.key_to_role = key_to_role
        self.jwt_secret = jwt_secret.encode("utf-8")
        self.jwt_issuer = jwt_issuer
        self.jwt_ttl_minutes = jwt_ttl_minutes

    def issue_token_from_api_key(self, api_key: str) -> dict[str, object]:
        role = self.key_to_role.get(api_key)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )
        return self.issue_token(principal="api_key_client", role=role)

    def issue_token(self, *, principal: str, role: str) -> dict[str, object]:
        now = datetime.now(tz=UTC)
        payload = {
            "sub": principal,
            "role": role,
            "iss": self.jwt_issuer,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=self.jwt_ttl_minutes)).timestamp()),
        }
        token = _encode_jwt_hs256(payload, self.jwt_secret)
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": self.jwt_ttl_minutes * 60,
            "role": role,
        }

    def require(self, allowed_roles: set[str]):
        def _dependency(
            authorization: str = Header(default="", alias="Authorization"),
            x_api_key: str = Header(default="", alias="X-API-Key"),
        ) -> AuthContext:
            if authorization.lower().startswith("bearer "):
                token = authorization.split(" ", 1)[1].strip()
                payload = _decode_jwt_hs256(token, self.jwt_secret)
                if payload.get("iss") != self.jwt_issuer:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token issuer")
                exp = int(payload.get("exp", 0))
                if exp <= int(datetime.now(tz=UTC).timestamp()):
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
                role = str(payload.get("role", "")).lower()
                if role not in allowed_roles:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Insufficient role for this endpoint",
                    )
                return AuthContext(principal=str(payload.get("sub", "token_client")), role=role, auth_type="jwt")

            role = self.key_to_role.get(x_api_key)
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing bearer token or valid API key",
                )
            if role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient role for this endpoint",
                )
            return AuthContext(principal="api_key_client", role=role, auth_type="api_key")

        return Depends(_dependency)


class EncryptionService:
    def __init__(self, key_b64: str):
        try:
            self._key = base64.b64decode(key_b64)
        except Exception as exc:
            raise ValueError("DOC_VERIFY_AES_KEY must be a base64 AES-256 key") from exc
        if len(self._key) != 32:
            raise ValueError("AES-256 key must be 32 bytes after base64 decoding")

    @staticmethod
    def generate_key() -> str:
        return base64.b64encode(os.urandom(32)).decode("ascii")

    def encrypt(self, payload: bytes) -> bytes:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        nonce = os.urandom(12)
        cipher = AESGCM(self._key)
        encrypted = cipher.encrypt(nonce, payload, associated_data=None)
        return nonce + encrypted

    def decrypt(self, payload: bytes) -> bytes:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        nonce, ciphertext = payload[:12], payload[12:]
        cipher = AESGCM(self._key)
        return cipher.decrypt(nonce, ciphertext, associated_data=None)


def _encode_jwt_hs256(payload: dict[str, object], secret: bytes) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = hmac.new(secret, signing_input, hashlib.sha256).digest()
    signature_b64 = _b64url(signature)
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def _decode_jwt_hs256(token: str, secret: bytes) -> dict[str, object]:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed token") from exc
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    expected_sig = hmac.new(secret, signing_input, hashlib.sha256).digest()
    actual_sig = _b64url_decode(signature_b64)
    if not hmac.compare_digest(expected_sig, actual_sig):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token signature")
    payload_raw = _b64url_decode(payload_b64)
    try:
        payload = json.loads(payload_raw.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload") from exc
    return payload if isinstance(payload, dict) else {}


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 210_000)
    return f"pbkdf2_sha256$210000${base64.urlsafe_b64encode(salt).decode('ascii')}${base64.urlsafe_b64encode(derived).decode('ascii')}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations_raw, salt_b64, hash_b64 = stored_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_raw)
        salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
        expected = base64.urlsafe_b64decode(hash_b64.encode("ascii"))
    except Exception:
        return False

    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(candidate, expected)
