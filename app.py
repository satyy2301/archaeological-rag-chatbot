"""
Online Archaeological Research Lab — Landing Page
Free, open-access browser workspace for survey docs, artifacts, and field data.
"""

import streamlit as st

from ui.icons import PILLAR_ICON_SVG, render_icon
from ui.session import (
    STATION_DESCRIPTIONS,
    STATION_ICONS,
    STATION_NAMES,
    STATION_ORDER,
    go_to_station,
    initialize_session_state,
)
from ui.preload import ensure_lab_warmed
from ui.theme import inject_theme

st.set_page_config(
    page_title="Online Archaeological Research Lab",
    page_icon="🏛",
    layout="wide",
    initial_sidebar_state="collapsed",
)

initialize_session_state()
ensure_lab_warmed(async_load=True)
inject_theme("landing")

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="landing-hero arl-surface">
        <div class="hero-pattern"></div>
        <div class="hero-content">
            <div class="badge-row">
                <span class="badge-pill">Free</span>
                <span class="badge-pill badge-pill-muted">No login</span>
                <span class="badge-pill badge-pill-muted">Open source</span>
            </div>
            <h1 class="hero-title">Online Archaeological Research Lab</h1>
            <p class="hero-subtitle">
                A free, browser-based workspace for archaeological survey documents, artifact analysis,
                field photos, maps, and research output. Bring your own OpenAI key — no signup required.
            </p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Centered primary + secondary CTAs
_spacer_l, cta_col, _spacer_r = st.columns([1, 2, 1])
with cta_col:
    btn_primary, btn_secondary = st.columns(2, gap="medium")
    with btn_primary:
        if st.button("Enter Research Lab", type="primary", use_container_width=True):
            st.switch_page("pages/1_Research_Lab.py")
    with btn_secondary:
        st.link_button("See how it works", url="#how-it-works", use_container_width=True)

st.markdown('<div class="arl-spacer-md"></div>', unsafe_allow_html=True)

# ── Value pillars ─────────────────────────────────────────────────────────────
st.markdown('<p class="section-header">What you can do here</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="section-sub">Four pillars of archaeological research support — all in your browser.</p>',
    unsafe_allow_html=True,
)

pillars = [
    ("Document Intelligence", "Upload a PDF and ask questions with source citations from your own documents."),
    ("Artifact Analysis", "Photo enhancement, OCR, and similar finds from public museum collections."),
    ("Field Tools", "Photo organizer, auto-extracted maps, and timelines from survey data."),
    ("Research Output", "Reports, compliance templates, glossary, and citation formatting."),
]
pillar_cols = st.columns(4)
for col, (title, desc) in zip(pillar_cols, pillars):
    with col:
        icon_name = PILLAR_ICON_SVG.get(title, "document")
        st.markdown(
            f"""
            <div class="feature-card arl-surface">
                <div class="feature-card-header">
                    {render_icon(icon_name, 22)}
                    <h3>{title}</h3>
                </div>
                <p>{desc}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown('<div class="arl-spacer-sm"></div>', unsafe_allow_html=True)

# ── How it works ──────────────────────────────────────────────────────────────
st.markdown(
    '<p class="section-header" id="how-it-works">How it works</p>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="section-sub">Three steps to start your research session.</p>',
    unsafe_allow_html=True,
)

step_cols = st.columns(3)
steps = [
    ("Paste your OpenAI API key", "Session only — never stored on our servers. Or set OPENAI_API_KEY in .env."),
    ("Upload a PDF or field photos", "Process archaeological survey reports, excavation notes, or research papers."),
    ("Analyze, visualize, export", "Chat with citations, map sites, assess artifacts, and generate reports."),
]
for col, (step_num, (title, desc)) in zip(step_cols, enumerate(steps, start=1)):
    with col:
        st.markdown(
            f"""
            <div class="step-card arl-surface">
                <div class="step-number">{step_num}</div>
                <h4>{title}</h4>
                <p>{desc}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown('<div class="arl-spacer-sm"></div>', unsafe_allow_html=True)

# ── Lab stations preview ───────────────────────────────────────────────────────
st.markdown('<p class="section-header">Lab stations</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="section-sub">Six specialized workstations — click to jump directly into the lab.</p>',
    unsafe_allow_html=True,
)

for row_start in range(0, len(STATION_ORDER), 3):
    row_stations = STATION_ORDER[row_start : row_start + 3]
    row_cols = st.columns(3)
    for col, station_id in zip(row_cols, row_stations):
        with col:
            icon_key = STATION_ICONS.get(station_id, "document")
            name = STATION_NAMES[station_id]
            desc = STATION_DESCRIPTIONS[station_id]
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
            if st.button(f"Open station", key=f"landing_station_{station_id}", use_container_width=True, type="primary"):
                go_to_station(station_id)

st.markdown('<div class="arl-spacer-sm"></div>', unsafe_allow_html=True)

# ── Trust & privacy ───────────────────────────────────────────────────────────
st.markdown('<p class="section-header">Trust & privacy</p>', unsafe_allow_html=True)
st.markdown(
    """
    <div class="trust-box arl-surface">
        <strong>Your data stays yours.</strong>
        <ul>
            <li><strong>No account required</strong> — open the lab and start working immediately.</li>
            <li><strong>Session-scoped files</strong> — uploaded PDFs and photos exist only in your browser session.</li>
            <li><strong>Bring your own key (BYOK)</strong> — your OpenAI API key is never written to disk or our servers.</li>
            <li><strong>Educational & research use</strong> — compliance guidance is informational; always verify against local law.</li>
        </ul>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="landing-footer">
        <p>
            <a href="https://github.com/satyy2301/archaeological-rag-chatbot" target="_blank">GitHub</a>
            &nbsp;·&nbsp; MIT License &nbsp;·&nbsp; Educational &amp; research use
        </p>
        <p>See <a href="https://github.com/satyy2301/archaeological-rag-chatbot/blob/main/QUICKSTART.md" target="_blank">Getting Started (QUICKSTART)</a> for setup instructions.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
