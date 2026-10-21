from __future__ import annotations

from typing import Any
from modules.core.dual_agent import run_dual_agent_audit
from modules.serper_module.serper_searcher import search_serper_property_data


def search_property_serper(address: str) -> dict[str, Any]:
    """
    Dedicated Serper Module Pipeline:
    1. Multi-cluster live Google Search via Serper API.
    2. Deep HTML webpage table reader.
    3. Dual-Agent Compliance Audit (Agent 1 Extractor + Agent 2 Zero-Temp Auditor).
    """
    clean_addr = address.strip()
    search_data = search_serper_property_data(clean_addr)
    return run_dual_agent_audit(
        address=clean_addr,
        search_data=search_data,
        engine_label="Google (via Serper) + Dual-Agent Compliance Audit",
    )
