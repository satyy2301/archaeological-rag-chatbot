"""
Vector Store Module for RAG System
Creates and manages embeddings and vector database
"""

import json
import os
from typing import List, Optional, Dict, Union
import time
from langchain_openai import OpenAIEmbeddings
try:
    from langchain_community.vectorstores import FAISS
except ImportError:
    from langchain.vectorstores import FAISS

# Handle LangChain version differences
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
    except ImportError:
        raise ImportError("Could not import RecursiveCharacterTextSplitter. Please install langchain-text-splitters: pip install langchain-text-splitters")

try:
    from langchain_core.documents import Document
except ImportError:
    try:
        from langchain.schema import Document
    except ImportError:
        raise ImportError("Could not import Document. Please install langchain-core: pip install langchain-core")

from config.providers import PROVIDER_META_FILENAME, ProviderConfig
from config.secrets import get_jina_api_key
from embeddings.jina_v3 import JinaV3Embeddings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _build_embeddings(provider: ProviderConfig):
    """Create embedding client for the active provider."""
    if provider.embedding_backend == "jina":
        api_key = get_jina_api_key()
        if not api_key:
            raise ValueError(
                "JINA_API_KEY not found. Set it in .env or Streamlit secrets for the free plan."
            )
        return JinaV3Embeddings(api_key=api_key, model=provider.embedding_model)

    if not provider.openai_api_key:
        raise ValueError("OpenAI API key is required for BYOK embeddings.")
    return OpenAIEmbeddings(
        model=provider.embedding_model,
        openai_api_key=provider.openai_api_key,
    )


def _provider_meta_path(persist_directory: str) -> str:
    return os.path.join(persist_directory, PROVIDER_META_FILENAME)


def _write_provider_meta(persist_directory: str, provider: ProviderConfig) -> None:
    meta = {
        "provider": provider.embedding_backend,
        "embedding_model": provider.embedding_model,
        "mode": provider.mode,
    }
    with open(_provider_meta_path(persist_directory), "w", encoding="utf-8") as handle:
        json.dump(meta, handle, indent=2)


def _read_provider_meta(persist_directory: str) -> Optional[Dict[str, str]]:
    path = _provider_meta_path(persist_directory)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _validate_provider_meta(persist_directory: str, provider: ProviderConfig) -> None:
    meta = _read_provider_meta(persist_directory)
    if not meta:
        return
    stored_backend = meta.get("provider")
    stored_model = meta.get("embedding_model")
    if stored_backend != provider.embedding_backend or stored_model != provider.embedding_model:
        raise ValueError(
            "This document index was built with a different embedding provider. "
            "Please upload and prepare your PDF again."
        )


class VectorStoreManager:
    """Manage vector store for document embeddings"""
    
    def __init__(self, 
                 provider: ProviderConfig,
                 vector_store_type: str = "faiss",
                 persist_directory: Optional[str] = None):
        """
        Initialize vector store manager
        
        Args:
            provider: Active embedding/chat provider configuration
            vector_store_type: currently only "faiss"
            persist_directory: Directory to persist vector store
        """
        self.provider = provider
        self.embedding_model = provider.embedding_model
        self.vector_store_type = vector_store_type.lower()
        self.persist_directory = persist_directory or "./vector_store"

        if self.vector_store_type != "faiss":
            raise ValueError("Only the FAISS vector store is supported in this deployment build.")

        # Initialize embeddings
        logger.info(f"Loading embedding model: {provider.embedding_model} ({provider.embedding_backend})")
        self.embeddings = _build_embeddings(provider)
        
        self.vector_store = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
    
    def create_vector_store(
        self,
        texts: Union[str, List[str]],
        metadata: Optional[List[Dict]] = None,
        already_chunked: bool = False,
    ) -> int:
        """
        Create vector store from full text or pre-chunked strings.

        Args:
            texts: Full document text, or list of page/chunk strings
            metadata: Optional metadata for each input document
            already_chunked: When True, skip RecursiveCharacterTextSplitter

        Returns:
            Number of embedded chunks written to the vector store
        """
        if isinstance(texts, str):
            if not texts.strip():
                raise ValueError("No texts provided for vector store creation")
            text_list = [texts]
        else:
            text_list = [text for text in texts if text and str(text).strip()]
            if not text_list:
                raise ValueError("No texts provided for vector store creation")

        started = time.perf_counter()
        logger.info(
            "Creating vector store from %s input document(s), already_chunked=%s",
            len(text_list),
            already_chunked,
        )

        documents = []
        for i, text in enumerate(text_list):
            doc_metadata = metadata[i] if metadata and i < len(metadata) else {}
            doc_metadata['chunk_index'] = i
            documents.append(Document(page_content=text, metadata=doc_metadata))

        if already_chunked:
            split_docs = documents
        else:
            split_docs = self.text_splitter.split_documents(documents)
        logger.info("Split into %s embedding chunks", len(split_docs))
        
        # Create vector store in batches to reduce memory spikes on Cloud deploys
        batch_size = 48
        os.makedirs(self.persist_directory, exist_ok=True)
        if len(split_docs) <= batch_size:
            self.vector_store = FAISS.from_documents(split_docs, self.embeddings)
        else:
            first_batch = split_docs[:batch_size]
            remainder = split_docs[batch_size:]
            self.vector_store = FAISS.from_documents(first_batch, self.embeddings)
            for start in range(0, len(remainder), batch_size):
                batch = remainder[start:start + batch_size]
                self.vector_store.add_documents(batch)
                logger.info(
                    "Indexed batch %s/%s chunks",
                    min(start + batch_size, len(remainder)),
                    len(remainder),
                )

        self.vector_store.save_local(self.persist_directory)
        _write_provider_meta(self.persist_directory, self.provider)
        elapsed = time.perf_counter() - started
        logger.info(
            "FAISS vector store saved to %s (%s chunks, %.2fs)",
            self.persist_directory,
            len(split_docs),
            elapsed,
        )
        return len(split_docs)
    
    def load_vector_store(self):
        """Load existing vector store from disk"""
        if not os.path.exists(self.persist_directory):
            raise FileNotFoundError(f"Vector store not found at {self.persist_directory}")

        _validate_provider_meta(self.persist_directory, self.provider)
        
        logger.info(f"Loading vector store from {self.persist_directory}")
        
        self.vector_store = FAISS.load_local(
            self.persist_directory,
            self.embeddings,
            allow_dangerous_deserialization=True
        )
        
        logger.info("Vector store loaded successfully")
    
    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """
        Search for similar documents
        
        Args:
            query: Search query
            k: Number of results to return
        
        Returns:
            List of similar documents
        """
        if self.vector_store is None:
            raise ValueError("Vector store not initialized. Create or load it first.")
        
        results = self.vector_store.similarity_search(query, k=k)
        return results
    
    def similarity_search_with_score(self, query: str, k: int = 4):
        """
        Search for similar documents with similarity scores
        
        Args:
            query: Search query
            k: Number of results to return
        
        Returns:
            List of tuples (document, score)
        """
        if self.vector_store is None:
            raise ValueError("Vector store not initialized. Create or load it first.")
        
        results = self.vector_store.similarity_search_with_score(query, k=k)
        return results
