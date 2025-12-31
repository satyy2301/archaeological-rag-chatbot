"""
RAG Chain Module
Implements Retrieval-Augmented Generation for archaeological survey chatbot
"""

import os
from typing import List, Optional
from langchain_openai import ChatOpenAI

# Handle LangChain version differences for chains
# In LangChain 1.0+, chains moved to langchain-classic
try:
    from langchain_classic.chains import RetrievalQA
except ImportError:
    try:
        from langchain.chains import RetrievalQA
    except ImportError:
        try:
            from langchain.chains.retrieval_qa.base import RetrievalQA
        except ImportError:
            raise ImportError("Could not import RetrievalQA. Please install langchain-classic: pip install langchain-classic")

# Handle LangChain version differences for prompts
try:
    from langchain_core.prompts import PromptTemplate
except ImportError:
    try:
        from langchain.prompts import PromptTemplate
    except ImportError:
        raise ImportError("Could not import PromptTemplate. Please install langchain-core: pip install langchain-core")

from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class ArchaeologicalRAGChain:
    """RAG chain for archaeological survey chatbot"""
    
    def __init__(self, 
                 vector_store_manager,
                 model_name: str = "gpt-3.5-turbo",
                 temperature: float = 0.7,
                 use_openai: bool = True):
        """
        Initialize RAG chain
        
        Args:
            vector_store_manager: VectorStoreManager instance
            model_name: LLM model name
            temperature: Model temperature
            use_openai: Whether to use OpenAI API (requires API key)
        """
        self.vector_store_manager = vector_store_manager
        self.model_name = model_name
        self.temperature = temperature
        self.use_openai = use_openai
        
        # Initialize LLM
        self.llm = self._initialize_llm()
        
        # Create prompt template
        self.prompt_template = self._create_prompt_template()
        
        # Initialize QA chain
        self.qa_chain = None
        self._initialize_qa_chain()
    
    def _initialize_llm(self):
        """Initialize language model"""
        if self.use_openai:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning("OPENAI_API_KEY not found. Using default model.")
                # Fallback to a local model or raise error
                raise ValueError("OPENAI_API_KEY not found in environment variables. "
                               "Please set it in .env file or use a local model.")
            
            try:
                # Try using ChatOpenAI from langchain_openai
                llm = ChatOpenAI(
                    model=self.model_name,
                    temperature=self.temperature,
                    openai_api_key=api_key
                )
                logger.info(f"Initialized OpenAI model: {self.model_name}")
                return llm
            except Exception as e:
                logger.error(f"Error initializing OpenAI model: {e}")
                raise
        else:
            # For local models, you can use Ollama or other local LLMs
            logger.info("Using local model (not implemented in this version)")
            raise NotImplementedError("Local models not implemented. Please use OpenAI.")
    
    def _create_prompt_template(self) -> PromptTemplate:
        """Create prompt template for archaeological survey questions"""
        template = """You are an expert archaeological survey assistant. Your role is to help users with archaeological survey questions based on the provided context from archaeological documents.

Use the following pieces of context to answer the question. If you don't know the answer based on the context, say so, but try to provide helpful information related to archaeological surveys in general.

Context from archaeological documents:
{context}

Question: {question}

Provide a detailed, accurate answer based on the context. If the context doesn't fully answer the question, provide the best answer you can and mention what additional information might be needed.

Answer:"""
        
        return PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
    
    def _initialize_qa_chain(self):
        """Initialize the QA chain"""
        if self.vector_store_manager.vector_store is None:
            raise ValueError("Vector store not initialized")
        
        # Create retriever
        retriever = self.vector_store_manager.vector_store.as_retriever(
            search_kwargs={"k": 4}
        )
        
        # Create QA chain
        try:
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=retriever,
                chain_type_kwargs={"prompt": self.prompt_template},
                return_source_documents=True
            )
            logger.info("QA chain initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing QA chain: {e}")
            raise
    
    def query(self, question: str) -> dict:
        """
        Query the RAG system
        
        Args:
            question: User's question
        
        Returns:
            Dictionary with answer and source documents
        """
        if self.qa_chain is None:
            raise ValueError("QA chain not initialized")
        
        try:
            result = self.qa_chain({"query": question})
            return {
                "answer": result.get("result", "I couldn't generate an answer."),
                "source_documents": result.get("source_documents", [])
            }
        except Exception as e:
            logger.error(f"Error querying RAG system: {e}")
            return {
                "answer": f"I encountered an error: {str(e)}",
                "source_documents": []
            }
    
    def get_sources(self, source_documents: List) -> List[dict]:
        """
        Format source documents for display
        
        Args:
            source_documents: List of source documents
        
        Returns:
            List of formatted source information
        """
        sources = []
        for i, doc in enumerate(source_documents[:3]):  # Limit to top 3 sources
            sources.append({
                "index": i + 1,
                "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                "metadata": doc.metadata
            })
        return sources

