import streamlit as st
import pandas as pd
from dotenv import load_dotenv

load_dotenv(override=True)

from modules.unified_pipeline import search_property_unified
from prompts.property_prompt import PROPERTY_SCHEMA_FIELDS
from utils.formatter import format_as_markdown
from utils.exporter import to_json_string, save_to_outputs

st.set_page_config(
    page_title="Real Estate Property Intelligence",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for executive dashboard styling & origin badges
st.markdown(
    """
    <style>
    .sample-chip-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #718096;
        margin-bottom: 6px;
    }
    .metric-card {
        background-color: var(--secondary-background-color, #f7fafc);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 12px;
        padding: 16px;
        min-height: 110px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 14px rgba(0, 0, 0, 0.08);
    }
    .metric-title {
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        opacity: 0.75;
    }
    .metric-value {
        font-size: 1.35rem;
        font-weight: 700;
        margin: 4px 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .metric-sub {
        font-size: 0.78rem;
        opacity: 0.8;
    }
    .badge-serper {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 9999px;
        font-size: 0.74rem;
        font-weight: 600;
        background-color: rgba(59, 130, 246, 0.15);
        color: #3b82f6;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    .badge-native {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 9999px;
        font-size: 0.74rem;
        font-weight: 600;
        background-color: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .badge-both {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 9999px;
        font-size: 0.74rem;
        font-weight: 600;
        background-color: rgba(139, 92, 246, 0.15);
        color: #8b5cf6;
        border: 1px solid rgba(139, 92, 246, 0.3);
    }
    .banner-provenance {
        background-color: var(--secondary-background-color, #f7fafc);
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 10px;
        padding: 12px 18px;
        margin: 12px 0 18px 0;
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🏠 Real Estate Property Intelligence & Lookup")
st.caption("Single-Click Unified Hybrid Engine: Live Google Search + Free Native Web Scraper with Zero-Hallucination Dual-Agent Audit.")

# Preset Benchmark Properties
SAMPLE_PROPERTIES = [
    ("🏢 Houston, TX (HCAD)", "2200 North Loop West, Houston, TX 77018"),
    ("🏙️ San Francisco, CA (SF Assessor)", "600 Montgomery St, San Francisco, CA 94111"),
    ("🏬 Lubbock, TX (Lubbock CAD)", "6102 Chicago Avenue, Lubbock, TX 79424"),
]

# Session state setup
if "address_input" not in st.session_state:
    st.session_state["address_input"] = ""
if "trigger_search" not in st.session_state:
    st.session_state["trigger_search"] = False

# Quick-Select Sample Chips
st.markdown('<div class="sample-chip-label">⚡ QUICK SAMPLE LOOKUPS:</div>', unsafe_allow_html=True)
sample_cols = st.columns(len(SAMPLE_PROPERTIES))
for i, (label, sample_addr) in enumerate(SAMPLE_PROPERTIES):
    if sample_cols[i].button(label, key=f"sample_{i}", use_container_width=True):
        st.session_state["address_input"] = sample_addr
        st.session_state["trigger_search"] = True
        st.rerun()

# Clean Single-Click Search Input (No confusing radio buttons)
search_col1, search_col2 = st.columns([5, 1])
with search_col1:
    address = st.text_input(
        "Property Address",
        placeholder="Enter street address, city, state, zip (e.g. 2200 North Loop West, Houston, TX 77018)",
        key="address_input",
        label_visibility="collapsed",
    )
with search_col2:
    search_clicked = st.button("🔍 Search Property", type="primary", use_container_width=True)

should_search = search_clicked or st.session_state["trigger_search"]
if st.session_state["trigger_search"]:
    st.session_state["trigger_search"] = False

if should_search and not address:
    st.warning("Please enter a property address or select a sample above.")

# Execute Unified Hybrid Pipeline (Only 2 LLM calls in total)
if should_search and address:
    with st.spinner(f"🚀 Running Unified Hybrid Pipeline (Google Search + Native Scraper + Table Reader) for '{address}'..."):
        try:
            res = search_property_unified(address)
            saved_path = save_to_outputs(res, property_name_or_address=address)
            st.session_state["saved_file"] = saved_path.name
            st.session_state["result"] = res
            st.session_state["address"] = address
        except Exception as e:
            st.error(f"Execution failed: {e}")


def _get_origin_badge(field_name: str, origins: dict) -> str:
    origin = origins.get(field_name, "Serper")
    if "Both" in origin or origin == "both":
        return "🤝 Dual-Engine Agreement"
    elif "Native" in origin or origin == "native":
        return "🐍 Native Scraper (DuckDuckGo)"
    else:
        return "🌐 Serper (Google Search)"


# Render Search Results
if "result" in st.session_state:
    result = st.session_state["result"]
    origins = result.get("_field_origins", {})

    all_fields = [k for k in PROPERTY_SCHEMA_FIELDS if k != "sources"]
    verified_fields = [k for k in all_fields if result.get(k) is not None]
    total_verified = len(verified_fields)
    pct = int((total_verified / len(all_fields)) * 100) if len(all_fields) > 0 else 0

    serper_count = sum(1 for k in verified_fields if "Serper" in origins.get(k, "Serper") and "Both" not in origins.get(k, ""))
    native_count = sum(1 for k in verified_fields if "Native" in origins.get(k, "") and "Both" not in origins.get(k, ""))
    both_count = sum(1 for k in verified_fields if "Both" in origins.get(k, "") or origins.get(k) == "both")
    # If both_count + serper_count + native_count doesn't equal total, attribute remainder to Serper
    remainder = total_verified - (serper_count + native_count + both_count)
    if remainder > 0:
        serper_count += remainder

    st.divider()

    # --- EXECUTIVE COMBINED EXTRACTION SCORECARD ---
    st.subheader(f"📊 Extraction Yield: {total_verified} Combined Fields Verified ({pct}% Total Schema)")

    stat_cols = st.columns(4)
    with stat_cols[0]:
        st.markdown(
            f"""
            <div class="metric-card" style="border-left: 4px solid #3b82f6;">
                <div class="metric-title">Total Combined Fields</div>
                <div class="metric-value">{total_verified} <span style="font-size: 0.95rem; font-weight: 400; opacity: 0.7;">/ {len(all_fields)}</span></div>
                <div class="metric-sub"><b>{pct}%</b> of 88 Schema Fields Populated</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with stat_cols[1]:
        st.markdown(
            f"""
            <div class="metric-card" style="border-left: 4px solid #60a5fa;">
                <div class="metric-title">🌐 Serper Google Captured</div>
                <div class="metric-value">{serper_count}</div>
                <div class="metric-sub">Primary Google Public Index</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with stat_cols[2]:
        st.markdown(
            f"""
            <div class="metric-card" style="border-left: 4px solid #10b981;">
                <div class="metric-title">🐍 Native Scraper Added</div>
                <div class="metric-value">{native_count}</div>
                <div class="metric-sub">DuckDuckGo Backfilled Fields</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with stat_cols[3]:
        st.markdown(
            f"""
            <div class="metric-card" style="border-left: 4px solid #8b5cf6;">
                <div class="metric-title">🤝 Dual-Engine Confirmed</div>
                <div class="metric-value">{both_count}</div>
                <div class="metric-sub">100% Agreement on Both Engines</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")
    st.progress(pct)
    st.caption(
        f"💡 **Combined Intelligence:** A total of **{total_verified}** non-null fields were extracted and audited at temperature=0.0 across Google Serper and DuckDuckGo Lite. "
        f"Remaining **{len(all_fields) - total_verified}** unverified fields were safely preserved as null to prevent hallucination."
    )
    st.write("")

    # Hero Metric Cards
    prop_type = result.get("propertyType") or result.get("propertySubtype") or "Not Specified"
    sqft_val = result.get("buildingAreaSqft")
    if sqft_val:
        try:
            sqft_clean = f"{int(float(str(sqft_val).replace(',', ''))):,} sqft"
        except (ValueError, TypeError):
            sqft_clean = f"{sqft_val} sqft"
    else:
        sqft_clean = "Not Listed"

    apn_val = result.get("property apn") or result.get("parcelId") or "Not Found"
    year_val = result.get("yearBuilt") or "Not Listed"

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Property Type</div>
                <div class="metric-value">{prop_type}</div>
                <div class="metric-sub">{_get_origin_badge('propertyType', origins)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Building Area</div>
                <div class="metric-value">{sqft_clean}</div>
                <div class="metric-sub">{_get_origin_badge('buildingAreaSqft', origins)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">APN / Parcel ID</div>
                <div class="metric-value">{apn_val}</div>
                <div class="metric-sub">{_get_origin_badge('property apn', origins)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Year Built</div>
                <div class="metric-value">{year_val}</div>
                <div class="metric-sub">{_get_origin_badge('yearBuilt', origins)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    # Detailed Interactive Data Table with Source Provenance
    st.subheader("📋 Comprehensive Property Ledger & Source Provenance")
    tab_table, tab_markdown, tab_sources = st.tabs(["📊 Verified Data Ledger", "📝 Executive Markdown Report", "🔗 Web Sources & Citations"])

    with tab_table:
        table_rows = []
        for field in all_fields:
            val = result.get(field)
            if val is not None:
                origin_label = _get_origin_badge(field, origins)
                table_rows.append({
                    "Property Field": field,
                    "Verified Value": str(val),
                    "Data Source Origin": origin_label,
                })

        if table_rows:
            df_table = pd.DataFrame(table_rows)
            st.dataframe(df_table, use_container_width=True, hide_index=True)
        else:
            st.info("No verified fields found.")

    with tab_markdown:
        st.markdown(format_as_markdown(result))

    with tab_sources:
        sources_list = result.get("sources", [])
        if sources_list:
            st.write(f"**Total Verified Web Sources ({len(sources_list)}):**")
            for idx, s in enumerate(sources_list, start=1):
                st.markdown(f"{idx}. [{s}]({s})")
        else:
            st.info("No source URLs recorded.")

    st.divider()

    # Dynamic JSON Report Download
    saved_name = st.session_state.get("saved_file", "property_report.json")
    st.download_button(
        label=f"📥 Download {saved_name}",
        data=to_json_string(result),
        file_name=saved_name,
        mime="application/json",
        use_container_width=True,
    )
