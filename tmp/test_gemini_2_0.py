import os
import asyncio
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

if os.getenv("GOOGLE_API_KEY"):
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

async def test_gemini_2_0():
    print("Testing gemini-2.0-flash...")
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        # generate_content is synchronous for basic genai 
        response = model.generate_content("Reply with '2.0-OK'")
        print(f"Result: {response.text.strip()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_gemini_2_0())
