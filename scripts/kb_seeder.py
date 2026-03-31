import json
import os
import lancedb
import pandas as pd
from sentence_transformers import SentenceTransformer
from pathlib import Path

# Config
DATA_PATH = Path("frontend/data/schemes_correct_383.json")
DB_PATH = "./lancedb_db"
TABLE_NAME = "scheme_vectors"
MODEL_NAME = "BAAI/bge-m3"

def seed_knowledge_base():
    print(f"🚀 Starting Phase 0: Knowledge Base Creation")
    
    if not DATA_PATH.exists():
        print(f"❌ Data file not found at {DATA_PATH}")
        return

    # 1. Load and Cleaning (Normalize)
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        schemes = json.load(f)
    
    print(f"📦 Loaded {len(schemes)} schemes for processing.")

    # 2. Intelligence Enrichment: Structured JSON + Context Generation
    # (The source JSON already has semantic_text, but we can verify/enrich here if needed)
    
    data_for_df = []
    for s in schemes:
        # Phase 0 Goal: Structured JSON + Context
        # We ensure every scheme has a rich semantic representation
        context = s.get("semantic_text")
        if not context:
            context = f"{s['scheme_name']} ({s['scheme_code']}) for {s['sector']} in {s['state']}. {s['description']} Eligibility: {s['eligibility']}"
        
        data_for_df.append({
            "id": s["scheme_id"],
            "name": s["scheme_name"],
            "code": s["scheme_code"],
            "state": s["state"],
            "sector": s["sector"],
            "description": s["description"],
            "eligibility": s["eligibility"],
            "text": context
        })

    df = pd.DataFrame(data_for_df)

    # 3. Semantic Embedding Generation
    print(f"🧠 Generating embeddings using {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    
    # Generate vectors for the 'text' column
    embeddings = model.encode(df['text'].tolist(), show_progress_bar=True)
    df['vector'] = embeddings.tolist()

    # 4. Storage (LanceDB)
    print(f"💾 Storing in LanceDB at {DB_PATH}...")
    db = lancedb.connect(DB_PATH)
    
    # Create or overwrite table
    if TABLE_NAME in db.table_names():
        db.drop_table(TABLE_NAME)
    
    tbl = db.create_table(TABLE_NAME, data=df)
    
    print(f"✅ Phase 0 Complete. Knowledge Base created with {len(tbl)} enriched records.")

if __name__ == "__main__":
    seed_knowledge_base()
