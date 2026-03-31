from __future__ import annotations

import time
import logging
from typing import Optional

import requests


logger = logging.getLogger(__name__)


class HttpClient:
    def __init__(self, user_agent: str, timeout: int, delay_seconds: float, max_retries: int = 3):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        self.timeout = timeout
        self.delay_seconds = delay_seconds
        self.max_retries = max_retries
        self._last_request_at = 0.0

    def get(self, url: str) -> Optional[requests.Response]:
        now = time.time()
        delta = now - self._last_request_at
        if delta < self.delay_seconds:
            time.sleep(self.delay_seconds - delta)

        for attempt in range(self.max_retries):
            try:
                resp = self.session.get(url, timeout=self.timeout, allow_redirects=True)
                self._last_request_at = time.time()
                return resp
            except requests.RequestException as e:
                if attempt < self.max_retries - 1:
                    wait_time = (2 ** attempt) + 1  # exponential backoff
                    logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries}) for {url}: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Request failed after {self.max_retries} attempts for {url}: {e}")
                    return None
