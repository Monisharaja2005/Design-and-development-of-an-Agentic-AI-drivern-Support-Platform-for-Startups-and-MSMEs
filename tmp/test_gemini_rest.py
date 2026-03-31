import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test_gemini():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Gemini Key: MISSING")
        return

    # Try gemini-pro if flash 404s
    models = ["gemini-1.5-flash", "gemini-pro"]
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": "Say 'Karios ONLINE'"}]}]
        }
        
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(url, json=payload, timeout=10.0)
                if res.status_code == 200:
                    print(f"✅ Gemini REST API ({model}): WORKING")
                    print(res.json()["candidates"][0]["content"]["parts"][0]["text"])
                    return
                else:
                    print(f"❌ Gemini REST API ({model}): FAILED ({res.status_code}) - {res.text}")
        except Exception as e:
            print(f"❌ Gemini Connection ({model}): {e}")

if __name__ == "__main__":
    asyncio.run(test_gemini())
