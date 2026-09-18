"""Load server-side API keys from Streamlit secrets or environment variables."""

import os
from typing import List, Optional


def _get_setting(name: str) -> Optional[str]:
    """Read a secret from Streamlit secrets or os.environ."""
    value = os.getenv(name, "").strip()
    try:
        import streamlit as st

        if name in st.secrets:
            secret_value = str(st.secrets[name]).strip()
            if secret_value:
                return secret_value
    except Exception:
        pass
    return value or None


def get_jina_api_key() -> Optional[str]:
    """Return hosted Jina API key."""
    return _get_setting("JINA_API_KEY")


def get_gemini_api_keys() -> List[str]:
    """Return non-empty Gemini API keys for rotation."""
    keys: List[str] = []
    for name in ("GEMINI_API_KEY_1", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3"):
        key = _get_setting(name)
        if key:
            keys.append(key)
    return keys


def get_user_openai_key(session_key: Optional[str]) -> Optional[str]:
    """Return sidebar OpenAI key only; never read owner key from env."""
    if session_key and session_key.strip():
        return session_key.strip()
    return None


def hosted_keys_available() -> bool:
    """True when both Jina and at least one Gemini key are configured."""
    return bool(get_jina_api_key() and get_gemini_api_keys())
