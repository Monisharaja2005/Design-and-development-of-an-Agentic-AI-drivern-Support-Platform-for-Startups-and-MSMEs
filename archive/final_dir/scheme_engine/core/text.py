from __future__ import annotations

import re
import hashlib


def normalize_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text


def fingerprint(text: str) -> str:
    norm = normalize_text(text).lower()
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()


def extract_title(text: str) -> str:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    return lines[0] if lines else ""
