from __future__ import annotations

import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(override=True)

# Multi-model fallback list to guarantee 99.9% uptime
PREFERRED_MODELS = [
    os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-3.8-flash",
    "gemini-3.1-flash-lite",
]


def get_gemini_client() -> genai.Client:
    load_dotenv(override=True)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set. Please check your .env file.")
    return genai.Client(api_key=api_key)


def call_gemini_with_fallback(prompt: str, temperature: float = 0.2) -> str:
    """Execute model inference with automatic fallback across Gemini flash models."""
    client = get_gemini_client()
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

    raise RuntimeError(f"All Gemini models failed. Last error: {last_error}")
