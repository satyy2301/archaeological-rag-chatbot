"""Artifact Analysis Station — photo and text artifact assessment."""

import json
import os
from datetime import datetime

import pandas as pd
import streamlit as st
from PIL import Image

from artifact_assessment import ArtifactAssessment
from image_analyzer import crop_box, get_script_profiles
from ui.components import render_station_header


def render() -> None:
    """Artifact assessment with photo upload and text description."""
    render_station_header("artifact_station")

    if not st.session_state.vector_store_initialized:
        st.info(
            "A loaded document is optional here — upload a PDF at the Document Intelligence Desk "
            "for richer, source-cited analysis."
        )

    if st.session_state.artifact_assessor is None:
        st.session_state.artifact_assessor = ArtifactAssessment(
            rag_chain=st.session_state.rag_chain if st.session_state.vector_store_initialized else None
        )

    assessor = st.session_state.artifact_assessor

    if st.session_state.vector_store_initialized and st.session_state.rag_chain:
        assessor.rag_chain = st.session_state.rag_chain

    with st.container(border=True):
        input_method = st.radio(
            "How would you like to submit your find?",
            ["Photo Upload", "Text Description"],
            horizontal=True,
        )

    if input_method == "Photo Upload":
        with st.container(border=True):
            st.markdown("#### Upload photo")
            script_profiles = get_script_profiles()
            uploaded_image = st.file_uploader(
                "Upload photo of artifact",
                type=["jpg", "jpeg", "png", "tiff", "tif"],
                help="Upload a clear photo of what you found",
            )

            if uploaded_image:
                image = Image.open(uploaded_image)
                with st.container(border=True):
                    st.image(image, caption="Uploaded image", width=400)

                with st.expander("Add context (optional)"):
                    script_profile = st.selectbox(
                        "Script / legend profile",
                        options=list(script_profiles.keys()),
                        format_func=lambda key: str(script_profiles[key]["label"]),
                        help="Choose the script family you expect.",
                    )
                    context = {
                        "artifact_type": st.selectbox(
                            "Artifact type",
                            ["unknown", "coin", "inscription", "manuscript page", "pottery", "seal", "other"],
                        ),
                        "material": st.selectbox(
                            "Material", ["unknown", "stone", "metal", "pottery", "bone", "glass", "organic"]
                        ),
                        "size": st.selectbox("Size", ["unknown", "coin-sized", "hand-sized", "larger", "very large"]),
                        "location": st.selectbox(
                            "Location found",
                            ["unknown", "garden", "construction site", "beach", "field", "archaeological site", "other"],
                        ),
                        "markings": st.text_area("Markings or decorations", ""),
                        "script_profile": script_profile,
                    }
                    context = {k: v for k, v in context.items() if v and v != "unknown"}

                if st.button("Assess artifact", use_container_width=True, type="primary"):
                    with st.spinner("Analyzing artifact..."):
                        assessment = assessor.assess_from_photo(image, context if "context" in locals() else None)

                        with st.container(border=True):
                            st.markdown("### Assessment results")
                            st.markdown("#### What this likely is")
                            summary_text = (
                                assessment.get("layman_summary")
                                or assessment.get("detailed_analysis")
                                or "No summary available for this image yet."
                            )
                            st.markdown(summary_text)

                            if assessment.get("detailed_analysis"):
                                with st.expander("Read full detailed assessment"):
                                    st.markdown(assessment["detailed_analysis"])
                                    if assessment.get("sources"):
                                        st.markdown("**Source snippets**")
                                        for source in assessment["sources"][:3]:
                                            if isinstance(source, dict):
                                                source_text = source.get("content") or source.get("page_content", "")
                                            else:
                                                source_text = getattr(source, "page_content", "")
                                            if not source_text:
                                                source_text = str(source)
                                            st.text(source_text[:500])

                        if assessment.get("visuals"):
                            with st.container(border=True):
                                st.markdown("#### Image enhancement comparison")
                                cols = st.columns(3)
                                with cols[0]:
                                    st.caption("CLAHE")
                                    st.image(assessment["visuals"]["enh_clahe"], caption="Contrast enhanced")
                                with cols[1]:
                                    st.caption("Retinex")
                                    st.image(assessment["visuals"]["enh_retinex"], caption="Illumination corrected")
                                with cols[2]:
                                    st.caption("Sharpen")
                                    st.image(assessment["visuals"]["enh_sharpen"], caption="Edge-highlighted")

                                with st.expander("Show preprocessing steps"):
                                    pcols = st.columns(3)
                                    with pcols[0]:
                                        st.caption("Denoised")
                                        st.image(assessment["visuals"]["pre_denosed"])
                                    with pcols[1]:
                                        st.caption("Shadow reduced")
                                        st.image(assessment["visuals"]["pre_shadow_reduced"])
                                    with pcols[2]:
                                        st.caption("Normalized")
                                        st.image(assessment["visuals"]["pre_normalized"])

                        if assessment.get("similar_finds"):
                            with st.container(border=True):
                                st.markdown("#### Similar finds")
                                st.caption("Approximate matches from public collections — may include unrelated items.")
                                for item in assessment["similar_finds"]:
                                    title = item.get("title", "Untitled result")
                                    source = item.get("source", "External source")
                                    description = item.get("description", "")
                                    url = item.get("url", "")
                                    image_url = item.get("image_url", "")
                                    with st.container(border=True):
                                        st.markdown(f"**{title}**")
                                        st.caption(source)
                                        if description:
                                            st.write(description)
                                        meta_bits = [bit for bit in [item.get("date", ""), item.get("material", "")] if bit]
                                        if meta_bits:
                                            st.caption(" | ".join(meta_bits))
                                        if image_url:
                                            st.image(image_url, width=220)
                                        if url:
                                            st.markdown(f"[Open record]({url})")
                        else:
                            st.caption("No similar public collection records found from the current image/context query.")

                        with st.container(border=True):
                            st.markdown("#### What to do next")
                            for rec in assessment.get("recommendations", []):
                                st.markdown(f"- {rec}")

                        with st.expander("Technical details (advanced)"):
                            st.markdown("**Image analysis payload**")
                            st.json(assessment.get("analysis", {}))

                            if assessment.get("analysis", {}).get("ocr_notes"):
                                st.info(assessment["analysis"]["ocr_notes"])

                            if assessment.get("analysis", {}).get("ocr"):
                                st.markdown("**Detected regions & OCR**")
                                st.image(assessment["visuals"].get("boxed", None), caption="Detected regions (numbered)")
                                ocr_items = assessment["analysis"]["ocr"]
                                table = pd.DataFrame(
                                    [
                                        {
                                            "index": i + 1,
                                            "text": item.get("text", ""),
                                            "confidence": round(float(item.get("confidence", 0.0)), 3),
                                            "top_candidates": " | ".join(item.get("top_candidates", [])[:3]),
                                        }
                                        for i, item in enumerate(ocr_items)
                                    ]
                                )
                                st.dataframe(table, use_container_width=True)

                                if assessment["analysis"].get("detected_text"):
                                    st.caption(f"Detected text summary: {assessment['analysis']['detected_text']}")
                                st.caption(f"OCR backend: {assessment['analysis'].get('ocr_backend', 'unknown')}")

                                selected_idx = st.number_input(
                                    "Zoom region index", min_value=1, max_value=len(ocr_items), value=1, step=1
                                )
                                if selected_idx:
                                    box = ocr_items[selected_idx - 1]["box"]
                                    zoom = crop_box(image, box)
                                    st.image(zoom, caption=f"Zoomed region #{selected_idx}")
                                    candidates = ocr_items[selected_idx - 1].get("top_candidates", [])
                                    if candidates:
                                        st.markdown("**Suggested readings**")
                                        for candidate in candidates:
                                            st.markdown(f"- {candidate}")

                                    correction = st.text_input("Suggest transcription / reading for this region")
                                    if st.button("Save correction", key=f"save_corr_{selected_idx}"):
                                        os.makedirs("user_data", exist_ok=True)
                                        corr_path = os.path.join("user_data", "corrections.json")
                                        data = []
                                        if os.path.exists(corr_path):
                                            try:
                                                with open(corr_path, "r", encoding="utf-8") as f:
                                                    data = json.load(f)
                                            except Exception:
                                                data = []
                                        entry = {
                                            "timestamp": datetime.now().isoformat(),
                                            "file_name": uploaded_image.name,
                                            "region_index": int(selected_idx),
                                            "box": box,
                                            "suggestion": correction,
                                            "context": context if "context" in locals() else {},
                                        }
                                        data.append(entry)
                                        with open(corr_path, "w", encoding="utf-8") as f:
                                            json.dump(data, f, ensure_ascii=False, indent=2)
                                        st.success("Correction saved. Thanks for the feedback!")

    else:
        with st.container(border=True):
            st.markdown("#### Text description")
            st.caption("Answer the guided questions to describe what you found")

            template = assessor.get_guided_questions_template()
            description = {}

            description["material"] = st.selectbox(
                template["material"]["question"],
                template["material"]["options"],
                key="desc_material",
            )
            description["size"] = st.selectbox(
                template["size"]["question"],
                template["size"]["options"],
                key="desc_size",
            )
            description["location"] = st.selectbox(
                template["location"]["question"],
                template["location"]["options"],
                key="desc_location",
            )
            description["markings"] = st.text_area(
                template["markings"]["question"],
                key="desc_markings",
                help="Describe any markings, inscriptions, or decorative elements",
            )
            description["additional_notes"] = st.text_area(
                template["additional_notes"]["question"],
                key="desc_notes",
                height=100,
            )

            if st.button("Assess artifact", use_container_width=True, key="assess_text_btn", type="primary"):
                with st.spinner("Analyzing artifact description..."):
                    assessment = assessor.assess_from_text(
                        description,
                        st.session_state.rag_chain if st.session_state.vector_store_initialized else None,
                    )

                    with st.container(border=True):
                        st.markdown("### Assessment results")
                        st.markdown("#### Your description")
                        st.markdown(assessment["analysis"].get("full_description", ""))

                        if assessment.get("detailed_analysis"):
                            st.markdown("#### Detailed assessment")
                            st.markdown(assessment["detailed_analysis"])

                            if assessment.get("sources"):
                                with st.expander("Sources"):
                                    for source in assessment["sources"][:3]:
                                        if isinstance(source, dict):
                                            source_text = source.get("content") or source.get("page_content", "")
                                        else:
                                            source_text = getattr(source, "page_content", "")
                                        if not source_text:
                                            source_text = str(source)
                                        st.text(source_text[:500])

                        st.markdown("#### Recommendations")
                        for rec in assessment.get("recommendations", []):
                            st.markdown(f"- {rec}")
