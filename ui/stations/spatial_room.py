"""Spatial Analysis Room — maps, timelines, and site relationships."""

import pandas as pd
import streamlit as st

from ui.components import render_empty_state, render_station_header

ACCENT_COLOR = "#8B7355"


def render() -> None:
    """Maps, timelines, and simple relationship views from tabular data."""
    render_station_header("spatial_room")

    with st.container(border=True):
        st.markdown("#### Interactive site map")
        st.caption(
            "If your PDF contains coordinates, the map will be pre-populated automatically. "
            "You can also upload a CSV with `site_name`, `latitude`, `longitude`, and optional `period` columns."
        )

        auto_sites_df = st.session_state.get("sites_df")
        if auto_sites_df is not None and not auto_sites_df.empty:
            st.markdown("**Automatically extracted from PDF:**")
            map_df = auto_sites_df[["latitude", "longitude"]].copy()
            if "site_name" in auto_sites_df.columns:
                map_df["site_name"] = auto_sites_df["site_name"].fillna("Unnamed Site")
            st.map(map_df)
            with st.expander("View extracted site coordinates"):
                display_cols = ["latitude", "longitude"]
                if "site_name" in auto_sites_df.columns:
                    display_cols = ["site_name"] + display_cols
                if "context" in auto_sites_df.columns:
                    display_cols.append("context")
                st.dataframe(auto_sites_df[display_cols], use_container_width=True)
        else:
            render_empty_state(
                title="No map data yet",
                body="Process a PDF with site coordinates, or upload a CSV with latitude and longitude columns.",
            )

        site_file = st.file_uploader(
            "Optionally upload additional site CSV for mapping", type=["csv"], key="map_csv"
        )
        if site_file is not None:
            df_sites = pd.read_csv(site_file)
            required_cols = {"latitude", "longitude"}
            if required_cols.issubset(df_sites.columns):
                st.markdown("**From uploaded CSV:**")
                st.map(df_sites[["latitude", "longitude"]])
                with st.expander("View uploaded site table"):
                    st.dataframe(df_sites, use_container_width=True)
            else:
                st.error(
                    f"CSV must include at least: {', '.join(required_cols)}. "
                    f"Found columns: {list(df_sites.columns)}"
                )

    with st.container(border=True):
        st.markdown("#### Timeline of excavations / surveys")
        st.caption(
            "If your PDF mentions years or year ranges, a basic timeline will be built automatically. "
            "You can also upload a CSV with `site_name`, `start_year`, and optional `end_year`."
        )

        auto_time_df = st.session_state.get("timeline_df")
        if auto_time_df is not None and not auto_time_df.empty:
            st.markdown("**Automatically extracted from PDF:**")
            try:
                import altair as alt

                if "site_name" in auto_time_df.columns:
                    y_col = "site_name"
                    tooltip_cols = ["site_name", "label", "start_year", "end_year", "context"]
                else:
                    y_col = "label"
                    tooltip_cols = ["label", "start_year", "end_year", "context"]

                chart_df = auto_time_df.copy()
                if "site_name" in chart_df.columns:
                    chart_df = chart_df[chart_df["site_name"].notna() | chart_df["label"].notna()]

                auto_chart = (
                    alt.Chart(chart_df)
                    .encode(
                        x="start_year:Q",
                        x2="end_year:Q",
                        y=alt.Y(f"{y_col}:N", sort="-x", title="Site/Period"),
                        tooltip=tooltip_cols,
                    )
                    .mark_bar(size=10, color=ACCENT_COLOR)
                )
                st.altair_chart(auto_chart, use_container_width=True)
            except Exception as e:  # pragma: no cover
                st.error(f"Could not render automatic timeline chart: {e}")
                st.dataframe(auto_time_df)
        else:
            render_empty_state(
                title="No timeline data yet",
                body="Process a PDF with date mentions, or upload a CSV with site_name and start_year columns.",
            )

        timeline_file = st.file_uploader(
            "Optionally upload additional timeline CSV", type=["csv"], key="timeline_csv"
        )
        if timeline_file is not None:
            df_time = pd.read_csv(timeline_file)
            if {"site_name", "start_year"}.issubset(df_time.columns):
                df_time["end_year"] = df_time.get("end_year", df_time["start_year"])
                df_time["start_year"] = pd.to_numeric(df_time["start_year"], errors="coerce")
                df_time["end_year"] = pd.to_numeric(df_time["end_year"], errors="coerce")
                df_time = df_time.dropna(subset=["start_year"])
                if not df_time.empty:
                    try:
                        import altair as alt

                        base = alt.Chart(df_time).encode(
                            x="start_year:Q",
                            x2="end_year:Q",
                            y=alt.Y("site_name:N", sort="-x"),
                            tooltip=["site_name", "start_year", "end_year"],
                        )
                        timeline = base.mark_bar(size=12, color=ACCENT_COLOR)
                        st.altair_chart(timeline, use_container_width=True)
                    except Exception as e:  # pragma: no cover
                        st.error(f"Could not render timeline chart: {e}")
                        st.dataframe(df_time)
                else:
                    st.warning("No valid rows after parsing years.")
            else:
                st.error("Timeline CSV must include at least `site_name` and `start_year` columns.")

    with st.container(border=True):
        st.markdown("#### Site relationships")
        st.caption("Sites, periods, and regions extracted from your document.")

        sites_list = st.session_state.get("sites_list")
        if sites_list:
            st.markdown("**Sites extracted from PDF:**")
            sites_df_display = pd.DataFrame(sites_list)
            st.dataframe(sites_df_display[["site_name", "site_type", "context"]], use_container_width=True)
            st.caption(f"Found {len(sites_list)} site(s) in the document")
        else:
            render_empty_state(
                title="No site relationships yet",
                body="Process a PDF with site mentions to see extracted relationships here.",
                cta_label="Go to Document Intelligence Desk",
                cta_key="spatial_goto_desk",
                cta_action="document_desk",
            )

        st.markdown(
            """
            This view encourages thinking in terms of **connections**:
            - Sites linked to **periods** and **regions**
            - Artifacts linked to **contexts** and **strata**

            For a full interactive knowledge graph, export your site table to tools
            like Neo4j, Gephi, or dedicated graph-visualisation platforms.
            """
        )
