from __future__ import annotations

from typing import Any

from prompts.property_prompt import PROPERTY_SCHEMA_FIELDS

SECTION_MAP = {
    "Property Overview": [
        "property apn", "parcelId", "propertyType", "propertySubtype",
        "propertyUse", "propertyName", "propertyDescription",
    ],
    "Location & Address": [
        "address", "city", "state", "postalCode", "county",
        "latitude", "longitude", "locationDescription", "locationType",
    ],
    "Owner & Legal": [
        "owner name", "ownership", "legalDescription",
    ],
    "Building Details": [
        "yearBuilt", "remodeledYear", "buildingAreaSqft", "numberOfBuildings",
        "numberOfStories", "numberOfUnits", "netRentableAreaSqft",
        "averageUnitSizeSqft", "buildingClass", "constructionClass",
    ],
    "Construction & Systems": [
        "foundation", "frame", "exteriorWall", "roof", "roofAgeYears",
        "interiorWall", "interiorFlooring", "lighting", "ceiling",
        "heating", "cooling", "plumbingElectrical", "fireSafety",
        "elevators", "restrooms", "sprinklers",
    ],
    "Condition & Age": [
        "condition", "physicalCondition", "physicalConditionBasedUpon",
        "actualAge", "effectiveAge", "remainingEconomicLife",
    ],
    "Land & Parcel": [
        "siteAreaAcres", "parcelSizeAcres", "usableLandAreaAcres",
        "excessLand", "surplusLand", "frontage", "frontageJson",
        "shape", "access",
    ],
    "Zoning": [
        "zoning", "zoningCode", "zoningDescription", "zoningAuthority",
        "municipality zoning", "legalPermissibility",
    ],
    "Utilities": [
        "water", "sewer", "electric", "gas", "telephone",
    ],
    "Flood & Environmental": [
        "floodMapPanel", "femaFloodplain", "floodMapDate", "easements",
    ],
    "Parking": [
        "parking", "parkingType", "numberOfParkingSpaces",
    ],
    "Occupancy": [
        "occupancyType", "occupancyPercent", "rentLossAnalysisNonStabilized",
    ],
    "Valuation & Highest Best Use": [
        "asVacant", "asImproved", "otherUseConsidered",
        "physicalFeasibility", "financialFeasibility", "maximumProductivity",
    ],
}


def _format_key(key: str) -> str:
    return key.replace("_", " ").replace("Sqft", " (sqft)").replace("Acres", " (acres)").title()


def format_as_markdown(data: dict[str, Any]) -> str:
    """Convert property JSON into a ChatGPT-style readable markdown report."""
    address = data.get("address") or "Unknown Property"
    lines = [f"# Property Report: {address}", ""]

    for section_title, fields in SECTION_MAP.items():
        section_entries = []
        for field in fields:
            value = data.get(field)
            if value is not None:
                section_entries.append(f"- **{_format_key(field)}**: {value}")

        if section_entries:
            lines.append(f"## {section_title}")
            lines.extend(section_entries)
            lines.append("")

    sources = data.get("sources") or []
    if sources:
        lines.append("## Sources")
        for url in sources:
            lines.append(f"- {url}")
        lines.append("")

    null_fields = [f for f in PROPERTY_SCHEMA_FIELDS if f != "sources" and data.get(f) is None]
    if null_fields:
        lines.append("---")
        lines.append(f"*{len(null_fields)} fields could not be verified from available sources and were omitted.*")
        lines.append("")

    return "\n".join(lines)
