import os
import httpx
from dotenv import load_dotenv

load_dotenv()

GROQ_KEY = os.getenv("GROQ_API_KEY")
print(f"Groq Key exists: {bool(GROQ_KEY)}")
if GROQ_KEY:
    print(f"Key preview: {GROQ_KEY[:10]}...{GROQ_KEY[-5:]}")

try:
    with httpx.Client(timeout=30) as client:
        resp = client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": "Say hello"}],
                "temperature": 0.2
            }
        )
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")
except Exception as e:
    print(f"Error: {e}")
