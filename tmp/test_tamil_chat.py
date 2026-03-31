import httpx
import json

base_url = "http://127.0.0.1:8001"

def test_chat_localization():
    # 1. Get a scheme ID
    rec_payload = {
        "sector": "Manufacturing",
        "state": "Tamil Nadu",
        "entityType": "Proprietorship",
        "language": "ta"
    }
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(f"{base_url}/v1/recommend", json=rec_payload)
            data = resp.json()
            schemes = data.get("schemes", [])
            if not schemes:
                print("No schemes found for testing.")
                return
            
            scheme = schemes[0]
            sid = scheme.get("scheme_id") or scheme.get("scheme_code")
            print(f"Testing with Scheme ID: {sid}")

            # 2. Test chat/scheme
            chat_payload = {
                "scheme_id": sid,
                "message": "What is this scheme about?",
                "language": "ta"
            }
            chat_resp = client.post(f"{base_url}/v1/chat/scheme", json=chat_payload)
            chat_data = chat_resp.json()
            reply = chat_data.get("reply", "")
            
            print("--- CHAT REPLY ---")
            print(reply[:500])
            print("------------------")
            
            # Check for localized headers
            # Tamil 'Strategic Intelligence' is 'மூலோபாய நுண்ணறிவு'
            if "மூலோபாய நுண்ணறிவு" in reply:
                print("SUCCESS: Localized header FOUND!")
            else:
                print("FAILURE: Header NOT localized.")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_chat_localization()
