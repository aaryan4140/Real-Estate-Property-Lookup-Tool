from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from utils.formatter import format_as_markdown

OUTPUTS_DIR = Path(__file__).resolve().parent.parent / "outputs"


def sanitize_filename(name: str) -> str:
    """Clean a string so it can be safely used as a filename across all OSes."""
    # Replace non-alphanumeric characters (except dashes and spaces)
    clean = re.sub(r"[^\w\s-]", "", name).strip()
    # Replace whitespace and repeated dashes with single underscores
    return re.sub(r"[-\s]+", "_", clean)


def get_unique_filepath(directory: Path, base_name: str, ext: str = "json") -> Path:
    """
    Generate a non-conflicting file path.
    If a file with base_name already exists, append a timestamp/counter so it is never overwritten.
    """
    directory.mkdir(exist_ok=True)
    target = directory / f"{base_name}.{ext}"
    if not target.exists():
        return target

    # File already exists: append timestamp to preserve historical runs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamp_target = directory / f"{base_name}_{timestamp}.{ext}"
    if not timestamp_target.exists():
        return timestamp_target

    # If even that exists (multiple runs in same second), append increment counter
    counter = 1
    while True:
        candidate = directory / f"{base_name}_{timestamp}_{counter}.{ext}"
        if not candidate.exists():
            return candidate
        counter += 1


def to_json_string(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


def to_markdown_string(data: dict[str, Any]) -> str:
    return format_as_markdown(data)


def save_to_outputs(
    data: dict[str, Any],
    property_name_or_address: str | None = None,
    suffix: str | None = None,
) -> Path:
    """
    Save single JSON report named after the property itself.
    Never overwrites existing files; creates a new unique file for each run.
    """
    OUTPUTS_DIR.mkdir(exist_ok=True)

    # 1. Determine base filename from property name or address
    raw_name = property_name_or_address or data.get("propertyName") or data.get("address") or "property_report"
    clean_base = sanitize_filename(raw_name)

    if suffix:
        clean_suffix = sanitize_filename(suffix)
        full_base = f"{clean_base}_{clean_suffix}"
    else:
        full_base = clean_base

    # 2. Get unique non-overwriting JSON path
    json_path = get_unique_filepath(OUTPUTS_DIR, full_base, ext="json")
    json_path.write_text(to_json_string(data) + "\n", encoding="utf-8")

    # 3. Markdown (.md) generation is commented out as requested.
    # Can be re-enabled whenever needed:
    # md_path = json_path.with_suffix(".md")
    # md_path.write_text(to_markdown_string(data) + "\n", encoding="utf-8")

    return json_path
