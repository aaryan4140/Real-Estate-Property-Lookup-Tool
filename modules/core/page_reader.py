from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup


def fetch_deep_page(url: str, timeout: int = 6, max_chars: int = 4000) -> tuple[str, str]:
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
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "header", "footer", "noscript", "svg"]):
                tag.decompose()
            cleaned_text = " ".join(soup.stripped_strings)
            return url, cleaned_text[:max_chars]
    except Exception:
        pass
    return url, ""


def is_high_value_property_url(url: str) -> bool:
    """Filter out generic search engines, social media, and focus on specific detail pages."""
    lower = url.lower()
    skip_domains = [
        "google.com", "facebook.com", "instagram.com", "twitter.com", "linkedin.com",
        "youtube.com", "yelp.com", "wikipedia.org", "yellowpages.com"
    ]
    if any(sd in lower for sd in skip_domains):
        return False

    high_value_keywords = [
        "enrichedrealestate.com", "propertyshark.com", "compass.com", "corriden.com",
        "loopnet.com/listing", "boxerproperty.com", "squarefoot.com/building",
        "har.com/commgate", "city-data.com", "hcad.org", "realtor.com", "redfin.com",
        "property", "building", "listing", "homedetails", "parcel", "tax", "cad", "assessor"
    ]
    return any(k in lower for k in high_value_keywords)


def url_priority_score(url: str) -> int:
    """
    Score URLs to guarantee official County Appraisal District (CAD),
    tax assessment, and property record cards are prioritized over generic marketing.
    """
    lower = url.lower()
    score = 0

    # Tier 1: Official Municipal & County Appraisal District Records (Highest Priority)
    tier1 = [".gov", "cad.org", "assessor", "hcad.org", "propertyshark.com", "enrichedrealestate.com", "corriden.com", "appraisal"]
    if any(k in lower for k in tier1):
        score += 50

    # Tier 2: Public Property Tax & Parcel Aggregators
    tier2 = ["tax", "parcel", "compass.com/homedetails", "city-data.com", "redfin.com", "realtor.com"]
    if any(k in lower for k in tier2):
        score += 25

    # Tier 3: Commercial Leasing Spec Portals
    tier3 = ["loopnet.com/listing", "crexi.com", "commercialcafe.com", "commercialsearch.com", "boxerproperty.com", "squarefoot.com"]
    if any(k in lower for k in tier3):
        score += 15

    return score


def scrape_top_pages_concurrently(urls: list[str], max_pages: int = 5) -> list[tuple[str, str]]:
    """
    Intelligently sorts discovered URLs by Public Record Authority,
    then concurrently scrapes full HTML tables from the highest-priority pages.
    """
    unique_candidates: list[str] = []
    seen = set()

    for u in urls:
        if u not in seen and is_high_value_property_url(u):
            seen.add(u)
            unique_candidates.append(u)

    if not unique_candidates:
        return []

    # Sort descending by priority score: County CAD/Tax records come FIRST
    ranked_candidates = sorted(unique_candidates, key=url_priority_score, reverse=True)
    selected_urls = ranked_candidates[:max_pages]

    with ThreadPoolExecutor(max_workers=min(5, len(selected_urls))) as executor:
        deep_results = list(executor.map(fetch_deep_page, selected_urls))
        return [(u, content) for u, content in deep_results if content and len(content) > 100]
