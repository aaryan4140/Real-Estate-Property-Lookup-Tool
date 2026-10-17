from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

from prompts.property_prompt import build_prompt

load_dotenv()

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")


def get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set. Please check your .env file.")
    return genai.Client(api_key=api_key)


def search_property(address: str) -> dict[str, Any]:
    """Single LLM call via official Google GenAI to fetch property data."""
    client = get_client()
    prompt = build_prompt(address)

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
        ),
    )
    response_text = response.text or ""
    return _parse_json(response_text)


def _parse_json(text: str) -> dict[str, Any]:
    """Extract the first JSON object from the response text."""
    if not text.strip():
        raise ValueError("Gemini returned an empty response.")

    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)

    decoder = json.JSONDecoder()
    for i, ch in enumerate(cleaned):
        if ch == "{":
            try:
                obj, _ = decoder.raw_decode(cleaned[i:])
                if isinstance(obj, dict):
                    return obj
            except json.JSONDecodeError:
                continue

    raise ValueError("Gemini response did not contain a valid JSON object.")
