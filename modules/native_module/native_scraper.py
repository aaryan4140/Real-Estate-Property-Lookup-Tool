from __future__ import annotations

import re
import urllib.parse
from typing import Any
import requests
from bs4 import BeautifulSoup

from modules.core.page_reader import scrape_top_pages_concurrently


def query_duckduckgo_lite(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """Live web search via DuckDuckGo without any API keys."""
    results: list[dict[str, str]] = []

    # Method 1: Official DDGS wrapper
    try:
        from duckduckgo_search import DDGS
        for item in DDGS().text(query, max_results=max_results):
            href = item.get("href", "").strip()
            title = item.get("title", "").strip()
            snippet = item.get("body", "").strip()
            if href and (title or snippet):
                results.append({"title": title, "url": href, "snippet": snippet})
        if results:
            return results
    except Exception:
        pass

    # Method 2: lite.duckduckgo.com fallback
    url = "https://lite.duckduckgo.com/lite/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    try:
        resp = requests.post(url, data={"q": query}, headers=headers, timeout=6)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            links = soup.find_all("a", class_="result-link")
            snippets = soup.find_all("td", class_="result-snippet")

            for link, snippet_td in zip(links, snippets):
                href = link.get("href", "").strip()
                title = link.get_text().strip()
                snippet = snippet_td.get_text().strip()

                if href and title and snippet:
                    if "uddg=" in href:
                        match = re.search(r"uddg=([^&]+)", href)
                        if match:
                            href = urllib.parse.unquote(match.group(1))

                    results.append({"title": title, "url": href, "snippet": snippet})

                if len(results) >= max_results:
                    break
    except Exception:
        pass

    return results


def search_native_property_data(address: str) -> dict[str, Any]:
    """
    Execute 100% free multi-cluster live search via DuckDuckGo,
    then scrape full HTML tables from top property detail pages.
    """
    clean_addr = address.strip()
    parts = [p.strip() for p in clean_addr.split(",") if p.strip()]
    street_part = parts[0] if parts else clean_addr
    city_state = " ".join(parts[1:3]) if len(parts) >= 2 else ""
    query_prefix = f'"{street_part}" {city_state}'.strip()

    clusters = [
        # Cluster 1: Public Records, CAD, Tax Roll & Parcel APN
        f'{query_prefix} "Account Number" CAD parcel APN assessor tax assessment property appraisal roll',
        # Cluster 2: Building Specs, Size, Year Built & Engineering
        f'{query_prefix} building area sqft year built stories construction elevators',
        # Cluster 3: Commercial Leasing & Official Property Description
        f'{query_prefix} commercial office rentable square feet brochure',
        # Cluster 4: Zoning, Municipality & Flood Map
        f'{query_prefix} zoning code FEMA flood map panel FIRM',
    ]

    all_items: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for q in clusters:
        items = query_duckduckgo_lite(q, max_results=5)
        for it in items:
            u = it["url"]
            if u not in seen_urls:
                seen_urls.add(u)
                all_items.append(it)

    # Scrape HTML tables concurrently from top candidate property pages
    deep_pages = scrape_top_pages_concurrently(list(seen_urls), max_pages=4)

    # Build structured dual-section corpus
    corpus_lines = []
    corpus_lines.append("=== SECTION 1: LIVE SEARCH ENGINE SNIPPETS (DUCKDUCKGO LITE) ===")
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
        "engine": "DuckDuckGo Lite (Free Scraper)",
    }
