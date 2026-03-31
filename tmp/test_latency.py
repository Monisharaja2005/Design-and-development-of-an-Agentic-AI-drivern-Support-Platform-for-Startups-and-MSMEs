import httpx
import time
import asyncio

async def test_chat_latency(lang="en"):
    url = "http://127.0.0.1:8001/v1/chat/stream"
    payload = {
        "query": "Tell me about MSME schemes in Tamil Nadu",
        "schemes": [],
        "profile": {},
        "language": lang
    }
    
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            print(f"Status Code: {response.status_code}")
            print(f"Time to first chunk: {time.time() - start:.2f}s")
            full_text = ""
            async for chunk in response.aiter_text():
                full_text += chunk
                if len(full_text) > 500:
                    break
            print(f"Content Preview:\n{full_text[:500]}...")
            print(f"Total time: {time.time() - start:.2f}s")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import sys
    lang = sys.argv[2] if len(sys.argv) > 2 else "en"
    asyncio.run(test_chat_latency(lang))
