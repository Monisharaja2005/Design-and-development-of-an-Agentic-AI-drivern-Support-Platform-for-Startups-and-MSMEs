"""
Backend configuration
"""

import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv   # ⭐ ADD THIS

# ⭐ LOAD ENV FILE
load_dotenv()

@dataclass
class Settings:
    """App settings"""
    openai_api_key: str
    enriched_schemes_path: str = "frontend/data/schemes_enriched.json"
    schemes_base_path: str = "frontend/data/schemes_correct_383.json"
    
    @classmethod
    def from_env(cls):
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            enriched_schemes_path=os.getenv(
                "ENRICHED_SCHEMES_PATH",
                "frontend/data/schemes_enriched.json"
            ),
        )

settings = Settings.from_env()