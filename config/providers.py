"""Provider resolution for hosted vs BYOK model backends."""

from dataclasses import dataclass
from typing import Literal, Optional

JINA_EMBEDDING_MODEL = "jina-embeddings-v3"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
GEMINI_LLM_MODEL = "gemini-3.6-flash"
OPENAI_LLM_MODEL = "gpt-3.5-turbo"
PROVIDER_META_FILENAME = "provider_meta.json"


@dataclass(frozen=True)
class ProviderConfig:
    mode: Literal["hosted", "byok"]
    embedding_backend: Literal["jina", "openai"]
    llm_backend: Literal["gemini", "openai"]
    embedding_model: str
    llm_model: str
    openai_api_key: Optional[str] = None


def resolve_provider(user_openai_key: Optional[str]) -> ProviderConfig:
    """Return BYOK OpenAI config when user key present, else hosted Jina+Gemini."""
    if user_openai_key and user_openai_key.strip():
        return ProviderConfig(
            mode="byok",
            embedding_backend="openai",
            llm_backend="openai",
            embedding_model=OPENAI_EMBEDDING_MODEL,
            llm_model=OPENAI_LLM_MODEL,
            openai_api_key=user_openai_key.strip(),
        )
    return ProviderConfig(
        mode="hosted",
        embedding_backend="jina",
        llm_backend="gemini",
        embedding_model=JINA_EMBEDDING_MODEL,
        llm_model=GEMINI_LLM_MODEL,
        openai_api_key=None,
    )
