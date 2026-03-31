import json
import os
import lancedb
from sentence_transformers import SentenceTransformer
import pandas as pd
from tqdm import tqdm

# Path Configuration
BASE_DIR = r"d:\Main_project1\final"
JSON_PATH = os.path.join(BASE_DIR, "frontend", "data", "schemes_merged_final.json")
DB_PATH = os.path.join(BASE_DIR, "lancedb_backup")
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

def reindex():
    print(f"Loading data from {JSON_PATH}...")
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Loaded {len(data)} schemes.")

    print(f"Loading model {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)

    # Connect to LanceDB
    db = lancedb.connect(DB_PATH)
    
    # Modern LanceDB checks
    existing_tables = db.list_tables()
    if "schemes" in existing_tables:
        db.drop_table("schemes")
    if "fields" in existing_tables:
        db.drop_table("fields")

    # Prepare data for indexing
    records = []
    print("Generating embeddings...")
    for s in tqdm(data):
        # Combine fields for better semantic context
        context = (
            f"Scheme: {s.get('scheme_name', '')}. "
            f"Sector: {s.get('sector', '')}. "
            f"State: {s.get('state', '')}. "
            f"Description: {s.get('description', '')}. "
            f"Eligibility: {' '.join(s.get('eligibility_criteria', []))}. "
            f"Procedures: {' '.join(s.get('procedure', []))}. "
        )
        
        vector = model.encode(context).tolist()
        records.append({
            "scheme_code": s.get("scheme_code") or s.get("scheme_id"),
            "scheme_name": s.get("scheme_name"),
            "vector": vector
        })

    # Create table and insert
    print(f"Creating table 'schemes' with {len(records)} records...")
    df = pd.DataFrame(records)
    db.create_table("schemes", data=df, mode="overwrite")
    
    # Optional: Fill field-specific table for deeper RAG
    print(f"Creating table 'fields'...")
    field_records = []
    for s in data:
        for key in ["eligibility_criteria", "procedure", "description", "documents_required"]:
            val = s.get(key)
            if val:
                # Handle list or string
                text_val = "; ".join(val) if isinstance(val, list) else str(val)
                field_records.append({
                    "scheme_code": s.get("scheme_code") or s.get("scheme_id"),
                    "text": f"{key}: {text_val}",
                    "vector": model.encode(f"{key}: {text_val}").tolist()
                })
    if field_records:
        df_f = pd.DataFrame(field_records)
        db.create_table("fields", data=df_f, mode="overwrite")
        
    print("Indexing complete.")

if __name__ == "__main__":
    reindex()
