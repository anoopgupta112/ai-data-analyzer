import os
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()


class OpenRouterError(Exception):
    """Raised when an OpenRouter call fails or returns an unexpected shape."""


API_KEY = os.getenv("OPENROUTER_API_KEY")
DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL", "amazon/nova-2-lite-v1:free")
DEFAULT_MAX_TOKENS = int(os.getenv("OPENROUTER_MAX_TOKENS", "2048"))
BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")
HTTP_REFERER = os.getenv("OPENROUTER_HTTP_REFERER", "http://localhost")
APP_TITLE = os.getenv("OPENROUTER_TITLE", "AI Data Analyzer")


def complete_chat(
    prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: Optional[int] = None,
) -> str:
    """Send a single-turn chat completion request to OpenRouter."""
    if not API_KEY:
        raise OpenRouterError("OPENROUTER_API_KEY is not configured.")

    payload = {
        "model": model or DEFAULT_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens or DEFAULT_MAX_TOKENS,
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": HTTP_REFERER,
        "X-Title": APP_TITLE,
    }

    resp = requests.post(BASE_URL, headers=headers, json=payload, timeout=60)
    if resp.status_code != 200:
        raise OpenRouterError(f"OpenRouter request failed ({resp.status_code}): {resp.text}")

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise OpenRouterError("OpenRouter response missing completion text.") from exc
