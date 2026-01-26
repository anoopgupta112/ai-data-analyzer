"""
Unified AI Client Router

This module routes AI completion requests to either OpenRouter or Gemini
based on the USE_GEMINI environment variable.
"""

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# Check which client to use
USE_GEMINI = os.getenv("USE_GEMINI", "false").lower() in ("true", "1", "yes")


class AIClientError(Exception):
    """Raised when an AI client call fails."""


def complete_chat(
    prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: Optional[int] = None,
) -> str:
    """
    Send a chat completion request to the configured AI provider.
    
    Args:
        prompt: The user prompt to send
        model: Optional model name (provider-specific)
        temperature: Sampling temperature (0.0 to 1.0)
        max_tokens: Maximum tokens in response
        
    Returns:
        The AI-generated text response
        
    Raises:
        AIClientError: If the request fails
    """
    if USE_GEMINI:
        try:
            from app.services import gemini_client
            return gemini_client.complete_chat(prompt, model, temperature, max_tokens)
        except Exception as exc:
            raise AIClientError(f"Gemini client error: {exc}") from exc
    else:
        try:
            from app.services import openrouter_client
            return openrouter_client.complete_chat(prompt, model, temperature, max_tokens)
        except Exception as exc:
            raise AIClientError(f"OpenRouter client error: {exc}") from exc


def get_current_provider() -> str:
    """Returns the name of the currently active AI provider."""
    return "Gemini" if USE_GEMINI else "OpenRouter"
