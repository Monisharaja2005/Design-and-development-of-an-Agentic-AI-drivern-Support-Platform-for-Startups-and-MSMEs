import os
import httpx
import asyncio
import re

def get_keys_manually():
    keys = {}
    try:
        with open("d:\\Main_project1\\final\\.env", "r") as f:
            content = f.read()
            match = re.search(r"GROQ_API_KEY=(gsk_[a-zA-Z0-9]+)", content)
            if match: keys["GROQ_API_KEY"] = match.group(1)
    except: pass
    return keys

async def list_groq_models():
    keys = get_keys_manually()
    gk = keys.get("GROQ_API_KEY")
    if not gk: return
    
    async with httpx.AsyncClient() as client:
        res = await client.get("https://api.groq.com/openai/v1/models", headers={"Authorization": f"Bearer {gk}"})
        if res.status_code == 200:
            models = [m["id"] for m in res.json()["data"]]
            print("GROQ MODELS:", models)
        else:
            print(f"FAILED: {res.status_code} - {res.text}")

if __name__ == "__main__":
    asyncio.run(list_groq_models())
