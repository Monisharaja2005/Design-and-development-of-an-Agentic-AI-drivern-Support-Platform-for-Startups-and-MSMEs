import requests
from bs4 import BeautifulSoup
from engine.portal_registry import PORTALS
from db.mongo import schemes_col
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}

def crawl_schemes():
    for portal in PORTALS:
        try:
            print(f"🌐 Trying: {portal['name']}")

            r = requests.get(
                portal["url"],
                headers=HEADERS,
                timeout=25,
                verify=False   # <-- bypass bad SSL
            )

            soup = BeautifulSoup(r.text, "html.parser")
            text = soup.get_text(" ", strip=True)

            schemes_col.insert_one({
                "scheme_name": portal["name"],
                "source_url": portal["url"],
                "raw_text": text[:15000]
            })

            print(f"✅ Crawled: {portal['name']}")
            time.sleep(3)  # be polite to servers

        except Exception as e:
            print(f"❌ Failed: {portal['name']} | {e}")
