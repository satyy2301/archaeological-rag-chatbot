"""Document Intelligence Desk — RAG chat station."""

import streamlit as st

from lab.services import build_mode_preface
from ui.components import render_station_header


def render() -> None:
    """Main chat experience with archaeology-specific modes."""
    render_station_header("document_desk")

    if st.session_state.vector_store_initialized and st.session_state.rag_chain:
        with st.container(border=True):
            st.markdown(
                f"**Active mode:** "
                f"<span class='pill'>{st.session_state.active_mode}</span>",
                unsafe_allow_html=True,
            )

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "sources" in message and message["sources"]:
                    with st.expander("Sources"):
                        for source in message["sources"]:
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

        placeholder = "Ask a question about archaeological surveys, sites, or regulations..."
        if prompt := st.chat_input(placeholder):
            preface = build_mode_preface(st.session_state.active_mode)
            full_prompt = f"{preface} User question: {prompt}" if preface else prompt

            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Thinking with your archaeological documents..."):
                    result = st.session_state.rag_chain.query(full_prompt)
                    answer = result["answer"]
                    sources = st.session_state.rag_chain.get_sources(result["source_documents"])

                    st.markdown(answer)

                    if sources:
                        with st.expander("Sources"):
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

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                }
            )
