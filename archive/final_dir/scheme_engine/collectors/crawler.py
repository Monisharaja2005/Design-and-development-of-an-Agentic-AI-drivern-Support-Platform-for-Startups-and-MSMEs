from __future__ import annotations

import logging
from collections import deque
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from scheme_engine.core.text import normalize_text


logger = logging.getLogger(__name__)


class Crawler:
    def __init__(self, http_client, allowed_content_types, max_pages_per_domain, max_depth):
        self.http_client = http_client
        self.allowed_content_types = allowed_content_types
        self.max_pages_per_domain = max_pages_per_domain
        self.max_depth = max_depth

    def crawl(self, seed_url: str, limit: int):
        domain = urlparse(seed_url).netloc
        visited = set()
        queue = deque([(seed_url, 0)])
        pages_seen = 0

        while queue and pages_seen < limit:
            url, depth = queue.popleft()
            if url in visited or depth > self.max_depth:
                continue
            visited.add(url)

            resp = self.http_client.get(url)
            if resp is None:
                continue

            content_type = resp.headers.get("Content-Type", "").split(";")[0].strip().lower()
            if content_type and content_type not in self.allowed_content_types:
                continue

            text = ""
            title = ""
            links = []

            if content_type == "text/html":
                soup = BeautifulSoup(resp.text, "lxml")
                title = normalize_text(soup.title.text) if soup.title else ""
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()
                text = normalize_text(soup.get_text("\n"))
                for a in soup.select("a[href]"):
                    href = a.get("href")
                    if not href:
                        continue
                    abs_url = urljoin(url, href)
                    if urlparse(abs_url).netloc != domain:
                        continue
                    links.append(abs_url)

            yield {
                "url": url,
                "content_type": content_type or "",
                "title": title,
                "text": text,
            }

            pages_seen += 1

            for link in links:
                if link not in visited:
                    queue.append((link, depth + 1))
