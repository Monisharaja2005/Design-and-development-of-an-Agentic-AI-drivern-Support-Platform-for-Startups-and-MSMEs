import json
import os
import sqlite3
import hashlib
import time
import google.generativeai as genai
import httpx
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Optional

load_dotenv()

# Configuration
API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
GROQ_KEY = os.getenv("GROQ_API_KEY")
TRANSLATION_DB = "translations_cache.db"
SCHEMES_PATH = r"d:\Main_project1\final\frontend\data\schemes_merged_final.json"
LANGS = ["hi", "mr", "kn", "ta", "te", "bn", "gu", "ml", "or", "pa", "ur", "as", "sat", "ks", "ne"]

if not API_KEY and not GROQ_KEY:
    print("Error: No API keys found.")
    exit(1)

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

def init_db():
    with sqlite3.connect(TRANSLATION_DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                text_hash TEXT,
                lang_code TEXT,
                original_text TEXT,
                translated_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (text_hash, lang_code)
            )
        """)
        conn.commit()

def set_cache(text, lang_code, translated):
    if not text or not translated: return
    text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    try:
        with sqlite3.connect(TRANSLATION_DB) as conn:
            conn.execute("""
                INSERT INTO cache (text_hash, lang_code, original_text, translated_text)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(text_hash, lang_code) DO UPDATE SET translated_text = excluded.translated_text
            """, (text_hash, lang_code, text, translated))
            conn.commit()
    except Exception as e:
        print(f"  Cache set error: {e}")

def is_cached(text, lang_code):
    text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    try:
        with sqlite3.connect(TRANSLATION_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM cache WHERE text_hash = ? AND lang_code = ?", (text_hash, lang_code))
            return cursor.fetchone() is not None
    except:
        return False

def translate_batch(texts, target_lang):
    """Translates a batch of strings into the target language."""
    if not texts: return []
    
    prompt = f"Translate the following JSON list of strings into {target_lang}. Return ONLY raw JSON array. JSON: {json.dumps(texts, ensure_ascii=False)}"
    
    try:
        response = model.generate_content(prompt)
        content = response.text.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        return json.loads(content)
    except Exception as e:
        print(f"  Translation error: {e}")
        return []

def main():
    init_db()
    if not os.path.exists(SCHEMES_PATH):
        print(f"Error: Schemes file not found at {SCHEMES_PATH}")
        return
        
    with open(SCHEMES_PATH, "r", encoding="utf-8") as f:
        schemes = json.load(f)
    
    print(f"Found {len(schemes)} schemes. Processing {len(LANGS)} languages...")
    
    for lang in LANGS:
        print(f"Processing {lang}...")
        all_texts = []
        
        # Collect unique scheme names and descriptions
        for s in schemes:
            name = s.get("scheme_name")
            desc = s.get("description")
            if name: all_texts.append(name)
            if desc: all_texts.append(desc)
        
        unique_texts = list(set(all_texts))
        to_translate = [t for t in unique_texts if not is_cached(t, lang)][:50]
        
        print(f"  {len(to_translate)} items to translate for {lang}")
        
        batch_size = 30
        for i in range(0, len(to_translate), batch_size):
            batch = to_translate[i:i+batch_size]
            print(f"  Translating batch {i//batch_size + 1}/{len(to_translate)//batch_size + 1}...")
            translated = translate_batch(batch, lang)
            if isinstance(translated, list) and len(translated) == len(batch):
                for original, trans in zip(batch, translated):
                    set_cache(original, lang, trans)
            else:
                print(f"  Failed batch at {i}")
            time.sleep(1)

if __name__ == "__main__":
    main()
