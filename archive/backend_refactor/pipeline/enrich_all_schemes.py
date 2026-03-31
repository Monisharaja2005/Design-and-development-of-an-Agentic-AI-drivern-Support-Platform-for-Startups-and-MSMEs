#!/usr/bin/env python3
"""
MASTER ENRICHMENT PIPELINE — FINAL DATASET SAFE VERSION
"""

import json
import logging
from pathlib import Path
from tqdm import tqdm
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "backend"))

from ai.scheme_enrichment_engine import SchemeEnrichmentEngine
from config.settings import settings


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PIPELINE")


def main():

    input_file = ROOT / "frontend/data/schemes_correct_383.json"
    output_file = ROOT / "frontend/data/schemes_enriched.json"

    if not input_file.exists():
        logger.error(f"❌ File not found → {input_file}")
        return

    with open(input_file, encoding="utf-8") as f:
        schemes = json.load(f)

    logger.info(f"📊 Total schemes → {len(schemes)}")

    engine = SchemeEnrichmentEngine(settings.openai_api_key)

    enriched_output = []

    for scheme in tqdm(schemes):

        try:

            # ⭐ SAFE NAME FETCH (NEW STRUCTURE)
            name = scheme.get("scheme_name") or scheme.get("Scheme_Name")

            if not name:
                logger.warning("⚠️ Skipping scheme without name")
                continue

            enriched = engine.enrich_single_scheme(scheme)

            enriched_output.append({
                **enriched.base_scheme,
                "embedding": enriched.embedding,
                "ai_eligibility_rules": enriched.eligibility_rules,
                "ai_required_documents": enriched.required_documents,
                "ai_application_steps": enriched.application_steps
            })

        except Exception as e:
            logger.error(f"❌ Failed scheme → {e}")

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(enriched_output, f, indent=2, ensure_ascii=False)

    logger.info(f"🎉 Saved {len(enriched_output)} enriched schemes")


if __name__ == "__main__":
    main()