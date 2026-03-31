import httpx
import json

url = "http://127.0.0.1:8001/v1/recommend"
payload = {
    "sector": "Manufacturing",
    "state": "Tamil Nadu",
    "entityType": "Proprietorship",
    "turnover": "1-5 Crore",
    "businessDescription": "Manufacturing of components",
    "language": "ta",
    "gender": "Male"
}

try:
    with httpx.Client(timeout=120.0) as client:
        resp = client.post(url, json=payload)
        print(f"Status: {resp.status_code}")
        data = resp.json()
        schemes = data.get("schemes", [])
        if schemes:
            first = schemes[0]
            print(f"DEBUG: lowercase name: {first.get('scheme_name')}")
            print(f"DEBUG: uppercase name: {first.get('Scheme_Name')}")
            print(f"DEBUG: desc: {first.get('description')[:50]}...")
            
            # Verify if they match (they should now!)
            if first.get('scheme_name') == first.get('Scheme_Name'):
                print("SUCCESS: Lowercase and Uppercase keys are SYNCED!")
            else:
                print("FAILURE: Sync missing between scheme_name and Scheme_Name.")
        else:
            print("No schemes returned.")
except Exception as e:
    print(f"Error: {e}")
