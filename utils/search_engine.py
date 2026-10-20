from __future__ import annotations

import json
import os
import re
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup

load_dotenv()


# Common address abbreviations used in public county appraisal districts & commercial databases
ABBREVIATIONS: list[tuple[str, str]] = [
    (r"\bNorth\b", "N"),
    (r"\bSouth\b", "S"),
    (r"\bEast\b", "E"),
    (r"\bWest\b", "W"),
    (r"\bLoop West\b", "Loop W"),
    (r"\bLoop North\b", "Loop N"),
    (r"\bLoop South\b", "Loop S"),
    (r"\bLoop East\b", "Loop E"),
    (r"\bRoad\b", "Rd"),
    (r"\bStreet\b", "St"),
    (r"\bBoulevard\b", "Blvd"),
    (r"\bAvenue\b", "Ave"),
    (r"\bHighway\b", "Hwy"),
    (r"\bDrive\b", "Dr"),
    (r"\bParkway\b", "Pkwy"),
    (r"\bSuite\b", "Ste"),
]


def normalize_address_variants(address: str) -> list[str]:
    """Generate both formal and abbreviated address variants for deep index matching."""
    clean = address.strip()
    variants = [clean]
    short_variant = clean
    for pat, rep in ABBREVIATIONS:
        short_variant = re.sub(pat, rep, short_variant, flags=re.IGNORECASE)

    if short_variant != clean:
        variants.append(short_variant)
    return variants


def _search_serper(query: str, api_key: str, max_results: int = 10) -> list[dict[str, str]]:
    """Query live Google Search index via Serper API with high result depth."""
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


def _fetch_deep_page(url: str) -> tuple[str, str]:
    """
    Fetch and clean live HTML from high-priority property detail pages.
    Extracts text, table values, property specs, APN, and tax assessments.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "header", "footer", "noscript", "svg"]):
                tag.decompose()
            cleaned_text = " ".join(soup.stripped_strings)
            # Limit page text to 3,500 chars to optimize LLM attention and token budget
            return url, cleaned_text[:3500]
    except Exception:
        pass
    return url, ""


def _is_high_value_property_url(url: str) -> bool:
    """Filter out generic homepages, search pages, social media, and focus on specific detail pages."""
    lower = url.lower()
    # Skip social, search engines, and generic roots
    skip_domains = [
        "google.com", "facebook.com", "instagram.com", "twitter.com", "linkedin.com",
        "youtube.com", "yelp.com", "wikipedia.org", "yellowpages.com"
    ]
    if any(sd in lower for sd in skip_domains):
        return False

    # Check if URL looks like a specific property detail or public records record
    high_value_keywords = [
        "enrichedrealestate.com", "propertyshark.com", "compass.com", "corriden.com",
        "loopnet.com/listing", "boxerproperty.com", "squarefoot.com/building",
        "har.com/commgate", "city-data.com", "hcad.org", "realtor.com", "redfin.com",
        "property", "building", "listing", "homedetails", "parcel", "tax"
    ]
    return any(k in lower for k in high_value_keywords)


def search_property_multi_cluster(address: str) -> dict[str, Any]:
    """
    Deep-Search Engine (Option 1):
    1. Normalizes address variants (formal and abbreviated).
    2. Executes targeted Google search queries across 4 clusters via Serper API.
    3. Identifies the top high-value property detail pages.
    4. Concurrently scrapes the full HTML tables/text from the top property pages.
    5. Returns an enriched dual-section corpus (live snippets + full webpage tables).
    """
    clean_addr = address.strip()
    variants = normalize_address_variants(clean_addr)
    short_addr = variants[-1]
    serper_api_key = os.getenv("SERPER_API_KEY", "").strip()

    clusters = [
        # Cluster 1: Public Records, CAD, Tax Roll, APN & Aggregators
        (
            f'"{short_addr}" (site:enrichedrealestate.com OR site:propertyshark.com OR '
            f'site:compass.com OR site:corriden.com OR site:har.com OR site:loopnet.com OR '
            f'parcel OR APN OR "account number" OR "assessed value")'
        ),
        # Cluster 2: Building Specs, Size, Year Built & Engineering
        f'"{clean_addr}" building area sqft year built stories construction elevators parking ratio',
        # Cluster 3: Commercial Leasing & Official Property Description
        f'"{clean_addr}" commercial office rentable square feet brochure lease',
        # Cluster 4: Zoning, Municipality & Flood Map
        f'"{clean_addr}" zoning municipality code FEMA flood map panel FIRM',
    ]

    all_items: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    # Step 1: Run Google Search via Serper (or DDG Lite fallback)
    for q in clusters:
        if serper_api_key:
            items = _search_serper(q, serper_api_key, max_results=8)
        else:
            items = _search_lite_cluster(q, max_results=4)

        for it in items:
            u = it["url"]
            if u not in seen_urls:
                seen_urls.add(u)
                all_items.append(it)

    # Step 2: Select Top High-Value Property Detail URLs for Deep Page Scraping
    candidate_urls: list[str] = []
    for it in all_items:
        u = it["url"]
        if _is_high_value_property_url(u) and u not in candidate_urls:
            candidate_urls.append(u)
        if len(candidate_urls) >= 4:
            break

    # Step 3: Concurrently Scrape Full Webpage Content from Top Candidate Pages
    deep_pages_content: list[tuple[str, str]] = []
    if candidate_urls:
        with ThreadPoolExecutor(max_workers=min(4, len(candidate_urls))) as executor:
            deep_results = list(executor.map(_fetch_deep_page, candidate_urls))
            for u, content in deep_results:
                if content and len(content) > 100:
                    deep_pages_content.append((u, content))

    # Step 4: Build Comprehensive Dual-Section Corpus for LLM Dual-Agent Pipeline
    corpus_lines = []
    corpus_lines.append("=== SECTION 1: LIVE SEARCH ENGINE SNIPPETS ===")
    for idx, item in enumerate(all_items, start=1):
        corpus_lines.append(f"SOURCE [{idx}]: {item['title']}")
        corpus_lines.append(f"URL: {item['url']}")
        corpus_lines.append(f"SNIPPET: {item['snippet']}")
        corpus_lines.append("---")

    if deep_pages_content:
        corpus_lines.append("\n=== SECTION 2: FULL SCRAPED WEBPAGE TABLES & DETAIL PAGES ===")
        for idx, (url, full_text) in enumerate(deep_pages_content, start=1):
            corpus_lines.append(f"PAGE [{idx}] URL: {url}")
            corpus_lines.append(f"PAGE CONTENT & TABLES:\n{full_text}")
            corpus_lines.append("---")

    all_sources = list(seen_urls)
    return {
        "corpus": "\n".join(corpus_lines),
        "sources": all_sources,
        "total_sources": len(all_sources),
        "deep_pages_scraped": len(deep_pages_content),
        "engine": "Google (via Serper) + Deep Webpage Reader" if serper_api_key else "DuckDuckGo Lite",
    }
