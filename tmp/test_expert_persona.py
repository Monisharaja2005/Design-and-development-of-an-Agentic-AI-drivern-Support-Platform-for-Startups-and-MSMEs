import asyncio
import json
import httpx

async def test_chat():
    url = "http://127.0.0.1:8001/v1/chat"
    payload = {
        "query": "I am a textile manufacturer in Tamil Nadu looking for electricity subsidies. Can you help?",
        "language": "hi", # Test Hindi for multilingual expert response
        "profile": {"sector": "Textile", "state": "Tamil Nadu"}
    }
    
    print("Sending chat request (Expert Persona)...")
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            resp = await client.post(url, json=payload)
            print(f"Status: {resp.status_code}")
            data = resp.json()
            print("\n--- CHAT RESPONSE ---")
            print(data.get("answer"))
            print("\n--- METADATA ---")
            print(f"Docs: {data.get('required_documents')}")
            print(f"Steps: {data.get('application_steps')}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_chat())
