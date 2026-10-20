# 🏠 Real Estate Property Lookup Tool

An AI-powered real estate property intelligence and public records extraction tool built with **Streamlit**, **Google Gemini API (`google-genai`)**, and a modular Python architecture.

The tool enables users to enter a property address, queries Gemini to retrieve factual property appraisal records mapped to an institutional 89-field real estate schema, renders a structured Markdown report across 13 intuitive categories, and supports automated exports in both JSON and Markdown formats.

---

## 📌 Architecture Overview

```
                        ┌────────────────────────┐
                        │   User Web Interface   │
                        │        (app.py)        │
                        └───────────┬────────────┘
                                    │
                                    ▼
                        ┌────────────────────────┐
                        │     Prompt Engine      │
                        │ (property_prompt.py)   │
                        └───────────┬────────────┘
                                    │
                                    ▼
                        ┌────────────────────────┐
                        │     LLM Connector      │
                        │   (gemini_client.py)   │
                        │   [gemini-2.5-flash]   │
                        └───────────┬────────────┘
                                    │
                     ┌──────────────┴──────────────┐
                     ▼                             ▼
        ┌─────────────────────────┐   ┌─────────────────────────┐
        │    Report Formatter     │   │      Export Engine      │
        │     (formatter.py)      │   │      (exporter.py)      │
        │  13 Structured Sections │   │   Saves to outputs/     │
        └─────────────────────────┘   └─────────────────────────┘
```

---

## 📂 Active Project Structure

```
Real_State/
├── app.py                      # Streamlit web application with multi-engine selection & comparative matrix
├── requirements.txt            # Python dependencies (Streamlit, Google GenAI, python-dotenv, pandas)
├── .env.example                # Environment variables template (copy to .env)
├── .gitignore                  # Git exclusions (.env, private docs, outputs, cache)
├── llm/
│   ├── gemini_baseline.py      # Baseline Engine: Direct Gemini LLM synthesis (pure memory)
│   ├── serper_agent_client.py  # Serper Engine: Live Google Search + Dual-Agent Compliance Audit
│   └── gemini_client.py        # Centralized client dispatcher
├── prompts/
│   └── property_prompt.py      # 89-field real estate schema & extraction prompt
└── utils/
    ├── search_engine.py        # Multi-cluster Google search scraper via Serper API
    ├── formatter.py            # Converts raw JSON into a categorized, 13-section Markdown report
    └── exporter.py             # Formats and saves JSON and Markdown reports with custom prefixes
```

---

## 🚀 Key Features

- **Multi-Engine Intelligence & Side-by-Side Comparison ([app.py](file:///Users/aaryantiwari/Desktop/My_Folder/Real_State/app.py)):** Switch seamlessly between the **Baseline Engine** (pure Gemini memory synthesis) and the **Serper-Powered Dual-Agent Engine** (live Google search + zero-temperature compliance audit), or run both concurrently to view an interactive side-by-side delta matrix.
- **Dual-Agent Verification Pipeline:** Agent 1 (The Extractor) maps live Google search snippets into the 89-field schema, while Agent 2 (The Compliance Auditor at `temperature=0.0`) cross-examines every number against the raw web text to eliminate hallucinations.
- **Multi-Cluster Live Search ([utils/search_engine.py](file:///Users/aaryantiwari/Desktop/My_Folder/Real_State/utils/search_engine.py)):** Scrapes data across 3 targeted clusters (CAD tax rolls, commercial offering brochures, municipal zoning & FEMA maps) via Serper.
- **Interactive Executive Dashboard:** Features quick-select sample property chips for 1-click lookups, responsive hero KPI metric cards (Property Type, Building Area, Year Built, APN, Owner), and an assessment completeness progress meter with verification badges.
- **Independent Dual-Format Exports:** Download distinct, timestamped reports (`property_report_baseline.json/.md` vs `property_report_serper_audited.json/.md`) with automated local persistence in `outputs/`.

---

## 📊 13 Appraisal Report Sections

[utils/formatter.py](file:///Users/aaryantiwari/Desktop/My_Folder/Real_State/utils/formatter.py) groups the 89 schema fields into the following structured categories:

| Section | Included Attributes |
| :--- | :--- |
| **1. Property Overview** | APN, Parcel ID, Property Type, Subtype, Use, Name, Description |
| **2. Location & Address** | Street Address, City, State, ZIP, County, Latitude, Longitude, Location Description/Type |
| **3. Owner & Legal** | Owner Name, Ownership Type, Legal Description |
| **4. Building Details** | Year Built, Remodeled Year, Building Area (sqft), Buildings, Stories, Units, Net Rentable Area, Building Class |
| **5. Construction & Systems** | Foundation, Frame, Exterior Walls, Roof & Age, Interior Walls & Flooring, HVAC, Plumbing/Electrical, Fire Safety, Elevators, Sprinklers |
| **6. Condition & Age** | Condition, Physical Condition, Actual Age, Effective Age, Remaining Economic Life |
| **7. Land & Parcel** | Site Area (acres), Parcel Size, Usable Land, Excess/Surplus Land, Frontage, Shape, Access |
| **8. Zoning** | Zoning Code, Description, Authority, Municipal Zoning, Legal Permissibility |
| **9. Utilities** | Water, Sewer, Electric, Gas, Telephone |
| **10. Flood & Environmental** | FEMA Floodplain, Flood Map Panel, Flood Map Date, Easements |
| **11. Parking** | Parking Type, Number of Parking Spaces |
| **12. Occupancy** | Occupancy Type, Occupancy Percentage, Rent Loss Analysis |
| **13. Valuation & Highest Best Use** | As Vacant, As Improved, Other Uses Considered, Financial/Physical Feasibility, Maximum Productivity |

---

## 🛡️ Data Integrity & Guardrails

- **Strict `null` Preservation:** The prompt explicitly instructs the model to use `null` for any field that cannot be verified against official assessment records. Guessing or fabricating data is strictly prohibited.
- **Clean Omission Reporting:** Fields returned as `null` are excluded from the user-facing report to avoid visual clutter, and a summary disclaimer at the bottom of the report states the exact number of omitted unverified fields.
- **Source Transparency:** Extracted sources and reference links are captured in the `sources` field and rendered in a dedicated section at the bottom of each report.

---

## 🛠️ Step-by-Step Installation & Setup

Follow these exact steps to set up and run the project locally:

### 1. Clone the Repository
```bash
git clone https://github.com/aaryan4140/Real-Estate-Property-Lookup-Tool.git
cd Real-Estate-Property-Lookup-Tool
```

### 2. Create and Activate Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```
*(On Windows: `venv\Scripts\activate`)*

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables (`.env.example` ➔ `.env`)
> [!IMPORTANT]
> For security reasons, the actual `.env` file containing private API keys is **excluded from Git tracking via `.gitignore`** and is not committed to the repository.
> 
> A template file named [`.env.example`](file:///.env.example) is provided. You **must create your local `.env` file** by copying it:

```bash
cp .env.example .env
```

Now, open `.env` in any text editor and replace the placeholder with your actual **Google Gemini API Key**:
```env
GEMINI_API_KEY=AIzaSy...your_actual_api_key_here
```
*(You can generate a free Gemini API key at [Google AI Studio](https://aistudio.google.com/)).*

### 5. Run the Application
Launch the interactive Streamlit dashboard:
```bash
streamlit run app.py
```

Once running, the application will be accessible in your web browser at:
`http://localhost:8501`

---

## 💻 How to Use

1. **Enter Address:** Type any US property address into the search input (e.g. `2200 North Loop West, Houston, TX 77018`).
2. **One-Click Testing:** Alternatively, click any of the **Quick Sample Lookup** buttons (Houston, San Francisco, Lubbock) to test benchmark properties instantly.
3. **Analyze Dashboard:** Review the top **Hero KPI Cards** (Property Type, Building Area, Year Built, APN, Owner) and the **Assessment Record Completeness Meter**.
4. **Read Report:** Scroll through the structured 13-section appraisal report.
5. **Export Data:** Click **📥 Download JSON** for the full 89-field payload or **📥 Download Markdown** for the clean formatted dossier.

