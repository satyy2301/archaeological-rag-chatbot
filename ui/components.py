"""Shared UI components: top bar, onboarding wizard, and empty states."""

import os
from pathlib import Path

import streamlit as st

from lab.services import load_existing_vector_store, process_pdf_and_create_vector_store
from ui.icons import render_icon
from ui.session import (
    STATION_DESCRIPTIONS,
    STATION_ICONS,
    STATION_LABELS,
    STATION_NAMES,
    STATION_ORDER,
    STATIONS_STANDALONE,
)


def render_status_chip(label: str, variant: str = "muted") -> str:
    """Return HTML for a status chip badge."""
    return f'<span class="status-chip status-chip--{variant}">{label}</span>'


def _api_key_ok() -> bool:
    return bool(st.session_state.get("user_openai_api_key", "").strip()) or bool(
        os.getenv("OPENAI_API_KEY")
    )


def render_session_hud(compact: bool = False) -> None:
    """Render session status chips: API key, document, active station."""
    chips = []
    if _api_key_ok():
        chips.append(render_status_chip("Key set", "ok"))
    else:
        chips.append(render_status_chip("Key required", "warn"))

    if st.session_state.vector_store_initialized:
        doc = st.session_state.uploaded_pdf_name or "Document loaded"
        chips.append(render_status_chip(doc[:28] + ("…" if len(doc) > 28 else ""), "ok"))
    else:
        chips.append(render_status_chip("No document", "muted"))

    station = STATION_NAMES.get(st.session_state.active_station, "Lab")
    short = station.replace(" Station", "").replace(" Desk", "").replace(" Room", "")
    chips.append(render_status_chip(short, "accent"))

    html = f'<div class="session-hud">{"".join(chips)}</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_station_header(station_id: str) -> None:
    """Consistent station page header: title, description, divider."""
    name = STATION_NAMES.get(station_id, station_id)
    desc = STATION_DESCRIPTIONS.get(station_id, "")
    icon_key = STATION_ICONS.get(station_id, "document")
    st.markdown(
        f"""
        <div>
            <div style="display:flex;align-items:center;gap:0.5rem;">
                {render_icon(icon_key, 22)}
                <p class="station-header-title">{name}</p>
            </div>
            <p class="station-header-desc">{desc}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()


def render_empty_state(
    title: str,
    body: str,
    cta_label: str | None = None,
    cta_key: str | None = None,
    cta_action: str | None = None,
) -> bool:
    """Unified empty-state card. Returns True if CTA clicked."""
    st.markdown(
        f"""
        <div class="empty-state-card arl-surface">
            <h3>{title}</h3>
            <p>{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if cta_label and cta_key:
        if st.button(cta_label, key=cta_key, type="primary"):
            if cta_action == "document_desk":
                st.session_state.active_station = "document_desk"
                st.rerun()
            return True
    return False


def render_station_empty_state(station_id: str) -> None:
    """Show helpful empty state when a document-dependent station has no PDF loaded."""
    label = STATION_NAMES.get(station_id, station_id)
    description = STATION_DESCRIPTIONS.get(station_id, "")
    render_empty_state(
        title=label,
        body=f"{description} Upload a PDF at the Document Intelligence Desk to use this station fully.",
        cta_label="Go to Document Intelligence Desk",
        cta_key=f"goto_desk_{station_id}",
        cta_action="document_desk",
    )


def render_station_nav() -> None:
    """Vertical station navigation using buttons (reliable across Streamlit versions)."""
    for station_id in STATION_ORDER:
        label = STATION_LABELS[station_id]
        is_active = station_id == st.session_state.active_station
        if st.button(
            label,
            key=f"nav_{station_id}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            if not is_active:
                st.session_state.active_station = station_id
                st.rerun()


def render_lab_topbar() -> None:
    """Top bar with lab title, session chips, and home link."""
    doc_name = st.session_state.uploaded_pdf_name
    api_ok = _api_key_ok()
    station_short = STATION_NAMES.get(st.session_state.active_station, "Lab")

    with st.container(border=True):
        left, right = st.columns([8, 1])
        with left:
            col_title, col_chips = st.columns([4, 6])
            with col_title:
                st.markdown(
                    '<p class="lab-header-title">Archaeological Research Lab</p>',
                    unsafe_allow_html=True,
                )
                if not doc_name:
                    st.markdown(
                        '<p class="lab-header-subtitle">Upload a document to begin analysis</p>',
                        unsafe_allow_html=True,
                    )
            with col_chips:
                chips = []
                if api_ok:
                    chips.append(render_status_chip("Key set", "ok"))
                else:
                    chips.append(render_status_chip("Key required", "warn"))
                if doc_name:
                    display = doc_name if len(doc_name) <= 24 else doc_name[:22] + "…"
                    chips.append(render_status_chip(display, "ok"))
                else:
                    chips.append(render_status_chip("No document", "muted"))
                chips.append(render_status_chip(station_short[:20], "accent"))
                st.markdown(
                    f'<div class="lab-header-chips">{"".join(chips)}</div>',
                    unsafe_allow_html=True,
                )
        with right:
            if st.button("Home", key="lab_topbar_home", type="secondary", use_container_width=True):
                st.switch_page("app.py")

    st.divider()


def render_onboarding_wizard() -> None:
    """Guided 3-step wizard: API key → upload PDF → choose station."""
    st.markdown(
        """
        <div>
            <p class="onboarding-welcome-title">Welcome to the Research Lab</p>
            <p class="onboarding-welcome-desc">
                Upload any archaeological PDF — a survey report, excavation notes, or research paper —
                and ask questions about it in plain English.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    step = st.session_state.onboarding_step
    api_key_ok = _api_key_ok()

    steps = [
        ("1", "Add your API key", "Paste your OpenAI key in the sidebar (session only, never stored)."),
        ("2", "Upload a PDF", "Upload and process your archaeological document."),
        ("3", "Choose a station", "Pick a lab station to start your analysis."),
    ]
    cols = st.columns(3)
    for i, (num, title, desc) in enumerate(steps):
        active_class = "onboarding-step-active" if step == i + 1 else ""
        complete_class = "onboarding-step-complete" if step > i + 1 else ""
        with cols[i]:
            st.markdown(
                f"""
                <div class="onboarding-step arl-surface {active_class} {complete_class}">
                    <div class="step-number">{num}</div>
                    <h4>{title}</h4>
                    <p>{desc}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    if step == 1:
        with st.container(border=True):
            if api_key_ok:
                st.success("API key detected — you're ready for step 2.")
                if st.button("Continue to upload", key="onboard_step1_next", type="primary"):
                    st.session_state.onboarding_step = 2
                    st.rerun()
            else:
                st.warning(
                    "Add your OpenAI API key first — paste it in the sidebar on the left, then click Continue."
                )
                if st.button("I've added my key", key="onboard_step1_check"):
                    if api_key_ok:
                        st.session_state.onboarding_step = 2
                        st.rerun()
                    else:
                        st.error("No API key found yet. Paste it in the sidebar.")

    elif step == 2:
        col_upload, col_help = st.columns([3, 2], gap="large")

        with col_upload:
            with st.container(border=True):
                st.markdown("#### Upload your document")
                if not api_key_ok:
                    st.warning("Add your OpenAI API key in the sidebar before processing.")

                pdf_file = st.file_uploader(
                    "Choose a PDF file (up to 200 MB)",
                    type=["pdf"],
                    key="main_pdf_uploader",
                    help="Your file is only used in this session and is never stored permanently.",
                )

                if pdf_file is not None:
                    st.session_state.uploaded_pdf_name = pdf_file.name
                    pdf_path = f"./temp_{pdf_file.name}"
                    with open(pdf_path, "wb") as f:
                        f.write(pdf_file.getbuffer())
                    st.success(f"**{pdf_file.name}** is ready to process")
                    if st.button(
                        "Process Document & Start Chatting",
                        use_container_width=True,
                        key="main_process_btn",
                        type="primary",
                        disabled=not api_key_ok,
                    ):
                        with st.status("Processing your document…", expanded=True) as status:
                            st.write("Reading and indexing PDF content…")
                            success = process_pdf_and_create_vector_store(pdf_path)
                            if success:
                                status.update(label="Document ready", state="complete")
                                if os.path.exists(pdf_path):
                                    os.remove(pdf_path)
                                st.session_state.onboarding_step = 3
                                st.rerun()
                            else:
                                status.update(label="Processing failed", state="error")

                vector_store_path = Path("./vector_store")
                if vector_store_path.exists() and not st.session_state.vector_store_initialized:
                    st.markdown("**Already processed a document before?**")
                    if st.button("Continue from last session", use_container_width=True, key="main_load_btn"):
                        if load_existing_vector_store():
                            st.session_state.onboarding_step = 3
                            st.rerun()
                        else:
                            st.error("Could not reload the previous session. Please upload a new document.")

        with col_help:
            with st.container(border=True):
                st.markdown("#### What can I ask?")
                st.markdown(
                    """
                    Once your document is loaded, try asking:

                    - *"What is this document about?"*
                    - *"Which archaeological sites are mentioned?"*
                    - *"What survey methods were used?"*
                    - *"Summarise the main findings."*
                    """
                )
                if st.button("Back to API key step", key="onboard_back_step1"):
                    st.session_state.onboarding_step = 1
                    st.rerun()

    elif step == 3:
        st.markdown("#### Choose a lab station to begin")
        for row_start in range(0, len(STATION_ORDER), 3):
            row_stations = STATION_ORDER[row_start : row_start + 3]
            row_cols = st.columns(3)
            for col, station_id in zip(row_cols, row_stations):
                with col:
                    name = STATION_NAMES[station_id]
                    desc = STATION_DESCRIPTIONS[station_id]
                    icon_key = STATION_ICONS[station_id]
                    st.markdown(
                        f"""
                        <div class="station-card-unit">
                            <div class="station-card-body arl-surface">
                                <div class="station-card-icon">{render_icon(icon_key, 28)}</div>
                                <div class="station-card-name">{name}</div>
                                <div class="station-card-desc">{desc}</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if st.button(f"Open {name}", key=f"onboard_station_{station_id}", use_container_width=True):
                        st.session_state.active_station = station_id
                        st.rerun()


def dispatch_active_station() -> None:
    """Route to the active station renderer or show onboarding/empty state."""
    from ui.stations import STATION_RENDERERS

    station = st.session_state.active_station
    initialized = st.session_state.vector_store_initialized

    if not initialized and station not in STATIONS_STANDALONE:
        if station == "document_desk":
            render_onboarding_wizard()
        else:
            render_station_empty_state(station)
        return

    renderer = STATION_RENDERERS.get(station)
    if renderer:
        renderer()
    else:
        st.error(f"Unknown station: {station}")
