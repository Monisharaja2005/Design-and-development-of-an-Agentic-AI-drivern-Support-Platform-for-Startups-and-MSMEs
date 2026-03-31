import httpx
import json
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

async def test_lmstudio():
    url = f"{os.getenv('LMSTUDIO_BASE_URL', 'http://localhost:1234/v1')}/chat/completions"
    model = os.getenv('LMSTUDIO_MODEL', 'google/gemma-3-4b')
    
    print(f"Testing LM Studio at {url} with model {model}...")
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Say hello!"}],
        "temperature": 0.7,
        "stream": False
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                print("Success!")
                print("Response:", resp.json()["choices"][0]["message"]["content"])
            else:
                print(f"Failed with status {resp.status_code}")
                print(resp.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_lmstudio())
