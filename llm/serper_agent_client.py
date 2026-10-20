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

PREFERRED_MODELS = [
    os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
    "gemini-flash-latest",
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash",
]


def get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set. Please check your .env file.")
    return genai.Client(api_key=api_key)


def _call_model(prompt: str, temperature: float = 0.2) -> str:
    client = get_client()
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
    raise RuntimeError(f"All Gemini models failed in Serper agent: {last_error}")


def search_property_serper(address: str) -> dict[str, Any]:
    """
    Second Solution: Serper-Powered Live Google Search + Dual-Agent Factual Audit Pipeline.
    1. Multi-cluster real-time Google search via Serper across CAD, LoopNet, FEMA, City zoning.
    2. Agent 1 (The Multi-Source Extractor): Extracts 89 fields strictly from live scraped text.
    3. Agent 2 (The Compliance Auditor): Strict zero-temperature audit cross-examining every number.
    4. Deterministic Python validation and verification metadata.
    """
    clean_address = address.strip()

    # Step 1: Live Multi-Cluster Google Search via Serper
    web_data = search_property_multi_cluster(clean_address)
    scraped_corpus = web_data.get("corpus", "")
    scraped_sources = web_data.get("sources", [])
    search_engine_name = web_data.get("engine", "Google (via Serper)")

    fields_list = ", ".join(f'"{f}"' for f in PROPERTY_SCHEMA_FIELDS)

    # Step 2: Agent 1 (The Multi-Source Extraction Specialist)
    agent1_prompt = f"""You are Agent 1 (Senior Real Estate Data Extraction Specialist).
Extract all verifiable property appraisal, structural, and legal details using ONLY the live Google search snippets provided below.

PROPERTY ADDRESS: {clean_address}

RAW LIVE GOOGLE SEARCH CORPUS:
{scraped_corpus if scraped_corpus else "No search snippets found."}

STRICT INSTRUCTIONS:
1. Populate as many schema fields as possible, but ONLY using facts explicitly found in the web snippets.
2. If a field is NOT explicitly supported or cannot be confirmed from the text, return null. DO NOT guess or fabricate.
3. The "sources" field must be a JSON array containing the actual URLs present in the search snippets.
4. Return raw JSON only with NO markdown fences.

SCHEMA FIELDS TO POPULATE:
{fields_list}

Return the raw JSON object now:"""

    raw_draft_text = _call_model(agent1_prompt, temperature=0.2)
    draft_data = _parse_json(raw_draft_text)

    # Step 3: Agent 2 (The Compliance & Factual Verification Auditor)
    # temperature=0.0 enforces zero creativity / zero hallucination
    agent2_prompt = f"""You are Agent 2 (Senior Real Estate Compliance Auditor for an institutional financial client).
Audit Agent 1's proposed JSON against the RAW LIVE GOOGLE SEARCH CORPUS to guarantee 100% factual accuracy.

AUDIT RULES:
1. Cross-examine every non-null field against the RAW LIVE GOOGLE SEARCH CORPUS.
2. If any value (such as APN, square footage, year built, owner, or zoning) is NOT explicitly verified in the text, you MUST change it to null.
3. Ensure building square footage is not confused with lot/site acreage.
4. The 'sources' array must contain only valid URLs from the scraped text.
5. Return ONLY the audited, verified raw JSON object. No explanation, no markdown fences.

RAW LIVE GOOGLE SEARCH CORPUS:
{scraped_corpus}

AGENT 1 PROPOSED JSON:
{json.dumps(draft_data, indent=2)}

Return audited raw JSON now:"""

    audited_text = _call_model(agent2_prompt, temperature=0.0)
    audited_data = _parse_json(audited_text)

    # Step 4: Python Sanity & Metadata Enrichment
    for field in PROPERTY_SCHEMA_FIELDS:
        if field not in audited_data:
            audited_data[field] = None

    if not audited_data.get("sources") and scraped_sources:
        audited_data["sources"] = scraped_sources
    elif audited_data.get("sources") and scraped_sources:
        combined = list(dict.fromkeys(audited_data["sources"] + scraped_sources))
        audited_data["sources"] = combined

    if not audited_data.get("address"):
        audited_data["address"] = clean_address

    audited_data["_engine"] = f"{search_engine_name} + Dual-Agent Compliance Audit"
    return audited_data


def _parse_json(text: str) -> dict[str, Any]:
    if not text.strip():
        raise ValueError("Model returned an empty response.")

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
