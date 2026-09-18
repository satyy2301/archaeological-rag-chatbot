"""Jina embeddings v3 with retrieval task types."""

from typing import List, Optional

import requests

try:
    from langchain_core.embeddings import Embeddings
except ImportError:
    from langchain.embeddings.base import Embeddings

JINA_EMBEDDINGS_URL = "https://api.jina.ai/v1/embeddings"


class JinaV3Embeddings(Embeddings):
    """LangChain embeddings wrapper for Jina v3 retrieval tasks."""

    def __init__(
        self,
        api_key: str,
        model: str = "jina-embeddings-v3",
        timeout: int = 60,
    ):
        if not api_key:
            raise ValueError("JINA_API_KEY is required for hosted embeddings.")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def _embed(self, texts: List[str], task: str) -> List[List[float]]:
        response = requests.post(
            JINA_EMBEDDINGS_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "input": texts,
                "task": task,
            },
            timeout=self.timeout,
        )
        if not response.ok:
            raise RuntimeError(
                f"Jina embedding request failed ({response.status_code}): {response.text[:300]}"
            )
        payload = response.json()
        if "data" not in payload:
            detail = payload.get("detail", payload)
            raise RuntimeError(f"Jina embedding response missing data: {detail}")
        sorted_rows = sorted(payload["data"], key=lambda row: row["index"])
        return [row["embedding"] for row in sorted_rows]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._embed(texts, task="retrieval.passage")

    def embed_query(self, text: str) -> List[float]:
        return self._embed([text], task="retrieval.query")[0]
