#!/usr/bin/env python3

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AI-SCHEME")

app = FastAPI(title="AI Scheme Recommendation Server")

# ⭐ CORS FIX
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SCHEMES_PATH = Path("frontend/data/schemes_correct_383.json")

schemes: List[Dict[str, Any]] = []
model: SentenceTransformer = None


# ⭐ PROFILE MODEL (MATCH FRONTEND)
class Profile(BaseModel):
    state: str = ""
    sector: str = ""
    entityType: str = ""


# ⭐ LOAD ENGINE
def load_engine():
    global schemes, model

    if not SCHEMES_PATH.exists():
        raise Exception("Schemes JSON not found")

    with open(SCHEMES_PATH, "r", encoding="utf-8") as f:
        schemes = json.load(f)

    logger.info(f"✅ Loaded {len(schemes)} schemes")

    logger.info("⚡ Loading Sentence-BERT Model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    logger.info("🔥 AI Recommendation Engine Ready")


@app.on_event("startup")
async def startup():
    load_engine()


# ⭐ AUTH ROUTES
@app.post("/v1/auth/login")
async def login(data: dict):
    return {
        "access_token": "demo-token",
        "user": {
            "email": data.get("email"),
            "name": "Demo User"
        }
    }


@app.post("/v1/auth/signup")
async def signup(data: dict):
    return {
        "access_token": "demo-token",
        "user": {
            "email": data.get("email"),
            "name": data.get("full_name", "User")
        }
    }


# ⭐ HYBRID RANKING FUNCTION
def compute_soft_score(profile: Profile, scheme: dict):

    score = 0

    if profile.state.lower() in str(scheme.get("state", "")).lower():
        score += 1

    if profile.sector.lower() in str(scheme.get("sector", "")).lower():
        score += 1

    if profile.entityType.lower() in str(scheme.get("eligibility", "")).lower():
        score += 1

    return score / 3


# ⭐ MAIN RECOMMEND API
@app.post("/v1/recommend")
async def recommend(profile: Profile, k: int = 5):

    if not schemes:
        raise HTTPException(500, "Schemes not loaded")

    logger.info(
        f"Profile → {profile.state} | {profile.sector} | {profile.entityType}"
    )

    candidates = []

    for s in schemes:
        soft_score = compute_soft_score(profile, s)

        if soft_score > 0:
            candidates.append((soft_score, s))

    logger.info(f"Soft Filter Candidates → {len(candidates)}")

    # ⭐ fallback
    if not candidates:
        logger.warning("No soft match → using full dataset")
        candidates = [(0.1, s) for s in schemes]

    texts = [
        c[1].get("semantic_text")
        or (c[1].get("scheme_name","") + " " + c[1].get("description",""))
        for c in candidates
    ]

    query = f"{profile.state} {profile.sector} {profile.entityType}"

    q_vec = model.encode([query])
    c_vec = model.encode(texts)

    semantic_scores = cosine_similarity(q_vec, c_vec)[0]

    # ⭐ SCORE FUSION
    final_scores = []

    for i, (soft, sch) in enumerate(candidates):
        final = 0.7 * semantic_scores[i] + 0.3 * soft
        final_scores.append((final, sch))

    final_scores.sort(reverse=True, key=lambda x: x[0])

    result = [fs[1] for fs in final_scores[:k]]

    return {
        "schemes": result,
        "total_candidates": len(candidates),
        "ai_engine": "Hybrid Semantic + Eligibility Ranking"
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "schemes_loaded": len(schemes),
        "model_loaded": model is not None
    }


if __name__ == "__main__":
    uvicorn.run(
        "recommendation_server_fixed:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )