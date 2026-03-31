from __future__ import annotations

from scheme_engine.core.text import fingerprint


def scheme_fingerprint(name: str, summary: str, benefits: str) -> str:
    combined = " ".join([name or "", summary or "", benefits or ""])
    return fingerprint(combined)
