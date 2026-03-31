#!/usr/bin/env python3
"""
KARIOS AI Recommendation Engine (FINAL ADVANCED VERSION)
FREE AI ENGINE — Semantic + Hybrid Ranking + Explainable AI
"""

import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path


INDEX_FILE = "backend/ai/faiss_scheme.index"
META_FILE = "backend/ai/faiss_scheme_meta.json"


class SchemeRecommender:

    def __init__(self):

        print("🚀 Loading Recommendation Engine...")

        self.index = faiss.read_index(INDEX_FILE)

        with open(META_FILE, encoding="utf-8") as f:
            self.schemes = json.load(f)

        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        print("✅ Recommendation Engine Ready")

    # ⭐ PROFILE → SEMANTIC TEXT
    def build_profile_text(self, profile):

        return (
            f"{profile.get('state','')} "
            f"{profile.get('sector','')} "
            f"{profile.get('entityType','')} "
            f"{profile.get('goal','')} "
            f"{profile.get('problem','')}"
        )

    # ⭐ HYBRID SCORING ENGINE
    def hybrid_score(self, scheme, profile, semantic_score):

        score = semantic_score * 60

        state = str(profile.get("state","")).lower()
        sector = str(profile.get("sector","")).lower()
        entity = str(profile.get("entityType","")).lower()
        goal = str(profile.get("goal","")).lower()

        if state and state in str(scheme.get("state","")).lower():
            score += 15

        if sector and sector in str(scheme.get("sector","")).lower():
            score += 10

        if entity and entity in str(scheme.get("beneficiary_tags","")).lower():
            score += 5

        if goal and goal in str(scheme.get("category","")).lower():
            score += 10

        return round(score,2)

    # ⭐ EXPLAINABLE AI
    def build_reason(self, scheme, profile):

        reasons = []

        if profile.get("state","").lower() in str(scheme.get("state","")).lower():
            reasons.append("Applicable in your state")

        if profile.get("sector","").lower() in str(scheme.get("sector","")).lower():
            reasons.append("Supports your sector")

        if "subsidy" in str(profile.get("goal","")).lower():
            if "subsidy" in str(scheme.get("category","")).lower():
                reasons.append("Provides subsidy support")

        if not reasons:
            reasons.append("Semantically similar to your business profile")

        return reasons

    # ⭐ MAIN RECOMMEND
    def recommend(self, profile, top_k=12):

        query_text = self.build_profile_text(profile)

        query_vec = self.model.encode(query_text).astype("float32")

        D, I = self.index.search(
            np.array([query_vec]),
            40
        )

        results = []

        for rank, idx in enumerate(I[0]):

            scheme = self.schemes[idx]

            semantic_score = float(1 / (1 + D[0][rank]))

            final_score = self.hybrid_score(
                scheme,
                profile,
                semantic_score
            )

            scheme["match_score"] = final_score
            scheme["ai_reason"] = self.build_reason(scheme, profile)

            results.append(scheme)

        results = sorted(
            results,
            key=lambda x: x["match_score"],
            reverse=True
        )

        return results[:top_k]