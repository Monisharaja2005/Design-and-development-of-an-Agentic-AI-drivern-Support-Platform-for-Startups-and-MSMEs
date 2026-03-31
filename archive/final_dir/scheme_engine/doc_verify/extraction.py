from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

from .adapters import OCRAdapter, QRAdapter, SignatureAdapter
from .models import ExtractedDocumentData

GSTIN_RE = re.compile(r"\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b")
PAN_RE = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")
UDYAM_RE = re.compile(r"\bUDYAM-[A-Z]{2}-\d{2}-\d{7}\b")
CIN_RE = re.compile(r"\b[LU]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}\b")
SERIAL_RE = re.compile(r"\b(?:Serial|Certificate|Cert|Reg(?:istration)?)\s*(?:No|Number|#)?\s*[:\-]?\s*([A-Z0-9\/\-]{6,})", re.I)
URL_RE = re.compile(r"\bhttps?://[a-zA-Z0-9\-._~:/?#\[\]@!$&'()*+,;=%]+\b")
DATE_RE = re.compile(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b")
TURNOVER_RE = re.compile(r"\bturnover\b[^0-9]{0,20}([0-9][0-9,]*(?:\.\d+)?)", re.I)
NAME_HINT_RE = re.compile(r"(?:name of (?:enterprise|business|applicant)|legal name)\s*[:\-]\s*(.+)", re.I)
AUTHORITY_LINE_RE = re.compile(r"(ministry|department|government|authority|board).{0,100}", re.I)

GOVERNMENT_HEADERS = (
    "government of india",
    "govt. of india",
    "bharat sarkar",
    "ministry of",
    "department of",
)


class DocumentExtractor:
    def __init__(self):
        self.ocr_adapter = OCRAdapter()
        self.qr_adapter = QRAdapter()
        self.signature_adapter = SignatureAdapter()

    def extract(self, file_name: str, content: bytes, content_type: str | None = None) -> ExtractedDocumentData:
        text, metadata = self._extract_text(file_name=file_name, content=content, content_type=content_type)
        return self._extract_structured(text=text, metadata=metadata, content=content, file_name=file_name)

    def extract_from_text(self, text: str, metadata: dict[str, Any] | None = None) -> ExtractedDocumentData:
        return self._extract_structured(text=text, metadata=metadata or {}, content=b"", file_name="text_input.txt")

    def _extract_text(self, file_name: str, content: bytes, content_type: str | None = None) -> tuple[str, dict[str, Any]]:
        ext = file_name.lower().rsplit(".", 1)[-1] if "." in file_name else ""
        metadata: dict[str, Any] = {"file_name": file_name, "content_type": content_type or "", "extension": ext}

        if content_type and content_type.startswith("text/"):
            return content.decode("utf-8", errors="ignore"), metadata

        if ext == "pdf":
            text = self._extract_pdf_text(content)
            return text, metadata

        if ext in {"png", "jpg", "jpeg", "tif", "tiff", "bmp"}:
            text = self._extract_ocr_text(content)
            return text, metadata

        return content.decode("utf-8", errors="ignore"), metadata

    def _extract_pdf_text(self, content: bytes) -> str:
        try:
            from io import BytesIO

            from pypdf import PdfReader  # type: ignore

            reader = PdfReader(BytesIO(content))
            return "\n".join((page.extract_text() or "") for page in reader.pages)
        except Exception:
            return content.decode("utf-8", errors="ignore")

    def _extract_ocr_text(self, content: bytes) -> str:
        try:
            from io import BytesIO

            return self.ocr_adapter.extract_from_image(content)
        except Exception:
            return ""

    def _extract_structured(self, text: str, metadata: dict[str, Any], content: bytes, file_name: str) -> ExtractedDocumentData:
        normalized = " ".join(text.split())
        name_match = NAME_HINT_RE.search(text)
        authority_match = AUTHORITY_LINE_RE.search(text)
        turnover_match = TURNOVER_RE.search(text)
        qr_payload = self._parse_qr_payload_hint(text)
        qr_scan = self.qr_adapter.decode(content) if content else None
        signature = self.signature_adapter.verify(text=text, file_name=file_name)

        final_qr_payload = qr_payload or (qr_scan.payload if qr_scan else None)
        qr_verified = bool(qr_scan and qr_scan.verified) or bool(qr_payload)
        qr_detail = qr_scan.detail if qr_scan else ("QRDATA marker parsed" if qr_payload else "No QR source available")

        return ExtractedDocumentData(
            text=text,
            business_name=name_match.group(1).strip() if name_match else None,
            gstin=_first_match(GSTIN_RE, text),
            pan=_first_match(PAN_RE, text),
            udyam_id=_first_match(UDYAM_RE, text),
            cin=_first_match(CIN_RE, text),
            certificate_number=_first_serial(text),
            serial_number=_first_serial(text),
            authority_name=authority_match.group(0).strip() if authority_match else None,
            urls=URL_RE.findall(text),
            dates=DATE_RE.findall(text),
            turnover=_to_float(turnover_match.group(1)) if turnover_match else None,
            has_government_header=any(h in normalized.lower() for h in GOVERNMENT_HEADERS),
            has_signature_block=signature.has_signature_block or _has_signature_block(text),
            signature_verified=signature.verified,
            signature_verification_detail=signature.detail,
            qr_payload=final_qr_payload,
            qr_verified=qr_verified,
            qr_verification_detail=qr_detail,
            metadata=metadata,
        )

    def normalize_dates(self, dates: list[str]) -> list[datetime]:
        parsed: list[datetime] = []
        for raw in dates:
            for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y"):
                try:
                    parsed.append(datetime.strptime(raw, fmt))
                    break
                except ValueError:
                    continue
        return parsed

    def _parse_qr_payload_hint(self, text: str) -> dict[str, Any] | None:
        marker = "QRDATA:"
        if marker not in text:
            return None
        try:
            payload = text.split(marker, 1)[1].strip().splitlines()[0]
            return json.loads(payload)
        except Exception:
            return None


def _first_match(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    return match.group(0) if match else None


def _first_serial(text: str) -> str | None:
    match = SERIAL_RE.search(text)
    return match.group(1) if match else None


def _to_float(raw: str) -> float | None:
    try:
        return float(raw.replace(",", ""))
    except Exception:
        return None


def _has_signature_block(text: str) -> bool:
    sample = text.lower()
    return any(
        token in sample
        for token in (
            "digitally signed",
            "digital signature",
            "signature valid",
            "signature",
        )
    )
