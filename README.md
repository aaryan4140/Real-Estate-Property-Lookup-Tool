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
├── app.py                      # Streamlit web application frontend and state manager
├── requirements.txt            # Python dependencies (Streamlit, Google GenAI, python-dotenv)
├── llm/
│   └── gemini_client.py        # Official Google GenAI Client wrapper & robust JSON decoder
├── prompts/
│   └── property_prompt.py      # 89-field real estate schema & extraction prompt
└── utils/
    ├── formatter.py            # Converts raw JSON into a categorized, 13-section Markdown report
    └── exporter.py             # Formats and saves property_report.json and property_report.md
```

---

## 🚀 Key Features

- **Interactive Executive Dashboard ([app.py](file:///Users/aaryantiwari/Desktop/My_Folder/Real_State/app.py)):** Features quick-select sample property chips for 1-click lookups, responsive hero KPI metric cards (Property Type, Building Area, Year Built, APN, Owner), and an assessment completeness progress meter with verification badges.
- **Enterprise LLM Integration ([llm/gemini_client.py](file:///Users/aaryantiwari/Desktop/My_Folder/Real_State/llm/gemini_client.py)):** Powered by Google's Gemini models using the official `google-genai` SDK, utilizing low temperature (`0.2`) for factual retrieval and schema conformity.
- **Fault-Tolerant JSON Parsing:** Custom streaming parser in [llm/gemini_client.py](file:///Users/aaryantiwari/Desktop/My_Folder/Real_State/llm/gemini_client.py) strips markdown code fences and uses `json.JSONDecoder().raw_decode()` to extract valid JSON even if accompanied by surrounding text.
- **Institutional 89-Field Schema ([prompts/property_prompt.py](file:///Users/aaryantiwari/Desktop/My_Folder/Real_State/prompts/property_prompt.py)):** Covers comprehensive property data ranging from basic parcel APNs and zoning to structural framing, HVAC, utilities, and flood panels.
- **Sectioned Markdown Presentation ([utils/formatter.py](file:///Users/aaryantiwari/Desktop/My_Folder/Real_State/utils/formatter.py)):** Organizes populated fields into 13 logical appraisal sections while omitting unverified fields to keep reports clean and readable.
- **Dual Format Export ([utils/exporter.py](file:///Users/aaryantiwari/Desktop/My_Folder/Real_State/utils/exporter.py)):** Provides one-click browser download buttons for both JSON and Markdown, while automatically persisting copies to the local `outputs/` folder.

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

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.10+
- Google Gemini API key configured in `.env` (`GEMINI_API_KEY=your_key`)

### Setup Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running the Application
Launch the Streamlit web application:
```bash
streamlit run app.py
```

Once running, navigate to the URL displayed in the terminal (typically `http://localhost:8501`) in your browser.

---

## 💻 Usage

1. Open the application in your browser.
2. Enter a property address in the input field (e.g., `2200 North Loop West, Houston, TX 77018` or `600 Montgomery St, San Francisco, CA 94111`).
3. Click **Search**.
4. Review the structured Markdown report generated on screen.
5. Use the download buttons to export the data:
   - **📥 Download JSON:** Full raw JSON object matching the 89-field schema.
   - **📥 Download Markdown:** Clean human-readable report.
