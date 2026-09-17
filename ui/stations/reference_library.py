"""Reference Library — source viewer, glossary, and outreach."""

import streamlit as st

from public_engagement import PublicEngagement
from ui.components import render_empty_state, render_station_header


def render() -> None:
    """Document-oriented tools: source snippets, glossary, and outreach."""
    render_station_header("reference_library")

    with st.container(border=True):
        st.markdown("#### Source highlighting")
        if st.session_state.uploaded_pdf_name:
            st.info(f"Most recent uploaded PDF: **{st.session_state.uploaded_pdf_name}**")
        else:
            st.caption("No document loaded yet.")

        st.markdown(
            """
            **How to trace answers to sources:**
            1. Open the **Document Intelligence Desk** and expand *Sources* under a message.
            2. Review the surrounding text and any page / chunk information.
            3. Use that page number in your own PDF viewer to jump to the exact place.
            """
        )

    with st.container(border=True):
        st.markdown("#### Archaeological terminology glossary")

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

    with st.expander("Outreach — site story builder"):
        st.caption("Generate public-facing site stories from extracted site data.")
        sites_list = st.session_state.get("sites_list")
        if not sites_list:
            render_empty_state(
                title="No site data available",
                body="Upload and process a PDF with site mentions to build site stories.",
                cta_label="Go to Document Intelligence Desk",
                cta_key="ref_goto_desk",
                cta_action="document_desk",
            )
        else:
            engagement = PublicEngagement(
                rag_chain=st.session_state.rag_chain if st.session_state.vector_store_initialized else None
            )
            site_names = [s.get("site_name", f"Site {i+1}") for i, s in enumerate(sites_list)]
            selected_site = st.selectbox("Select a site:", site_names, key="outreach_site_select")
            site_data = next(
                (s for s in sites_list if s.get("site_name") == selected_site),
                sites_list[0],
            )
            if st.button("Build site story", key="build_site_story_btn", type="primary"):
                story = engagement.build_site_story(site_data)
                st.markdown(story)
                st.download_button(
                    "Download story",
                    data=story,
                    file_name=f"{selected_site.replace(' ', '_')}_story.md",
                    mime="text/markdown",
                    key="download_site_story",
                )
