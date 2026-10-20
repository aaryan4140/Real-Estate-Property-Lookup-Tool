from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from utils.formatter import format_as_markdown

OUTPUTS_DIR = Path(__file__).resolve().parent.parent / "outputs"


def to_json_string(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


def to_markdown_string(data: dict[str, Any]) -> str:
    return format_as_markdown(data)


def save_to_outputs(data: dict[str, Any], filename_prefix: str = "property_report") -> None:
    """Save formatted JSON and Markdown reports to outputs folder."""
    OUTPUTS_DIR.mkdir(exist_ok=True)
    json_path = OUTPUTS_DIR / f"{filename_prefix}.json"
    md_path = OUTPUTS_DIR / f"{filename_prefix}.md"
    json_path.write_text(to_json_string(data) + "\n", encoding="utf-8")
    md_path.write_text(to_markdown_string(data) + "\n", encoding="utf-8")
