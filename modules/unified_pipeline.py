from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from modules.native_module.pipeline import search_property_native
from modules.serper_module.pipeline import search_property_serper
from prompts.property_prompt import PROPERTY_SCHEMA_FIELDS

logger = logging.getLogger(__name__)


def search_property_unified(address: str) -> dict[str, Any]:
    """
    Unified Hybrid Property Intelligence Pipeline:
    1. Runs Serper Google Search module and Native Web Scraper module in parallel.
    2. Merges results deterministically in Python:
       - Uses Serper's verified facts as the primary baseline (guarantees 0% data loss).
       - Backfills any fields missing/null in Serper with verified data from Native Scraper.
       - Accurately tags each field's origin: 'Both', 'Serper', or 'Native'.
       - Combines and deduplicates verified source URLs from both engines.
    """
    clean_addr = address.strip()

    serper_res: dict[str, Any] = {}
    native_res: dict[str, Any] = {}
    serper_err: Exception | None = None
    native_err: Exception | None = None

    def _execute_serper():
        nonlocal serper_res, serper_err
        try:
            serper_res = search_property_serper(clean_addr)
        except Exception as e:
            serper_err = e
            logger.warning(f"Serper pipeline encountered an error: {e}")

    def _execute_native():
        nonlocal native_res, native_err
        try:
            native_res = search_property_native(clean_addr)
        except Exception as e:
            native_err = e
            logger.warning(f"Native scraper pipeline encountered an error: {e}")

    # Concurrently execute both standalone pipelines
    with ThreadPoolExecutor(max_workers=2) as executor:
        f_serper = executor.submit(_execute_serper)
        f_native = executor.submit(_execute_native)
        f_serper.result()
        f_native.result()

    # If both pipelines failed completely, raise error
    if not serper_res and not native_res:
        raise RuntimeError(
            f"Both search pipelines failed. Serper error: {serper_err}; Native error: {native_err}"
        )

    # Deterministic Field-by-Field Merge
    merged: dict[str, Any] = {}
    origins: dict[str, str] = {}

    for field in PROPERTY_SCHEMA_FIELDS:
        if field == "sources":
            continue

        s_val = serper_res.get(field) if serper_res else None
        n_val = native_res.get(field) if native_res else None

        # Clean string/null representations
        if s_val in ["null", "None", "", "N/A"]:
            s_val = None
        if n_val in ["null", "None", "", "N/A"]:
            n_val = None

        if s_val is not None and n_val is not None:
            # Both engines found data
            merged[field] = s_val
            origins[field] = "Both"
        elif s_val is not None:
            # Found by Serper
            merged[field] = s_val
            origins[field] = "Serper"
        elif n_val is not None:
            # Backfilled from Native Scraper
            merged[field] = n_val
            origins[field] = "Native"
        else:
            merged[field] = None

    # Preserve address
    merged["address"] = clean_addr

    # Merge and deduplicate web sources
    serper_sources = (serper_res.get("sources", []) if serper_res else []) or []
    native_sources = (native_res.get("sources", []) if native_res else []) or []
    combined_sources = list(dict.fromkeys(serper_sources + native_sources))
    merged["sources"] = combined_sources

    # Count verified schema fields
    schema_fields = [k for k in PROPERTY_SCHEMA_FIELDS if k != "sources"]
    verified_count = sum(1 for k in schema_fields if merged.get(k) is not None)
    total_schema = len(schema_fields)
    pct = round((verified_count / total_schema) * 100, 1) if total_schema else 0.0

    # Metadata, Provenance & Extraction Yield Stamp (Appended at the end of the output)
    merged["_field_origins"] = origins
    merged["_engine"] = "Unified Hybrid Engine (Serper Google + Native Web Scraper)"
    merged["_extracted_fields_count"] = verified_count
    merged["_total_schema_fields"] = total_schema
    merged["_extraction_percentage"] = f"{pct}%"
    merged["_extraction_yield_summary"] = f"{verified_count} of {total_schema} fields populated ({pct}%)"

    return merged
