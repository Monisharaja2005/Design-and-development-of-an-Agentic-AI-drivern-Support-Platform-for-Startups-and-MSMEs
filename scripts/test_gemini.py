import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
print(f"Key exists: {bool(API_KEY)}")

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

try:
    response = model.generate_content("Say hello in Tamil")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
