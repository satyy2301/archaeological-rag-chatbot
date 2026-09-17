"""
Streamlit Web Application for Archaeological Survey RAG Chatbot
Enhanced UI with visualization and archaeology-specific tools.
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from pdf_processor import PDFProcessor
from rag_chain import ArchaeologicalRAGChain
from vector_store import VectorStoreManager
from photo_organizer import PhotoOrganizer
from artifact_assessment import ArtifactAssessment
from report_generator import ReportGenerator
from ui.copy import COPY
from deploy_utils import is_streamlit_cloud
from image_analyzer import is_easyocr_available, is_easyocr_initialized
from PIL import Image
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Archaeological Survey Assistant",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for a more modern, user‑friendly UI
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.6rem;
        font-weight: 800;
        color: #1f2937;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        text-align: center;
        color: #6b7280;
        margin-bottom: 1.5rem;
    }
    .stChatMessage {
        border-radius: 0.75rem !important;
        padding: 0.85rem 1rem !important;
    }
    .st-emotion-cache-1c7y2kd {
        border-radius: 0.75rem !important;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #1f77b4, #0ea5e9);
        color: white;
        border-radius: 999px;
        border: none;
        font-weight: 600;
    }
    .stButton>button:hover {
        opacity: 0.9;
    }
    .pill {
        display: inline-block;
        padding: 0.15rem 0.6rem;
        border-radius: 999px;
        background-color: #e5e7eb;
        font-size: 0.75rem;
        margin-right: 0.25rem;
        margin-bottom: 0.25rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def initialize_session_state():
    """Initialize session state variables"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'vector_store_initialized' not in st.session_state:
        st.session_state.vector_store_initialized = False
    if 'rag_chain' not in st.session_state:
        st.session_state.rag_chain = None
    if 'vector_store_manager' not in st.session_state:
        st.session_state.vector_store_manager = None
    if 'active_mode' not in st.session_state:
        st.session_state.active_mode = "General Q&A"
    if 'uploaded_pdf_name' not in st.session_state:
        st.session_state.uploaded_pdf_name = None
    if 'sites_df' not in st.session_state:
        st.session_state.sites_df = None
    if 'timeline_df' not in st.session_state:
        st.session_state.timeline_df = None
    if 'sites_list' not in st.session_state:
        st.session_state.sites_list = None
    if 'photo_organizer' not in st.session_state:
        st.session_state.photo_organizer = None
    if 'artifact_assessor' not in st.session_state:
        st.session_state.artifact_assessor = None
    if 'user_openai_api_key' not in st.session_state:
        st.session_state.user_openai_api_key = ""


def _get_openai_api_key() -> Optional[str]:
    """Resolve OpenAI API key from session state or environment."""
    session_key = st.session_state.get("user_openai_api_key", "").strip()
    if session_key:
        return session_key
    env_key = os.getenv("OPENAI_API_KEY", "").strip()
    return env_key or None


def _initialize_rag_chain_with_current_key() -> bool:
    """Initialize or refresh the RAG chain using a user key (if provided) or .env key."""
    if not st.session_state.vector_store_manager:
        st.error(COPY["errors"]["no_document_indexed"])
        return False

    api_key = _get_openai_api_key()
    try:
        rag_chain = ArchaeologicalRAGChain(
            vector_store_manager=st.session_state.vector_store_manager,
            model_name="gpt-3.5-turbo",
            temperature=0.7,
            openai_api_key=api_key,
        )
        st.session_state.rag_chain = rag_chain
        st.success(f"✅ {COPY['status']['assistant_ready']}")
        return True
    except Exception as e:
        st.session_state.rag_chain = None
        st.error(COPY["errors"]["assistant_init"].format(error=str(e)))
        st.info(COPY["errors"]["api_key_invalid"])
        return False


def process_pdf_and_create_vector_store(pdf_path: str):
    """Process PDF and create vector store."""
    try:
        with st.spinner(f"📖 {COPY['status']['reading_document']}"):
            # Process PDF
            processor = PDFProcessor(pdf_path)
            text_chunks = processor.process(chunk_size=1000, chunk_overlap=200)

            # Automatic extraction of coordinates, dates, and sites for visualisations
            try:
                coords = processor.extract_coordinates()
                dates = processor.extract_dates()
                sites = processor.extract_sites()

                if coords:
                    st.session_state.sites_df = pd.DataFrame(coords)
                else:
                    st.session_state.sites_df = None

                if dates:
                    st.session_state.timeline_df = pd.DataFrame(dates)
                else:
                    st.session_state.timeline_df = None
                
                if sites:
                    st.session_state.sites_list = sites
                else:
                    st.session_state.sites_list = None
                    
                if coords or dates or sites:
                    extraction_summary = []
                    if coords:
                        extraction_summary.append(f"{len(coords)} coordinate(s)")
                    if dates:
                        extraction_summary.append(f"{len(dates)} date(s)")
                    if sites:
                        extraction_summary.append(f"{len(sites)} site(s)")
                    st.info(
                        f"📊 {COPY['status']['auto_extracted'].format(summary=', '.join(extraction_summary))}"
                    )
            except Exception as e:  # pragma: no cover
                logger.warning(f"Auto-extraction for maps/timelines failed: {e}")
                st.session_state.sites_df = None
                st.session_state.timeline_df = None
                st.session_state.sites_list = None
            
            if not text_chunks:
                st.error(COPY["errors"]["no_pdf_text"])
                return False
            
            st.success(
                f"✅ {COPY['status']['document_read_sections'].format(count=len(text_chunks))}"
            )
            
            # Create vector store
            with st.spinner(f"🗂️ {COPY['status']['indexing_document']}"):
                vector_store_manager = VectorStoreManager(
                    embedding_model="text-embedding-3-small",
                    vector_store_type="faiss",
                    persist_directory="./vector_store",
                    openai_api_key=_get_openai_api_key(),
                )
                vector_store_manager.create_vector_store(text_chunks)
                st.session_state.vector_store_manager = vector_store_manager
                st.session_state.vector_store_initialized = True
                st.success(f"✅ {COPY['status']['document_prepared']}")
            
            # Initialize RAG chain (best effort so document processing still succeeds)
            with st.spinner(f"🤖 {COPY['status']['setting_up_assistant']}"):
                _initialize_rag_chain_with_current_key()
            return True
                    
    except Exception as e:
        st.error(COPY["errors"]["pdf_processing"].format(error=str(e)))
        return False


def load_existing_vector_store():
    """Load existing vector store if available"""
    try:
        vector_store_manager = VectorStoreManager(
            embedding_model="text-embedding-3-small",
            vector_store_type="faiss",
            persist_directory="./vector_store",
            openai_api_key=_get_openai_api_key(),
        )
        vector_store_manager.load_vector_store()
        st.session_state.vector_store_manager = vector_store_manager
        st.session_state.vector_store_initialized = True
        
        # Initialize RAG chain (best effort)
        _initialize_rag_chain_with_current_key()
        return True
    except Exception as e:
        logger.info(f"Could not load existing vector store: {e}")
        return False


def _build_mode_preface(mode: str) -> str:
    """Short instruction that biases the LLM towards a specialized archaeological task."""
    # Simplified modes: merged from 11 into 4 user-friendly categories
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


def _render_sidebar():
    """Sidebar: API key, document status, and quick tools."""
    with st.sidebar:
        st.header(f"🔑 {COPY['sidebar']['api_key_header']}")
        st.caption(COPY["sidebar"]["api_key_caption"])
        entered_key = st.text_input(
            COPY["sidebar"]["api_key_label"],
            type="password",
            value=st.session_state.user_openai_api_key,
            placeholder=COPY["sidebar"]["api_key_placeholder"],
            help=COPY["sidebar"]["api_key_help"],
        )
        st.session_state.user_openai_api_key = entered_key

        col_key1, col_key2 = st.columns(2)
        with col_key1:
            if st.button("Apply key", width="stretch"):
                if st.session_state.vector_store_initialized and st.session_state.vector_store_manager:
                    _initialize_rag_chain_with_current_key()
                else:
                    st.success(COPY["sidebar"]["apply_key_saved"])
        with col_key2:
            if st.button("Clear key", width="stretch"):
                st.session_state.user_openai_api_key = ""
                st.info(COPY["sidebar"]["clear_key_info"])

        st.markdown("---")
        # Show current document name if one is loaded
        if st.session_state.vector_store_initialized:
            st.success(
                f"📄 **{st.session_state.uploaded_pdf_name or 'Document'}** {COPY['sidebar']['document_loaded']}"
            )
            if st.button(f"🔄 {COPY['sidebar']['load_different_document']}", width="stretch"):
                st.session_state.vector_store_initialized = False
                st.session_state.rag_chain = None
                st.session_state.vector_store_manager = None
                st.session_state.uploaded_pdf_name = None
                st.session_state.messages = []
                st.rerun()
            st.markdown("---")

        st.header(f"🧭 {COPY['sidebar']['assistant_mode_header']}")
        mode = st.selectbox(
            COPY["sidebar"]["assistant_mode_label"],
            [
                "General Q&A",
                "Field Work & Analysis",
                "Documentation & Reporting",
                "Legal & Compliance",
                "Site Management",
            ],
            index=0,
            help=COPY["sidebar"]["assistant_mode_help"],
        )
        st.session_state.active_mode = mode

        st.caption(f"💡 {COPY['sidebar']['api_key_tip']}")

        st.markdown("---")
        st.subheader(COPY["sidebar"]["quick_starter_header"])
        examples = {
            "Field Work": "Help me identify this artifact and determine appropriate dating methods:",
            "Documentation": "Generate a survey methodology template for a walkover survey:",
            "Legal & Compliance": "What permits might be required for a survey in this region?",
            "Site Management": "What preservation strategy would you recommend for this site?",
        }
        for label, prompt in examples.items():
            if st.button(label, key=f"q_{label}"):
                st.session_state.messages.append(
                    {"role": "user", "content": prompt + " (replace with your details)."}
                )


def _render_chat_tab():
    """Main chat experience with archaeology-specific modes."""
    st.markdown(
        '<h1 class="main-header">🏛️ Archaeological Survey Assistant</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="sub-header">{COPY["chat"]["subheader"]}</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.vector_store_initialized and st.session_state.rag_chain:
        # Display current mode as pills
        st.markdown(
            f"**{COPY['chat']['active_mode']}** "
            f"<span class='pill'>{st.session_state.active_mode}</span>",
            unsafe_allow_html=True,
        )

        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "sources" in message and message["sources"]:
                    with st.expander(f"📖 {COPY['chat']['view_sources']}"):
                        for source in message["sources"]:
                            st.write(f"**Source {source['index']}:**")
                            st.write(source["content"])
                            meta = source.get("metadata") or {}
                            # Try to surface page or chunk info if present
                            page = meta.get("page") or meta.get("page_number")
                            chunk_idx = meta.get("chunk_index")
                            meta_bits = []
                            if page is not None:
                                meta_bits.append(f"Page: {page}")
                            if chunk_idx is not None:
                                meta_bits.append(f"Chunk: {chunk_idx}")
                            if meta_bits:
                                st.caption(" | ".join(meta_bits))
                            elif meta:
                                st.caption(f"Metadata: {meta}")
        
        # Chat input
        placeholder = "Ask a question about archaeological surveys, sites, or regulations..."
        if prompt := st.chat_input(placeholder):
            # Apply specialized mode preface
            preface = _build_mode_preface(st.session_state.active_mode)
            full_prompt = f"{preface} User question: {prompt}" if preface else prompt

            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Get response
            with st.chat_message("assistant"):
                with st.spinner("Thinking with your archaeological documents..."):
                    result = st.session_state.rag_chain.query(full_prompt)
                    answer = result["answer"]
                    sources = st.session_state.rag_chain.get_sources(
                        result["source_documents"]
                    )
                    
                    st.markdown(answer)
                    
                    if sources:
                        with st.expander(f"📖 {COPY['chat']['view_sources']}"):
                            for source in sources:
                                st.write(f"**Source {source['index']}:**")
                                st.write(source["content"])
                                meta = source.get("metadata") or {}
                                page = meta.get("page") or meta.get("page_number")
                                chunk_idx = meta.get("chunk_index")
                                meta_bits = []
                                if page is not None:
                                    meta_bits.append(f"Page: {page}")
                                if chunk_idx is not None:
                                    meta_bits.append(f"Chunk: {chunk_idx}")
                                if meta_bits:
                                    st.caption(" | ".join(meta_bits))
                                elif meta:
                                    st.caption(f"Metadata: {meta}")
            
            # Add assistant message
            st.session_state.messages.append(
                {
                "role": "assistant",
                "content": answer,
                    "sources": sources,
                }
            )
    
    else:
        # ── Onboarding / upload screen ────────────────────────────────────────
        st.markdown(f"## 👋 {COPY['chat']['welcome_title']}")
        st.markdown(COPY["chat"]["welcome_body"])
        st.markdown("---")

        col_upload, col_help = st.columns([3, 2], gap="large")

        with col_upload:
            st.markdown(f"### 📄 {COPY['chat']['step1_title']}")

            # Warn if no API key yet
            api_key_ok = bool(_get_openai_api_key())
            if not api_key_ok:
                st.warning(f"⚠️ **{COPY['chat']['api_key_warning']}**")

            pdf_file = st.file_uploader(
                COPY["chat"]["pdf_uploader_label"],
                type=["pdf"],
                key="main_pdf_uploader",
                help=COPY["chat"]["pdf_uploader_help"],
            )

            if pdf_file is not None:
                st.session_state.uploaded_pdf_name = pdf_file.name
                pdf_path = f"./temp_{pdf_file.name}"
                with open(pdf_path, "wb") as f:
                    f.write(pdf_file.getbuffer())
                st.success(
                    f"✅ {COPY['status']['pdf_ready_named'].format(name=pdf_file.name)}"
                )
                if st.button(
                    f"⚙️ {COPY['chat']['process_button']}",
                    width="stretch",
                    key="main_process_btn",
                    disabled=not api_key_ok,
                ):
                    success = process_pdf_and_create_vector_store(pdf_path)
                    if success:
                        if os.path.exists(pdf_path):
                            os.remove(pdf_path)
                        st.rerun()

            # Resume from a previously indexed document on disk
            vector_store_path = Path("./vector_store")
            if vector_store_path.exists() and not st.session_state.vector_store_initialized:
                st.markdown("---")
                st.markdown(f"**{COPY['chat']['resume_prompt']}**")
                if st.button(
                    f"📂 {COPY['chat']['resume_button']}",
                    width="stretch",
                    key="main_load_btn",
                ):
                    if load_existing_vector_store():
                        st.rerun()
                    else:
                        st.error(COPY["chat"]["resume_error"])

        with col_help:
            st.markdown(f"### 💡 {COPY['chat']['what_can_i_ask_title']}")
            st.markdown(COPY["chat"]["what_can_i_ask_body"])
            st.markdown(f"### 🔑 {COPY['chat']['api_key_help_title']}")
            st.markdown(COPY["chat"]["api_key_help_body"])


def _render_visualisations_tab():
    """Maps, timelines, and simple relationship views from tabular data."""
    st.subheader(f"🌍 {COPY['maps']['map_title']}")
    st.caption(COPY["maps"]["map_caption"])

    auto_sites_df = st.session_state.get("sites_df")
    if auto_sites_df is not None and not auto_sites_df.empty:
        st.markdown(f"**{COPY['maps']['map_from_pdf']}**")
        # Use site_name in map if available, otherwise show coordinates
        map_df = auto_sites_df[["latitude", "longitude"]].copy()
        if "site_name" in auto_sites_df.columns:
            # Add site_name as a column for better display
            map_df["site_name"] = auto_sites_df["site_name"].fillna("Unnamed Site")
        st.map(map_df)
        with st.expander(COPY["maps"]["map_coords_expander"]):
            # Show site_name prominently if available
            display_cols = ["latitude", "longitude"]
            if "site_name" in auto_sites_df.columns:
                display_cols = ["site_name"] + display_cols
            if "context" in auto_sites_df.columns:
                display_cols.append("context")
            st.dataframe(auto_sites_df[display_cols], width="stretch")

    site_file = st.file_uploader(
        COPY["maps"]["map_csv_label"], type=["csv"], key="map_csv"
    )
    if site_file is not None:
        df_sites = pd.read_csv(site_file)
        required_cols = {"latitude", "longitude"}
        if required_cols.issubset(df_sites.columns):
            st.markdown(f"**{COPY['maps']['map_csv_from_upload']}**")
            st.map(df_sites[["latitude", "longitude"]])
            with st.expander(COPY["maps"]["map_csv_table_expander"]):
                st.dataframe(df_sites, width="stretch")
        else:
            st.error(
                COPY["maps"]["map_csv_error"].format(
                    required=", ".join(required_cols),
                    found=list(df_sites.columns),
                )
            )

    st.markdown("---")
    st.subheader(f"⏳ {COPY['maps']['timeline_title']}")
    st.caption(COPY["maps"]["timeline_caption"])

    auto_time_df = st.session_state.get("timeline_df")
    if auto_time_df is not None and not auto_time_df.empty:
        st.markdown(f"**{COPY['maps']['timeline_from_pdf']}**")
        try:
            import altair as alt

            # Use site_name if available, otherwise use label
            if "site_name" in auto_time_df.columns:
                y_col = "site_name"
                tooltip_cols = ["site_name", "label", "start_year", "end_year", "context"]
            else:
                y_col = "label"
                tooltip_cols = ["label", "start_year", "end_year", "context"]
            
            # Filter out None site_names for cleaner display
            chart_df = auto_time_df.copy()
            if "site_name" in chart_df.columns:
                chart_df = chart_df[chart_df["site_name"].notna() | chart_df["label"].notna()]

            auto_chart = (
                alt.Chart(chart_df)
                .encode(
                    x="start_year:Q",
                    x2="end_year:Q",
                    y=alt.Y(f"{y_col}:N", sort="-x", title="Site/Period"),
                    tooltip=tooltip_cols,
                )
                .mark_bar(size=10, color="#1f77b4")
            )
            st.altair_chart(auto_chart, width="stretch")
        except Exception as e:  # pragma: no cover
            st.error(COPY["maps"]["timeline_chart_error"].format(error=e))
            st.dataframe(auto_time_df)

    timeline_file = st.file_uploader(
        COPY["maps"]["timeline_csv_label"], type=["csv"], key="timeline_csv"
    )
    if timeline_file is not None:
        df_time = pd.read_csv(timeline_file)
        if {"site_name", "start_year"}.issubset(df_time.columns):
            # Normalise years
            df_time["end_year"] = df_time.get("end_year", df_time["start_year"])
            df_time["start_year"] = pd.to_numeric(df_time["start_year"], errors="coerce")
            df_time["end_year"] = pd.to_numeric(df_time["end_year"], errors="coerce")
            df_time = df_time.dropna(subset=["start_year"])
            if not df_time.empty:
                try:
                    import altair as alt

                    base = alt.Chart(df_time).encode(
                        x="start_year:Q",
                        x2="end_year:Q",
                        y=alt.Y("site_name:N", sort="-x"),
                        tooltip=["site_name", "start_year", "end_year"],
                    )
                    timeline = base.mark_bar(size=12, color="#1f77b4")
                    st.altair_chart(timeline, width="stretch")
                except Exception as e:  # pragma: no cover
                    st.error(COPY["maps"]["timeline_chart_error"].format(error=e))
                    st.dataframe(df_time)
            else:
                st.warning(COPY["maps"]["timeline_no_valid_rows"])
        else:
            st.error(COPY["maps"]["timeline_csv_error"])

    st.markdown("---")
    st.subheader(f"🕸️ {COPY['maps']['graph_title']}")
    st.caption(COPY["maps"]["graph_caption"])
    
    # Show extracted sites if available
    sites_list = st.session_state.get("sites_list")
    if sites_list:
        st.markdown(f"**{COPY['maps']['sites_from_pdf']}**")
        sites_df_display = pd.DataFrame(sites_list)
        st.dataframe(sites_df_display[["site_name", "site_type", "context"]], width="stretch")
        st.caption(COPY["maps"]["sites_count"].format(count=len(sites_list)))
    
    st.markdown(COPY["maps"]["graph_body"])


def _render_docs_glossary_tab():
    """Document‑oriented tools: source snippets, glossary, and highlighting helper."""
    st.subheader(f"📄 {COPY['docs_glossary']['viewer_title']}")
    st.caption(COPY["docs_glossary"]["viewer_caption"])

    if st.session_state.uploaded_pdf_name:
        st.info(
            COPY["docs_glossary"]["recent_pdf"].format(
                name=st.session_state.uploaded_pdf_name
            )
        )

    st.markdown(COPY["docs_glossary"]["highlighting_tip"])

    st.markdown("---")
    st.subheader(f"📘 {COPY['docs_glossary']['glossary_title']}")

    glossary = COPY["docs_glossary"]["glossary"]

    term = st.selectbox(COPY["docs_glossary"]["glossary_lookup"], sorted(glossary.keys()))
    st.write(f"**{term}**: {glossary[term]}")

    with st.expander(COPY["docs_glossary"]["glossary_full"]):
        for k, v in glossary.items():
            st.markdown(f"- **{k}**: {v}")


def _render_compliance_tools_tab():
    """Regulatory, methodology, reporting, and citation helpers (prompt-based)."""
    st.subheader(f"⚖️ {COPY['compliance']['title']}")
    st.caption(COPY["compliance"]["caption"])

    col1, col2 = st.columns(2)

    with col1:
        permit_notes = st.text_area(
            COPY["compliance"]["permit_label"],
            placeholder=COPY["compliance"]["permit_placeholder"],
            height=120,
        )
        if st.button(COPY["compliance"]["permit_button"]) and permit_notes:
            if not (
                st.session_state.vector_store_initialized
                and st.session_state.rag_chain
            ):
                st.error(COPY["errors"]["need_pdf_first"])
            else:
                with st.spinner(COPY["compliance"]["spinner_permits"]):
                    prompt = (
                        "You are an archaeological regulatory assistant. "
                        "Based on the following project description, outline likely permit "
                        "requirements, responsible authorities, and key legal considerations. "
                        "Use bullet points and clearly mark any assumptions.\n\n"
                        f"Project description:\n{permit_notes}"
                    )
                    result = st.session_state.rag_chain.query(prompt)
                    st.markdown(result["answer"])

    with col2:
        report_context = st.text_area(
            COPY["compliance"]["report_label"],
            placeholder=COPY["compliance"]["report_placeholder"],
            height=120,
        )
        if st.button(COPY["compliance"]["report_button"]):
            if not (
                st.session_state.vector_store_initialized
                and st.session_state.rag_chain
            ):
                st.error(COPY["errors"]["need_pdf_first"])
            else:
                with st.spinner(COPY["compliance"]["spinner_report"]):
                    prompt = (
                        "Generate a structured archaeological compliance report template. "
                        "Use headings and bullet points. Tailor it to the following project context:\n\n"
                        f"{report_context}"
                    )
                    result = st.session_state.rag_chain.query(prompt)
                    st.markdown(result["answer"])

    st.markdown("---")
    st.subheader(f"📝 {COPY['compliance']['methodology_title']}")
    meth_context = st.text_area(
        COPY["compliance"]["methodology_label"],
        placeholder=COPY["compliance"]["methodology_placeholder"],
        height=120,
    )
    if st.button(COPY["compliance"]["methodology_button"]):
        if not (
            st.session_state.vector_store_initialized and st.session_state.rag_chain
        ):
            st.error(COPY["errors"]["need_pdf_first"])
        else:
            with st.spinner(COPY["compliance"]["spinner_methodology"]):
                prompt = (
                    "Create a detailed survey methodology template for this project, "
                    "including sampling strategy, recording system, and data management:\n\n"
                    f"{meth_context}"
                )
                result = st.session_state.rag_chain.query(prompt)
                st.markdown(result["answer"])

    st.markdown("---")
    st.subheader(f"📝 {COPY['compliance']['report_generator_title']}")
    
    # Initialize report generator
    if 'report_generator' not in st.session_state:
        st.session_state.report_generator = ReportGenerator(
            rag_chain=st.session_state.rag_chain if st.session_state.vector_store_initialized else None
        )
    else:
        # Update RAG chain if available
        if st.session_state.vector_store_initialized:
            st.session_state.report_generator.rag_chain = st.session_state.rag_chain
    
    report_type = st.selectbox(
        COPY["compliance"]["report_type_label"],
        options=list(ReportGenerator.REPORT_TYPES.keys()),
        format_func=lambda x: ReportGenerator.REPORT_TYPES[x],
        key="report_type_select"
    )
    
    # Collect project data (simplified - in production would load from data manager)
    project_data = {
        'project_name': st.text_input(
            COPY["compliance"]["project_name_label"],
            value=COPY["compliance"]["project_name_default"],
            key="report_project_name",
        ),
        'location': st.text_input(COPY["compliance"]["location_label"], key="report_location"),
        'sites': st.session_state.sites_list or [],
        'artifacts': [],  # Would load from data manager
        'methodology': {},
    }
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            f"📄 {COPY['compliance']['generate_report_button']}",
            width="stretch",
            key="generate_report_btn",
        ):
            with st.spinner(COPY["compliance"]["spinner_generating_report"]):
                report_content = st.session_state.report_generator.generate_report(
                    report_type, project_data
                )
                st.session_state.generated_report = report_content
                st.session_state.report_type_generated = report_type
    
    with col2:
        if st.button(
            f"💾 {COPY['compliance']['export_report_button']}",
            width="stretch",
            key="export_report_btn",
            disabled='generated_report' not in st.session_state,
        ):
            if 'generated_report' in st.session_state:
                report_filename = f"{report_type}_report_{datetime.now().strftime('%Y%m%d')}.md"
                st.download_button(
                    COPY["compliance"]["download_report_button"],
                    data=st.session_state.generated_report,
                    file_name=report_filename,
                    mime="text/markdown",
                    key="download_report_btn"
                )
    
    if 'generated_report' in st.session_state:
        st.markdown(f"### {COPY['compliance']['report_preview_title']}")
        st.markdown(st.session_state.generated_report)
    
    st.markdown("---")
    st.subheader(f"📚 {COPY['compliance']['citation_title']}")
    citation_info = st.text_area(
        COPY["compliance"]["citation_label"],
        placeholder=COPY["compliance"]["citation_placeholder"],
        height=120,
    )
    style = st.selectbox(
        COPY["compliance"]["citation_style_label"],
        ["Harvard", "Chicago", "APA", "Custom archaeological"],
        index=0,
    )
    if st.button(COPY["compliance"]["citation_button"]):
        if not (
            st.session_state.vector_store_initialized and st.session_state.rag_chain
        ):
            st.error(COPY["errors"]["need_pdf_first"])
        else:
            with st.spinner(COPY["compliance"]["spinner_citation"]):
                prompt = (
                    f"Format the following bibliographic details as a {style} style citation. "
                    f"If information is missing, clearly mark it with placeholders:\n\n"
                    f"{citation_info}"
                )
                result = st.session_state.rag_chain.query(prompt)
                st.markdown(result["answer"])


def _scan_photos_with_progress(photo_directory: str, analyze_images: bool):
    """Scan photos and show per-file progress in the UI."""
    organizer = PhotoOrganizer(photo_directory, analyze_images=analyze_images)
    progress = st.progress(0.0)
    status = st.empty()
    first_ocr_notice = st.empty()

    def _on_progress(current: int, total: int, filename: str) -> None:
        fraction = current / total if total else 1.0
        progress.progress(fraction)
        status.caption(
            COPY["photo_organizer"]["progress_photo"].format(
                current=current,
                total=total,
                filename=filename,
            )
        )
        if (
            analyze_images
            and is_easyocr_available()
            and not is_easyocr_initialized()
            and current == 1
        ):
            first_ocr_notice.info(COPY["photo_organizer"]["spinner_ocr_first_run"])

    photos = organizer.scan_directory(progress_callback=_on_progress)
    progress.empty()
    status.empty()
    first_ocr_notice.empty()
    return organizer, photos


def _render_photo_organizer_tab():
    """Dig Photo Organizer - auto-organize photos by trench/locus, artifact types, etc."""
    st.subheader(f"📸 {COPY['photo_organizer']['title']}")
    st.caption(COPY["photo_organizer"]["intro"])

    analyze_images = st.checkbox(
        COPY["photo_organizer"]["analyze_checkbox"],
        value=True,
        help=COPY["photo_organizer"]["analyze_help"],
    )
    if analyze_images and is_streamlit_cloud() and is_easyocr_available():
        st.caption(COPY["photo_organizer"]["ocr_cloud_note"])

    # Directory input or file upload
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"### {COPY['photo_organizer']['scan_option_title']}")
        photo_dir = st.text_input(
            COPY["photo_organizer"]["scan_path_label"],
            placeholder=COPY["photo_organizer"]["scan_path_placeholder"],
            help=COPY["photo_organizer"]["scan_path_help"],
        )
        if st.button(COPY["photo_organizer"]["scan_button"], width="stretch") and photo_dir:
            try:
                organizer, photos = _scan_photos_with_progress(photo_dir, analyze_images)
                st.session_state.photo_organizer = organizer
                st.success(COPY["photo_organizer"]["scan_success"].format(count=len(photos)))
            except Exception as e:
                st.error(COPY["errors"]["scan_directory"].format(error=str(e)))

    with col2:
        st.markdown(f"### {COPY['photo_organizer']['upload_option_title']}")
        uploaded_files = st.file_uploader(
            COPY["photo_organizer"]["upload_label"],
            type=['jpg', 'jpeg', 'png', 'tiff', 'tif'],
            accept_multiple_files=True,
            help=COPY["photo_organizer"]["upload_help"],
        )
        if uploaded_files:
            temp_dir = Path("./temp_photos")
            temp_dir.mkdir(exist_ok=True)
            for uploaded_file in uploaded_files:
                with open(temp_dir / uploaded_file.name, "wb") as f:
                    f.write(uploaded_file.getbuffer())
            try:
                organizer, photos = _scan_photos_with_progress(str(temp_dir), analyze_images)
                st.session_state.photo_organizer = organizer
                st.success(COPY["photo_organizer"]["upload_success"].format(count=len(photos)))
            except Exception as e:
                st.error(COPY["errors"]["process_photos"].format(error=str(e)))
    
    # Display organization options
    if st.session_state.photo_organizer and st.session_state.photo_organizer.photos:
        organizer = st.session_state.photo_organizer

        if organizer.last_ocr_backend == 'contour-fallback':
            st.warning(COPY["photo_organizer"]["ocr_limited_warning"])

        st.markdown("---")
        st.markdown(f"### {COPY['photo_organizer']['organize_title']}")
        
        org_method = st.radio(
            COPY["photo_organizer"]["organize_label"],
            ["Trench", "Locus", "Artifact Type", "Stratigraphy Layer", "Date"],
            horizontal=True
        )
        
        if org_method == "Trench":
            organized = organizer.organize_by_trench()
        elif org_method == "Locus":
            organized = organizer.organize_by_locus()
        elif org_method == "Artifact Type":
            organized = organizer.organize_by_artifact_type()
        elif org_method == "Stratigraphy Layer":
            organized = organizer.organize_by_stratigraphy()
        else:  # Date
            organized = organizer.organize_by_date()
        
        # Display organized photos
        for category, photos in sorted(organized.items()):
            with st.expander(f"{org_method}: {category} ({len(photos)} photos)"):
                cols = st.columns(min(4, len(photos)))
                for idx, photo in enumerate(photos[:12]):  # Show first 12
                    with cols[idx % 4]:
                        try:
                            img = Image.open(photo['file_path'])
                            st.image(img, width='stretch', caption=photo['file_name'])
                        except Exception:
                            st.text(photo['file_name'])
                        chips = PhotoOrganizer.format_photo_chips(photo)
                        if chips:
                            st.caption(" · ".join(chips))

                with st.expander(COPY["photo_organizer"]["detection_details"], expanded=False):
                    for photo in photos[:12]:
                        labels = photo.get('detected_labels') or []
                        sources = photo.get('metadata_sources') or []
                        st.markdown(f"**{photo['file_name']}**")
                        if labels:
                            for label in labels[:6]:
                                st.markdown(f"- {label}")
                        if sources:
                            st.caption(f"{COPY['photo_organizer']['sources_label']} {', '.join(sources)}")
                        if not labels and not sources:
                            st.caption(COPY["photo_organizer"]["no_details"])
        
        st.markdown("---")
        st.markdown(f"### {COPY['photo_organizer']['reports_title']}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(
                f"📊 {COPY['photo_organizer']['field_report_button']}",
                width="stretch",
            ):
                report = organizer.generate_field_report()
                st.text_area(COPY["photo_organizer"]["field_report_area_label"], report, height=400)
                st.download_button(
                    COPY["photo_organizer"]["download_report_button"],
                    data=report,
                    file_name="field_report.md",
                    mime="text/markdown"
                )
        
        with col2:
            if st.button(
                f"🔍 {COPY['photo_organizer']['duplicates_button']}",
                width="stretch",
            ):
                duplicates = organizer.find_duplicates()
                if duplicates:
                    st.warning(
                        COPY["photo_organizer"]["duplicates_found"].format(count=len(duplicates))
                    )
                    for idx, group in enumerate(duplicates[:5]):  # Show first 5 groups
                        with st.expander(
                            COPY["photo_organizer"]["duplicate_group"].format(index=idx + 1)
                        ):
                            for photo in group:
                                st.text(f"- {photo['file_name']} ({photo.get('file_size', 0)} bytes)")
                else:
                    st.success(COPY["photo_organizer"]["no_duplicates"])
        
        # Statistics
        with st.expander(f"📈 {COPY['photo_organizer']['statistics_expander']}"):
            stats = organizer.get_statistics()
            st.json(stats)


def _render_layman_summary_sections(assessment: dict) -> None:
    """Render structured plain-language assessment sections."""
    sections = assessment.get('layman_summary_sections')
    if sections:
        intro_heading = (
            "What we know from your description"
            if assessment.get('input_type') == 'text'
            else "What we see in your photo"
        )
        st.markdown(f"#### {intro_heading}")
        st.markdown(sections.get('what_we_see', ''))

        st.markdown("#### What this likely is")
        st.markdown(sections.get('likely_identification', ''))

        st.markdown("#### How confident we are")
        confidence_level = sections.get('confidence_level', 'Unknown')
        confidence_explanation = sections.get('confidence_explanation', '')
        st.markdown(f"**{confidence_level} confidence.** {confidence_explanation}")

        st.markdown("#### Why we think this")
        st.markdown(sections.get('why_we_think_this', ''))

        st.markdown("#### What to do next")
        st.markdown(sections.get('suggested_next_steps', ''))
        return

    summary_text = (
        assessment.get('layman_summary')
        or assessment.get('detailed_analysis')
        or COPY["found_something"]["no_summary"]
    )
    st.markdown("#### What this likely is")
    st.markdown(summary_text)


def _render_found_something_tab():
    """Found Something? - Artifact assessment with photo upload and text description."""
    st.subheader(f"🔍 {COPY['found_something']['title']}")
    st.caption(COPY["found_something"]["intro"])
    
    # Initialize artifact assessor if not exists
    if st.session_state.artifact_assessor is None:
        st.session_state.artifact_assessor = ArtifactAssessment(
            rag_chain=st.session_state.rag_chain if st.session_state.vector_store_initialized else None
        )
    
    assessor = st.session_state.artifact_assessor
    
    # Update RAG chain if available
    if st.session_state.vector_store_initialized and st.session_state.rag_chain:
        assessor.rag_chain = st.session_state.rag_chain
    
    input_method = st.radio(
        COPY["found_something"]["input_method_label"],
        ["📷 Photo Upload", "✍️ Text Description"],
        horizontal=True
    )
    
    st.markdown("---")
    
    if input_method == "📷 Photo Upload":
        st.markdown(f"### {COPY['found_something']['photo_option_title']}")
        from image_analyzer import get_script_profiles

        script_profiles = get_script_profiles()
        uploaded_image = st.file_uploader(
            COPY["found_something"]["photo_uploader_label"],
            type=['jpg', 'jpeg', 'png', 'tiff', 'tif'],
            help=COPY["found_something"]["photo_uploader_help"],
        )
        
        if uploaded_image:
            image = Image.open(uploaded_image)
            st.image(image, caption=COPY["found_something"]["uploaded_caption"], width=400)
            
            # Optional context
            with st.expander(COPY["found_something"]["context_expander"]):
                script_profile = st.selectbox(
                    COPY["found_something"]["script_profile_label"],
                    options=list(script_profiles.keys()),
                    format_func=lambda key: str(script_profiles[key]["label"]),
                    help=COPY["found_something"]["script_profile_help"],
                )
                context = {
                    'artifact_type': st.selectbox("Artifact type", ['unknown', 'coin', 'inscription', 'manuscript page', 'pottery', 'seal', 'other']),
                    'material': st.selectbox("Material", ['unknown', 'stone', 'metal', 'pottery', 'bone', 'glass', 'organic']),
                    'size': st.selectbox("Size", ['unknown', 'coin-sized', 'hand-sized', 'larger', 'very large']),
                    'location': st.selectbox("Location found", ['unknown', 'garden', 'construction site', 'beach', 'field', 'archaeological site', 'other']),
                    'markings': st.text_area("Markings or decorations", ""),
                    'script_profile': script_profile,
                }
                context = {k: v for k, v in context.items() if v and v != 'unknown'}
            
            if st.button(f"🔍 {COPY['found_something']['assess_button']}", width="stretch"):
                with st.spinner(COPY["found_something"]["spinner_photo"]):
                    assessment = assessor.assess_from_photo(image, context if 'context' in locals() else None)
                    
                    st.markdown(f"### {COPY['found_something']['results_title']}")
                    _render_layman_summary_sections(assessment)

                    # Optional deeper narrative
                    if assessment.get('detailed_analysis'):
                        with st.expander(COPY["found_something"]["full_assessment_expander"]):
                            st.markdown(assessment['detailed_analysis'])
                            if assessment.get('sources'):
                                st.markdown(f"**{COPY['found_something']['source_snippets']}**")
                                for source in assessment['sources'][:3]:
                                    if isinstance(source, dict):
                                        source_text = source.get('content') or source.get('page_content', '')
                                    else:
                                        source_text = getattr(source, 'page_content', '')
                                    if not source_text:
                                        source_text = str(source)
                                    st.text(source_text[:500])

                    # Enhancement comparison
                    if assessment.get('visuals'):
                        st.markdown(f"#### {COPY['found_something']['enhancement_title']}")
                        cols = st.columns(3)
                        with cols[0]:
                            st.caption(COPY["found_something"]["enh_clahe"])
                            st.image(
                                assessment['visuals']['enh_clahe'],
                                caption=COPY["found_something"]["enh_clahe_caption"],
                            )
                        with cols[1]:
                            st.caption(COPY["found_something"]["enh_retinex"])
                            st.image(
                                assessment['visuals']['enh_retinex'],
                                caption=COPY["found_something"]["enh_retinex_caption"],
                            )
                        with cols[2]:
                            st.caption(COPY["found_something"]["enh_sharpen"])
                            st.image(
                                assessment['visuals']['enh_sharpen'],
                                caption=COPY["found_something"]["enh_sharpen_caption"],
                            )

                        # Preprocessing preview
                        with st.expander(COPY["found_something"]["preprocessing_expander"]):
                            pcols = st.columns(3)
                            with pcols[0]:
                                st.caption(COPY["found_something"]["pre_denoised"])
                                st.image(assessment['visuals']['pre_denosed'])
                            with pcols[1]:
                                st.caption(COPY["found_something"]["pre_shadow"])
                                st.image(assessment['visuals']['pre_shadow_reduced'])
                            with pcols[2]:
                                st.caption(COPY["found_something"]["pre_normalized"])
                                st.image(assessment['visuals']['pre_normalized'])

                    if assessment.get('similar_finds'):
                        st.markdown(f"#### {COPY['found_something']['similar_finds_title']}")
                        st.caption(COPY["found_something"]["similar_finds_caption"])
                        for item in assessment['similar_finds']:
                            title = item.get('title', 'Untitled result')
                            source = item.get('source', 'External source')
                            description = item.get('description', '')
                            url = item.get('url', '')
                            image_url = item.get('image_url', '')
                            with st.container(border=True):
                                st.markdown(f"**{title}**")
                                st.caption(source)
                                if description:
                                    st.write(description)
                                meta_bits = [bit for bit in [item.get('date', ''), item.get('material', '')] if bit]
                                if meta_bits:
                                    st.caption(" | ".join(meta_bits))
                                if image_url:
                                    st.image(image_url, width=220)
                                if url:
                                    st.markdown(f"[Open record]({url})")
                    else:
                        st.caption(COPY["found_something"]["no_similar_finds"])

                    # Recommendations
                    st.markdown(f"#### {COPY['found_something']['recommendations_title']}")
                    for rec in assessment.get('recommendations', []):
                        st.markdown(f"- {rec}")

                    # Technical/advanced details
                    with st.expander(COPY["found_something"]["technical_expander"]):
                        st.markdown(f"**{COPY['found_something']['technical_payload']}**")
                        st.json(assessment.get('analysis', {}))

                        if assessment.get('analysis', {}).get('ocr_notes'):
                            st.info(assessment['analysis']['ocr_notes'])

                        # OCR overlays and interactive zoom
                        if assessment.get('analysis', {}).get('ocr'):
                            st.markdown(f"**{COPY['found_something']['detected_regions']}**")
                            st.image(
                                assessment['visuals'].get('boxed', None),
                                caption=COPY["found_something"]["detected_regions_caption"],
                            )
                            ocr_items = assessment['analysis']['ocr']
                            # Build simple table
                            import pandas as _pd
                            table = _pd.DataFrame([
                                {
                                    'index': i + 1,
                                    'text': item.get('text', ''),
                                    'confidence': round(float(item.get('confidence', 0.0)), 3),
                                    'top_candidates': ' | '.join(item.get('top_candidates', [])[:3]),
                                }
                                for i, item in enumerate(ocr_items)
                            ])
                            st.dataframe(table, width="stretch")

                            if assessment['analysis'].get('detected_text'):
                                st.caption(
                                    COPY["found_something"]["detected_text_summary"].format(
                                        text=assessment['analysis']['detected_text']
                                    )
                                )
                            st.caption(
                                COPY["found_something"]["text_reader_note"].format(
                                    backend=assessment['analysis'].get('ocr_backend', 'unknown')
                                )
                            )

                            selected_idx = st.number_input(
                                COPY["found_something"]["zoom_region_label"],
                                min_value=1,
                                max_value=len(ocr_items),
                                value=1,
                                step=1,
                            )
                            if selected_idx:
                                from image_analyzer import crop_box
                                box = ocr_items[selected_idx - 1]['box']
                                zoom = crop_box(image, box)
                                st.image(zoom, caption=f"Zoomed region #{selected_idx}")
                                candidates = ocr_items[selected_idx - 1].get('top_candidates', [])
                                if candidates:
                                    st.markdown(f"**{COPY['found_something']['suggested_readings']}**")
                                    for candidate in candidates:
                                        st.markdown(f"- {candidate}")

                                # Manual correction feedback
                                correction = st.text_input(COPY["found_something"]["correction_label"])
                                if st.button(
                                    COPY["found_something"]["save_correction_button"],
                                    key=f"save_corr_{selected_idx}",
                                ):
                                    import json, os
                                    os.makedirs("user_data", exist_ok=True)
                                    corr_path = os.path.join("user_data", "corrections.json")
                                    data = []
                                    if os.path.exists(corr_path):
                                        try:
                                            with open(corr_path, "r", encoding="utf-8") as f:
                                                data = json.load(f)
                                        except Exception:
                                            data = []
                                    entry = {
                                        'timestamp': datetime.now().isoformat(),
                                        'file_name': uploaded_image.name,
                                        'region_index': int(selected_idx),
                                        'box': box,
                                        'suggestion': correction,
                                        'context': context if 'context' in locals() else {}
                                    }
                                    data.append(entry)
                                    with open(corr_path, "w", encoding="utf-8") as f:
                                        json.dump(data, f, ensure_ascii=False, indent=2)
                                    st.success(COPY["found_something"]["correction_saved"])
    
    else:  # Text Description
        st.markdown(f"### {COPY['found_something']['text_option_title']}")
        st.caption(COPY["found_something"]["text_option_caption"])
        
        template = assessor.get_guided_questions_template()
        description = {}
        
        # Material
        description['material'] = st.selectbox(
            template['material']['question'],
            template['material']['options'],
            key="desc_material"
        )
        
        # Size
        description['size'] = st.selectbox(
            template['size']['question'],
            template['size']['options'],
            key="desc_size"
        )
        
        # Location
        description['location'] = st.selectbox(
            template['location']['question'],
            template['location']['options'],
            key="desc_location"
        )
        
        # Markings (optional)
        description['markings'] = st.text_area(
            template['markings']['question'],
            key="desc_markings",
            help=COPY["found_something"]["markings_help"],
        )
        
        # Additional notes (optional)
        description['additional_notes'] = st.text_area(
            template['additional_notes']['question'],
            key="desc_notes",
            height=100
        )
        
        if st.button(f"🔍 {COPY['found_something']['assess_button']}", width="stretch"):
            with st.spinner(COPY["found_something"]["spinner_text"]):
                assessment = assessor.assess_from_text(description, st.session_state.rag_chain if st.session_state.vector_store_initialized else None)
                
                st.markdown(f"### {COPY['found_something']['results_title']}")

                st.markdown(f"#### {COPY['found_something']['your_description']}")
                st.markdown(assessment['analysis'].get('full_description', ''))

                _render_layman_summary_sections(assessment)
                
                # Detailed assessment
                if assessment.get('detailed_analysis'):
                    st.markdown(f"#### {COPY['found_something']['detailed_assessment']}")
                    st.markdown(assessment['detailed_analysis'])
                    
                    if assessment.get('sources'):
                        with st.expander(f"📖 {COPY['found_something']['view_sources']}"):
                            for source in assessment['sources'][:3]:
                                if isinstance(source, dict):
                                    source_text = source.get('content') or source.get('page_content', '')
                                else:
                                    source_text = getattr(source, 'page_content', '')
                                if not source_text:
                                    source_text = str(source)
                                st.text(source_text[:500])
                
                # Recommendations
                st.markdown(f"#### {COPY['found_something']['recommendations']}")
                for rec in assessment.get('recommendations', []):
                    st.markdown(f"- {rec}")


def main():
    """Main application entry point."""
    initialize_session_state()

    _render_sidebar()

    chat_tab, found_tab, photo_tab, viz_tab, docs_tab, compliance_tab = st.tabs(
        [
            "💬 Chat & Analysis",
            "🔍 Found Something?",
            "📸 Photo Organizer",
            "📊 Maps & Timelines",
            "📄 Docs & Glossary",
            "⚖️ Compliance & Templates",
        ]
    )

    with chat_tab:
        _render_chat_tab()
    
    with found_tab:
        _render_found_something_tab()
    
    with photo_tab:
        _render_photo_organizer_tab()

    with viz_tab:
        _render_visualisations_tab()

    with docs_tab:
        _render_docs_glossary_tab()

    with compliance_tab:
        _render_compliance_tools_tab()


if __name__ == "__main__":
    main()

