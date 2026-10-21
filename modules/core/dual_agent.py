from __future__ import annotations

import json
from typing import Any

from modules.core.gemini_caller import call_gemini_with_fallback
from prompts.property_prompt import PROPERTY_SCHEMA_FIELDS


def _parse_json(text: str) -> dict[str, Any]:
    """Robust JSON extraction from LLM response text."""
    clean = text.strip()
    if clean.startswith("```"):
        first_newline = clean.find("\n")
        if first_newline != -1:
            clean = clean[first_newline + 1 :]
        if clean.endswith("```"):
            clean = clean[:-3]
        clean = clean.strip()

    try:
        data = json.loads(clean)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    # Fallback to balanced brace matching
    start_idx = clean.find("{")
    while start_idx != -1:
        depth = 0
        for i in range(start_idx, len(clean)):
            if clean[i] == "{":
                depth += 1
            elif clean[i] == "}":
                depth -= 1
                if depth == 0:
                    candidate = clean[start_idx : i + 1]
                    try:
                        data = json.loads(candidate)
                        if isinstance(data, dict):
                            return data
                    except json.JSONDecodeError:
                        break
        start_idx = clean.find("{", start_idx + 1)

    raise ValueError("LLM response did not contain a valid JSON object.")


def run_dual_agent_audit(
    address: str,
    search_data: dict[str, Any],
    engine_label: str = "Live Web Search",
) -> dict[str, Any]:
    """
    Shared Institutional Dual-Agent Pipeline:
    1. Agent 1 (Extraction Specialist): Maps facts to 89-field schema from search snippets & tables.
    2. Agent 2 (Compliance Auditor at temp=0.0): Strict cross-examination verifying every single number.
    3. Normalizes and validates output dictionary.
    """
    clean_address = address.strip()
    scraped_corpus = search_data.get("corpus", "")
    scraped_sources = search_data.get("sources", [])

    fields_list = ", ".join(f'"{f}"' for f in PROPERTY_SCHEMA_FIELDS)

    # Step 1: Agent 1 (The Multi-Source Extraction Specialist)
    agent1_prompt = f"""You are Agent 1 (Senior Real Estate Data Extraction Specialist for an institutional financial client).
Extract all factual property appraisal, structural, tax, assessment, and legal details using BOTH the live search snippets AND the full scraped webpage tables provided below.

PROPERTY ADDRESS: {clean_address}

RAW LIVE WEB SCRAPED CORPUS (SERPER + NATIVE + DEEP WEBPAGE TABLES):
{scraped_corpus if scraped_corpus else "No web results found."}

EXTRACTION RULES:
1. Examine all search snippets (Serper Google and Native DuckDuckGo) AND Full Scraped Webpage Tables.
2. Look specifically for:
   - "property apn" / "parcelId": Extract the official county parcel identifier. In Texas (HCAD/CAD) and other jurisdictions that do not use the term 'APN', look for 'Account Number', 'CAD Quick Ref ID', or 'Property ID' (e.g., 10-to-13-digit numbers like 0432050020010, R55010, or 0207-032). CRITICAL: Never mistake commercial broker advertising listing IDs (e.g., LoopNet Listing ID, Crexi ID, or HAR ID) for a county parcel number.
   - "legalDescription": Extract from "The legal description -", "Legal:", or deed abstract.
   - "buildingAreaSqft" / "netRentableAreaSqft": Extract gross building area or net rentable square footage.
   - "siteAreaAcres" / "parcelSizeAcres": Extract land size / lot area (convert sq ft to acres if provided in sf: 1 acre = 43,560 sq ft).
   - "yearBuilt", "remodeledYear", "numberOfStories", "elevators", "parking".
   - "county", "city", "state", "postalCode".
   - "zoning", "zoningAuthority", "municipality zoning".
   - "owner name", "ownership".
3. If a field is NOT found or verified in the text, return null. DO NOT guess or fabricate.
4. The "sources" field must be a JSON array containing the actual URLs present in the text.
5. PROVENANCE TRACKING: Include a "_field_origins" JSON object mapping each non-null field to its discovered source:
   - "Serper" if discovered in [SERPER SOURCE]
   - "Native" if discovered in [NATIVE SOURCE]
   - "Both" if confirmed in both engines or in [DEEP PAGE]
6. Return raw JSON only with NO markdown fences.

SCHEMA FIELDS TO POPULATE:
{fields_list}

Return the raw JSON object now:"""

    raw_draft = call_gemini_with_fallback(agent1_prompt, temperature=0.2)
    draft_data = _parse_json(raw_draft)

    # Step 2: Agent 2 (The Compliance & Factual Verification Auditor at temp=0.0)
    agent2_prompt = f"""You are Agent 2 (Senior Real Estate Compliance Auditor for an institutional financial client).
Audit Agent 1's proposed JSON against the RAW LIVE WEB SCRAPED CORPUS to guarantee 100% factual accuracy.

AUDIT RULES:
1. Cross-examine every non-null field against the RAW LIVE WEB CORPUS (including Serper Snippets, Native Snippets, and Full Webpage Tables).
2. If a value (such as Account Number/APN, Legal Description, Gross/Net SF, Land Size, Year Built, Stories) IS supported by the text or tables, KEEP IT and ensure high fidelity.
3. If any value is NOT explicitly verified in the text or tables, you MUST change it to null.
4. Do not confuse building square footage with lot/land square footage.
5. The 'sources' array must contain only valid URLs from the scraped text.
6. Verify and preserve the '_field_origins' mapping for all non-null fields.
7. Return ONLY the audited, verified raw JSON object. No explanation, no markdown fences.

RAW LIVE WEB SCRAPED CORPUS:
{scraped_corpus}

AGENT 1 PROPOSED JSON:
{json.dumps(draft_data, indent=2)}

Return audited raw JSON now:"""

    audited_text = call_gemini_with_fallback(agent2_prompt, temperature=0.0)
    audited_data = _parse_json(audited_text)

    # Step 3: Standardize Schema Keys, Origins & Source Attribution
    field_origins = audited_data.get("_field_origins", {})
    if not isinstance(field_origins, dict):
        field_origins = {}

    for field in PROPERTY_SCHEMA_FIELDS:
        if field not in audited_data:
            audited_data[field] = None
        # Backfill origin if missing for a populated field
        if audited_data[field] is not None and field not in field_origins:
            field_origins[field] = "Serper"

    audited_data["_field_origins"] = field_origins

    if not audited_data.get("sources") and scraped_sources:
        audited_data["sources"] = scraped_sources
    elif audited_data.get("sources") and scraped_sources:
        audited_data["sources"] = list(dict.fromkeys(audited_data["sources"] + scraped_sources))

    if not audited_data.get("address"):
        audited_data["address"] = clean_address

    audited_data["_engine"] = engine_label
    return audited_data
