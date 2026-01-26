import os
from typing import Optional

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


class GeminiError(Exception):
    """Raised when a Gemini API call fails or returns an unexpected shape."""


API_KEY = os.getenv("GEMINI_API_KEY")
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
DEFAULT_MAX_TOKENS = int(os.getenv("GEMINI_MAX_TOKENS", "2048"))


def complete_chat(
    prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: Optional[int] = None,
) -> str:
    """Send a single-turn chat completion request to Gemini."""
    if not API_KEY:
        raise GeminiError("GEMINI_API_KEY is not configured.")

    # Configure Gemini API
    genai.configure(api_key=API_KEY)

    # Initialize the model
    model_name = model or DEFAULT_MODEL
    generation_config = {
        "temperature": temperature,
        "max_output_tokens": max_tokens or DEFAULT_MAX_TOKENS,
    }

    try:
        model_instance = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config,
        )

        # Generate response
        response = model_instance.generate_content(prompt)

        # Extract text from response
        if not response.text:
            raise GeminiError("Gemini response is empty.")

        return response.text

    except Exception as exc:
        raise GeminiError(f"Gemini API request failed: {exc}") from exc
