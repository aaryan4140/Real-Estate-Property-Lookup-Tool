from __future__ import annotations

from typing import Any
from modules.core.dual_agent import run_dual_agent_audit
from modules.native_module.native_scraper import search_native_property_data


def search_property_native(address: str) -> dict[str, Any]:
    """
    Dedicated Free Native Module Pipeline:
    1. Multi-cluster live search via DuckDuckGo Lite (0 API keys).
    2. Deep HTML webpage table reader.
    3. Dual-Agent Compliance Audit (Agent 1 Extractor + Agent 2 Zero-Temp Auditor).
    """
    clean_addr = address.strip()
    search_data = search_native_property_data(clean_addr)
    return run_dual_agent_audit(
        address=clean_addr,
        search_data=search_data,
        engine_label="Python-Native Scraper (DuckDuckGo Lite) + Dual-Agent Audit",
    )
