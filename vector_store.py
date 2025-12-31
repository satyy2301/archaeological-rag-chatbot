"""
Vector Store Module for RAG System
Creates and manages embeddings and vector database
"""

import os
import pickle
from typing import List, Optional, Dict
try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import FAISS, Chroma
except ImportError:
    from langchain.embeddings import HuggingFaceEmbeddings
    from langchain.vectorstores import FAISS, Chroma

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

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Manage vector store for document embeddings"""
    
    def __init__(self, 
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
                 vector_store_type: str = "faiss",
                 persist_directory: Optional[str] = None):
        """
        Initialize vector store manager
        
        Args:
            embedding_model: HuggingFace model name for embeddings
            vector_store_type: "faiss" or "chroma"
            persist_directory: Directory to persist vector store
        """
        self.embedding_model = embedding_model
        self.vector_store_type = vector_store_type
        self.persist_directory = persist_directory or "./vector_store"
        
        # Initialize embeddings
        logger.info(f"Loading embedding model: {embedding_model}")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={'device': 'cpu'}
        )
        
        self.vector_store = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
    
    def create_vector_store(self, texts: List[str], metadata: Optional[List[Dict]] = None):
        """
        Create vector store from text chunks
        
        Args:
            texts: List of text chunks
            metadata: Optional metadata for each chunk
        """
        if not texts:
            raise ValueError("No texts provided for vector store creation")
        
        logger.info(f"Creating vector store from {len(texts)} text chunks")
        
        # Create Document objects
        documents = []
        for i, text in enumerate(texts):
            doc_metadata = metadata[i] if metadata and i < len(metadata) else {}
            doc_metadata['chunk_index'] = i
            documents.append(Document(page_content=text, metadata=doc_metadata))
        
        # Split documents if needed
        split_docs = self.text_splitter.split_documents(documents)
        logger.info(f"Split into {len(split_docs)} documents")
        
        # Create vector store
        if self.vector_store_type == "faiss":
            self.vector_store = FAISS.from_documents(split_docs, self.embeddings)
            # Save FAISS index
            os.makedirs(self.persist_directory, exist_ok=True)
            self.vector_store.save_local(self.persist_directory)
            logger.info(f"FAISS vector store saved to {self.persist_directory}")
        
        elif self.vector_store_type == "chroma":
            os.makedirs(self.persist_directory, exist_ok=True)
            self.vector_store = Chroma.from_documents(
                split_docs,
                self.embeddings,
                persist_directory=self.persist_directory
            )
            logger.info(f"Chroma vector store saved to {self.persist_directory}")
        
        else:
            raise ValueError(f"Unknown vector store type: {self.vector_store_type}")
    
    def load_vector_store(self):
        """Load existing vector store from disk"""
        if not os.path.exists(self.persist_directory):
            raise FileNotFoundError(f"Vector store not found at {self.persist_directory}")
        
        logger.info(f"Loading vector store from {self.persist_directory}")
        
        if self.vector_store_type == "faiss":
            self.vector_store = FAISS.load_local(
                self.persist_directory,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
        elif self.vector_store_type == "chroma":
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
        else:
            raise ValueError(f"Unknown vector store type: {self.vector_store_type}")
        
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

