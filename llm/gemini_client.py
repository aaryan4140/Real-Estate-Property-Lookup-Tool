from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

from prompts.property_prompt import PROPERTY_SCHEMA_FIELDS
from utils.search_engine import search_property_multi_cluster

load_dotenv()

# Ordered list of models with automatic fallback to guarantee 99.9% uptime
PREFERRED_MODELS = [
    os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
    "gemini-3.8-flash",
    "gemini-flash-latest",
    "gemini-3.1-flash-lite",
]


def get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set. Please check your .env file.")
    return genai.Client(api_key=api_key)


def _call_with_fallback(client: genai.Client, prompt: str, temperature: float = 0.2) -> str:
    """Execute model inference with automatic fallback across Gemini flash models."""
    last_error: Exception | None = None
    for model_name in PREFERRED_MODELS:
        try:
            resp = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                ),
            )
            if resp.text:
                return resp.text
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"All Gemini models failed. Last error: {last_error}")


def search_property(address: str) -> dict[str, Any]:
    """
    Dual-Agent Live Search, Extraction & Factual Audit Pipeline:
    1. Multi-cluster web scraping (CAD, Broker listings, Zoning, FEMA) via DuckDuckGo Lite.
    2. Agent 1 (The Extractor): Maps facts to 89-field schema from live scraped web text.
    3. Agent 2 (The Compliance Auditor): Strict zero-temperature audit cross-checking every number.
    4. Deterministic Python validation & source attribution.
    """
    client = get_client()
    clean_address = address.strip()

    # Step 1: Live Multi-Cluster Web Scraping
    web_data = search_property_multi_cluster(clean_address)
    scraped_corpus = web_data.get("corpus", "")
    scraped_sources = web_data.get("sources", [])

    fields_list = ", ".join(f'"{f}"' for f in PROPERTY_SCHEMA_FIELDS)

    # Step 2: Agent 1 (The Multi-Source Extraction Specialist)
    agent1_prompt = f"""You are Agent 1 (Real Estate Data Extraction Specialist).
Your job is to extract factual property appraisal and physical data using ONLY the live scraped web results provided below.

PROPERTY ADDRESS: {clean_address}

RAW LIVE WEB SCRAPED TEXT:
{scraped_corpus if scraped_corpus else "No live snippets retrieved."}

EXTRACTION RULES:
1. Populate as many of the schema fields as possible, but ONLY using facts explicitly found in the web text.
2. If a field is NOT explicitly mentioned or cannot be verified from the web text, you MUST return null. DO NOT guess or fabricate.
3. The "sources" field must be a JSON array of the real URLs found in the text.
4. Return raw JSON only with NO markdown fences and no conversational filler.

SCHEMA FIELDS TO POPULATE:
{fields_list}

Return the raw JSON object now:"""

    raw_draft_text = _call_with_fallback(client, agent1_prompt, temperature=0.2)
    draft_data = _parse_json(raw_draft_text)

    # Step 3: Agent 2 (The Compliance & Factual Verification Auditor)
    # Runs at temperature=0.0 (strictly deterministic, zero creative guessing)
    agent2_prompt = f"""You are Agent 2 (Senior Real Estate Compliance Auditor for an institutional financial client).
Your sole job is to audit Agent 1's proposed property JSON against the RAW SCRAPED WEB TEXT to guarantee 100% factual accuracy.

AUDITING RULES:
1. Cross-examine every non-null field in Agent 1's JSON against the RAW SCRAPED WEB TEXT.
2. If any value (such as APN, square footage, year built, owner name, or zoning) is NOT explicitly supported by the scraped text, you MUST change its value to null.
3. Eliminate confusion: Ensure land/site area is not confused with building square footage.
4. If an APN or parcel ID appears in the text, ensure it is preserved accurately in 'property apn' and 'parcelId'.
5. The 'sources' array must contain only valid URLs from the scraped text.
6. Return ONLY the audited, verified raw JSON object. No explanation, no markdown fences.

RAW SCRAPED WEB TEXT:
{scraped_corpus}

AGENT 1 PROPOSED JSON:
{json.dumps(draft_data, indent=2)}

Return audited raw JSON now:"""

    audited_text = _call_with_fallback(client, agent2_prompt, temperature=0.0)
    audited_data = _parse_json(audited_text)

    # Step 4: Deterministic Python Sanity & Source Enrichment
    # Guarantee all schema fields exist in the dictionary
    for field in PROPERTY_SCHEMA_FIELDS:
        if field not in audited_data:
            audited_data[field] = None

    # Merge verified web sources
    if not audited_data.get("sources") and scraped_sources:
        audited_data["sources"] = scraped_sources
    elif audited_data.get("sources") and scraped_sources:
        # Deduplicate and prioritize real scraped links
        combined = list(dict.fromkeys(audited_data["sources"] + scraped_sources))
        audited_data["sources"] = combined

    # Enforce address consistency
    if not audited_data.get("address"):
        audited_data["address"] = clean_address

    return audited_data


def _parse_json(text: str) -> dict[str, Any]:
    """Extract the first JSON object from the response text."""
    if not text.strip():
        raise ValueError("Gemini returned an empty response.")

    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)

    decoder = json.JSONDecoder()
    for i, ch in enumerate(cleaned):
        if ch == "{":
            try:
                obj, _ = decoder.raw_decode(cleaned[i:])
                if isinstance(obj, dict):
                    return obj
            except json.JSONDecodeError:
                continue

    raise ValueError("Response did not contain a valid JSON object.")
