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


def save_to_outputs(data: dict[str, Any]) -> None:
    """Clear the outputs folder and save fresh JSON + MD files."""
    OUTPUTS_DIR.mkdir(exist_ok=True)
    for f in OUTPUTS_DIR.iterdir():
        if f.is_file():
            f.unlink()
    (OUTPUTS_DIR / "property_report.json").write_text(to_json_string(data) + "\n", encoding="utf-8")
    (OUTPUTS_DIR / "property_report.md").write_text(to_markdown_string(data) + "\n", encoding="utf-8")
