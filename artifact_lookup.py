"""
Lightweight external artifact lookup helpers.

Uses public APIs where possible so the deployed app can suggest similar finds
without shipping large local reference datasets.
"""

from __future__ import annotations

import logging
import os
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class ArtifactLookupClient:
    """Search lightweight public collections for similar artifacts."""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "archaeological-rag-chatbot/1.0",
                "Accept": "application/json",
            }
        )

    def search_similar_finds(self, query: str, context: Optional[Dict] = None, limit: int = 6) -> List[Dict]:
        """Aggregate and normalize results from lightweight public sources."""
        if not query.strip():
            return []

        results: List[Dict] = []
        results.extend(self._search_met(query, limit=max(2, limit // 2)))
        results.extend(self._search_wikidata(query, limit=max(2, limit // 2)))

        europeana_key = os.getenv("EUROPEANA_API_KEY", "").strip()
        if europeana_key:
            results.extend(self._search_europeana(query, europeana_key, limit=max(2, limit // 2)))

        # Deduplicate by url/title while preserving order.
        seen = set()
        deduped = []
        for item in results:
            key = (item.get("source", ""), item.get("url", ""), item.get("title", ""))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)

        return deduped[:limit]

    def _search_met(self, query: str, limit: int = 3) -> List[Dict]:
        try:
            search_resp = self.session.get(
                "https://collectionapi.metmuseum.org/public/collection/v1/search",
                params={"q": query, "hasImages": "true"},
                timeout=self.timeout,
            )
            search_resp.raise_for_status()
            payload = search_resp.json()
            object_ids = (payload or {}).get("objectIDs") or []
            results = []
            for object_id in object_ids[:limit]:
                detail_resp = self.session.get(
                    f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{object_id}",
                    timeout=self.timeout,
                )
                detail_resp.raise_for_status()
                obj = detail_resp.json()
                results.append(
                    {
                        "source": "The Met",
                        "title": obj.get("title") or f"Object {object_id}",
                        "description": obj.get("culture") or obj.get("period") or obj.get("medium") or "Museum collection record",
                        "url": obj.get("objectURL") or "",
                        "image_url": obj.get("primaryImageSmall") or obj.get("primaryImage") or "",
                        "date": obj.get("objectDate") or "",
                        "material": obj.get("medium") or "",
                    }
                )
            return results
        except Exception as exc:  # pragma: no cover - network dependent
            logger.info("Met lookup unavailable: %s", exc)
            return []

    def _search_wikidata(self, query: str, limit: int = 3) -> List[Dict]:
        try:
            response = self.session.get(
                "https://www.wikidata.org/w/api.php",
                params={
                    "action": "wbsearchentities",
                    "format": "json",
                    "language": "en",
                    "type": "item",
                    "limit": limit,
                    "search": query,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
            results = []
            for item in payload.get("search", []):
                results.append(
                    {
                        "source": "Wikidata",
                        "title": item.get("label") or item.get("id") or "Wikidata item",
                        "description": item.get("description") or "Linked open data result",
                        "url": item.get("concepturi") or "",
                        "image_url": "",
                        "date": "",
                        "material": "",
                    }
                )
            return results
        except Exception as exc:  # pragma: no cover - network dependent
            logger.info("Wikidata lookup unavailable: %s", exc)
            return []

    def _search_europeana(self, query: str, api_key: str, limit: int = 3) -> List[Dict]:
        try:
            response = self.session.get(
                "https://api.europeana.eu/record/v2/search.json",
                params={
                    "wskey": api_key,
                    "query": query,
                    "rows": limit,
                    "media": "true",
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
            results = []
            for item in payload.get("items", []):
                title = (item.get("title") or [""])[0]
                desc = (item.get("dcDescription") or [""])[0]
                image_url = (item.get("edmPreview") or [""])[0]
                guid = item.get("guid") or ""
                results.append(
                    {
                        "source": "Europeana",
                        "title": title or "Europeana result",
                        "description": desc or "Europeana collection record",
                        "url": guid,
                        "image_url": image_url,
                        "date": "",
                        "material": "",
                    }
                )
            return results
        except Exception as exc:  # pragma: no cover - network dependent
            logger.info("Europeana lookup unavailable: %s", exc)
            return []
