import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test_llms():
    results = ["--- KARIOS LLM DIAGNOSTIC ---"]
    
    # 1. Test Groq
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        results.append(f"Groq Key found: {groq_key[:10]}...")
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {groq_key}"},
                    json={"model": "llama3-8b-8192", "messages": [{"role": "user", "content": "hi"}]},
                    timeout=10.0
                )
                if res.status_code == 200:
                    results.append("✅ Groq API: WORKING")
                else:
                    results.append(f"❌ Groq API: FAILED ({res.status_code}) - {res.text}")
        except Exception as e:
            results.append(f"❌ Groq Connection: FAILED - {e}")
    else:
        results.append("❌ Groq Key: NOT FOUND in .env")

    # 2. Test OpenAI
    oa_key = os.getenv("OPENAI_API_KEY")
    if oa_key:
        results.append(f"OpenAI Key found: {oa_key[:10]}...")
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {oa_key}"},
                    json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hi"}]},
                    timeout=10.0
                )
                if res.status_code == 200:
                    results.append("✅ OpenAI API: WORKING")
                else:
                    results.append(f"❌ OpenAI API: FAILED ({res.status_code}) - {res.text}")
        except Exception as e:
            results.append(f"❌ OpenAI Connection: FAILED - {e}")
    else:
        results.append("❌ OpenAI Key: NOT FOUND in .env")

    output = "\n".join(results)
    print(output)
    with open("d:\\Main_project1\\final\\tmp\\llm_results.txt", "w", encoding="utf-8") as f:
        f.write(output)

if __name__ == "__main__":
    asyncio.run(test_llms())
