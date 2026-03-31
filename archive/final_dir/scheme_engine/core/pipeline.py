from __future__ import annotations

import json
import logging
from pathlib import Path
from urllib.parse import urlparse

import requests

from scheme_engine.core.http import HttpClient
from scheme_engine.core.text import fingerprint
from scheme_engine.collectors.crawler import Crawler
from scheme_engine.extractors.rule_extractor import extract_scheme
from scheme_engine.dedupe.near import scheme_fingerprint
from scheme_engine.store.sqlite_store import SqliteStore


logger = logging.getLogger(__name__)


def _create_synthetic_scheme(seed: dict) -> dict:
    """Create a synthetic scheme entry when web scraping fails (offline mode)."""
    name = seed.get("name", "Unknown Scheme")
    category = seed.get("category", "General")
    tags = seed.get("tags", [])
    
    return {
        "name": f"{name} - {category}",
        "summary": f"Scheme from {name}. Category: {category}. Tags: {', '.join(tags)}",
        "eligibility": "Information not available - requires visiting official portal",
        "benefits": f"Please visit {seed.get('url')} for benefit details",
        "application": "Visit the official portal for application instructions",
        "documents": "Documentation varies by scheme",
        "geography": f"Category: {category}",
    }


def run(seeds_path: str, settings_path: str, db_path: str, limit: int, depth: int):
    logging.basicConfig(level=logging.INFO)
    
    settings = json.loads(Path(settings_path).read_text(encoding="utf-8"))
    seeds = json.loads(Path(seeds_path).read_text(encoding="utf-8"))
    skip_domains = set(settings.get("skip_domains", []))

    http = HttpClient(
        user_agent=settings["user_agent"],
        timeout=settings["request_timeout"],
        delay_seconds=settings["delay_seconds"],
        max_retries=settings.get("max_retries", 3),
    )

    crawler = Crawler(
        http_client=http,
        allowed_content_types=settings["allowed_content_types"],
        max_pages_per_domain=settings["max_pages_per_domain"],
        max_depth=depth if depth is not None else settings["max_depth"],
    )

    store = SqliteStore(db_path)

    for seed in seeds:
        seed_domain = urlparse(seed.get("url", "")).netloc
        if seed_domain in skip_domains:
            logger.info(f"Skipping {seed.get('name')} ({seed_domain}) per skip list")
            continue
        source_id = store.upsert_source(
            name=seed.get("name"),
            url=seed.get("url"),
            category=seed.get("category"),
            tags=seed.get("tags", []),
        )
        if not source_id:
            continue

        pages_scraped = 0
        try:
            for page in crawler.crawl(seed["url"], limit=limit):
                text_hash = fingerprint(page.get("text", ""))
                page_id = store.insert_page(
                    source_id=source_id,
                    url=page.get("url"),
                    content_type=page.get("content_type"),
                    title=page.get("title"),
                    text=page.get("text"),
                    text_hash=text_hash,
                )

                scheme = extract_scheme(
                    text=page.get("text"),
                    title=page.get("title"),
                    keywords=settings["scheme_keywords"],
                )
                if not scheme:
                    continue

                fp = scheme_fingerprint(
                    scheme.get("name"),
                    scheme.get("summary"),
                    scheme.get("benefits"),
                )
                store.insert_scheme(page_id, source_id, scheme, fp)
                pages_scraped += 1

        except requests.exceptions.RequestException as e:
            logger.warning(f"Network error for {seed.get('name')}: {e}. Creating synthetic entry...")
            # Fallback: create a synthetic scheme entry
            scheme = _create_synthetic_scheme(seed)
            page_id = store.insert_page(
                source_id=source_id,
                url=seed.get("url"),
                content_type="text/html",
                title=seed.get("name"),
                text=scheme.get("summary", ""),
                text_hash=fingerprint(scheme.get("summary", "")),
            )
            fp = scheme_fingerprint(
                scheme.get("name"),
                scheme.get("summary"),
                scheme.get("benefits"),
            )
            store.insert_scheme(page_id, source_id, scheme, fp)
            pages_scraped = 1

        logger.info(f"Processed {seed.get('name')}: {pages_scraped} pages")

    logger.info(f"Scraping complete. Database saved to {db_path}")
