"""Centralized session state for the Research Lab."""

import streamlit as st

STATION_NAMES = {
    "document_desk": "Document Intelligence Desk",
    "artifact_station": "Artifact Analysis Station",
    "photo_archive": "Field Photo Archive",
    "spatial_room": "Spatial Analysis Room",
    "reference_library": "Reference Library",
    "output_office": "Research Output Office",
}

STATION_ICONS = {
    "document_desk": "chat",
    "artifact_station": "search",
    "photo_archive": "camera",
    "spatial_room": "map",
    "reference_library": "book",
    "output_office": "output",
}

# Backward-compatible labels (no emoji) for radio/nav display
STATION_LABELS = STATION_NAMES.copy()

STATION_ORDER = list(STATION_NAMES.keys())

STATIONS_STANDALONE = {"artifact_station", "photo_archive"}

STATION_DESCRIPTIONS = {
    "document_desk": "Upload PDFs and chat with source citations.",
    "artifact_station": "Assess artifacts from photos or descriptions.",
    "photo_archive": "Organize field photos by trench, locus, and date.",
    "spatial_room": "Maps, timelines, and site relationships.",
    "reference_library": "Glossary, source tips, and outreach stories.",
    "output_office": "Reports, compliance templates, and citations.",
}

LAB_PAGE = "pages/1_Research_Lab.py"


def initialize_session_state() -> None:
    """Initialize session state variables."""
    defaults = {
        "messages": [],
        "vector_store_initialized": False,
        "rag_chain": None,
        "vector_store_manager": None,
        "active_mode": "General Q&A",
        "uploaded_pdf_name": None,
        "sites_df": None,
        "timeline_df": None,
        "sites_list": None,
        "photo_organizer": None,
        "artifact_assessor": None,
        "user_openai_api_key": "",
        "active_station": "document_desk",
        "onboarding_step": 1,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def go_to_station(station_id: str) -> None:
    """Set active station and navigate to the lab workbench."""
    st.session_state.active_station = station_id
    st.switch_page(LAB_PAGE)
