from __future__ import annotations

import re
from scheme_engine.core.text import normalize_text


SECTION_PATTERNS = [
    ("eligibility", re.compile(r"eligibility|who can apply|who can avail", re.I)),
    ("benefits", re.compile(r"benefits|subsidy|grant|assistance|incentive", re.I)),
    ("application", re.compile(r"how to apply|application|process|steps", re.I)),
    ("documents", re.compile(r"documents|required documents|checklist", re.I)),
    ("geography", re.compile(r"state|district|region|area", re.I)),
]


def is_scheme_like(text: str, keywords: list[str]) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return any(k in lowered for k in keywords)


def extract_sections(text: str) -> dict:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    joined = "\n".join(lines)

    sections = {"eligibility": "", "benefits": "", "application": "", "documents": "", "geography": ""}
    for name, pattern in SECTION_PATTERNS:
        match = pattern.search(joined)
        if not match:
            continue
        start = match.start()
        snippet = joined[start:start + 1200]
        sections[name] = normalize_text(snippet)

    return sections


def extract_scheme(text: str, title: str, keywords: list[str]) -> dict | None:
    if not is_scheme_like(text, keywords):
        return None

    sections = extract_sections(text)
    summary = normalize_text(text[:2000])

    return {
        "name": title or "Untitled Scheme",
        "summary": summary,
        "eligibility": sections.get("eligibility", ""),
        "benefits": sections.get("benefits", ""),
        "application": sections.get("application", ""),
        "documents": sections.get("documents", ""),
        "geography": sections.get("geography", ""),
        "confidence": 0.35,
    }
