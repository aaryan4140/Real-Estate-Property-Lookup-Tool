import streamlit as st

from llm.gemini_client import search_property
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
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🏠 Property Intelligence & Appraisal Lookup")
st.caption("Extract authoritative assessment data, parcel identifiers, and structural specs from public CAD records.")

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

# Determine if search should execute (manual click or sample chip trigger)
should_search = search_clicked or st.session_state["trigger_search"]
if st.session_state["trigger_search"]:
    st.session_state["trigger_search"] = False

if should_search and not address:
    st.warning("Please enter a property address or select a sample above.")

if should_search and address:
    with st.spinner(f"Querying appraisal records for '{address}'..."):
        try:
            result = search_property(address)
            save_to_outputs(result)
            st.session_state["result"] = result
            st.session_state["address"] = address
        except ValueError as e:
            st.error(f"Configuration error: {e}")
        except Exception as e:
            st.error(f"Search failed: {e}")

# Render Dashboard if Result Exists
if "result" in st.session_state:
    result = st.session_state["result"]
    addr = st.session_state.get("address", "Property")

    st.divider()

    # --- SUGGESTION 1: HERO KPI METRIC CARDS ---
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
    county = result.get("county") or "County Cad"

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

    st.write("")

    # --- SUGGESTION 5: DATA COMPLETENESS & VERIFICATION PROGRESS METER ---
    assessable_fields = [f for f in PROPERTY_SCHEMA_FIELDS if f != "sources"]
    total_fields = len(assessable_fields)
    verified_fields = sum(1 for f in assessable_fields if result.get(f) is not None)
    completeness_pct = int((verified_fields / total_fields) * 100) if total_fields else 0

    meter_col1, meter_col2 = st.columns([3, 1])
    with meter_col1:
        st.progress(
            completeness_pct / 100,
            text=f"📊 Assessment Record Completeness: {verified_fields} of {total_fields} fields verified ({completeness_pct}%)",
        )
    with meter_col2:
        if verified_fields >= 15:
            st.markdown(
                '<div style="text-align: right; padding-top: 6px;"><span class="badge-verified">🟢 Assessor Records Verified</span></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="text-align: right; padding-top: 6px;"><span class="badge-partial">🟡 Partial Public Record</span></div>',
                unsafe_allow_html=True,
            )

    st.divider()

    # --- FULL DETAILED REPORT & EXPORT OPTIONS ---
    report_md = format_as_markdown(result)
    st.markdown(report_md)

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📥 Download JSON",
            data=to_json_string(result),
            file_name="property_report.json",
            mime="application/json",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            label="📥 Download Markdown",
            data=to_markdown_string(result),
            file_name="property_report.md",
            mime="text/markdown",
            use_container_width=True,
        )
