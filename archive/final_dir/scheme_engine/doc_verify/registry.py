from __future__ import annotations

import json
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path


@dataclass(frozen=True)
class AuthorityRecord:
    authority_name: str
    aliases: list[str]
    domains: list[str]
    document_types: list[str]


class AuthorityRegistry:
    def __init__(self, records: list[AuthorityRecord]):
        self._records = records

    @classmethod
    def from_file(cls, path: Path) -> "AuthorityRegistry":
        raw = json.loads(path.read_text(encoding="utf-8"))
        records = [
            AuthorityRecord(
                authority_name=item["authority_name"],
                aliases=[alias.lower() for alias in item.get("aliases", [])],
                domains=[domain.lower() for domain in item.get("domains", [])],
                document_types=[doc.lower() for doc in item.get("document_types", [])],
            )
            for item in raw
        ]
        return cls(records)

    @property
    def records(self) -> list[AuthorityRecord]:
        return self._records

    def detect_from_text(self, text: str) -> AuthorityRecord | None:
        sample = text.lower()
        best: tuple[int, int, AuthorityRecord] | None = None
        for record in self._records:
            hits = 0
            strongest = 0
            tokens = [record.authority_name.lower(), *record.aliases]
            for token in tokens:
                if token and token in sample:
                    hits += 1
                    strongest = max(strongest, len(token))
            if hits == 0:
                continue
            candidate = (hits, strongest, record)
            if best is None or (candidate[0], candidate[1]) > (best[0], best[1]):
                best = candidate
        return best[2] if best else None

    def match_name(self, candidate: str | None, threshold: float = 0.78) -> AuthorityRecord | None:
        if not candidate:
            return None
        candidate_norm = candidate.strip().lower()
        best: tuple[float, AuthorityRecord] | None = None
        for record in self._records:
            names = [record.authority_name.lower(), *record.aliases]
            score = max(SequenceMatcher(None, candidate_norm, name).ratio() for name in names)
            if best is None or score > best[0]:
                best = (score, record)
        if best and best[0] >= threshold:
            return best[1]
        return None
