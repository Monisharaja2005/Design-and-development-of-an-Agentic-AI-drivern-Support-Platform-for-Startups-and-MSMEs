from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Any


@dataclass
class QRResult:
    payload: dict[str, Any] | None
    verified: bool
    detail: str


@dataclass
class SignatureResult:
    has_signature_block: bool
    verified: bool
    detail: str


class OCRAdapter:
    def extract_from_image(self, content: bytes) -> str:
        try:
            import pytesseract  # type: ignore
            from PIL import Image  # type: ignore

            image = Image.open(BytesIO(content))
            return pytesseract.image_to_string(image)
        except Exception:
            return ""


class QRAdapter:
    def decode(self, content: bytes) -> QRResult:
        # Primary path: pyzbar for common QR extraction.
        try:
            from PIL import Image  # type: ignore
            from pyzbar.pyzbar import decode  # type: ignore

            image = Image.open(BytesIO(content))
            decoded = decode(image)
            if not decoded:
                return QRResult(payload=None, verified=False, detail="No QR code detected")
            raw = decoded[0].data.decode("utf-8", errors="ignore").strip()
            payload = _parse_payload(raw)
            return QRResult(payload=payload, verified=payload is not None, detail="QR decoded")
        except Exception as exc:
            return QRResult(payload=None, verified=False, detail=f"QR decode adapter unavailable: {exc}")


class SignatureAdapter:
    def verify(self, text: str, file_name: str) -> SignatureResult:
        sample = text.lower()
        has_block = any(token in sample for token in ("digitally signed", "digital signature", "signature valid"))
        if not has_block:
            return SignatureResult(has_signature_block=False, verified=False, detail="No signature block found")
        if "signature valid" in sample or "digitally signed" in sample:
            return SignatureResult(
                has_signature_block=True,
                verified=True,
                detail=f"Signature validation passed by adapter heuristic for {file_name}",
            )
        # Placeholder for PKI verification integration.
        # In production, parse PKCS#7 or PDF signature dictionaries and verify chain/trust.
        return SignatureResult(
            has_signature_block=True,
            verified=False,
            detail=f"Signature block detected in {file_name}; PKI trust-chain validation not configured",
        )


def _parse_payload(raw: str) -> dict[str, Any] | None:
    import json

    if not raw:
        return None
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {"value": parsed}
    except Exception:
        # fallback key-value parser: GSTIN=..;PAN=..
        payload: dict[str, Any] = {}
        for item in raw.split(";"):
            if "=" in item:
                key, value = item.split("=", 1)
                payload[key.strip().lower()] = value.strip()
        return payload or {"value": raw}
