"""Tests for provider resolution."""

from config.providers import (
    GEMINI_LLM_MODEL,
    JINA_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    OPENAI_LLM_MODEL,
    resolve_provider,
)


def test_resolve_provider_hosted_when_no_user_key():
    provider = resolve_provider(None)
    assert provider.mode == "hosted"
    assert provider.embedding_backend == "jina"
    assert provider.llm_backend == "gemini"
    assert provider.embedding_model == JINA_EMBEDDING_MODEL
    assert provider.llm_model == GEMINI_LLM_MODEL
    assert provider.openai_api_key is None


def test_resolve_provider_hosted_when_blank_user_key():
    provider = resolve_provider("   ")
    assert provider.mode == "hosted"


def test_resolve_provider_byok_when_user_key_present():
    provider = resolve_provider("sk-test-key")
    assert provider.mode == "byok"
    assert provider.embedding_backend == "openai"
    assert provider.llm_backend == "openai"
    assert provider.embedding_model == OPENAI_EMBEDDING_MODEL
    assert provider.llm_model == OPENAI_LLM_MODEL
    assert provider.openai_api_key == "sk-test-key"
