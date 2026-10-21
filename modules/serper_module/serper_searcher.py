from __future__ import annotations

import json
import os
from typing import Any
from dotenv import load_dotenv
import requests

from modules.core.page_reader import scrape_top_pages_concurrently

load_dotenv(override=True)


def query_serper_api(query: str, api_key: str, max_results: int = 8) -> list[dict[str, str]]:
    """Query live Google Search index via Serper API."""
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query, "num": max_results})
    headers = {
        "X-API-KEY": api_key.strip(),
        "Content-Type": "application/json",
    }
    results: list[dict[str, str]] = []
    try:
        resp = requests.post(url, headers=headers, data=payload, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("organic", []):
                title = item.get("title", "").strip()
                link = item.get("link", "").strip()
                snippet = item.get("snippet", "").strip()
                if link and (title or snippet):
                    results.append({"title": title, "url": link, "snippet": snippet})
    except Exception:
        pass
    return results


def search_serper_property_data(address: str) -> dict[str, Any]:
    """
    Execute targeted multi-cluster live Google searches via Serper,
    then scrape full HTML tables from top property detail pages.
    """
    clean_addr = address.strip()
    api_key = os.getenv("SERPER_API_KEY", "").strip()
    if not api_key:
        raise ValueError("SERPER_API_KEY is not set in your .env file. Please add your key.")

    parts = [p.strip() for p in clean_addr.split(",") if p.strip()]
    street_part = parts[0] if parts else clean_addr
    city_state = " ".join(parts[1:3]) if len(parts) >= 2 else ""
    query_prefix = f'"{street_part}" {city_state}'.strip()

    clusters = [
        # Cluster 1: Public Records, CAD, Tax Roll, APN & Aggregators
        (
            f'{query_prefix} ("Account Number" OR "CAD" OR "Assessor" OR "Tax Roll" OR '
            f'"Property Record Card" OR "APN" OR "parcelId" OR site:propertyshark.com OR '
            f'site:enrichedrealestate.com OR site:corriden.com OR site:compass.com)'
        ),
        # Cluster 2: Building Specs, Size, Year Built & Engineering
        f'{query_prefix} building area sqft year built stories construction elevators parking ratio',
        # Cluster 3: Commercial Leasing & Official Property Description
        f'{query_prefix} commercial office rentable square feet brochure lease',
        # Cluster 4: Zoning, Municipality & Flood Map
        f'{query_prefix} zoning municipality code FEMA flood map panel FIRM',
    ]

    all_items: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for q in clusters:
        items = query_serper_api(q, api_key, max_results=8)
        for it in items:
            u = it["url"]
            if u not in seen_urls:
                seen_urls.add(u)
                all_items.append(it)

    # Scrape HTML tables concurrently from top candidate property pages
    deep_pages = scrape_top_pages_concurrently(list(seen_urls), max_pages=4)

    # Build structured dual-section corpus
    corpus_lines = []
    corpus_lines.append("=== SECTION 1: LIVE SEARCH ENGINE SNIPPETS ===")
    for idx, item in enumerate(all_items, start=1):
        corpus_lines.append(f"SOURCE [{idx}]: {item['title']}")
        corpus_lines.append(f"URL: {item['url']}")
        corpus_lines.append(f"SNIPPET: {item['snippet']}")
        corpus_lines.append("---")

    if deep_pages:
        corpus_lines.append("\n=== SECTION 2: FULL SCRAPED WEBPAGE TABLES & DETAIL PAGES ===")
        for idx, (url, full_text) in enumerate(deep_pages, start=1):
            corpus_lines.append(f"PAGE [{idx}] URL: {url}")
            corpus_lines.append(f"PAGE CONTENT & TABLES:\n{full_text}")
            corpus_lines.append("---")

    return {
        "corpus": "\n".join(corpus_lines),
        "sources": list(seen_urls),
        "total_sources": len(seen_urls),
        "deep_pages_scraped": len(deep_pages),
        "engine": "Google (via Serper)",
    }
