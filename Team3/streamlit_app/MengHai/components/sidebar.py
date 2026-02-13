"""Sidebar filter components for the Salary Explorer."""

import streamlit as st
from datetime import date
from config.settings import EXPERIENCE_BANDS, SALARY_BANDS
from data.connection import get_filter_options


def render_sidebar():
    """Render sidebar with all filter controls. Returns filter dictionary."""
    st.sidebar.header("Filters")

    # Get filter options from database
    options = get_filter_options()

    # Category filter
    selected_categories = st.sidebar.multiselect(
        "Job Categories",
        options=options["categories"],
        default=[],
        placeholder="All categories",
    )

    # Experience filter
    selected_experience = st.sidebar.multiselect(
        "Experience Level",
        options=EXPERIENCE_BANDS,
        default=[],
        placeholder="All experience levels",
    )

    # Company comparison - persistent selection using session state
    if "compared_companies" not in st.session_state:
        st.session_state.compared_companies = []

    st.sidebar.subheader("Compare Companies")

    # Search and add companies
    company_search = st.sidebar.text_input(
        "Search Company",
        value="",
        placeholder="Type to search (min 2 chars)...",
        help="Search and add multiple companies to compare",
        key="company_search_input",
    )

    # Show matching companies if search has 2+ characters
    if len(company_search.strip()) >= 2:
        from data.connection import search_companies
        matching_companies = search_companies(company_search.strip())
        # Filter out already selected companies
        available_companies = [c for c in matching_companies if c not in st.session_state.compared_companies]

        if available_companies:
            selected_to_add = st.sidebar.multiselect(
                "Add to comparison",
                options=available_companies,
                default=[],
                placeholder="Select companies to add...",
                key="companies_to_add",
            )
            # Add button
            if selected_to_add:
                if st.sidebar.button("➕ Add to Compare", use_container_width=True):
                    st.session_state.compared_companies.extend(selected_to_add)
                    st.rerun()
        elif matching_companies:
            st.sidebar.caption("All matching companies already added")
        else:
            st.sidebar.caption("No companies found")

    # Show currently selected companies
    if st.session_state.compared_companies:
        st.sidebar.markdown(f"**Selected ({len(st.session_state.compared_companies)}):**")
        for company in st.session_state.compared_companies:
            col1, col2 = st.sidebar.columns([4, 1])
            with col1:
                display_name = company[:25] + "..." if len(company) > 25 else company
                st.caption(display_name)
            with col2:
                if st.button("✕", key=f"remove_{company}", help=f"Remove {company}"):
                    st.session_state.compared_companies.remove(company)
                    st.rerun()

        if st.sidebar.button("Clear All Companies", use_container_width=True):
            st.session_state.compared_companies = []
            st.rerun()

    selected_companies = st.session_state.compared_companies

    # Salary bands filter
    selected_salary_bands = st.sidebar.multiselect(
        "Salary Range (Monthly)",
        options=SALARY_BANDS,
        default=[],
        placeholder="All salary ranges",
    )

    # Date range
    st.sidebar.subheader("Posting Date")
    if options["date_min"] and options["date_max"]:
        date_range = st.sidebar.date_input(
            "Date Range",
            value=(options["date_min"], options["date_max"]),
            min_value=options["date_min"],
            max_value=options["date_max"],
        )
        # Handle single date selection
        if isinstance(date_range, tuple) and len(date_range) == 2:
            date_start, date_end = date_range
        else:
            date_start = date_range if isinstance(date_range, date) else options["date_min"]
            date_end = options["date_max"]
    else:
        date_start = None
        date_end = None

    st.sidebar.divider()

    # Reset button
    if st.sidebar.button("Reset Filters", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    # Download button placeholder
    st.sidebar.download_button(
        label="Download Filtered Data (CSV)",
        data="",  # Will be populated by main app
        file_name="sg_jobs_filtered.csv",
        mime="text/csv",
        disabled=True,
        use_container_width=True,
        key="download_placeholder",
    )

    return {
        "categories": selected_categories,
        "experience": selected_experience,
        "companies": selected_companies,
        "salary_bands": selected_salary_bands,
        "date_start": date_start,
        "date_end": date_end,
    }


def build_filter_clause(filters: dict, table_prefix: str = "", for_categories_table: bool = False) -> str:
    """Build SQL WHERE clause from filters dictionary.

    Args:
        filters: Dictionary of filter values
        table_prefix: Optional table prefix for column names
        for_categories_table: If True, filter category_name directly.
                             If False, use subquery on job_id.
    """
    clauses = []
    prefix = f"{table_prefix}." if table_prefix else ""

    if filters.get("categories"):
        cats = ", ".join([f"'{c}'" for c in filters["categories"]])
        if for_categories_table:
            # Direct filter on jobs_categories table
            clauses.append(f"{prefix}category_name IN ({cats})")
        else:
            # Subquery filter for jobs_enriched table (no category_name column)
            clauses.append(f"{prefix}job_id IN (SELECT DISTINCT job_id FROM jobs_categories WHERE category_name IN ({cats}))")

    if filters.get("experience"):
        exps = ", ".join([f"'{e}'" for e in filters["experience"]])
        clauses.append(f"{prefix}experience_band IN ({exps})")

    if filters.get("companies"):
        comps = ", ".join([f"'{c.replace(chr(39), chr(39)+chr(39))}'" for c in filters["companies"]])
        clauses.append(f"{prefix}company_name IN ({comps})")

    if filters.get("salary_bands"):
        bands = ", ".join([f"'{b}'" for b in filters["salary_bands"]])
        clauses.append(f"{prefix}salary_band IN ({bands})")

    if filters.get("date_start"):
        clauses.append(f"{prefix}posting_date >= '{filters['date_start']}'")

    if filters.get("date_end"):
        clauses.append(f"{prefix}posting_date <= '{filters['date_end']}'")

    if clauses:
        return " AND " + " AND ".join(clauses)
    return ""
