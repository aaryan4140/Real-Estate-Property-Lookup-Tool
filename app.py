import streamlit as st
import pandas as pd

from llm.gemini_baseline import search_property_baseline
from llm.serper_agent_client import search_property_serper
from prompts.property_prompt import PROPERTY_SCHEMA_FIELDS
from utils.formatter import format_as_markdown
from utils.exporter import to_json_string, to_markdown_string, save_to_outputs

st.set_page_config(
    page_title="Real Estate Property Intelligence",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for executive dashboard styling & responsive metric cards
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
    .badge-verified {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
        background-color: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .badge-partial {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
        background-color: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    .badge-engine {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        background-color: rgba(59, 130, 246, 0.15);
        color: #3b82f6;
        border: 1px solid rgba(59, 130, 246, 0.3);
        margin-bottom: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🏠 Property Intelligence & Appraisal Lookup")
st.caption("Compare pure Gemini synthesis against live Google Search scraping & dual-agent compliance auditing.")

# Preset Benchmark Properties for 1-click test
SAMPLE_PROPERTIES = [
    ("🏢 Houston, TX (HCAD)", "2200 North Loop West, Houston, TX 77018"),
    ("🏙️ San Francisco, CA (SF Assessor)", "600 Montgomery St, San Francisco, CA 94111"),
    ("🏬 Lubbock, TX (Lubbock CAD)", "6102 Chicago Avenue, Lubbock, TX 77083"),
]

# Initialize session state keys
if "address_input" not in st.session_state:
    st.session_state["address_input"] = ""
if "trigger_search" not in st.session_state:
    st.session_state["trigger_search"] = False

# Quick-Select Chips (Tier 1)
st.markdown('<div class="sample-chip-label">⚡ QUICK SAMPLE LOOKUPS:</div>', unsafe_allow_html=True)
sample_cols = st.columns(len(SAMPLE_PROPERTIES))
for i, (label, sample_addr) in enumerate(SAMPLE_PROPERTIES):
    if sample_cols[i].button(label, key=f"sample_{i}", use_container_width=True):
        st.session_state["address_input"] = sample_addr
        st.session_state["trigger_search"] = True
        st.rerun()

# Execution Mode Selector (Allows comparing Baseline vs Serper-Powered solution)
engine_choice = st.radio(
    "Choose Extraction & Audit Mode:",
    [
        "🌐 Serper-Powered (Live Google Search + Dual-Agent Compliance Audit)",
        "🧠 Baseline Solution (Pure Gemini Synthesis)",
        "⚖️ Side-by-Side Comparison (Run Both & Compare Directly)",
    ],
    index=0,
    horizontal=True,
)

# Search Form Layout
search_col1, search_col2 = st.columns([5, 1])
with search_col1:
    address = st.text_input(
        "Property Address",
        placeholder="Enter full street address, city, state, zip (e.g. 2200 North Loop West, Houston, TX 77018)",
        key="address_input",
        label_visibility="collapsed",
    )
with search_col2:
    search_clicked = st.button("🔍 Search", type="primary", use_container_width=True)

# Determine if search should execute
should_search = search_clicked or st.session_state["trigger_search"]
if st.session_state["trigger_search"]:
    st.session_state["trigger_search"] = False

if should_search and not address:
    st.warning("Please enter a property address or select a sample above.")

# Execute Selected Mode
if should_search and address:
    if "Side-by-Side" in engine_choice:
        with st.spinner("⚖️ Running Dual Execution: Baseline Synthesis + Serper Google Dual-Agent Audit..."):
            try:
                res_baseline = search_property_baseline(address)
                save_to_outputs(res_baseline, filename_prefix="property_report_baseline")
                st.session_state["result_baseline"] = res_baseline

                res_serper = search_property_serper(address)
                save_to_outputs(res_serper, filename_prefix="property_report_serper_audited")
                st.session_state["result_serper"] = res_serper

                st.session_state["mode"] = "comparison"
                st.session_state["address"] = address
            except Exception as e:
                st.error(f"Execution failed: {e}")

    elif "Serper-Powered" in engine_choice:
        with st.spinner(f"🌐 Scraping live Google Search records via Serper & auditing with Agent 2 for '{address}'..."):
            try:
                res_serper = search_property_serper(address)
                save_to_outputs(res_serper, filename_prefix="property_report_serper_audited")
                save_to_outputs(res_serper, filename_prefix="property_report")
                st.session_state["result_single"] = res_serper
                st.session_state["mode"] = "single"
                st.session_state["address"] = address
            except Exception as e:
                st.error(f"Serper live search failed: {e}")

    else:
        with st.spinner(f"🧠 Querying baseline Gemini model for '{address}'..."):
            try:
                res_baseline = search_property_baseline(address)
                save_to_outputs(res_baseline, filename_prefix="property_report_baseline")
                save_to_outputs(res_baseline, filename_prefix="property_report")
                st.session_state["result_single"] = res_baseline
                st.session_state["mode"] = "single"
                st.session_state["address"] = address
            except Exception as e:
                st.error(f"Baseline query failed: {e}")


def _render_hero_metrics(result: dict):
    prop_type = result.get("propertyType") or result.get("propertySubtype") or "Not Specified"
    building_class = result.get("buildingClass") or result.get("constructionClass")
    type_sub = f"Class {building_class}" if building_class else "Public Record"

    sqft_val = result.get("buildingAreaSqft")
    if sqft_val:
        try:
            sqft_clean = f"{int(float(str(sqft_val).replace(',', ''))):,} sqft"
        except (ValueError, TypeError):
            sqft_clean = f"{sqft_val} sqft"
    else:
        sqft_clean = "Not Listed"

    year_built = result.get("yearBuilt")
    if year_built:
        actual_age = result.get("actualAge")
        year_sub = f"Age: ~{actual_age} yrs" if actual_age else "Original Build"
    else:
        year_built = "Unknown"
        year_sub = "CAD Historic"

    apn = result.get("property apn") or result.get("parcelId") or "Unassigned"
    county = result.get("county") or "County CAD"

    owner = result.get("owner name") or "Public Record / Undisclosed"
    ownership = result.get("ownership") or "Deed Record"

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">🏷️ Property Type</div>
                <div class="metric-value">{prop_type}</div>
                <div class="metric-sub">{type_sub}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with kpi2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">📐 Building Area</div>
                <div class="metric-value">{sqft_clean}</div>
                <div class="metric-sub">Gross Assessable Area</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with kpi3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">📅 Year Built</div>
                <div class="metric-value">{year_built}</div>
                <div class="metric-sub">{year_sub}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with kpi4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">📍 Parcel APN</div>
                <div class="metric-value">{apn}</div>
                <div class="metric-sub">{county}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with kpi5:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">👤 Recorded Owner</div>
                <div class="metric-value" title="{owner}">{owner}</div>
                <div class="metric-sub">{ownership}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_completeness(result: dict):
    assessable = [f for f in PROPERTY_SCHEMA_FIELDS if f != "sources"]
    total = len(assessable)
    verified = sum(1 for f in assessable if result.get(f) is not None)
    pct = int((verified / total) * 100) if total else 0

    c1, c2 = st.columns([3, 1])
    with c1:
        st.progress(
            pct / 100,
            text=f"📊 Assessment Record Completeness: {verified} of {total} fields verified ({pct}%)",
        )
    with c2:
        if "Serper" in result.get("_engine", ""):
            st.markdown(
                '<div style="text-align: right; padding-top: 6px;"><span class="badge-verified">🛡️ Serper Live Audited</span></div>',
                unsafe_allow_html=True,
            )
        elif verified >= 15:
            st.markdown(
                '<div style="text-align: right; padding-top: 6px;"><span class="badge-verified">🟢 Public Assessor Data</span></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="text-align: right; padding-top: 6px;"><span class="badge-partial">🟡 Partial Public Record</span></div>',
                unsafe_allow_html=True,
            )


# --- RENDER RESULTS ---
if st.session_state.get("mode") == "comparison" and "result_baseline" in st.session_state and "result_serper" in st.session_state:
    b_res = st.session_state["result_baseline"]
    s_res = st.session_state["result_serper"]

    st.divider()
    st.subheader("⚖️ Side-by-Side Comparison: Baseline vs. Serper-Audited Pipeline")

    tab_comp, tab_serper, tab_baseline = st.tabs([
        "📊 Comparative Delta Matrix",
        "🌐 Serper-Audited Full Report",
        "🧠 Baseline Full Report",
    ])

    with tab_comp:
        # Comparison Highlights Matrix
        key_metrics = [
            ("Property APN", "property apn"),
            ("County", "county"),
            ("Building Area (sqft)", "buildingAreaSqft"),
            ("Year Built", "yearBuilt"),
            ("Recorded Owner", "owner name"),
            ("Zoning Code", "zoning"),
            ("Property Type", "propertyType"),
            ("Verified Sources Count", "sources"),
        ]

        matrix_rows = []
        for label, key in key_metrics:
            val_base = b_res.get(key)
            val_serp = s_res.get(key)

            if key == "sources":
                str_base = f"{len(val_base)} URLs" if isinstance(val_base, list) else "0 URLs"
                str_serp = f"{len(val_serp)} Live URLs" if isinstance(val_serp, list) else "0 URLs"
                match_status = "🌐 Live Google Scraped"
            else:
                str_base = str(val_base) if val_base is not None else "null (unverified)"
                str_serp = str(val_serp) if val_serp is not None else "null (unverified)"
                if str_base == str_serp and str_base != "null (unverified)":
                    match_status = "✅ Match"
                elif str_base != str_serp and str_serp != "null (unverified)":
                    match_status = "✨ Serper Verified"
                elif str_serp == "null (unverified)" and str_base != "null (unverified)":
                    match_status = "⚠️ Baseline Guess / Unverified"
                else:
                    match_status = "— Both Null"

            matrix_rows.append({
                "Property Metric": label,
                "Baseline (Gemini Memory)": str_base,
                "Serper-Audited (Live Google)": str_serp,
                "Verification Audit": match_status,
            })

        df_matrix = pd.DataFrame(matrix_rows)
        st.dataframe(df_matrix, use_container_width=True, hide_index=True)

        st.caption(
            "💡 **Audit Insight:** The Baseline solution relies on LLM training memory and may guess values. "
            "The Serper solution strictly verifies every single field against live Google Search snippets, "
            "dropping unconfirmed numbers to null to protect financial accuracy."
        )

        st.divider()
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.download_button(
                label="📥 Download Serper-Audited Report (JSON)",
                data=to_json_string(s_res),
                file_name="property_report_serper_audited.json",
                mime="application/json",
                use_container_width=True,
            )
        with col_d2:
            st.download_button(
                label="📥 Download Baseline Report (JSON)",
                data=to_json_string(b_res),
                file_name="property_report_baseline.json",
                mime="application/json",
                use_container_width=True,
            )

    with tab_serper:
        st.markdown(f'<div class="badge-engine">{s_res.get("_engine", "Serper-Audited Engine")}</div>', unsafe_allow_html=True)
        _render_hero_metrics(s_res)
        st.write("")
        _render_completeness(s_res)
        st.divider()
        st.markdown(format_as_markdown(s_res))
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                label="📥 Download Serper JSON",
                data=to_json_string(s_res),
                file_name="property_report_serper_audited.json",
                mime="application/json",
                use_container_width=True,
            )
        with c2:
            st.download_button(
                label="📥 Download Serper Markdown",
                data=to_markdown_string(s_res),
                file_name="property_report_serper_audited.md",
                mime="text/markdown",
                use_container_width=True,
            )

    with tab_baseline:
        st.markdown(f'<div class="badge-engine">{b_res.get("_engine", "Baseline Engine")}</div>', unsafe_allow_html=True)
        _render_hero_metrics(b_res)
        st.write("")
        _render_completeness(b_res)
        st.divider()
        st.markdown(format_as_markdown(b_res))
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                label="📥 Download Baseline JSON",
                data=to_json_string(b_res),
                file_name="property_report_baseline.json",
                mime="application/json",
                use_container_width=True,
            )
        with c2:
            st.download_button(
                label="📥 Download Baseline Markdown",
                data=to_markdown_string(b_res),
                file_name="property_report_baseline.md",
                mime="text/markdown",
                use_container_width=True,
            )

elif st.session_state.get("mode") == "single" and "result_single" in st.session_state:
    result = st.session_state["result_single"]

    st.divider()
    st.markdown(f'<div class="badge-engine">{result.get("_engine", "Property Intelligence")}</div>', unsafe_allow_html=True)

    _render_hero_metrics(result)
    st.write("")
    _render_completeness(result)

    st.divider()
    report_md = format_as_markdown(result)
    st.markdown(report_md)

    st.divider()
    prefix = "property_report_serper_audited" if "Serper" in result.get("_engine", "") else "property_report_baseline"
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label=f"📥 Download {prefix}.json",
            data=to_json_string(result),
            file_name=f"{prefix}.json",
            mime="application/json",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            label=f"📥 Download {prefix}.md",
            data=to_markdown_string(result),
            file_name=f"{prefix}.md",
            mime="text/markdown",
            use_container_width=True,
        )
