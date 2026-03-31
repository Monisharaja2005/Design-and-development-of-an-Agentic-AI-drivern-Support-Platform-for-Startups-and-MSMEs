#!/usr/bin/env python3
"""Scheme Recommendation Server — JSON → BERT + FAISS Recommendations"""

import sys
import json
import numpy as np
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from sentence_transformers import SentenceTransformer
import faiss
import uvicorn


ROOT = Path(__file__).parent
JSON_PATH = ROOT / "frontend" / "data" / "schemes_correct_383.json"


class RetrievedScheme(BaseModel):
    score: float
    scheme: dict


app = FastAPI(title="Scheme Recommendation API")


# ⭐ STRONG CORS CONFIG
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ⭐ EXTRA SAFETY (HANDLE PREFLIGHT)
@app.options("/{rest_of_path:path}")
async def preflight_handler():
    return {"status": "ok"}


class SchemeRecommender:

    def __init__(self):
        self.schemes = []
        self.texts = []
        self.model = None
        self.index = None

        self._load()
        self._build()

    def _load(self):
        if not JSON_PATH.exists():
            print("❌ JSON NOT FOUND")
            sys.exit(1)

        with open(JSON_PATH, "r", encoding="utf-8") as f:
            self.schemes = json.load(f)

        print(f"✅ Loaded {len(self.schemes)} schemes")

        self.texts = [
            f"{s.get('scheme_name','')} {s.get('state','')} "
            f"{s.get('sector','')} {s.get('eligibility','')} "
            f"{s.get('description','')}"
            for s in self.schemes
        ]

    def _build(self):
        print("⚡ Loading model...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        emb = self.model.encode(self.texts)
        emb = emb / np.linalg.norm(emb, axis=1, keepdims=True)

        dim = emb.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(emb.astype("float32"))

        print("🔥 FAISS READY")

    def recommend(self, profile: dict, k=10):

        query = f"{profile.get('state','')} {profile.get('sector','')} business"

        q = self.model.encode([query])
        q = q / np.linalg.norm(q, axis=1, keepdims=True)

        scores, ids = self.index.search(q.astype("float32"), k)

        result = []

        for i, idx in enumerate(ids[0]):
            if idx < len(self.schemes):
                result.append({
                    "score": float(scores[0][i]),
                    "scheme": self.schemes[idx]
                })

        return result


recommender = SchemeRecommender()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/v1/auth/login")
def login(data: dict):
    return {"token": "demo"}


@app.post("/v1/recommend")
def recommend(profile: dict):
    return recommender.recommend(profile)


# ⭐ IMPORTANT — RUN WITHOUT RELOAD
if __name__ == "__main__":
    print("🚀 SERVER STARTING...")
    uvicorn.run(app, host="0.0.0.0", port=8000)