import json
import requests

url = "http://127.0.0.1:8001/v1/chat/stream"
payload = {
    "message": "What are the required documents for APEDA?",
    "profile": {
        "sector": "Food Processing",
        "state": "Tamil Nadu"
    },
    "history": [],
    "language": "en"
}

try:
    response = requests.post(url, json=payload, stream=True, timeout=10)
    print("Streaming started...")
    for line in response.iter_lines():
        if line:
            print(line.decode('utf-8'))
except Exception as e:
    print(f"Error: {e}")
