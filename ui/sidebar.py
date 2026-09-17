"""Lab sidebar: API key, document status, station navigator, and quick prompts."""

import streamlit as st

from lab.services import initialize_rag_chain_with_current_key
from ui.components import render_session_hud, render_station_nav


def render_sidebar() -> None:
    """Sidebar: API key, session status, station nav, assistant mode, quick prompts."""
    with st.sidebar:
        with st.container(border=True):
            st.markdown('<p class="sidebar-section-label">API Key</p>', unsafe_allow_html=True)
            st.caption("Paste your OpenAI API key for this browser session.")
            entered_key = st.text_input(
                "OpenAI API Key",
                type="password",
                value=st.session_state.user_openai_api_key,
                placeholder="sk-...",
                label_visibility="collapsed",
                help="Not stored in files or database. Cleared when session ends.",
            )
            st.session_state.user_openai_api_key = entered_key

            col_key1, col_key2 = st.columns(2)
            with col_key1:
                if st.button("Apply", use_container_width=True, type="primary"):
                    if st.session_state.vector_store_initialized and st.session_state.vector_store_manager:
                        initialize_rag_chain_with_current_key()
                    else:
                        st.success("Key saved for this session.")
            with col_key2:
                if st.button("Clear", use_container_width=True):
                    st.session_state.user_openai_api_key = ""
                    st.info("Session key cleared.")

        st.divider()

        with st.container(border=True):
            st.markdown('<p class="sidebar-section-label">Session Status</p>', unsafe_allow_html=True)
            render_session_hud(compact=True)

        if st.session_state.vector_store_initialized:
            st.success(f"**{st.session_state.uploaded_pdf_name or 'Document'}** loaded")
            if st.button("Load a different document", use_container_width=True):
                st.session_state.vector_store_initialized = False
                st.session_state.rag_chain = None
                st.session_state.vector_store_manager = None
                st.session_state.uploaded_pdf_name = None
                st.session_state.messages = []
                st.session_state.onboarding_step = 2
                st.session_state.active_station = "document_desk"
                st.rerun()
            st.divider()

        st.markdown('<p class="sidebar-section-label">Lab Stations</p>', unsafe_allow_html=True)
        with st.container(border=True):
            render_station_nav()

        st.divider()

        with st.container(border=True):
            st.markdown('<p class="sidebar-section-label">Assistant Mode</p>', unsafe_allow_html=True)
            mode = st.selectbox(
                "Focus area",
                [
                    "General Q&A",
                    "Field Work & Analysis",
                    "Documentation & Reporting",
                    "Legal & Compliance",
                    "Site Management",
                ],
                index=0,
                label_visibility="collapsed",
                help="Choose a category to focus the assistant's expertise on your task.",
            )
            st.session_state.active_mode = mode

        st.caption("Tip: set OPENAI_API_KEY in .env as an alternative.")

        with st.expander("Quick prompts", expanded=False):
            examples = {
                "Field Work": "Help me identify this artifact and determine appropriate dating methods:",
                "Documentation": "Generate a survey methodology template for a walkover survey:",
                "Legal & Compliance": "What permits might be required for a survey in this region?",
                "Site Management": "What preservation strategy would you recommend for this site?",
            }
            for label, prompt in examples.items():
                if st.button(label, key=f"q_{label}", use_container_width=True):
                    st.session_state.messages.append(
                        {"role": "user", "content": prompt + " (replace with your details)."}
                    )
                    st.session_state.active_station = "document_desk"
                    st.rerun()
