from __future__ import annotations

import json
import os
import re
import urllib.parse
from typing import Any
import requests
from bs4 import BeautifulSoup


def _search_serper(query: str, api_key: str, max_results: int = 5) -> list[dict[str, str]]:
    """Clean Google Search API via Serper (2,500 free searches, no credit card required)."""
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


def _search_lite_cluster(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """Live search via DuckDuckGo Lite fallback without API keys."""
    url = "https://lite.duckduckgo.com/lite/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    results: list[dict[str, str]] = []
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


def search_property_multi_cluster(address: str) -> dict[str, Any]:
    """
    Execute multi-cluster targeted live search across CAD, broker brochures, and zoning.
    Automatically uses SERPER_API_KEY if present in .env, otherwise uses DuckDuckGo Lite.
    """
    clean_addr = address.strip()
    serper_api_key = os.getenv("SERPER_API_KEY", "").strip()

    clusters = [
        # Cluster 1: Official CAD, Tax Roll & Parcel APN
        f"{clean_addr} parcel APN assessor tax assessment property appraisal roll",
        # Cluster 2: Building Specs, Size, Year Built & Engineering
        f"{clean_addr} building area sqft year built stories construction elevators roof",
        # Cluster 3: Commercial Leasing, Zoning & Flood Map
        f"{clean_addr} zoning code FEMA flood map panel occupancy rentable brochure",
    ]

    all_items: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for q in clusters:
        if serper_api_key:
            items = _search_serper(q, serper_api_key, max_results=4)
        else:
            items = _search_lite_cluster(q, max_results=4)

        for it in items:
            u = it["url"]
            if u not in seen_urls:
                seen_urls.add(u)
                all_items.append(it)

    # Format structured corpus with numbered citations for LLM agents
    corpus_lines = []
    for idx, item in enumerate(all_items, start=1):
        corpus_lines.append(f"SOURCE [{idx}]: {item['title']}")
        corpus_lines.append(f"URL: {item['url']}")
        corpus_lines.append(f"SNIPPET: {item['snippet']}")
        corpus_lines.append("---")

    return {
        "corpus": "\n".join(corpus_lines),
        "sources": list(seen_urls),
        "total_sources": len(seen_urls),
        "engine": "Google (via Serper)" if serper_api_key else "DuckDuckGo Lite",
    }
