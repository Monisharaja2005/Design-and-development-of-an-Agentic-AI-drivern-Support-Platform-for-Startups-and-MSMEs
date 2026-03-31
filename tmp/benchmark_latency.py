import time
import hashlib
import json
import sqlite3
from sentence_transformers import SentenceTransformer

def benchmark():
    print("--- LATENCY BENCHMARK ---")
    
    start_load = time.time()
    model = SentenceTransformer("BAAI/bge-m3", device="cpu")
    print(f"Model Load Time: {time.time() - start_load:.2f}s")

    query = "I am a textile manufacturer looking for electricity subsidies."
    
    # Test 1: Cold Encoding
    start_enc1 = time.time()
    vec1 = model.encode(query).tolist()
    print(f"Cold Encoding Time: {time.time() - start_enc1:.2f}s")

    # Test 2: Warm Encoding (repeated)
    start_enc2 = time.time()
    vec2 = model.encode(query).tolist()
    print(f"Warm Encoding Time: {time.time() - start_enc2:.2f}s")

    # Test 3: VectorCache (Simulated)
    db_path = "vector_cache_bench.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS cache (hash TEXT PRIMARY KEY, embedding TEXT)")
        h = hashlib.md5(query.encode()).hexdigest()
        conn.execute("INSERT OR REPLACE INTO cache (hash, embedding) VALUES (?, ?)", (h, json.dumps(vec1)))
    
    start_cache = time.time()
    with sqlite3.connect(db_path) as conn:
        res = conn.execute("SELECT embedding FROM cache WHERE hash=?", (h,)).fetchone()
        cached_vec = json.loads(res[0])
    print(f"VectorCache Retrieval Time: {time.time() - start_cache:.4f}s")

if __name__ == "__main__":
    benchmark()
