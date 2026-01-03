"""
Streamlit Web Application for Archaeological Survey RAG Chatbot
Enhanced UI with visualization and archaeology-specific tools.
"""

import os
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st

from pdf_processor import PDFProcessor
from rag_chain import ArchaeologicalRAGChain
from vector_store import VectorStoreManager
from photo_organizer import PhotoOrganizer
from artifact_assessment import ArtifactAssessment
from user_manager import UserManager, StreamlitSessionManager
from report_generator import ReportGenerator
from PIL import Image
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    if 'user_manager' not in st.session_state:
        st.session_state.user_manager = UserManager()
    if 'session_manager' not in st.session_state:
        st.session_state.session_manager = StreamlitSessionManager(st.session_state.user_manager)
    if 'show_registration' not in st.session_state:
        st.session_state.show_registration = False


def process_pdf_and_create_vector_store(pdf_path: str):
    """Process PDF and create vector store"""
    try:
        with st.spinner("Processing PDF document..."):
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
                    st.info(f"📊 Auto-extracted: {', '.join(extraction_summary)} from PDF")
            except Exception as e:  # pragma: no cover
                logger.warning(f"Auto-extraction for maps/timelines failed: {e}")
                st.session_state.sites_df = None
                st.session_state.timeline_df = None
                st.session_state.sites_list = None
            
            if not text_chunks:
                st.error("No text could be extracted from the PDF.")
                return False
            
            st.success(f"Extracted {len(text_chunks)} text chunks from PDF")
            
            # Create vector store
            with st.spinner("Creating vector embeddings..."):
                vector_store_manager = VectorStoreManager(
                    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
                    vector_store_type="faiss",
                    persist_directory="./vector_store"
                )
                vector_store_manager.create_vector_store(text_chunks)
                st.session_state.vector_store_manager = vector_store_manager
                st.session_state.vector_store_initialized = True
                st.success("Vector store created successfully!")
            
            # Initialize RAG chain
            with st.spinner("Initializing RAG chain..."):
                try:
                    rag_chain = ArchaeologicalRAGChain(
                        vector_store_manager=vector_store_manager,
                        model_name="gpt-3.5-turbo",
                        temperature=0.7
                    )
                    st.session_state.rag_chain = rag_chain
                    st.success("RAG system ready!")
                    return True
                except Exception as e:
                    st.error(f"Error initializing RAG chain: {str(e)}")
                    st.info("Please make sure you have set OPENAI_API_KEY in your .env file")
                    return False
                    
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        return False


def load_existing_vector_store():
    """Load existing vector store if available"""
    try:
        vector_store_manager = VectorStoreManager(
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            vector_store_type="faiss",
            persist_directory="./vector_store"
        )
        vector_store_manager.load_vector_store()
        st.session_state.vector_store_manager = vector_store_manager
        st.session_state.vector_store_initialized = True
        
        # Initialize RAG chain
        rag_chain = ArchaeologicalRAGChain(
            vector_store_manager=vector_store_manager,
            model_name="gpt-3.5-turbo",
            temperature=0.7
        )
        st.session_state.rag_chain = rag_chain
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
    """Sidebar: document setup + quick tools."""
    with st.sidebar:
        # User Authentication Section
        st.header("🔐 Account")
        
        session_manager = st.session_state.session_manager
        user_manager = st.session_state.user_manager
        current_user = session_manager.get_current_user(st.session_state)
        
        if current_user:
            # User is logged in
            st.success(f"👤 {current_user['name']}")
            st.caption(f"Role: {current_user['role']}")
            if st.button("🚪 Logout", use_container_width=True):
                session_manager.logout(st.session_state)
                st.rerun()
        else:
            # User is not logged in
            if not st.session_state.show_registration:
                # Login form
                st.subheader("Login")
                login_email = st.text_input("Email", key="login_email")
                login_password = st.text_input("Password", type="password", key="login_password")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔑 Login", use_container_width=True):
                        if login_email and login_password:
                            result = session_manager.login(st.session_state, login_email, login_password)
                            if result['success']:
                                st.success(result['message'])
                                st.rerun()
                            else:
                                st.error(result['message'])
                        else:
                            st.warning("Please enter email and password")
                
                with col2:
                    if st.button("📝 Register", use_container_width=True):
                        st.session_state.show_registration = True
                        st.rerun()
            else:
                # Registration form
                st.subheader("Register")
                reg_name = st.text_input("Name", key="reg_name")
                reg_email = st.text_input("Email", key="reg_email")
                reg_password = st.text_input("Password", type="password", key="reg_password")
                reg_role = st.selectbox(
                    "Role",
                    options=['public', 'student', 'professional'],
                    format_func=lambda x: user_manager.USER_ROLES.get(x, x),
                    key="reg_role"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Create Account", use_container_width=True):
                        if reg_name and reg_email and reg_password:
                            result = user_manager.register_user(reg_email, reg_password, reg_role, reg_name)
                            if result['success']:
                                st.success(result['message'])
                                st.session_state.show_registration = False
                                st.rerun()
                            else:
                                st.error(result['message'])
                        else:
                            st.warning("Please fill all fields")
                
                with col2:
                    if st.button("← Back to Login", use_container_width=True):
                        st.session_state.show_registration = False
                        st.rerun()
        
        st.markdown("---")
        st.header("📚 Document Setup")
        
        # Check if vector store exists
        vector_store_path = Path("./vector_store")
        if vector_store_path.exists() and st.session_state.vector_store_initialized is False:
            if st.button("Load Existing Vector Store", use_container_width=True):
                if load_existing_vector_store():
                    st.success("Vector store loaded!")
                else:
                    st.error("Failed to load vector store")
        
        # PDF upload
        st.subheader("Upload PDF Document")
        pdf_file = st.file_uploader(
            "Choose a PDF file",
            type=["pdf"],
            help="Upload the archaeological survey PDF document",
        )
        
        if pdf_file is not None:
            st.session_state.uploaded_pdf_name = pdf_file.name
            # Save uploaded file temporarily
            pdf_path = f"./temp_{pdf_file.name}"
            with open(pdf_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            
            if st.button("⚙️ Process PDF and Initialize", use_container_width=True):
                success = process_pdf_and_create_vector_store(pdf_path)
                if success and os.path.exists(pdf_path):
                        os.remove(pdf_path)
        
        # Default PDF path
        st.subheader("Or Use Default PDF")
        possible_paths = [
            "../archelogical pdf pr0ooject.pdf",
            "archelogical pdf pr0ooject.pdf",
            "../archelogical pdf pr0ooject.pdf",
        ]
        default_pdf_path = None
        for path in possible_paths:
            if os.path.exists(path):
                default_pdf_path = path
                break
        
        if default_pdf_path:
            if st.button("📄 Process Default PDF", use_container_width=True):
                _ = process_pdf_and_create_vector_store(default_pdf_path)
        else:
            st.info("Default PDF not found. Please upload a PDF file.")
        
        st.markdown("---")

        st.header("🧭 Assistant Mode")
        mode = st.selectbox(
            "What are you working on?",
            [
                "General Q&A",
                "Field Work & Analysis",
                "Documentation & Reporting",
                "Legal & Compliance",
                "Site Management",
            ],
            index=0,
            help="Choose a category to focus the assistant's expertise on your task.",
        )
        st.session_state.active_mode = mode

        st.caption(
            "💡 Tip: Make sure to set your `OPENAI_API_KEY` in a `.env` file for the chatbot to work."
        )

        st.markdown("---")
        st.subheader("Quick Starter Questions")
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
        '<div class="sub-header">Ask questions, analyse sites, plan surveys, and check compliance using your own archaeological documents.</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.vector_store_initialized and st.session_state.rag_chain:
        # Display current mode as pills
        st.markdown(
            f"**Active mode:** "
            f"<span class='pill'>{st.session_state.active_mode}</span>",
            unsafe_allow_html=True,
        )

        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "sources" in message and message["sources"]:
                    with st.expander("📖 View Sources & Locations"):
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
                        with st.expander("📖 View Sources & Locations"):
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
        # Welcome message
        st.info(
            "👋 Welcome! Upload and process a PDF document in the sidebar to unlock chat and tools."
        )
        st.markdown(
            """
            ### How to use
            1. **Upload PDF** in the sidebar (or use the default PDF if available).
            2. **Process Document** to create embeddings and initialise the RAG system.
            3. **Pick an Assistant Mode** (e.g. artifact identification, stratigraphy, permits).
            4. **Start Chatting** in this tab using archaeological language.

            ### Example questions
        - What are the key steps in conducting an archaeological survey?
            - How do I identify potential archaeological sites from this description?
            - Suggest a survey methodology for a river valley transect.
            - What legal permissions are typically required before excavation?
            - Summarise the main findings from this report.
            """
        )


def _render_visualisations_tab():
    """Maps, timelines, and simple relationship views from tabular data."""
    st.subheader("🌍 Interactive Site Map")
    st.caption(
        "If your PDF contains coordinates, the map will be pre-populated automatically. "
        "You can also upload a CSV with `site_name`, `latitude`, `longitude`, and optional `period` columns."
    )

    auto_sites_df = st.session_state.get("sites_df")
    if auto_sites_df is not None and not auto_sites_df.empty:
        st.markdown("**Automatically extracted from PDF:**")
        # Use site_name in map if available, otherwise show coordinates
        map_df = auto_sites_df[["latitude", "longitude"]].copy()
        if "site_name" in auto_sites_df.columns:
            # Add site_name as a column for better display
            map_df["site_name"] = auto_sites_df["site_name"].fillna("Unnamed Site")
        st.map(map_df)
        with st.expander("View extracted site coordinates"):
            # Show site_name prominently if available
            display_cols = ["latitude", "longitude"]
            if "site_name" in auto_sites_df.columns:
                display_cols = ["site_name"] + display_cols
            if "context" in auto_sites_df.columns:
                display_cols.append("context")
            st.dataframe(auto_sites_df[display_cols], use_container_width=True)

    site_file = st.file_uploader(
        "Optionally upload additional site CSV for mapping", type=["csv"], key="map_csv"
    )
    if site_file is not None:
        df_sites = pd.read_csv(site_file)
        required_cols = {"latitude", "longitude"}
        if required_cols.issubset(df_sites.columns):
            st.markdown("**From uploaded CSV:**")
            st.map(df_sites[["latitude", "longitude"]])
            with st.expander("View uploaded site table"):
                st.dataframe(df_sites, use_container_width=True)
        else:
            st.error(
                f"CSV must include at least: {', '.join(required_cols)}. "
                f"Found columns: {list(df_sites.columns)}"
            )

    st.markdown("---")
    st.subheader("⏳ Timeline of Excavations / Surveys")
    st.caption(
        "If your PDF mentions years or year ranges, a basic timeline will be built automatically. "
        "You can also upload a CSV with `site_name`, `start_year`, and optional `end_year`."
    )

    auto_time_df = st.session_state.get("timeline_df")
    if auto_time_df is not None and not auto_time_df.empty:
        st.markdown("**Automatically extracted from PDF (labelled by context):**")
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
            st.altair_chart(auto_chart, use_container_width=True)
        except Exception as e:  # pragma: no cover
            st.error(f"Could not render automatic timeline chart: {e}")
            st.dataframe(auto_time_df)

    timeline_file = st.file_uploader(
        "Optionally upload additional timeline CSV", type=["csv"], key="timeline_csv"
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
                    st.altair_chart(timeline, use_container_width=True)
                except Exception as e:  # pragma: no cover
                    st.error(f"Could not render timeline chart: {e}")
                    st.dataframe(df_time)
            else:
                st.warning("No valid rows after parsing years.")
        else:
            st.error(
                "Timeline CSV must include at least `site_name` and `start_year` columns."
            )

    st.markdown("---")
    st.subheader("🕸️ Simple Knowledge Graph (Sites ↔ Periods)")
    st.caption(
        "Based on the same CSVs, you can start to think of relationships between sites, periods, and regions."
    )
    
    # Show extracted sites if available
    sites_list = st.session_state.get("sites_list")
    if sites_list:
        st.markdown("**Sites extracted from PDF:**")
        sites_df_display = pd.DataFrame(sites_list)
        st.dataframe(sites_df_display[["site_name", "site_type", "context"]], use_container_width=True)
        st.caption(f"Found {len(sites_list)} site(s) in the document")
    
    st.markdown(
        """
        This basic view encourages you to think in terms of **connections**:
        - Sites linked to **periods** and **regions**
        - Artifacts linked to **contexts** and **strata**

        For a full interactive knowledge graph, you can later export your site table to tools
        like Neo4j, Gephi, or dedicated graph-visualisation platforms.
        """
    )


def _render_docs_glossary_tab():
    """Document‑oriented tools: source snippets, glossary, and highlighting helper."""
    st.subheader("📄 Document & Source Viewer")
    st.caption(
        "When the assistant answers from your PDF, the **Sources** section in the chat tab shows "
        "the exact text chunks and any page/metadata available."
    )

    if st.session_state.uploaded_pdf_name:
        st.info(f"Most recent uploaded PDF: **{st.session_state.uploaded_pdf_name}**")

    st.markdown(
        """
        **Highlighting tip:**  
        To quickly see where an answer came from:
        1. Open the **chat tab** and expand *“View Sources & Locations”* under a message.
        2. Look at the surrounding text and any page / chunk information.
        3. Use that page number in your own PDF viewer to jump to the exact place.
        """
    )

    st.markdown("---")
    st.subheader("📘 Archaeological Terminology Glossary")

    glossary = {
        "Context": "A discrete unit of stratigraphy representing a single event of deposition or cut.",
        "Stratigraphy": "The study and recording of layered deposits and their relationships over time.",
        "Feature": "A non-portable archaeological element such as a pit, ditch, wall, or hearth.",
        "Assemblage": "A group of artifacts found together in the same context, interpreted as related.",
        "Phase": "A group of contexts interpreted as belonging to the same broad period of activity.",
        "Datum": "A fixed reference point used for surveying and recording elevations.",
        "Transect": "A systematic survey line or corridor walked during field survey.",
    }

    term = st.selectbox("Look up a term:", sorted(glossary.keys()))
    st.write(f"**{term}**: {glossary[term]}")

    with st.expander("Show full glossary"):
        for k, v in glossary.items():
            st.markdown(f"- **{k}**: {v}")


def _render_compliance_tools_tab():
    """Regulatory, methodology, reporting, and citation helpers (prompt-based)."""
    st.subheader("⚖️ Regulatory & Compliance Helper")
    st.caption(
        "These tools use your documents plus general archaeological knowledge. "
        "Always verify against current local legislation."
    )

    col1, col2 = st.columns(2)

    with col1:
        permit_notes = st.text_area(
            "Describe your project and location for permit guidance",
            placeholder="e.g. fieldwalking survey near a river in [region], with planned shovel test pits...",
            height=120,
        )
        if st.button("Generate permit requirement checklist") and permit_notes:
            if not (
                st.session_state.vector_store_initialized
                and st.session_state.rag_chain
            ):
                st.error("Please process a PDF first so the assistant has context.")
            else:
                with st.spinner("Checking likely permits and legal steps..."):
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
            "Reporting / compliance details",
            placeholder="Summarise your project, methods, and key findings to draft a report template...",
            height=120,
        )
        if st.button("Draft reporting template / outline"):
            if not (
                st.session_state.vector_store_initialized
                and st.session_state.rag_chain
            ):
                st.error("Please process a PDF first so the assistant has context.")
            else:
                with st.spinner("Drafting a structured report outline..."):
                    prompt = (
                        "Generate a structured archaeological compliance report template. "
                        "Use headings and bullet points. Tailor it to the following project context:\n\n"
                        f"{report_context}"
                    )
                    result = st.session_state.rag_chain.query(prompt)
                    st.markdown(result["answer"])

    st.markdown("---")
    st.subheader("📝 Survey Methodology Template")
    meth_context = st.text_area(
        "Survey parameters (environment, aims, constraints)",
        placeholder="e.g. intensive pedestrian survey over 5 km² of agricultural land...",
        height=120,
    )
    if st.button("Generate methodology template"):
        if not (
            st.session_state.vector_store_initialized and st.session_state.rag_chain
        ):
            st.error("Please process a PDF first so the assistant has context.")
        else:
            with st.spinner("Building a methodology template..."):
                prompt = (
                    "Create a detailed survey methodology template for this project, "
                    "including sampling strategy, recording system, and data management:\n\n"
                    f"{meth_context}"
                )
                result = st.session_state.rag_chain.query(prompt)
                st.markdown(result["answer"])

    st.markdown("---")
    st.subheader("📝 Report Generator")
    
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
        "Report Type",
        options=list(ReportGenerator.REPORT_TYPES.keys()),
        format_func=lambda x: ReportGenerator.REPORT_TYPES[x],
        key="report_type_select"
    )
    
    # Collect project data (simplified - in production would load from data manager)
    project_data = {
        'project_name': st.text_input("Project Name", value="Archaeological Investigation", key="report_project_name"),
        'location': st.text_input("Location", key="report_location"),
        'sites': st.session_state.sites_list or [],
        'artifacts': [],  # Would load from data manager
        'methodology': {},
    }
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📄 Generate Report", use_container_width=True, key="generate_report_btn"):
            with st.spinner("Generating report..."):
                report_content = st.session_state.report_generator.generate_report(
                    report_type, project_data
                )
                st.session_state.generated_report = report_content
                st.session_state.report_type_generated = report_type
    
    with col2:
        if st.button("💾 Export Report", use_container_width=True, key="export_report_btn", disabled='generated_report' not in st.session_state):
            if 'generated_report' in st.session_state:
                report_filename = f"{report_type}_report_{datetime.now().strftime('%Y%m%d')}.md"
                st.download_button(
                    "Download Report",
                    data=st.session_state.generated_report,
                    file_name=report_filename,
                    mime="text/markdown",
                    key="download_report_btn"
                )
    
    if 'generated_report' in st.session_state:
        st.markdown("### Generated Report Preview")
        st.markdown(st.session_state.generated_report)
    
    st.markdown("---")
    st.subheader("📚 Citation Generator")
    citation_info = st.text_area(
        "Enter bibliographic details (author, year, title, publisher, etc.)",
        placeholder="e.g. Renfrew, C. and Bahn, P. 2016. Archaeology: Theories, Methods and Practice. London: Thames & Hudson.",
        height=120,
    )
    style = st.selectbox(
        "Preferred style", ["Harvard", "Chicago", "APA", "Custom archaeological"], index=0
    )
    if st.button("Format citation"):
        if not (
            st.session_state.vector_store_initialized and st.session_state.rag_chain
        ):
            st.error("Please process a PDF first so the assistant has context.")
        else:
            with st.spinner("Formatting citation..."):
                prompt = (
                    f"Format the following bibliographic details as a {style} style citation. "
                    f"If information is missing, clearly mark it with placeholders:\n\n"
                    f"{citation_info}"
                )
                result = st.session_state.rag_chain.query(prompt)
                st.markdown(result["answer"])


def _render_photo_organizer_tab():
    """Dig Photo Organizer - auto-organize photos by trench/locus, artifact types, etc."""
    st.subheader("📸 Dig Photo Organizer")
    st.caption(
        "Upload or select a directory of dig photos to automatically organize them by trench, locus, "
        "artifact type, stratigraphy, and date. Generate field reports and find duplicates."
    )
    
    # Directory input or file upload
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Option 1: Scan Directory")
        photo_dir = st.text_input(
            "Enter photo directory path:",
            placeholder="C:/path/to/photos or ./photos",
            help="Enter the full path to a directory containing photos"
        )
        if st.button("Scan Directory", use_container_width=True) and photo_dir:
            try:
                organizer = PhotoOrganizer(photo_dir)
                photos = organizer.scan_directory()
                st.session_state.photo_organizer = organizer
                st.success(f"Found {len(photos)} photos!")
            except Exception as e:
                st.error(f"Error scanning directory: {e}")
    
    with col2:
        st.markdown("### Option 2: Upload Photos")
        uploaded_files = st.file_uploader(
            "Upload photos",
            type=['jpg', 'jpeg', 'png', 'tiff', 'tif'],
            accept_multiple_files=True,
            help="Upload multiple photos to organize"
        )
        if uploaded_files:
            # Create temporary directory and save files
            temp_dir = Path("./temp_photos")
            temp_dir.mkdir(exist_ok=True)
            for uploaded_file in uploaded_files:
                with open(temp_dir / uploaded_file.name, "wb") as f:
                    f.write(uploaded_file.getbuffer())
            try:
                organizer = PhotoOrganizer(str(temp_dir))
                photos = organizer.scan_directory()
                st.session_state.photo_organizer = organizer
                st.success(f"Processed {len(photos)} photos!")
            except Exception as e:
                st.error(f"Error processing photos: {e}")
    
    # Display organization options
    if st.session_state.photo_organizer and st.session_state.photo_organizer.photos:
        organizer = st.session_state.photo_organizer
        
        st.markdown("---")
        st.markdown("### Organize Photos")
        
        org_method = st.radio(
            "Organize by:",
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
                            st.image(img, use_container_width=True, caption=photo['file_name'])
                        except:
                            st.text(photo['file_name'])
        
        st.markdown("---")
        st.markdown("### Reports & Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Generate Field Report", use_container_width=True):
                report = organizer.generate_field_report()
                st.text_area("Field Report", report, height=400)
                st.download_button(
                    "Download Report",
                    data=report,
                    file_name="field_report.md",
                    mime="text/markdown"
                )
        
        with col2:
            if st.button("🔍 Find Duplicates", use_container_width=True):
                duplicates = organizer.find_duplicates()
                if duplicates:
                    st.warning(f"Found {len(duplicates)} potential duplicate groups")
                    for idx, group in enumerate(duplicates[:5]):  # Show first 5 groups
                        with st.expander(f"Duplicate Group {idx + 1}"):
                            for photo in group:
                                st.text(f"- {photo['file_name']} ({photo.get('file_size', 0)} bytes)")
                else:
                    st.success("No duplicates found!")
        
        # Statistics
        with st.expander("📈 Statistics"):
            stats = organizer.get_statistics()
            st.json(stats)


def _render_found_something_tab():
    """Found Something? - Artifact assessment with photo upload and text description."""
    st.subheader("🔍 Found Something?")
    st.caption(
        "Upload a photo or describe what you found. Get expert assessment, identification help, "
        "and recommendations for next steps."
    )
    
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
        "How would you like to submit your find?",
        ["📷 Photo Upload", "✍️ Text Description"],
        horizontal=True
    )
    
    st.markdown("---")
    
    if input_method == "📷 Photo Upload":
        st.markdown("### Option A: Upload Photo")
        uploaded_image = st.file_uploader(
            "Upload photo of artifact",
            type=['jpg', 'jpeg', 'png', 'tiff', 'tif'],
            help="Upload a clear photo of what you found"
        )
        
        if uploaded_image:
            image = Image.open(uploaded_image)
            st.image(image, caption="Uploaded Image", width=400)
            
            # Optional context
            with st.expander("Add Context (Optional)"):
                context = {
                    'material': st.selectbox("Material", ['unknown', 'stone', 'metal', 'pottery', 'bone', 'glass', 'organic']),
                    'size': st.selectbox("Size", ['unknown', 'coin-sized', 'hand-sized', 'larger', 'very large']),
                    'location': st.selectbox("Location found", ['unknown', 'garden', 'construction site', 'beach', 'field', 'archaeological site', 'other']),
                    'markings': st.text_area("Markings or decorations", ""),
                }
                context = {k: v for k, v in context.items() if v and v != 'unknown'}
            
            if st.button("🔍 Assess Artifact", use_container_width=True):
                with st.spinner("Analyzing artifact..."):
                    assessment = assessor.assess_from_photo(image, context if 'context' in locals() else None)
                    
                    st.markdown("### Assessment Results")
                    
                    # Basic analysis
                    st.markdown("#### Image Analysis")
                    st.json(assessment['analysis'])
                    
                    # Detailed assessment
                    if assessment.get('detailed_analysis'):
                        st.markdown("#### Detailed Assessment")
                        st.markdown(assessment['detailed_analysis'])
                        
                        if assessment.get('sources'):
                            with st.expander("📖 View Sources"):
                                for source in assessment['sources'][:3]:
                                    st.text(source.get('content', '')[:500])
                    
                    # Recommendations
                    st.markdown("#### Recommendations")
                    for rec in assessment.get('recommendations', []):
                        st.markdown(f"- {rec}")
    
    else:  # Text Description
        st.markdown("### Option B: Text Description")
        st.caption("Answer the guided questions to describe what you found")
        
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
            help="Describe any markings, inscriptions, or decorative elements"
        )
        
        # Additional notes (optional)
        description['additional_notes'] = st.text_area(
            template['additional_notes']['question'],
            key="desc_notes",
            height=100
        )
        
        if st.button("🔍 Assess Artifact", use_container_width=True):
            with st.spinner("Analyzing artifact description..."):
                assessment = assessor.assess_from_text(description, st.session_state.rag_chain if st.session_state.vector_store_initialized else None)
                
                st.markdown("### Assessment Results")
                
                # Description summary
                st.markdown("#### Your Description")
                st.markdown(assessment['analysis'].get('full_description', ''))
                
                # Detailed assessment
                if assessment.get('detailed_analysis'):
                    st.markdown("#### Detailed Assessment")
                    st.markdown(assessment['detailed_analysis'])
                    
                    if assessment.get('sources'):
                        with st.expander("📖 View Sources"):
                            for source in assessment['sources'][:3]:
                                st.text(source.get('content', '')[:500])
                
                # Recommendations
                st.markdown("#### Recommendations")
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

