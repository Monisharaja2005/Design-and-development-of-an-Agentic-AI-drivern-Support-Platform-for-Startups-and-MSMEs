import httpx
import asyncio
import re

def get_keys_manually():
    keys = {}
    try:
        with open("d:\\Main_project1\\final\\.env", "r") as f:
            content = f.read()
            # Find GROQ_API_KEY
            match = re.search(r"GROQ_API_KEY=(gsk_[a-zA-Z0-9]+)", content)
            if match: keys["GROQ_API_KEY"] = match.group(1)
            # Find OPENAI_API_KEY
            match = re.search(r"OPENAI_API_KEY=(sk-[a-zA-Z0-9-]+)", content)
            if match: keys["OPENAI_API_KEY"] = match.group(1)
            # Find GEMINI
            match = re.search(r"GEMINI_API_KEY=([a-zA-Z0-9_-]+)", content)
            if match: keys["GEMINI_API_KEY"] = match.group(1)
    except Exception as e:
        print(f"Error reading .env: {e}")
    return keys

async def test_keys():
    keys = get_keys_manually()
    print("--- MANUAL ENV TEST ---")
    
    # 1. Test Groq from .env
    gk = keys.get("GROQ_API_KEY")
    if gk:
        print(f"Testing Groq (.env): {gk[:10]}...")
        async with httpx.AsyncClient() as client:
            res = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {gk}"},
                json={"model": "llama3-8b-8192", "messages": [{"role": "user", "content": "hi"}]},
                timeout=10.0
            )
            print(f"Groq res: {res.status_code}")
    
    # 2. Test OpenAI from .env
    ok = keys.get("OPENAI_API_KEY")
    if ok:
        print(f"Testing OpenAI (.env): {ok[:10]}...")
        async with httpx.AsyncClient() as client:
            res = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {ok}"},
                json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hi"}]},
                timeout=10.0
            )
            print(f"OpenAI res: {res.status_code}")
            if res.status_code != 200:
                print(res.text)

if __name__ == "__main__":
    asyncio.run(test_keys())
