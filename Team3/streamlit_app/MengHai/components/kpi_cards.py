"""KPI card components for the Salary Explorer."""

import streamlit as st
import pandas as pd
from data.connection import execute_query
from config.queries import QUERY_SALARY_SUMMARY


def format_salary(value):
    """Format salary value in compact K notation."""
    if value >= 1000:
        return f"${value/1000:.1f}K"
    return f"${value:,.0f}"


def render_kpi_cards(filter_clause: str = ""):
    """Render KPI metric cards in a row."""
    # Execute summary query with filters
    query = QUERY_SALARY_SUMMARY.format(filters=filter_clause)
    df = execute_query(query)

    if df.empty:
        st.warning("No data available for the selected filters.")
        return

    row = df.iloc[0]

    # Create 4-column layout for KPIs
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Average Salary",
            value=format_salary(row['avg_salary']),
            help="Mean monthly salary across all filtered jobs",
        )

    with col2:
        st.metric(
            label="Median Salary",
            value=format_salary(row['median_salary']),
            help="50th percentile salary (middle value)",
        )

    with col3:
        st.metric(
            label="Total Jobs",
            value=f"{int(row['total_jobs']):,}",
            help="Number of job postings matching filters",
        )

    with col4:
        # Compact format: $2.9K-5.5K (no $ on second value, no spaces)
        p25_val = row['p25_salary']/1000
        p75_val = row['p75_salary']/1000
        st.metric(
            label="Salary IQR",
            value=f"${p25_val:.1f}K-{p75_val:.1f}K",
            help="25th to 75th percentile range (middle 50% of salaries)",
        )
