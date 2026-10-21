from __future__ import annotations

import json
import os
import re
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from typing import Any
import requests
from bs4 import BeautifulSoup

from modules.core.page_reader import scrape_top_pages_concurrently


def _query_serper(query: str, api_key: str, max_results: int = 8) -> list[dict[str, str]]:
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
                    results.append({"title": title, "url": link, "snippet": snippet, "origin": "serper"})
    except Exception:
        pass
    return results


def _query_duckduckgo_lite(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """Live web search via DuckDuckGo Lite without any API keys."""
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

                    results.append({"title": title, "url": href, "snippet": snippet, "origin": "native"})

                if len(results) >= max_results:
                    break
    except Exception:
        pass

    return results


def search_unified_multi_engine(address: str) -> dict[str, Any]:
    """
    Execute Serper Google search AND Free Native search in parallel,
    then scrape full HTML tables from top property detail pages.
    """
    clean_addr = address.strip()
    api_key = os.getenv("SERPER_API_KEY", "").strip()

    serper_clusters = [
        f'"{clean_addr}" (site:enrichedrealestate.com OR site:propertyshark.com OR site:compass.com OR site:corriden.com OR site:har.com OR site:loopnet.com OR parcel OR APN OR "account number" OR "assessed value")',
        f'"{clean_addr}" building area sqft year built stories construction elevators parking ratio',
        f'"{clean_addr}" commercial office rentable square feet brochure lease',
        f'"{clean_addr}" zoning municipality code FEMA flood map panel FIRM',
    ]

    native_clusters = [
        f'"{clean_addr}" parcel APN assessor tax assessment property appraisal roll',
        f'"{clean_addr}" building area sqft year built stories construction elevators',
        f'"{clean_addr}" commercial office rentable square feet brochure',
        f'"{clean_addr}" zoning code FEMA flood map panel FIRM',
    ]

    serper_items: list[dict[str, str]] = []
    native_items: list[dict[str, str]] = []
    all_seen_urls: set[str] = set()

    def run_serper():
        nonlocal serper_items
        if not api_key:
            return
        for q in serper_clusters:
            items = _query_serper(q, api_key, max_results=8)
            for it in items:
                serper_items.append(it)
                all_seen_urls.add(it["url"])

    def run_native():
        nonlocal native_items
        for q in native_clusters:
            items = _query_duckduckgo_lite(q, max_results=5)
            for it in items:
                native_items.append(it)
                all_seen_urls.add(it["url"])

    # Run both search engines concurrently
    with ThreadPoolExecutor(max_workers=2) as executor:
        f_serper = executor.submit(run_serper)
        f_native = executor.submit(run_native)
        f_serper.result()
        f_native.result()

    # Scrape HTML tables concurrently from top candidate property pages
    deep_pages = scrape_top_pages_concurrently(list(all_seen_urls), max_pages=4)

    # Format structured unified corpus with clear source labeling
    corpus_lines = []
    corpus_lines.append("=== ENGINE A: GOOGLE SEARCH SNIPPETS (VIA SERPER) ===")
    seen_serp_u: set[str] = set()
    for idx, item in enumerate(serper_items, start=1):
        if item["url"] not in seen_serp_u:
            seen_serp_u.add(item["url"])
            corpus_lines.append(f"[SERPER SOURCE {idx}]: {item['title']}")
            corpus_lines.append(f"URL: {item['url']}")
            corpus_lines.append(f"SNIPPET: {item['snippet']}")
            corpus_lines.append("---")

    corpus_lines.append("\n=== ENGINE B: DUCKDUCKGO LITE SNIPPETS (FREE NATIVE SCRAPER) ===")
    seen_nat_u: set[str] = set()
    for idx, item in enumerate(native_items, start=1):
        if item["url"] not in seen_nat_u:
            seen_nat_u.add(item["url"])
            corpus_lines.append(f"[NATIVE SOURCE {idx}]: {item['title']}")
            corpus_lines.append(f"URL: {item['url']}")
            corpus_lines.append(f"SNIPPET: {item['snippet']}")
            corpus_lines.append("---")

    if deep_pages:
        corpus_lines.append("\n=== ENGINE C: FULL SCRAPED WEBPAGE TABLES & PUBLIC RECORDS ===")
        for idx, (url, full_text) in enumerate(deep_pages, start=1):
            corpus_lines.append(f"[DEEP PAGE {idx}] URL: {url}")
            corpus_lines.append(f"CONTENT & TABLES:\n{full_text}")
            corpus_lines.append("---")

    all_sources = list(dict.fromkeys(list(seen_serp_u) + list(seen_nat_u)))
    return {
        "corpus": "\n".join(corpus_lines),
        "serper_sources": list(seen_serp_u),
        "native_sources": list(seen_nat_u),
        "sources": all_sources,
        "total_sources": len(all_sources),
        "deep_pages_scraped": len(deep_pages),
    }
