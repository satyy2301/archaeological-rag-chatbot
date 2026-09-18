"""Gemini chat LLM with API-key rotation on quota errors."""

import logging
from typing import List

from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)


class HostedLimitExceeded(Exception):
    """Raised when all hosted Gemini keys are exhausted."""


def build_rotating_gemini_llm(
    api_keys: List[str],
    model_name: str = "gemini-3.6-flash",
    temperature: float = 0.7,
):
    """Build a Gemini chat model that falls back across multiple API keys."""
    if not api_keys:
        raise ValueError("No Gemini API keys configured for hosted chat.")

    llms = [
        ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            google_api_key=key,
        )
        for key in api_keys
    ]
    if len(llms) == 1:
        return llms[0]
    logger.info("Configured Gemini chat with %s rotating API keys.", len(llms))
    return llms[0].with_fallbacks(llms[1:])
