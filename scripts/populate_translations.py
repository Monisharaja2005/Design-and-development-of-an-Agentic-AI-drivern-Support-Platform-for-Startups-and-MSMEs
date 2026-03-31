import json
import os
import time
import google.generativeai as genai
import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
GROQ_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY and not GROQ_KEY:
    print("Error: No API keys found in .env")
    exit(1)

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

BASE_PATH = r"d:\Main_project1\final\frontend\src\locales"
LANGS = ["hi", "mr", "kn", "ta", "te", "bn", "gu", "ml", "or", "pa", "ur", "as", "sat", "ks", "ne"]

def translate_batch(texts, target_lang):
    """Translates a batch of strings into the target language with retries and failover."""
    if not texts:
        return {}
    
    prompt = f"""
    Translate the following JSON object values into {target_lang}.
    KEEP the keys exactly as they are.
    Respond ONLY with the translated JSON object.
    Do NOT include markdown formatting or explanations.
    
    JSON: {json.dumps(texts, ensure_ascii=False)}
    """
    
    # Try Gemini first
    if API_KEY:
        for attempt in range(2): # Reduce Gemini attempts to failover faster
            try:
                response = model.generate_content(prompt)
                content = response.text.strip()
                if content.startswith("```json"): content = content[7:]
                if content.startswith("```"): content = content[3:]
                if content.endswith("```"): content = content[:-3]
                return json.loads(content.strip())
            except Exception as e:
                print(f"    Gemini error: {e}")
                time.sleep(2)

    # Fallback to Groq
    if GROQ_KEY:
        print("    Falling back to Groq...")
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [
                            {"role": "system", "content": "You are a specialized JSON translation engine. Return only raw JSON mapping original keys to translated values."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.2
                    }
                )
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]
                if content.startswith("```json"): content = content[7:]
                if content.startswith("```"): content = content[3:]
                if content.endswith("```"): content = content[:-3]
                return json.loads(content.strip())
        except Exception as e:
            print(f"    Groq error: {e}")

    return {}

def flatten_dict(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def unflatten_dict(d, sep='.'):
    result = {}
    for k, v in d.items():
        parts = k.split(sep)
        curr = result
        for part in parts[:-1]:
            if part not in curr:
                curr[part] = {}
            curr = curr[part]
        curr[parts[-1]] = v
    return result

def process_language(lang):
    print(f"Processing {lang}...")
    en_path = os.path.join(BASE_PATH, "en", "translation.json")
    target_path = os.path.join(BASE_PATH, lang, "translation.json")
    
    with open(en_path, "r", encoding="utf-8") as f:
        en_data = json.load(f)
    
    target_data = {}
    if os.path.exists(target_path):
        with open(target_path, "r", encoding="utf-8") as f:
            try:
                target_data = json.load(f)
            except:
                pass

    en_flat = flatten_dict(en_data)
    target_flat = flatten_dict(target_data)
    
    to_translate = {}
    for k, v in en_flat.items():
        # Heuristic: If key missing or value is exactly same as EN (and not a scheme ID)
        if k not in target_flat or target_flat[k] == v:
            if not k.startswith("schemes."): # Handle schemes separately or in limited batches
                to_translate[k] = v
    
    if not to_translate:
        print(f"  No new translations needed for {lang}.")
        return

    # Process in batches of 40 for efficiency (Groq handles this well)
    items = list(to_translate.items())
    batch_size = 40
    translated_flat = dict(target_flat)
    
    for i in range(0, len(items), batch_size):
        batch = dict(items[i:i+batch_size])
        print(f"  Translating batch {i // batch_size + 1} ({len(batch)} items)...")
        translated_batch = translate_batch(batch, lang)
        if isinstance(translated_batch, dict):
            translated_flat.update(translated_batch)
        time.sleep(1) # Rate limit protection
        
    # Special handle for schemes (just a few major ones for now if missing)
    # Ideally we should translate all 383, but that's a lot of API calls.
    # The frontend is designed to fetch these dynamically anyway.
    
    final_data = unflatten_dict(translated_flat)
    
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    print(f"  Updated {target_path}")

if __name__ == "__main__":
    for lang in LANGS:
        process_language(lang)
    print("Done!")
