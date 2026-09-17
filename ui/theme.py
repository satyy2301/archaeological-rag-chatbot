"""Shared theme injection for landing and lab pages."""

from pathlib import Path

import streamlit as st

_CSS_PATH = Path(__file__).resolve().parent.parent / "assets" / "styles.css"

_LANDING_CSS = """
[data-testid="stSidebarNav"] {
    display: none;
}
/* Landing: no sidebar rail — full-width centered content */
[data-testid="stSidebar"] {
    display: none !important;
}
[data-testid="collapsedControl"] {
    display: none !important;
}
section[data-testid="stMain"] {
    margin-left: 0 !important;
}
section[data-testid="stMain"] > div {
    max-width: 1100px;
    margin-left: auto !important;
    margin-right: auto !important;
}
"""

_LAB_CSS = """
[data-testid="stSidebarNav"] {
    display: none;
}
[data-testid="stSidebar"] > div:first-child {
    padding-top: 0.75rem;
}
/* Lab topbar — compact Home button inside bordered header */
.lab-topbar-wrap .stButton > button,
[data-testid="stVerticalBlockBorderWrapper"] .stButton > button[kind="secondary"] {
    min-height: 2.25rem;
    font-size: 0.875rem;
    white-space: nowrap;
}
"""


def inject_theme(page: str = "lab") -> None:
    """Load shared CSS with optional page-specific overrides."""
    css_parts = []
    if _CSS_PATH.exists():
        css_parts.append(_CSS_PATH.read_text(encoding="utf-8"))
    if page == "landing":
        css_parts.append(_LANDING_CSS)
    elif page == "lab":
        css_parts.append(_LAB_CSS)
    if css_parts:
        st.markdown(f"<style>{''.join(css_parts)}</style>", unsafe_allow_html=True)
