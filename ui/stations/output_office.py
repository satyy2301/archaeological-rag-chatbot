"""Research Output Office — compliance, reports, citations, and QA."""

import json
from datetime import datetime

import streamlit as st

from quality_assurance import QualityAssurance
from report_generator import ReportGenerator
from ui.components import render_empty_state, render_station_header


def _build_session_export() -> dict:
    """Serialize current session data for download (no server persistence)."""
    export = {
        "exported_at": datetime.now().isoformat(),
        "project_name": st.session_state.get("uploaded_pdf_name") or "session_export",
        "uploaded_pdf_name": st.session_state.uploaded_pdf_name,
        "sites_list": st.session_state.sites_list or [],
        "messages": st.session_state.messages,
    }
    if st.session_state.sites_df is not None:
        export["sites_df"] = st.session_state.sites_df.to_dict(orient="records")
    if st.session_state.timeline_df is not None:
        export["timeline_df"] = st.session_state.timeline_df.to_dict(orient="records")
    return export


def render() -> None:
    """Regulatory, methodology, reporting, and citation helpers."""
    render_station_header("output_office")

    has_rag = st.session_state.vector_store_initialized and st.session_state.rag_chain

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("#### Permit guidance")
            permit_notes = st.text_area(
                "Describe your project and location",
                placeholder="e.g. fieldwalking survey near a river in [region], with planned shovel test pits...",
                height=120,
                label_visibility="collapsed",
            )
            if st.button("Generate permit checklist", type="primary") and permit_notes:
                if not has_rag:
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
        with st.container(border=True):
            st.markdown("#### Reporting template")
            report_context = st.text_area(
                "Project context for report outline",
                placeholder="Summarise your project, methods, and key findings...",
                height=120,
                label_visibility="collapsed",
            )
            if st.button("Draft report outline"):
                if not has_rag:
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

    with st.container(border=True):
        st.markdown("#### Survey methodology template")
        meth_context = st.text_area(
            "Survey parameters (environment, aims, constraints)",
            placeholder="e.g. intensive pedestrian survey over 5 km² of agricultural land...",
            height=120,
        )
        if st.button("Generate methodology template"):
            if not has_rag:
                render_empty_state(
                    title="Document required",
                    body="Process a PDF at the Document Intelligence Desk to generate methodology templates with document context.",
                    cta_label="Go to Document Intelligence Desk",
                    cta_key="output_goto_desk",
                    cta_action="document_desk",
                )
            else:
                with st.spinner("Building a methodology template..."):
                    prompt = (
                        "Create a detailed survey methodology template for this project, "
                        "including sampling strategy, recording system, and data management:\n\n"
                        f"{meth_context}"
                    )
                    result = st.session_state.rag_chain.query(prompt)
                    st.markdown(result["answer"])

    with st.container(border=True):
        st.markdown("#### Report generator")

        if "report_generator" not in st.session_state:
            st.session_state.report_generator = ReportGenerator(
                rag_chain=st.session_state.rag_chain if has_rag else None
            )
        elif has_rag:
            st.session_state.report_generator.rag_chain = st.session_state.rag_chain

        report_type = st.selectbox(
            "Report type",
            options=list(ReportGenerator.REPORT_TYPES.keys()),
            format_func=lambda x: ReportGenerator.REPORT_TYPES[x],
            key="report_type_select",
        )

        project_data = {
            "project_name": st.text_input(
                "Project name", value="Archaeological Investigation", key="report_project_name"
            ),
            "location": st.text_input("Location", key="report_location"),
            "sites": st.session_state.sites_list or [],
            "artifacts": [],
            "methodology": {},
        }

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Generate report", use_container_width=True, key="generate_report_btn", type="primary"):
                with st.spinner("Generating report..."):
                    report_content = st.session_state.report_generator.generate_report(report_type, project_data)
                    st.session_state.generated_report = report_content
                    st.session_state.report_type_generated = report_type

        with col2:
            if st.button(
                "Export report",
                use_container_width=True,
                key="export_report_btn",
                disabled="generated_report" not in st.session_state,
            ):
                if "generated_report" in st.session_state:
                    report_filename = f"{report_type}_report_{datetime.now().strftime('%Y%m%d')}.md"
                    st.download_button(
                        "Download report",
                        data=st.session_state.generated_report,
                        file_name=report_filename,
                        mime="text/markdown",
                        key="download_report_btn",
                    )

        if "generated_report" in st.session_state:
            st.markdown("##### Generated report preview")
            st.markdown(st.session_state.generated_report)

            st.markdown("##### Pre-submission quality check")
            qa = QualityAssurance()
            qa_data = {
                "sites": st.session_state.sites_list or [],
                "artifacts": [],
                "report_content": st.session_state.generated_report,
            }
            if st.button("Run QA check", key="run_qa_btn"):
                report = qa.generate_quality_report(qa_data)
                st.metric("Overall quality score", f"{report.get('overall_score', 0):.0f}%")
                if report.get("recommendations"):
                    st.markdown("**Recommendations:**")
                    for rec in report["recommendations"]:
                        st.markdown(f"- {rec}")
                st.json(report)

    with st.container(border=True):
        st.markdown("#### Citation generator")
        citation_info = st.text_area(
            "Bibliographic details (author, year, title, publisher, etc.)",
            placeholder="e.g. Renfrew, C. and Bahn, P. 2016. Archaeology: Theories, Methods and Practice.",
            height=120,
        )
        style = st.selectbox("Preferred style", ["Harvard", "Chicago", "APA", "Custom archaeological"], index=0)
        if st.button("Format citation", type="primary"):
            if not citation_info.strip():
                st.error("Enter bibliographic details first.")
            elif has_rag:
                with st.spinner("Formatting citation..."):
                    prompt = (
                        f"Format the following bibliographic details as a {style} style citation. "
                        f"If information is missing, clearly mark it with placeholders:\n\n"
                        f"{citation_info}"
                    )
                    result = st.session_state.rag_chain.query(prompt)
                    st.markdown(result["answer"])
            else:
                formatted = st.session_state.report_generator.generate_citation(
                    author="",
                    year="",
                    title=citation_info,
                    style=style.lower().replace(" custom archaeological", ""),
                )
                st.markdown(formatted)

    with st.container(border=True):
        st.markdown("#### Session export")
        st.caption("Download your current session data as JSON or CSV. Nothing is stored on the server.")

        export_data = _build_session_export()
        st.download_button(
            "Download session JSON",
            data=json.dumps(export_data, indent=2, default=str),
            file_name=f"session_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            key="download_session_json",
        )

        if st.session_state.sites_df is not None and not st.session_state.sites_df.empty:
            csv_data = st.session_state.sites_df.to_csv(index=False)
            st.download_button(
                "Download sites CSV",
                data=csv_data,
                file_name=f"sites_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key="download_sites_csv",
            )
