from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

from prompts.property_prompt import PROPERTY_SCHEMA_FIELDS, build_prompt

load_dotenv()

PREFERRED_MODELS = [
    os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
    "gemini-flash-latest",
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash",
]


def get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set. Please check your .env file.")
    return genai.Client(api_key=api_key)


def _call_baseline_model(prompt: str, temperature: float = 0.2) -> str:
    client = get_client()
    last_error: Exception | None = None
    for model_name in PREFERRED_MODELS:
        try:
            resp = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                ),
            )
            if resp.text:
                return resp.text
        except Exception as e:
            last_error = e
            continue
    raise RuntimeError(f"All Gemini models failed in baseline client: {last_error}")


def search_property_baseline(address: str) -> dict[str, Any]:
    """
    Baseline Solution: Direct Gemini LLM synthesis using model memory/training knowledge.
    Fast, single-call, but does not use external search APIs.
    """
    clean_address = address.strip()
    prompt = build_prompt(clean_address)
    raw_response = _call_baseline_model(prompt, temperature=0.2)
    data = _parse_json(raw_response)

    # Standardize schema keys
    for field in PROPERTY_SCHEMA_FIELDS:
        if field not in data:
            data[field] = None

    if not data.get("address"):
        data["address"] = clean_address

    data["_engine"] = "Baseline (Pure Gemini Synthesis)"
    return data


def _parse_json(text: str) -> dict[str, Any]:
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

    raise ValueError("Baseline response did not contain a valid JSON object.")
