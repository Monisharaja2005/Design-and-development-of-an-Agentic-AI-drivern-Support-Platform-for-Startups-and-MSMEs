"""
KARIOS Scheme Routes — FINAL PRODUCTION VERSION
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
import json
from pathlib import Path
from functools import lru_cache

from config.settings import settings
from ai.recommendation_engine import SchemeRecommender


router = APIRouter(prefix="/schemes", tags=["schemes"])

recommender = SchemeRecommender()


# ⭐ Request Model
class SchemeMatchRequest(BaseModel):
    profile: Dict[str, Any]
    limit: int = 12


# ⭐ Cached Loader
@lru_cache(maxsize=1)
def load_enriched_schemes():

    path = Path(settings.enriched_schemes_path)

    if not path.exists():
        print("❌ Enriched schemes file NOT FOUND:", path)
        return []

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    # ⭐ Auto YouTube Query
    for s in data:
        if not s.get("youtube_query"):
            s["youtube_query"] = (
                f"how to apply {s.get('scheme_name','')} scheme India"
            )

    print("✅ Loaded enriched schemes:", len(data))
    return data


# ⭐ Get ALL Schemes (Listing Page)
@router.get("/all")
async def get_all_schemes():

    schemes = load_enriched_schemes()

    if not schemes:
        return {"error": "Run enrichment pipeline first"}

    return schemes


# ⭐ Get Single Scheme (Modal Details)
@router.get("/{scheme_id}")
async def get_scheme_details(scheme_id: str):

    schemes = load_enriched_schemes()

    scheme = next(
        (s for s in schemes if str(s.get("scheme_id")) == str(scheme_id)),
        None
    )

    if not scheme:
        return {"error": "Scheme not found"}

    return scheme


# ⭐⭐ BASIC RULE MATCHING (fallback engine)
@router.post("/match")
async def match_schemes(request: SchemeMatchRequest):

    schemes = load_enriched_schemes()
    profile = request.profile

    state = str(profile.get("state","")).lower()
    sector = str(profile.get("sector","")).lower()

    results = []

    for s in schemes:

        score = 0

        if state in str(s.get("state","")).lower():
            score += 40

        if sector in str(s.get("sector","")).lower():
            score += 40

        if "subsidy" in str(profile.get("goal","")).lower():
            if "subsidy" in str(s.get("category","")).lower():
                score += 20

        results.append({
            "scheme": s,
            "match_score": score
        })

    results = sorted(results, key=lambda x: x["match_score"], reverse=True)

    return results[:request.limit]


# ⭐⭐⭐⭐ REAL AI RECOMMENDATION (FAISS + Semantic)
@router.post("/recommend")
async def recommend_schemes(profile: Dict[str, Any]):

    results = recommender.recommend(profile)

    return {
        "total": len(results),
        "recommendations": results
    }