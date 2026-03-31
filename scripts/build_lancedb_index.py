import json
import lancedb
import pandas as pd
from sentence_transformers import SentenceTransformer

DB_PATH = "./lancedb_db"
JSON_PATH = "frontend/data/schemes_correct_383.json"

print("🔥 Building LanceDB Index...")

# Load Schemes
with open(JSON_PATH, "r", encoding="utf-8") as f:
    schemes = json.load(f)

model = SentenceTransformer("BAAI/bge-m3")

rows = []

for s in schemes:

    text = (
        s.get("semantic_text")
        or (s.get("scheme_name","") + " " + s.get("description",""))
    )

    vec = model.encode(text).tolist()

    rows.append({
        "scheme_id": s["scheme_id"],
        "state": s.get("state",""),
        "sector": s.get("sector",""),
        "vector": vec
    })

df = pd.DataFrame(rows)

db = lancedb.connect(DB_PATH)

tbl = db.create_table("scheme_vectors", data=df, mode="overwrite")

print("✅ LanceDB Index Created")
print(f"Table info: {tbl.to_pandas()}")
