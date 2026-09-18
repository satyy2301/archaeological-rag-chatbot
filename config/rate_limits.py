"""Session rate limits for hosted (free) tier."""

from typing import Optional

from config.providers import ProviderConfig

HOSTED_MAX_CHAT = 20
HOSTED_MAX_INDEX = 1
HOSTED_MAX_PAGES = 50


def _is_byok(provider: ProviderConfig) -> bool:
    return provider.mode == "byok"


def init_rate_limit_state(session_state) -> None:
    """Ensure rate-limit counters exist in Streamlit session state."""
    if "hosted_chat_count" not in session_state:
        session_state.hosted_chat_count = 0
    if "hosted_index_count" not in session_state:
        session_state.hosted_index_count = 0


def remaining_chat(session_state, provider: ProviderConfig) -> Optional[int]:
    """Return remaining hosted chat quota, or None for BYOK."""
    if _is_byok(provider):
        return None
    init_rate_limit_state(session_state)
    return max(0, HOSTED_MAX_CHAT - session_state.hosted_chat_count)


def can_chat(session_state, provider: ProviderConfig) -> bool:
    if _is_byok(provider):
        return True
    init_rate_limit_state(session_state)
    return session_state.hosted_chat_count < HOSTED_MAX_CHAT


def record_chat(session_state, provider: ProviderConfig) -> None:
    if _is_byok(provider):
        return
    init_rate_limit_state(session_state)
    session_state.hosted_chat_count += 1


def can_index(session_state, provider: ProviderConfig) -> bool:
    if _is_byok(provider):
        return True
    init_rate_limit_state(session_state)
    return session_state.hosted_index_count < HOSTED_MAX_INDEX


def record_index(session_state, provider: ProviderConfig) -> None:
    """Increment hosted index count. Skip for BYOK and provider-switch re-index."""
    if _is_byok(provider):
        return
    init_rate_limit_state(session_state)
    session_state.hosted_index_count += 1


def check_page_limit(page_count: int, provider: ProviderConfig, max_pages: int = HOSTED_MAX_PAGES) -> bool:
    """Return True if page count is within hosted limit."""
    if _is_byok(provider):
        return True
    if page_count <= 0:
        return True
    return page_count <= max_pages
