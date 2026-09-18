"""Tests for hosted session rate limits."""

from config.providers import resolve_provider
from config.rate_limits import (
    HOSTED_MAX_CHAT,
    HOSTED_MAX_INDEX,
    HOSTED_MAX_PAGES,
    can_chat,
    can_index,
    check_page_limit,
    record_chat,
    record_index,
    remaining_chat,
)


class _SessionState(dict):
    """Minimal session-state stand-in for tests."""

    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        self[name] = value


def test_hosted_chat_limit_blocks_at_ceiling():
    state = _SessionState()
    provider = resolve_provider(None)

    assert can_chat(state, provider) is True
    for _ in range(HOSTED_MAX_CHAT):
        record_chat(state, provider)
    assert can_chat(state, provider) is False
    assert remaining_chat(state, provider) == 0


def test_hosted_index_limit_blocks_at_ceiling():
    state = _SessionState()
    provider = resolve_provider(None)

    assert can_index(state, provider) is True
    record_index(state, provider)
    assert can_index(state, provider) is False


def test_hosted_page_limit_enforced():
    provider = resolve_provider(None)
    assert check_page_limit(HOSTED_MAX_PAGES, provider) is True
    assert check_page_limit(HOSTED_MAX_PAGES + 1, provider) is False


def test_byok_bypasses_limits():
    state = _SessionState()
    provider = resolve_provider("sk-test")

    for _ in range(HOSTED_MAX_CHAT + 5):
        record_chat(state, provider)
    for _ in range(HOSTED_MAX_INDEX + 5):
        record_index(state, provider)

    assert can_chat(state, provider) is True
    assert can_index(state, provider) is True
    assert check_page_limit(HOSTED_MAX_PAGES + 100, provider) is True
    assert remaining_chat(state, provider) is None


def test_provider_switch_reindex_does_not_consume_extra_hosted_index_slot():
    """First upload uses the hosted index slot; provider-switch re-index skips record_index."""
    state = _SessionState()
    provider = resolve_provider(None)

    record_index(state, provider)
    assert state.hosted_index_count == HOSTED_MAX_INDEX
    assert can_index(state, provider) is False
    # Provider-switch path bypasses can_index/record_index; count must stay at 1.
    assert state.hosted_index_count == 1
