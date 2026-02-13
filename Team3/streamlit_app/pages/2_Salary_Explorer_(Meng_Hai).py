"""Wrapper page for MengHai's Salary Explorer dashboard."""

import streamlit as st

st.set_page_config(
    page_title="Salary Explorer — Meng Hai",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

import sys
from pathlib import Path

# Add MengHai's folder to sys.path so its internal imports resolve
_menghai_dir = str(Path(__file__).parent.parent / "MengHai")
if _menghai_dir not in sys.path:
    sys.path.insert(0, _menghai_dir)

# Load MengHai's CSS
_css_path = Path(_menghai_dir) / "assets" / "style.css"
if _css_path.exists():
    with open(_css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Import components (NOT app.py — to avoid duplicate set_page_config)
from config.settings import COLORS, SEGMENT_PROFILES
from components.sidebar import render_sidebar, build_filter_clause
from components.kpi_cards import render_kpi_cards
from components.charts import render_job_listings_table
from components.salary_analysis import render_salary_analysis_section
from components.insights import render_segment_insights
from data.connection import get_connection


def main():
    st.title("SG Job Market Salary Explorer")
    st.markdown(
        "Explore salary trends and opportunities from **1M+ job postings** in Singapore."
    )

    with st.spinner("Loading data..."):
        try:
            get_connection()
        except Exception as e:
            st.error(f"Failed to load data: {e}")
            st.stop()

    # Profile selector
    profile_options = list(SEGMENT_PROFILES.keys())
    selected_profile = st.radio(
        "I am a:",
        profile_options,
        horizontal=True,
        index=0,
    )

    profile = SEGMENT_PROFILES[selected_profile]
    st.caption(f"{profile['icon']} {profile['description']}")

    # Sidebar filters
    filters = render_sidebar()

    filter_clause = build_filter_clause(filters)
    category_filter_clause = build_filter_clause(filters, for_categories_table=True)

    # Apply segment filter
    segment_filter = profile["filter"]
    segment_clause = filter_clause + " " + segment_filter
    if segment_filter:
        segment_category_clause = (
            category_filter_clause
            + " AND job_id IN (SELECT job_id FROM jobs_enriched WHERE 1=1 "
            + segment_filter
            + ")"
        )
    else:
        segment_category_clause = category_filter_clause

    st.divider()

    if selected_profile == "Everyone":
        st.caption("Key metrics at a glance based on your selected filters")
        render_kpi_cards(filter_clause)
        st.divider()
        render_salary_analysis_section(filter_clause, category_filter_clause)
    else:
        render_segment_insights(
            selected_profile, filter_clause, category_filter_clause, filters
        )
        st.divider()
        render_salary_analysis_section(segment_clause, segment_category_clause)

    st.divider()

    st.subheader("Job Listings")
    st.caption("Browse individual job postings — sorted by most recent")
    df = render_job_listings_table(segment_clause)

    if not df.empty:
        csv_data = df.to_csv(index=False)
        st.sidebar.download_button(
            label="Download Filtered Data (CSV)",
            data=csv_data,
            file_name="sg_jobs_filtered.csv",
            mime="text/csv",
            use_container_width=True,
            key="menghai_download",
        )

    st.divider()
    st.markdown(
        "<div style='text-align: center; color: #6B7280; font-size: 0.875rem;'>"
        "Data source: Singapore Government Job Portal | "
        "Built with Streamlit & DuckDB"
        "</div>",
        unsafe_allow_html=True,
    )


main()
