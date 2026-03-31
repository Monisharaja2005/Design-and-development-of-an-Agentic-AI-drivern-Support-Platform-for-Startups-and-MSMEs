import os
import asyncio
from dotenv import load_dotenv
import logging
import openai
import httpx

load_dotenv()

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("TEST-LLM")

client_oa = None
if os.getenv("OPENAI_API_KEY"):
    client_oa = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

genai_active = False
try:
    import google.generativeai as genai
    if os.getenv("GOOGLE_API_KEY"):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        genai_active = True
except ImportError:
    pass

async def _try_groq_text(prompt, system="", temperature=0.2):
    key = os.getenv("GROQ_API_KEY")
    if not key: raise Exception("No GROQ_API_KEY")
    messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={"model": "llama-3.3-70b-versatile", "messages": messages, "temperature": temperature})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

async def _try_gemini_text(prompt, system="", temperature=0.2):
    if not genai_active: raise Exception("Gemini not active")
    # The server uses 2.0-flash
    m = genai.GenerativeModel("gemini-1.5-flash") # 1.5-flash is more stable for testing
    full_prompt = f"{system}\n\n{prompt}".strip() if system else prompt
    # Need to run in executor since generate_content is synchronous in some versions
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, lambda: m.generate_content(full_prompt))
    return response.text

async def _try_openai_text(prompt, system="", temperature=0.2):
    if not client_oa: raise Exception("OpenAI not active")
    messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
    response = await client_oa.chat.completions.create(model="gpt-3.5-turbo", messages=messages)
    return response.choices[0].message.content

async def run_test():
    prompt = "Reply with exactly 'OK-KARIOS' if you receive this."
    
    providers = [
        ("Groq", _try_groq_text),
        ("Gemini", _try_gemini_text),
        ("OpenAI", _try_openai_text)
    ]
    
    for name, fn in providers:
        print(f"--- Testing {name} ---")
        try:
            res = await fn(prompt, "You are a test assistant.")
            print(f"{name} Result: {res.strip()}")
        except Exception as e:
            print(f"{name} Error: {str(e)[:150]}")
        print()

if __name__ == "__main__":
    asyncio.run(run_test())
