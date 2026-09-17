"""PDF processing and RAG initialization services."""

import logging

import pandas as pd
import streamlit as st

from pdf_processor import PDFProcessor
from rag_chain import ArchaeologicalRAGChain
from vector_store import VectorStoreManager

logger = logging.getLogger(__name__)


def initialize_rag_chain_with_current_key() -> bool:
    """Initialize or refresh the RAG chain using a user key (if provided) or .env key."""
    if not st.session_state.vector_store_manager:
        st.error("No document has been indexed yet. Please upload and process a PDF first.")
        return False

    api_key = st.session_state.get("user_openai_api_key", "").strip() or None
    try:
        rag_chain = ArchaeologicalRAGChain(
            vector_store_manager=st.session_state.vector_store_manager,
            model_name="gpt-3.5-turbo",
            temperature=0.7,
            openai_api_key=api_key,
        )
        st.session_state.rag_chain = rag_chain
        st.success("✅ Assistant is ready — start chatting below!")
        return True
    except Exception as e:
        st.session_state.rag_chain = None
        st.error(f"Error initializing assistant: {str(e)}")
        st.info(
            "Please add a valid OpenAI API key in the sidebar (or set OPENAI_API_KEY in your .env file) and try again."
        )
        return False


def process_pdf_and_create_vector_store(pdf_path: str) -> bool:
    """Process PDF and create vector store."""
    try:
        with st.spinner("📖 Reading your document..."):
            processor = PDFProcessor(pdf_path)
            text_chunks = processor.process(chunk_size=1000, chunk_overlap=200)

            try:
                coords = processor.extract_coordinates()
                dates = processor.extract_dates()
                sites = processor.extract_sites()

                st.session_state.sites_df = pd.DataFrame(coords) if coords else None
                st.session_state.timeline_df = pd.DataFrame(dates) if dates else None
                st.session_state.sites_list = sites if sites else None

                if coords or dates or sites:
                    extraction_summary = []
                    if coords:
                        extraction_summary.append(f"{len(coords)} coordinate(s)")
                    if dates:
                        extraction_summary.append(f"{len(dates)} date(s)")
                    if sites:
                        extraction_summary.append(f"{len(sites)} site(s)")
                    st.info(f"📊 Auto-extracted: {', '.join(extraction_summary)} from PDF")
            except Exception as e:  # pragma: no cover
                logger.warning(f"Auto-extraction for maps/timelines failed: {e}")
                st.session_state.sites_df = None
                st.session_state.timeline_df = None
                st.session_state.sites_list = None

            if not text_chunks:
                st.error("No text could be extracted from the PDF.")
                return False

            st.success(f"✅ Document read — found {len(text_chunks)} sections of text.")

            with st.spinner("🗂️ Indexing your document (this may take a minute)..."):
                vector_store_manager = VectorStoreManager(
                    embedding_model="text-embedding-3-small",
                    vector_store_type="faiss",
                    persist_directory="./vector_store",
                )
                vector_store_manager.create_vector_store(text_chunks)
                st.session_state.vector_store_manager = vector_store_manager
                st.session_state.vector_store_initialized = True
                st.success("✅ Document indexed successfully!")

            with st.spinner("🤖 Setting up your assistant..."):
                initialize_rag_chain_with_current_key()
            return True

    except Exception as e:
        msg = str(e).strip() or "An unexpected error occurred. Check that the PDF is valid and your API key is set."
        st.error(f"Error processing PDF: {msg}")
        return False


def load_existing_vector_store() -> bool:
    """Load existing vector store if available."""
    try:
        vector_store_manager = VectorStoreManager(
            embedding_model="text-embedding-3-small",
            vector_store_type="faiss",
            persist_directory="./vector_store",
        )
        vector_store_manager.load_vector_store()
        st.session_state.vector_store_manager = vector_store_manager
        st.session_state.vector_store_initialized = True
        initialize_rag_chain_with_current_key()
        return True
    except Exception as e:
        logger.info(f"Could not load existing vector store: {e}")
        return False


def build_mode_preface(mode: str) -> str:
    """Short instruction that biases the LLM towards a specialized archaeological task."""
    mapping = {
        "General Q&A": "",
        "Field Work & Analysis": (
            "You are assisting with field work tasks including artifact identification, dating assistance, "
            "stratigraphy analysis, site classification, and terminology explanations. "
            "Provide practical, field-ready guidance based on archaeological best practices. "
        ),
        "Documentation & Reporting": (
            "You are helping with documentation tasks including report generation, methodology templates, "
            "citation formatting, and creating structured documentation. Focus on professional standards and clarity. "
        ),
        "Legal & Compliance": (
            "You are guiding about permits, heritage laws, legal compliance, and ethical guidelines. "
            "Always remind users to check the latest local regulations and consult authorities. "
            "Emphasize community engagement and long-term conservation. "
        ),
        "Site Management": (
            "You are advising on site preservation, conservation strategies, risk assessment, and site management. "
            "Consider physical, chemical, and human threats and recommend minimally invasive strategies. "
        ),
    }
    return mapping.get(mode, "")
