#!/usr/bin/env python3
"""
Build Semantic Vector Index for Scheme Recommendation
FREE Version — Sentence Transformers + FAISS
"""

import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path


INPUT_FILE = "frontend/data/schemes_enriched_free.json"
INDEX_FILE = "backend/ai/faiss_scheme.index"
META_FILE = "backend/ai/faiss_scheme_meta.json"


print("🚀 Loading enriched schemes...")

with open(INPUT_FILE, encoding="utf-8") as f:
    schemes = json.load(f)

print(f"✅ Total schemes: {len(schemes)}")

model = SentenceTransformer("all-MiniLM-L6-v2")

vectors = []
metadata = []

for s in schemes:

    text = (
        str(s.get("scheme_name","")) + " " +
        str(s.get("description","")) + " " +
        str(s.get("eligibility","")) + " " +
        str(s.get("sector","")) + " " +
        str(s.get("category",""))
    )

    emb = model.encode(text)

    vectors.append(emb)
    metadata.append(s)


vectors = np.array(vectors).astype("float32")

print("📐 Vector Shape:", vectors.shape)

dim = vectors.shape[1]

index = faiss.IndexFlatL2(dim)

index.add(vectors)

Path("backend/ai").mkdir(parents=True, exist_ok=True)

faiss.write_index(index, INDEX_FILE)

with open(META_FILE, "w", encoding="utf-8") as f:
    json.dump(metadata, f)

print("🔥 FAISS INDEX BUILT SUCCESSFULLY")