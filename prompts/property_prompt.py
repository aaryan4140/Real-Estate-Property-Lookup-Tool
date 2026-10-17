PROPERTY_SCHEMA_FIELDS = [
    "property apn",
    "propertyType",
    "propertySubtype",
    "county",
    "propertyUse",
    "propertyName",
    "address",
    "yearBuilt",
    "siteAreaAcres",
    "buildingAreaSqft",
    "owner name",
    "ownership",
    "municipality zoning",
    "constructionClass",
    "condition",
    "parking",
    "numberOfUnits",
    "netRentableAreaSqft",
    "averageUnitSizeSqft",
    "legalDescription",
    "parcelId",
    "city",
    "state",
    "postalCode",
    "latitude",
    "longitude",
    "locationDescription",
    "frontage",
    "shape",
    "access",
    "parcelSizeAcres",
    "usableLandAreaAcres",
    "excessLand",
    "surplusLand",
    "zoning",
    "zoningAuthority",
    "zoningCode",
    "zoningDescription",
    "water",
    "sewer",
    "electric",
    "gas",
    "telephone",
    "floodMapPanel",
    "femaFloodplain",
    "floodMapDate",
    "easements",
    "asVacant",
    "asImproved",
    "otherUseConsidered",
    "legalPermissibility",
    "physicalFeasibility",
    "financialFeasibility",
    "maximumProductivity",
    "locationType",
    "frontageJson",
    "propertyDescription",
    "foundation",
    "frame",
    "exteriorWall",
    "roof",
    "roofAgeYears",
    "interiorWall",
    "interiorFlooring",
    "lighting",
    "ceiling",
    "heating",
    "cooling",
    "plumbingElectrical",
    "fireSafety",
    "elevators",
    "restrooms",
    "buildingClass",
    "occupancyType",
    "occupancyPercent",
    "rentLossAnalysisNonStabilized",
    "numberOfBuildings",
    "numberOfStories",
    "remodeledYear",
    "physicalCondition",
    "physicalConditionBasedUpon",
    "actualAge",
    "effectiveAge",
    "remainingEconomicLife",
    "parkingType",
    "numberOfParkingSpaces",
    "sprinklers",
    "sources",
]


PROPERTY_LOOKUP_PROMPT = """You are a real estate property research assistant. Given a property address,
search the internet and find as much factual information as possible about this property.

PROPERTY ADDRESS: {address}

Your task:
1. Search for this property on official county appraisal district (CAD) websites, property tax records,
   and other authoritative public sources.
2. Extract all available property details.
3. Return ONLY a valid JSON object with the fields listed below.
4. Use null for any field you cannot verify from search results. Do NOT guess or fabricate values.
5. The "sources" field must be a list of URLs you actually found information from.

IMPORTANT RULES:
- Prefer official government sources (county assessor, appraisal district, tax records).
- Do not invent or hallucinate any data. If a field is not found, use null.
- Do not use general knowledge to fill fields — only use data from search results.
- Return raw JSON only. No markdown fences, no explanatory text outside the JSON.

JSON FIELDS TO POPULATE:
{schema_fields}

Return the JSON object now.
"""


def build_prompt(address: str) -> str:
    fields_str = ", ".join(f'"{f}"' for f in PROPERTY_SCHEMA_FIELDS)
    return PROPERTY_LOOKUP_PROMPT.format(address=address.strip(), schema_fields=fields_str)
