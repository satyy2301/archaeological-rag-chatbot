"""Field Photo Archive — dig photo organization and field checklist."""

from pathlib import Path

import streamlit as st
from PIL import Image

from photo_organizer import PhotoOrganizer
from smart_field_assistant import SmartFieldAssistant
from ui.components import render_empty_state, render_station_header


def render() -> None:
    """Dig photo organizer and field checklist."""
    render_station_header("photo_archive")

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("#### Scan directory")
            photo_dir = st.text_input(
                "Enter photo directory path:",
                placeholder="C:/path/to/photos or ./photos",
                help="Enter the full path to a directory containing photos",
            )
            if st.button("Scan directory", use_container_width=True, type="primary") and photo_dir:
                try:
                    organizer = PhotoOrganizer(photo_dir)
                    photos = organizer.scan_directory()
                    st.session_state.photo_organizer = organizer
                    st.success(f"Found {len(photos)} photos.")
                except Exception as e:
                    st.error(f"Error scanning directory: {e}")

    with col2:
        with st.container(border=True):
            st.markdown("#### Upload photos")
            uploaded_files = st.file_uploader(
                "Upload photos",
                type=["jpg", "jpeg", "png", "tiff", "tif"],
                accept_multiple_files=True,
                help="Upload multiple photos to organize",
            )
            if uploaded_files:
                temp_dir = Path("./temp_photos")
                temp_dir.mkdir(exist_ok=True)
                for uploaded_file in uploaded_files:
                    with open(temp_dir / uploaded_file.name, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                try:
                    organizer = PhotoOrganizer(str(temp_dir))
                    photos = organizer.scan_directory()
                    st.session_state.photo_organizer = organizer
                    st.success(f"Processed {len(photos)} photos.")
                except Exception as e:
                    st.error(f"Error processing photos: {e}")

    if st.session_state.photo_organizer and st.session_state.photo_organizer.photos:
        organizer = st.session_state.photo_organizer

        with st.container(border=True):
            st.markdown("#### Organize photos")
            org_method = st.radio(
                "Organize by:",
                ["Trench", "Locus", "Artifact Type", "Stratigraphy Layer", "Date"],
                horizontal=True,
            )

            if org_method == "Trench":
                organized = organizer.organize_by_trench()
            elif org_method == "Locus":
                organized = organizer.organize_by_locus()
            elif org_method == "Artifact Type":
                organized = organizer.organize_by_artifact_type()
            elif org_method == "Stratigraphy Layer":
                organized = organizer.organize_by_stratigraphy()
            else:
                organized = organizer.organize_by_date()

            for category, photos in sorted(organized.items()):
                with st.expander(f"{org_method}: {category} ({len(photos)} photos)"):
                    cols = st.columns(min(4, len(photos)))
                    for idx, photo in enumerate(photos[:12]):
                        with cols[idx % 4]:
                            try:
                                img = Image.open(photo["file_path"])
                                st.image(img, width="stretch", caption=photo["file_name"])
                            except Exception:
                                st.text(photo["file_name"])

        with st.container(border=True):
            st.markdown("#### Reports & analysis")
            col1, col2 = st.columns(2)

            with col1:
                if st.button("Generate field report", use_container_width=True):
                    report = organizer.generate_field_report()
                    st.text_area("Field report", report, height=400)
                    st.download_button(
                        "Download report",
                        data=report,
                        file_name="field_report.md",
                        mime="text/markdown",
                    )

            with col2:
                if st.button("Find duplicates", use_container_width=True):
                    duplicates = organizer.find_duplicates()
                    if duplicates:
                        st.warning(f"Found {len(duplicates)} potential duplicate groups")
                        for idx, group in enumerate(duplicates[:5]):
                            with st.expander(f"Duplicate group {idx + 1}"):
                                for photo in group:
                                    st.text(f"- {photo['file_name']} ({photo.get('file_size', 0)} bytes)")
                    else:
                        st.success("No duplicates found.")

            with st.expander("Statistics"):
                stats = organizer.get_statistics()
                st.json(stats)
    else:
        render_empty_state(
            title="No photos loaded",
            body="Scan a directory or upload field photos to organize them by trench, locus, and date.",
        )

    with st.expander("Field checklist"):
        st.caption("Daily field tasks and context-aware preparation prompts.")
        assistant = SmartFieldAssistant()
        alerts = assistant.get_context_aware_alerts()
        if alerts:
            for alert in alerts:
                level = alert.get("level", "info")
                if level == "warning":
                    st.warning(f"**{alert.get('title', 'Alert')}**: {alert.get('message', '')}")
                else:
                    st.info(f"**{alert.get('title', 'Tip')}**: {alert.get('message', '')}")

        tasks = assistant.get_today_tasks()
        st.markdown("**Today's tasks:**")
        for task in tasks:
            priority = task.get("priority", "medium")
            st.markdown(f"- [{priority}] {task.get('task', '')}")
