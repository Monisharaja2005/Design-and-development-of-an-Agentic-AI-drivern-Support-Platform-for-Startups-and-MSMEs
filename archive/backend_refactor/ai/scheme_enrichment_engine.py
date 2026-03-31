#!/usr/bin/env python3
"""
ULTRA FINAL SCHEME ENRICHMENT ENGINE
Supports mixed dataset schema
Safe fallback + retry + rate-limit safe + progress + strong normalization
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List

from openai import OpenAI
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ENRICH_ENGINE")


class SchemeEnrichmentEngine:

    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

    # ⭐ FIELD NORMALIZER (VERY IMPORTANT)
    def normalize(self, s: Dict[str, Any]):

        s["scheme_name"] = (
            s.get("scheme_name")
            or s.get("Scheme_Name")
            or ""
        )

        s["description"] = (
            s.get("description")
            or s.get("Scheme_Description")
            or ""
        )

        s["eligibility"] = (
            s.get("eligibility")
            or s.get("Eligibility_Criteria")
            or ""
        )

        s["sector"] = (
            s.get("sector")
            or s.get("Target_Sector")
            or "General"
        )

        s["state"] = (
            s.get("state")
            or s.get("State_Applicable")
            or "India"
        )

        return s

    # ⭐ SAFE JSON PARSER
    def safe_json(self, txt: str):
        try:
            start = txt.find("{")
            end = txt.rfind("}") + 1
            return json.loads(txt[start:end])
        except:
            return {}

    # ⭐ HEURISTIC FALLBACK INTELLIGENCE
    def fallback_logic(self, desc: str):

        d = desc.lower()

        if "cluster" in d or "infrastructure" in d:
            return 120, "High"
        if "capital subsidy" in d:
            return 90, "High"
        if "subsidy" in d:
            return 75, "Medium"
        if "loan" in d or "credit" in d:
            return 60, "Medium"
        if "startup" in d or "innovation" in d:
            return 45, "High"

        return 90, "Low"

    # ⭐ MAIN ENRICH
    def enrich_single_scheme(self, raw_scheme: Dict[str, Any]):

        s = self.normalize(raw_scheme)

        name = s["scheme_name"]
        desc = s["description"]
        eligibility = s["eligibility"]
        sector = s["sector"]
        state = s["state"]

        text = f"{name} {desc} {eligibility} {sector} {state}"

        # ⭐ Embedding
        embedding = self.embedder.encode(text).tolist()

        prompt = f"""
You are Indian MSME scheme intelligence engine.

Return STRICT JSON only.

{{
"timeline_days": number,
"priority_level": "High | Medium | Low",
"benefits_summary": "...",
"eligibility_rules": ["..."],
"required_documents": ["..."],
"application_steps": ["..."],
"youtube_query": "how to apply {name} scheme"
}}

Scheme:
{name}

Description:
{desc[:900]}

Eligibility:
{eligibility[:600]}
"""

        ai = {}

        # ⭐ RATE LIMIT SAFE CALL
        for attempt in range(3):

            try:
                res = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                    timeout=40
                )

                ai = self.safe_json(res.choices[0].message.content)
                break

            except Exception as e:
                logger.warning(f"Retry {attempt+1} → {name} → {e}")
                time.sleep(2)

        fallback_timeline, fallback_priority = self.fallback_logic(desc)

        # ⭐ FINAL WRITEBACK FOR FRONTEND
        s["Timeline_Days"] = ai.get("timeline_days") or fallback_timeline
        s["Priority_Level"] = ai.get("priority_level") or fallback_priority
        s["Benefits_Summary"] = ai.get("benefits_summary") or desc[:220]
        s["Youtube_Query"] = ai.get(
            "youtube_query",
            f"how to apply {name} scheme eligibility documents"
        )

        s["ai_eligibility_rules"] = ai.get("eligibility_rules", [])
        s["ai_required_documents"] = ai.get("required_documents", [])
        s["ai_application_steps"] = ai.get("application_steps", [])
        s["embedding"] = embedding

        logger.info(f"✅ Enriched → {name}")

        return s

    # ⭐ BATCH PIPELINE
    def enrich_batch(self, input_file: str, output_file: str):

        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        with open(input_file, encoding="utf-8") as f:
            schemes = json.load(f)

        enriched = []

        for s in tqdm(schemes):
            try:
                enriched.append(self.enrich_single_scheme(s))
            except Exception as e:
                logger.error(f"❌ Failed → {s.get('scheme_name')} → {e}")

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(enriched, f, indent=2, ensure_ascii=False)

        logger.info(f"🔥 {len(enriched)} schemes enriched → {output_file}")

        return enriched