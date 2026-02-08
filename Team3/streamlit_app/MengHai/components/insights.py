"""Segment-specific insight charts for the Salary Explorer."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from data.connection import execute_query
from config.settings import COLORS, CHART_COLORS, CHART_HEIGHT
from config.queries import (
    QUERY_SEGMENT_SALARY_SUMMARY,
    QUERY_SEGMENT_EMPLOYMENT_TYPE,
    QUERY_GRAD_TOP_HIRING_COMPANIES,
    QUERY_GRAD_TOP_CATEGORIES,
    QUERY_GRAD_SALARY_BY_EMPLOYMENT_TYPE,
    QUERY_MID_CATEGORY_SALARY_COMPARE,
    QUERY_MID_EXPERIENCE_PREMIUM,
    QUERY_MID_TOP_HIRING_COMPANIES,
    QUERY_EXP_POSITION_LEVEL_SALARY,
    QUERY_EXP_TOP_PAYING_CATEGORIES,
    QUERY_EXP_TOP_PAYING_COMPANIES,
)
from components.salary_analysis import apply_chart_theme
from components.kpi_cards import format_salary


def _prefix_segment_filter(segment_filter: str, prefix: str = "je") -> str:
    """Add table prefix to column names in segment filter for JOIN queries."""
    result = segment_filter
    for col in ("position_level", "experience_band"):
        result = result.replace(col, f"{prefix}.{col}")
    return result


def _build_segment_clause(filter_clause: str, segment_filter: str) -> dict:
    """Build format dict for segment queries."""
    return {"filters": filter_clause, "segment_filter": segment_filter}


def _build_category_segment_clause(
    filter_clause: str, segment_filter: str, filters: dict
) -> dict:
    """Build format dict for segment queries that JOIN with jobs_categories.

    For category-joined queries, the {filters} placeholder uses je. prefix
    and the segment filter columns also need je. prefix to avoid ambiguity.
    """
    from components.sidebar import build_filter_clause

    je_filter = build_filter_clause(filters, table_prefix="je")
    je_segment = _prefix_segment_filter(segment_filter)
    return {"filters": je_filter, "segment_filter": je_segment}


# =============================================================================
# SHARED: Segment KPI Cards
# =============================================================================


def _render_segment_kpis(filter_clause: str, segment_filter: str):
    """Render 4 KPI cards for the current segment."""
    fmt = _build_segment_clause(filter_clause, segment_filter)
    df = execute_query(QUERY_SEGMENT_SALARY_SUMMARY.format(**fmt))

    if df.empty or df.iloc[0]["total_jobs"] == 0:
        st.warning("No data available for this profile with the selected filters.")
        return False

    row = df.iloc[0]
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Average Salary",
            value=format_salary(row["avg_salary"]),
            help="Mean monthly salary for this segment",
        )
    with col2:
        st.metric(
            label="Median Salary",
            value=format_salary(row["median_salary"]),
            help="50th percentile salary",
        )
    with col3:
        st.metric(
            label="Total Jobs",
            value=f"{int(row['total_jobs']):,}",
            help="Number of job postings in this segment",
        )
    with col4:
        p25_val = row["p25_salary"] / 1000
        p75_val = row["p75_salary"] / 1000
        st.metric(
            label="Salary IQR",
            value=f"${p25_val:.1f}K-{p75_val:.1f}K",
            help="25th to 75th percentile range",
        )

    return True


# =============================================================================
# FRESH GRADUATE
# =============================================================================


def _render_grad_top_hiring(filter_clause: str, segment_filter: str):
    """Top hiring companies for fresh graduates."""
    fmt = _build_segment_clause(filter_clause, segment_filter)
    df = execute_query(QUERY_GRAD_TOP_HIRING_COMPANIES.format(**fmt))

    if df.empty:
        st.info("No company data available.")
        return

    df = df.sort_values("job_count", ascending=True)

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=df["company_name"].apply(
                lambda x: x[:30] + "..." if len(x) > 30 else x
            ),
            x=df["job_count"],
            orientation="h",
            marker_color=COLORS["primary"],
            hovertemplate="<b>%{y}</b><br>Jobs: %{x:,}<br>Avg Salary: $%{customdata:,.0f}<extra></extra>",
            customdata=df["avg_salary"],
        )
    )

    fig.update_layout(
        height=max(350, len(df) * 35),
        title="Top Hiring Companies for Graduates",
        xaxis_title="Number of Jobs",
        yaxis_title="",
    )

    fig = apply_chart_theme(fig)
    st.plotly_chart(fig, use_container_width=True)


def _render_grad_top_categories(
    filter_clause: str, segment_filter: str, filters: dict
):
    """Most popular categories for fresh graduates with median salary."""
    fmt = _build_category_segment_clause(filter_clause, segment_filter, filters)
    df = execute_query(QUERY_GRAD_TOP_CATEGORIES.format(**fmt))

    if df.empty:
        st.info("No category data available.")
        return

    df = df.sort_values("job_count", ascending=True)

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=df["category_name"].apply(
                lambda x: x[:30] + "..." if len(x) > 30 else x
            ),
            x=df["job_count"],
            orientation="h",
            marker_color=CHART_COLORS[1],
            hovertemplate="<b>%{y}</b><br>Jobs: %{x:,}<br>Median Salary: $%{customdata:,.0f}<extra></extra>",
            customdata=df["median_salary"],
        )
    )

    fig.update_layout(
        height=max(350, len(df) * 35),
        title="Most Popular Categories (with Median Salary)",
        xaxis_title="Number of Jobs",
        yaxis_title="",
    )

    fig = apply_chart_theme(fig)
    st.plotly_chart(fig, use_container_width=True)


def _render_grad_employment_type(filter_clause: str, segment_filter: str):
    """Salary comparison by employment type for graduates."""
    fmt = _build_segment_clause(filter_clause, segment_filter)
    df = execute_query(QUERY_GRAD_SALARY_BY_EMPLOYMENT_TYPE.format(**fmt))

    if df.empty:
        st.info("No employment type data available.")
        return

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df["employment_type"],
            y=df["avg_salary"],
            name="Average",
            marker_color=COLORS["primary"],
            hovertemplate="<b>%{x}</b><br>Avg: $%{y:,.0f}<br>Jobs: %{customdata:,}<extra></extra>",
            customdata=df["job_count"],
        )
    )
    fig.add_trace(
        go.Bar(
            x=df["employment_type"],
            y=df["median_salary"],
            name="Median",
            marker_color=COLORS["secondary"],
            hovertemplate="<b>%{x}</b><br>Median: $%{y:,.0f}<extra></extra>",
        )
    )

    fig.update_layout(
        height=CHART_HEIGHT,
        title="Salary by Employment Type",
        xaxis_title="Employment Type",
        yaxis_title="Monthly Salary (SGD)",
        barmode="group",
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
    )

    fig = apply_chart_theme(fig)
    st.plotly_chart(fig, use_container_width=True)


def _render_fresh_grad_insights(
    filter_clause: str, segment_filter: str, filters: dict
):
    """Render all Fresh Graduate insight charts."""
    st.subheader("Fresh Graduate Insights")

    if not _render_segment_kpis(filter_clause, segment_filter):
        return

    col1, col2 = st.columns(2)
    with col1:
        _render_grad_top_hiring(filter_clause, segment_filter)
    with col2:
        _render_grad_top_categories(filter_clause, segment_filter, filters)

    _render_grad_employment_type(filter_clause, segment_filter)


# =============================================================================
# MID-CAREER SWITCHER
# =============================================================================


def _render_mid_category_compare(
    filter_clause: str, segment_filter: str, filters: dict
):
    """Category salary comparison for mid-career pivots."""
    fmt = _build_category_segment_clause(filter_clause, segment_filter, filters)
    df = execute_query(QUERY_MID_CATEGORY_SALARY_COMPARE.format(**fmt))

    if df.empty:
        st.info("No category salary data available.")
        return

    df = df.sort_values("avg_salary", ascending=True)

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=df["category_name"].apply(
                lambda x: x[:30] + "..." if len(x) > 30 else x
            ),
            x=df["avg_salary"],
            name="Average",
            orientation="h",
            marker_color=COLORS["primary"],
            hovertemplate="<b>%{y}</b><br>Avg: $%{x:,.0f}<br>Jobs: %{customdata:,}<extra></extra>",
            customdata=df["job_count"],
        )
    )
    fig.add_trace(
        go.Bar(
            y=df["category_name"].apply(
                lambda x: x[:30] + "..." if len(x) > 30 else x
            ),
            x=df["median_salary"],
            name="Median",
            orientation="h",
            marker_color=COLORS["secondary"],
            hovertemplate="<b>%{y}</b><br>Median: $%{x:,.0f}<extra></extra>",
        )
    )

    fig.update_layout(
        height=max(400, len(df) * 35),
        title="Salary by Category (for Career Pivots)",
        xaxis_title="Monthly Salary (SGD)",
        yaxis_title="",
        barmode="group",
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
    )

    fig = apply_chart_theme(fig)
    st.plotly_chart(fig, use_container_width=True)


def _render_mid_experience_premium(filter_clause: str, filters: dict):
    """Salary uplift from mid to senior experience by category."""
    from components.sidebar import build_filter_clause

    je_filter = build_filter_clause(filters, table_prefix="je")
    df = execute_query(QUERY_MID_EXPERIENCE_PREMIUM.format(filters=je_filter))

    if df.empty:
        st.info("No experience premium data available.")
        return

    # Pivot to get mid vs senior salaries per category
    pivot = df.pivot_table(
        index="category_name",
        columns="experience_band",
        values="avg_salary",
    )

    if "Mid (3-5 years)" not in pivot.columns or "Senior (6-10 years)" not in pivot.columns:
        st.info("Insufficient data to compare experience bands.")
        return

    pivot = pivot.dropna()
    if pivot.empty:
        st.info("No categories with both mid and senior data.")
        return

    pivot["premium_pct"] = (
        (pivot["Senior (6-10 years)"] - pivot["Mid (3-5 years)"])
        / pivot["Mid (3-5 years)"]
        * 100
    )
    pivot = pivot.sort_values("premium_pct", ascending=True).tail(15)

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=pivot.index.map(lambda x: x[:30] + "..." if len(x) > 30 else x),
            x=pivot["premium_pct"],
            orientation="h",
            marker_color=[
                COLORS["secondary"] if v >= 0 else COLORS["error"]
                for v in pivot["premium_pct"]
            ],
            hovertemplate="<b>%{y}</b><br>Premium: %{x:.1f}%<br>Mid: $%{customdata[0]:,.0f}<br>Senior: $%{customdata[1]:,.0f}<extra></extra>",
            customdata=pivot[
                ["Mid (3-5 years)", "Senior (6-10 years)"]
            ].values,
        )
    )

    fig.update_layout(
        height=max(400, len(pivot) * 35),
        title="Salary Premium: Senior vs Mid Experience",
        xaxis_title="Salary Premium (%)",
        yaxis_title="",
    )

    fig = apply_chart_theme(fig)
    st.plotly_chart(fig, use_container_width=True)


def _render_mid_top_companies(filter_clause: str, segment_filter: str):
    """Top hiring companies at mid-career level."""
    fmt = _build_segment_clause(filter_clause, segment_filter)
    df = execute_query(QUERY_MID_TOP_HIRING_COMPANIES.format(**fmt))

    if df.empty:
        st.info("No company data available.")
        return

    df = df.sort_values("job_count", ascending=True)

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=df["company_name"].apply(
                lambda x: x[:30] + "..." if len(x) > 30 else x
            ),
            x=df["job_count"],
            orientation="h",
            marker_color=CHART_COLORS[3],
            hovertemplate="<b>%{y}</b><br>Jobs: %{x:,}<br>Avg Salary: $%{customdata:,.0f}<extra></extra>",
            customdata=df["avg_salary"],
        )
    )

    fig.update_layout(
        height=max(350, len(df) * 35),
        title="Top Hiring Companies (Mid-Career)",
        xaxis_title="Number of Jobs",
        yaxis_title="",
    )

    fig = apply_chart_theme(fig)
    st.plotly_chart(fig, use_container_width=True)


def _render_mid_career_insights(
    filter_clause: str, segment_filter: str, filters: dict
):
    """Render all Mid-Career Switcher insight charts."""
    st.subheader("Mid-Career Switcher Insights")

    if not _render_segment_kpis(filter_clause, segment_filter):
        return

    _render_mid_category_compare(filter_clause, segment_filter, filters)

    col1, col2 = st.columns(2)
    with col1:
        _render_mid_experience_premium(filter_clause, filters)
    with col2:
        _render_mid_top_companies(filter_clause, segment_filter)


# =============================================================================
# EXPERIENCED PROFESSIONAL
# =============================================================================


def _render_exp_position_salary(filter_clause: str, segment_filter: str):
    """Salary by position level for experienced professionals."""
    fmt = _build_segment_clause(filter_clause, segment_filter)
    df = execute_query(QUERY_EXP_POSITION_LEVEL_SALARY.format(**fmt))

    if df.empty:
        st.info("No position level data available.")
        return

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df["position_level"],
            y=df["avg_salary"],
            name="Average",
            marker_color=COLORS["primary"],
            hovertemplate="<b>%{x}</b><br>Avg: $%{y:,.0f}<br>Jobs: %{customdata:,}<extra></extra>",
            customdata=df["job_count"],
        )
    )
    fig.add_trace(
        go.Bar(
            x=df["position_level"],
            y=df["median_salary"],
            name="Median",
            marker_color=COLORS["secondary"],
            hovertemplate="<b>%{x}</b><br>Median: $%{y:,.0f}<extra></extra>",
        )
    )

    fig.update_layout(
        height=CHART_HEIGHT,
        title="Salary by Position Level",
        xaxis_title="Position Level",
        yaxis_title="Monthly Salary (SGD)",
        barmode="group",
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
    )

    fig = apply_chart_theme(fig)
    st.plotly_chart(fig, use_container_width=True)


def _render_exp_top_categories(
    filter_clause: str, segment_filter: str, filters: dict
):
    """Top paying categories for experienced professionals."""
    fmt = _build_category_segment_clause(filter_clause, segment_filter, filters)
    df = execute_query(QUERY_EXP_TOP_PAYING_CATEGORIES.format(**fmt))

    if df.empty:
        st.info("No category data available.")
        return

    df = df.sort_values("avg_salary", ascending=True)

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=df["category_name"].apply(
                lambda x: x[:30] + "..." if len(x) > 30 else x
            ),
            x=df["avg_salary"],
            orientation="h",
            marker_color=CHART_COLORS[2],
            hovertemplate="<b>%{y}</b><br>Avg: $%{x:,.0f}<br>Median: $%{customdata[0]:,.0f}<br>Jobs: %{customdata[1]:,}<extra></extra>",
            customdata=df[["median_salary", "job_count"]].values,
        )
    )

    fig.update_layout(
        height=max(350, len(df) * 35),
        title="Top Paying Categories",
        xaxis_title="Average Monthly Salary (SGD)",
        yaxis_title="",
    )

    fig = apply_chart_theme(fig)
    st.plotly_chart(fig, use_container_width=True)


def _render_exp_top_companies(filter_clause: str, segment_filter: str):
    """Top paying companies for experienced professionals."""
    fmt = _build_segment_clause(filter_clause, segment_filter)
    df = execute_query(QUERY_EXP_TOP_PAYING_COMPANIES.format(**fmt))

    if df.empty:
        st.info("No company data available.")
        return

    df = df.sort_values("avg_salary", ascending=True)

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=df["company_name"].apply(
                lambda x: x[:30] + "..." if len(x) > 30 else x
            ),
            x=df["avg_salary"],
            orientation="h",
            marker_color=CHART_COLORS[4],
            hovertemplate="<b>%{y}</b><br>Avg: $%{x:,.0f}<br>Median: $%{customdata[0]:,.0f}<br>Jobs: %{customdata[1]:,}<extra></extra>",
            customdata=df[["median_salary", "job_count"]].values,
        )
    )

    fig.update_layout(
        height=max(350, len(df) * 35),
        title="Top Paying Companies",
        xaxis_title="Average Monthly Salary (SGD)",
        yaxis_title="",
    )

    fig = apply_chart_theme(fig)
    st.plotly_chart(fig, use_container_width=True)


def _render_experienced_insights(
    filter_clause: str, segment_filter: str, filters: dict
):
    """Render all Experienced Professional insight charts."""
    st.subheader("Experienced Professional Insights")

    if not _render_segment_kpis(filter_clause, segment_filter):
        return

    _render_exp_position_salary(filter_clause, segment_filter)

    col1, col2 = st.columns(2)
    with col1:
        _render_exp_top_categories(filter_clause, segment_filter, filters)
    with col2:
        _render_exp_top_companies(filter_clause, segment_filter)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================


def render_segment_insights(
    profile_name: str,
    filter_clause: str,
    category_filter_clause: str,
    filters: dict,
):
    """Render segment-specific insights based on the selected profile."""
    from config.settings import SEGMENT_PROFILES

    profile = SEGMENT_PROFILES[profile_name]
    segment_filter = profile["filter"]

    if profile_name == "Fresh Graduate":
        _render_fresh_grad_insights(filter_clause, segment_filter, filters)
    elif profile_name == "Mid-Career Switcher":
        _render_mid_career_insights(filter_clause, segment_filter, filters)
    elif profile_name == "Experienced Professional":
        _render_experienced_insights(filter_clause, segment_filter, filters)
