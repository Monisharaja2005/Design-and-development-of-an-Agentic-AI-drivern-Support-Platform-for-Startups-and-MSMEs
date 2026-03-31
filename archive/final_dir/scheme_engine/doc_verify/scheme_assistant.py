from __future__ import annotations
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _tokenize(text: str) -> set[str]:
    return {tok for tok in text.lower().replace("/", " ").replace("-", " ").split() if len(tok) > 2}


def _normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec))
    if norm <= 0:
        return vec
    return [v / norm for v in vec]


def _dot(a: list[float], b: list[float]) -> float:
    size = min(len(a), len(b))
    return sum(a[i] * b[i] for i in range(size))


@dataclass
class RetrievedScheme:
    score: float
    scheme: dict[str, Any]


class SchemeSemanticIndex:
    def __init__(self, *, csv_path: Path, embedding_model: str, cache_path: Path):
        self.csv_path = csv_path
        self.embedding_model = embedding_model
        self.cache_path = cache_path
        self.rows: list[dict[str, str]] = []
        self.row_texts: list[str] = []
        self.embeddings: list[list[float]] | None = None
        self.backend: str = "lexical"
        self._model = None
        self._load_rows()
        self._load_or_build()

    def _load_rows(self) -> None:
        if not self.csv_path.exists():
            self.rows = []
            self.row_texts = []
            return
        with self.csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            self.rows = [dict(row) for row in reader]
        self.row_texts = [self._row_to_text(row) for row in self.rows]

    def _row_to_text(self, row: dict[str, str]) -> str:
        # Handle both CSV and JSON schemes_correct_383.json formats
        keys = [
            "Scheme_Name", "scheme_name",      # CSV or JSON
            "Scheme_Category", "sector",        # CSV or JSON
            "Ministry", "state",                # CSV or JSON
            "State_Applicable", "state",        # CSV or JSON  
            "Target_Sector", "sector",          # CSV or JSON
            "Target_Audience", "eligibility",   # CSV or JSON
            "Application_Process", "description" # CSV or JSON
        ]
        return " | ".join(str(row.get(k, "")).strip() for k in keys)

    def _load_or_build(self) -> None:
        if not self.rows:
            return
        if self._try_load_cache():
            return
        if self._try_build_embeddings():
            self._save_cache()

    def _try_build_embeddings(self) -> bool:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except Exception:
            self.backend = "lexical"
            self.embeddings = None
            return False
        try:
            self._model = SentenceTransformer(self.embedding_model)
            vectors = self._model.encode(self.row_texts, show_progress_bar=False)
            self.embeddings = [_normalize([float(v) for v in row]) for row in vectors]
            self.backend = "sentence-transformers"
            return True
        except Exception:
            self.backend = "lexical"
            self.embeddings = None
            self._model = None
            return False

    def _save_cache(self) -> None:
        if not self.embeddings:
            return
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "csv_path": str(self.csv_path),
            "csv_mtime": self.csv_path.stat().st_mtime,
            "embedding_model": self.embedding_model,
            "backend": self.backend,
            "embeddings": self.embeddings,
        }
        self.cache_path.write_text(json.dumps(payload), encoding="utf-8")

    def _try_load_cache(self) -> bool:
        if not self.cache_path.exists() or not self.csv_path.exists():
            return False
        try:
            payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
            if payload.get("csv_path") != str(self.csv_path):
                return False
            if float(payload.get("csv_mtime", -1)) != float(self.csv_path.stat().st_mtime):
                return False
            if payload.get("embedding_model") != self.embedding_model:
                return False
            embeddings = payload.get("embeddings")
            if not isinstance(embeddings, list) or len(embeddings) != len(self.rows):
                return False
            self.embeddings = [[float(v) for v in row] for row in embeddings]
            self.backend = str(payload.get("backend", "sentence-transformers"))
            return True
        except Exception:
            return False

    def search(self, *, query: str, k: int = 8) -> list[RetrievedScheme]:
        if not self.rows:
            return []
        top_k = max(1, min(k, 50))
        if self.embeddings is not None:
            return self._search_embedding(query=query, k=top_k)
        return self._search_lexical(query=query, k=top_k)

    def _search_embedding(self, *, query: str, k: int) -> list[RetrievedScheme]:
        if self._model is None:
            # Cache-loaded vectors but no model object for query encoding: fallback to lexical.
            return self._search_lexical(query=query, k=k)
        try:
            qvec_raw = self._model.encode([query], show_progress_bar=False)[0]
            qvec = _normalize([float(v) for v in qvec_raw])
        except Exception:
            return self._search_lexical(query=query, k=k)

        scored = []
        for idx, vec in enumerate(self.embeddings or []):
            score = _dot(qvec, vec)
            scored.append((score, self.rows[idx]))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [RetrievedScheme(score=float(score), scheme=row) for score, row in scored[:k]]

    def _search_lexical(self, *, query: str, k: int) -> list[RetrievedScheme]:
        qtokens = _tokenize(query)
        scored = []
        for idx, text in enumerate(self.row_texts):
            stokens = _tokenize(text)
            overlap = len(qtokens.intersection(stokens))
            denom = max(1, len(qtokens))
            score = overlap / denom
            scored.append((float(score), self.rows[idx]))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [RetrievedScheme(score=score, scheme=row) for score, row in scored[:k]]

import faiss
import numpy as np

class FaissRecommendation:
    """Faiss-based recommendation using semantic embeddings for profile matching."""
    def __init__(self, semantic_index: 'SchemeSemanticIndex'):
        self.index = semantic_index
        self.faiss_index = None
        self._build_faiss()

    def _build_faiss(self):
        if self.index.embeddings is None or len(self.index.embeddings) == 0:
            self.faiss_index = None
            return
        emb_array = np.array(self.index.embeddings, dtype=np.float32)
        dim = emb_array.shape[1]
        self.faiss_index = faiss.IndexFlatIP(dim)  # Inner Product for cosine similarity (normalized vectors)
        self.faiss_index.add(emb_array)

    def recommend(self, profile_query: str, k: int = 20) -> list[RetrievedScheme]:
        """Recommend schemes for business profile using Faiss ANN search."""
        if self.faiss_index is None or self.index._model is None:
            return self.index.search(query=profile_query, k=k)

        # BART-like semantic encoding (mpnet/paraphrase model handles schematic matching well)
        try:
            qvec_raw = self.index._model.encode([profile_query])[0]
            qvec = _normalize([float(v) for v in qvec_raw])
            q_array = np.array([qvec], dtype=np.float32)
            
            scores, indices = self.faiss_index.search(q_array, k)
            scored = []
            for i in range(indices.shape[1]):
                idx = indices[0][i]
                if idx < len(self.index.rows):
                    scored.append((scores[0][i], self.index.rows[idx]))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [RetrievedScheme(score=float(s), scheme=r) for s, r in scored]
        except Exception:
            # Fallback to lexical if Faiss fails
            return self.index._search_lexical(query=profile_query, k=k)
