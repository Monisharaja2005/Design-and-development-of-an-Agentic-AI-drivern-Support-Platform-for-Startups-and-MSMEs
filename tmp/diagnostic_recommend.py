import requests

url = "http://127.0.0.1:8001/v1/recommend"
payload = {
    "sector": "Food Processing",
    "state": "Tamil Nadu",
    "entityType": "Proprietorship",
    "turnover": "₹50 Lakh",
    "investment": "₹10 Lakh",
    "businessAge": "2 years",
    "isExporting": True,
    "fundingRequirement": "₹20 Lakh",
    "purpose": "Expansion",
    "preferredLanguage": "en"
}

try:
    response = requests.post(url, json=payload, timeout=30)
    print(response.status_code)
    print(response.text)
except Exception as e:
    print(f"Error: {e}")
