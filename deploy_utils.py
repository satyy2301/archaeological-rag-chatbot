"""Helpers for cloud vs local deployment behavior."""

import os


def is_streamlit_cloud() -> bool:
    """Return True when running on Streamlit Community Cloud."""
    return os.getenv("STREAMLIT_RUNTIME_ENV") == "cloud"
