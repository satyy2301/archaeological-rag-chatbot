"""
Streamlit Web Application for Archaeological Survey RAG Chatbot
Enhanced UI with visualization and archaeology-specific tools.
"""

import os
from pathlib import Path

import pandas as pd
import streamlit as st

from pdf_processor import PDFProcessor
from rag_chain import ArchaeologicalRAGChain
from vector_store import VectorStoreManager
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
    mapping = {
        "General Q&A": "",
        "Artifact identification": (
            "You are helping identify archaeological artifacts from textual descriptions. "
            "Ask for material, form, decoration, context, and stratigraphic information when needed. "
        ),
        "Dating assistance": (
            "You are assisting with dating archaeological materials and contexts. "
            "Discuss relative and absolute dating methods, their limitations, and confidence levels. "
        ),
        "Stratigraphy analysis": (
            "You are interpreting stratigraphic sequences. Focus on superposition, interfaces, "
            "cuts, fills, and formation processes. "
        ),
        "Site preservation": (
            "You are advising on conservation and site preservation. Consider physical, chemical, "
            "and human threats and recommend minimally invasive strategies. "
        ),
        "Site classification": (
            "You are classifying archaeological sites based on descriptions, function, period, and setting. "
        ),
        "Permit & legal compliance": (
            "You are guiding the user about permits, heritage laws, and legal compliance. "
            "Always remind them to check the latest local regulations and consult authorities. "
        ),
        "Reporting & methodology templates": (
            "You are helping draft structured templates for survey methodologies and compliance reports. "
        ),
        "Ethical guidelines": (
            "You are explaining ethical guidelines in archaeology, with emphasis on local communities "
            "and long-term conservation. "
        ),
        "Citation help": (
            "You are generating properly formatted citations and bibliographic entries from the provided information. "
        ),
        "Terminology help": (
            "You are explaining archaeological terminology in clear, concise language for students and practitioners. "
        ),
    }
    return mapping.get(mode, "")


def _render_sidebar():
    """Sidebar: document setup + quick tools."""
    with st.sidebar:
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
                "Artifact identification",
                "Dating assistance",
                "Stratigraphy analysis",
                "Site preservation",
                "Site classification",
                "Permit & legal compliance",
                "Reporting & methodology templates",
                "Ethical guidelines",
                "Citation help",
                "Terminology help",
            ],
            index=0,
            help="This gently steers the assistant towards the kind of help you need.",
        )
        st.session_state.active_mode = mode

        st.caption(
            "💡 Tip: Make sure to set your `OPENAI_API_KEY` in a `.env` file for the chatbot to work."
        )

        st.markdown("---")
        st.subheader("Quick Starter Questions")
        examples = {
            "Artifact identification": "Describe this artifact and suggest possible identifications:",
            "Dating assistance": "Given this context, what dating methods would be appropriate?",
            "Stratigraphy analysis": "Help me interpret this stratigraphic sequence:",
            "Site preservation": "What preservation strategy would you recommend for this site?",
            "Permit & legal compliance": "What permits might be required for a survey in this region?",
            "Reporting & methodology templates": "Generate a survey methodology template for a walkover survey.",
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


def main():
    """Main application entry point."""
    initialize_session_state()

    _render_sidebar()

    chat_tab, viz_tab, docs_tab, compliance_tab = st.tabs(
        [
            "💬 Chat & Analysis",
            "📊 Maps & Timelines",
            "📄 Docs & Glossary",
            "⚖️ Compliance & Templates",
        ]
    )

    with chat_tab:
        _render_chat_tab()

    with viz_tab:
        _render_visualisations_tab()

    with docs_tab:
        _render_docs_glossary_tab()

    with compliance_tab:
        _render_compliance_tools_tab()


if __name__ == "__main__":
    main()

