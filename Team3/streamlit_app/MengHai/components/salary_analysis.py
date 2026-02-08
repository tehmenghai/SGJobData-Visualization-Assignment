"""Salary Analysis charts - Salary by Category and Salary by Company."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from data.connection import execute_query
from config.settings import COLORS, CHART_COLORS, CHART_HEIGHT, SALARY_BANDS


def apply_chart_theme(fig):
    """Apply consistent theme to all charts."""
    fig.update_layout(
        font_family="system-ui, -apple-system, sans-serif",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=40, b=20),
        hoverlabel=dict(font_size=12),
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="#E5E7EB")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="#E5E7EB")
    return fig


# =============================================================================
# SALARY BY CATEGORY
# =============================================================================

def render_salary_distribution_by_category(filter_clause: str = "", sort_by: str = "Most Jobs"):
    """Box plot showing salary distribution for top categories."""

    # Get top 10 categories based on sort criteria
    if sort_by == "Highest Avg Salary":
        top_cats = execute_query(f"""
            SELECT category_name, AVG(avg_salary) as avg_sal, COUNT(*) as cnt
            FROM jobs_categories
            WHERE category_name IS NOT NULL AND avg_salary > 0 {filter_clause}
            GROUP BY category_name
            ORDER BY avg_sal DESC
            LIMIT 10
        """)
    elif sort_by == "Highest Median Salary":
        top_cats = execute_query(f"""
            SELECT category_name,
                   PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY avg_salary) as median_sal,
                   COUNT(*) as cnt
            FROM jobs_categories
            WHERE category_name IS NOT NULL AND avg_salary > 0 {filter_clause}
            GROUP BY category_name
            ORDER BY median_sal DESC
            LIMIT 10
        """)
    else:  # Most Jobs
        top_cats = execute_query(f"""
            SELECT category_name, COUNT(*) as cnt
            FROM jobs_categories
            WHERE category_name IS NOT NULL {filter_clause}
            GROUP BY category_name
            ORDER BY cnt DESC
            LIMIT 10
        """)

    if top_cats.empty:
        st.info("No category data available.")
        return

    cat_list = top_cats["category_name"].tolist()
    cat_filter = ", ".join([f"'{c.replace(chr(39), chr(39)+chr(39))}'" for c in cat_list])

    # Get salary data for these categories (with same filters applied)
    df = execute_query(f"""
        SELECT category_name, avg_salary
        FROM jobs_categories
        WHERE category_name IN ({cat_filter})
          AND avg_salary > 0 AND avg_salary < 50000
          {filter_clause}
    """)

    if df.empty:
        st.info("No salary data available.")
        return

    # Order categories by median salary
    cat_order = df.groupby("category_name")["avg_salary"].median().sort_values(ascending=True).index.tolist()

    fig = go.Figure()

    for i, cat in enumerate(cat_order):
        cat_data = df[df["category_name"] == cat]["avg_salary"]
        fig.add_trace(go.Box(
            y=[cat] * len(cat_data),
            x=cat_data,
            name=cat[:25] + "..." if len(cat) > 25 else cat,
            orientation="h",
            marker_color=CHART_COLORS[i % len(CHART_COLORS)],
            boxpoints=False,
        ))

    fig.update_layout(
        height=max(350, len(cat_order) * 40),
        title="Salary Range by Category",
        xaxis_title="Monthly Salary (SGD)",
        yaxis_title="",
        showlegend=False,
    )

    fig = apply_chart_theme(fig)
    st.plotly_chart(fig, use_container_width=True)


def render_salary_band_by_category(filter_clause: str = "", sort_by: str = "Most Jobs"):
    """Stacked bar showing salary band distribution by category."""

    df = execute_query(f"""
        SELECT
            category_name,
            salary_band,
            COUNT(*) as job_count
        FROM jobs_categories
        WHERE category_name IS NOT NULL
          AND salary_band IS NOT NULL
          {filter_clause}
        GROUP BY category_name, salary_band
    """)

    if df.empty:
        st.info("No data available.")
        return

    # Get top 10 categories using the same sort criteria as the box plot
    if sort_by == "Highest Avg Salary":
        avg_salary = execute_query(f"""
            SELECT category_name, AVG(avg_salary) as avg_sal
            FROM jobs_categories
            WHERE category_name IS NOT NULL AND avg_salary > 0 {filter_clause}
            GROUP BY category_name
            ORDER BY avg_sal DESC
            LIMIT 10
        """)
        top_cats = avg_salary["category_name"].tolist()
    elif sort_by == "Highest Median Salary":
        median_salary = execute_query(f"""
            SELECT category_name,
                   PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY avg_salary) as median_sal
            FROM jobs_categories
            WHERE category_name IS NOT NULL AND avg_salary > 0 {filter_clause}
            GROUP BY category_name
            ORDER BY median_sal DESC
            LIMIT 10
        """)
        top_cats = median_salary["category_name"].tolist()
    else:  # Most Jobs
        top_cats = df.groupby("category_name")["job_count"].sum().nlargest(10).index.tolist()

    df = df[df["category_name"].isin(top_cats)]

    # Pivot and calculate percentages
    pivot = df.pivot(index="category_name", columns="salary_band", values="job_count").fillna(0)
    pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

    # Order by high salary percentage (12K+ combined)
    high_salary_cols = [c for c in pivot_pct.columns if "12K" in c or "20K" in c]
    if high_salary_cols:
        pivot_pct["_sort"] = pivot_pct[high_salary_cols].sum(axis=1)
        pivot_pct = pivot_pct.sort_values("_sort", ascending=True)
        pivot_pct = pivot_pct.drop("_sort", axis=1)

    # Define colors for salary bands
    band_colors = {
        "< 3K": "#FEE2E2",      # Light red (low)
        "3K - 5K": "#FEF3C7",   # Light yellow
        "5K - 8K": "#D1FAE5",   # Light green
        "8K - 12K": "#DBEAFE",  # Light blue
        "12K - 20K": "#C7D2FE", # Light indigo
        "20K+": "#2563EB",      # Primary blue (high)
    }

    fig = go.Figure()

    for band in SALARY_BANDS:
        if band in pivot_pct.columns:
            fig.add_trace(go.Bar(
                y=pivot_pct.index,
                x=pivot_pct[band],
                name=band,
                orientation="h",
                marker_color=band_colors.get(band, "#888"),
                hovertemplate=f"<b>%{{y}}</b><br>{band}: %{{x:.1f}}%<extra></extra>",
            ))

    fig.update_layout(
        height=max(350, len(pivot_pct) * 40),
        title="Salary Bands by Category",
        xaxis_title="Percentage (%)",
        yaxis_title="",
        barmode="stack",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    fig = apply_chart_theme(fig)
    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# SALARY BY COMPANY
# =============================================================================

def render_top_paying_companies(filter_clause: str = ""):
    """Horizontal bar chart of top paying companies."""

    df = execute_query(f"""
        SELECT
            company_name,
            AVG(avg_salary) as avg_salary,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY avg_salary) as median_salary,
            COUNT(*) as job_count
        FROM jobs_enriched
        WHERE company_name IS NOT NULL
          AND avg_salary > 0
          {filter_clause}
        GROUP BY company_name
        HAVING COUNT(*) >= 5
        ORDER BY avg_salary DESC
        LIMIT 15
    """)

    if df.empty:
        st.info("No company data available.")
        return

    df = df.sort_values("avg_salary", ascending=True)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=df["company_name"].apply(lambda x: x[:30] + "..." if len(x) > 30 else x),
        x=df["avg_salary"],
        orientation="h",
        marker_color=COLORS["primary"],
        hovertemplate="<b>%{y}</b><br>Avg Salary: $%{x:,.0f}<br>Jobs: %{customdata[0]:,}<br>Median: $%{customdata[1]:,.0f}<extra></extra>",
        customdata=df[["job_count", "median_salary"]].values,
    ))

    fig.update_layout(
        height=max(400, len(df) * 30),
        title="Top Paying Companies",
        xaxis_title="Average Monthly Salary (SGD)",
        yaxis_title="",
    )

    fig = apply_chart_theme(fig)
    st.plotly_chart(fig, use_container_width=True)


def render_salary_band_by_company(filter_clause: str = ""):
    """Stacked bar showing salary band distribution by top companies."""

    # Get top 10 companies by job count
    top_companies = execute_query(f"""
        SELECT company_name, COUNT(*) as cnt
        FROM jobs_enriched
        WHERE company_name IS NOT NULL {filter_clause}
        GROUP BY company_name
        ORDER BY cnt DESC
        LIMIT 10
    """)

    if top_companies.empty:
        st.info("No company data available.")
        return

    company_list = top_companies["company_name"].tolist()
    company_filter = ", ".join([f"'{c.replace(chr(39), chr(39)+chr(39))}'" for c in company_list])

    df = execute_query(f"""
        SELECT
            company_name,
            salary_band,
            COUNT(*) as job_count
        FROM jobs_enriched
        WHERE company_name IN ({company_filter})
          AND salary_band IS NOT NULL
        GROUP BY company_name, salary_band
    """)

    if df.empty:
        st.info("No data available.")
        return

    # Pivot and calculate percentages
    pivot = df.pivot(index="company_name", columns="salary_band", values="job_count").fillna(0)
    pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

    # Order by high salary percentage
    high_salary_cols = [c for c in pivot_pct.columns if "12K" in c or "20K" in c]
    if high_salary_cols:
        pivot_pct["_sort"] = pivot_pct[high_salary_cols].sum(axis=1)
        pivot_pct = pivot_pct.sort_values("_sort", ascending=True)
        pivot_pct = pivot_pct.drop("_sort", axis=1)

    # Define colors for salary bands
    band_colors = {
        "< 3K": "#FEE2E2",
        "3K - 5K": "#FEF3C7",
        "5K - 8K": "#D1FAE5",
        "8K - 12K": "#DBEAFE",
        "12K - 20K": "#C7D2FE",
        "20K+": "#2563EB",
    }

    fig = go.Figure()

    for band in SALARY_BANDS:
        if band in pivot_pct.columns:
            fig.add_trace(go.Bar(
                y=pivot_pct.index.map(lambda x: x[:25] + "..." if len(x) > 25 else x),
                x=pivot_pct[band],
                name=band,
                orientation="h",
                marker_color=band_colors.get(band, "#888"),
                hovertemplate=f"<b>%{{y}}</b><br>{band}: %{{x:.1f}}%<extra></extra>",
            ))

    fig.update_layout(
        height=max(350, len(pivot_pct) * 40),
        title="Salary Bands by Company",
        xaxis_title="Percentage (%)",
        yaxis_title="",
        barmode="stack",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    fig = apply_chart_theme(fig)
    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# SALARY BAND BY JOB TITLE
# =============================================================================

def render_salary_band_by_job_title(filter_clause: str = ""):
    """Stacked bar showing salary band distribution by top job titles."""

    # Get top 10 job titles by job count
    top_titles = execute_query(f"""
        SELECT title, COUNT(*) as cnt
        FROM jobs_enriched
        WHERE title IS NOT NULL {filter_clause}
        GROUP BY title
        ORDER BY cnt DESC
        LIMIT 10
    """)

    if top_titles.empty:
        st.info("No job title data available.")
        return

    title_list = top_titles["title"].tolist()
    title_filter = ", ".join([f"'{t.replace(chr(39), chr(39)+chr(39))}'" for t in title_list])

    df = execute_query(f"""
        SELECT
            title,
            salary_band,
            COUNT(*) as job_count
        FROM jobs_enriched
        WHERE title IN ({title_filter})
          AND salary_band IS NOT NULL
        GROUP BY title, salary_band
    """)

    if df.empty:
        st.info("No data available.")
        return

    # Pivot and calculate percentages
    pivot = df.pivot(index="title", columns="salary_band", values="job_count").fillna(0)
    pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

    # Order by high salary percentage
    high_salary_cols = [c for c in pivot_pct.columns if "12K" in c or "20K" in c]
    if high_salary_cols:
        pivot_pct["_sort"] = pivot_pct[high_salary_cols].sum(axis=1)
        pivot_pct = pivot_pct.sort_values("_sort", ascending=True)
        pivot_pct = pivot_pct.drop("_sort", axis=1)

    # Define colors for salary bands
    band_colors = {
        "< 3K": "#FEE2E2",
        "3K - 5K": "#FEF3C7",
        "5K - 8K": "#D1FAE5",
        "8K - 12K": "#DBEAFE",
        "12K - 20K": "#C7D2FE",
        "20K+": "#2563EB",
    }

    fig = go.Figure()

    for band in SALARY_BANDS:
        if band in pivot_pct.columns:
            fig.add_trace(go.Bar(
                y=pivot_pct.index.map(lambda x: x[:30] + "..." if len(x) > 30 else x),
                x=pivot_pct[band],
                name=band,
                orientation="h",
                marker_color=band_colors.get(band, "#888"),
                hovertemplate=f"<b>%{{y}}</b><br>{band}: %{{x:.1f}}%<extra></extra>",
            ))

    fig.update_layout(
        height=max(350, len(pivot_pct) * 40),
        title="Salary Bands by Job Title",
        xaxis_title="Percentage (%)",
        yaxis_title="",
        barmode="stack",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    fig = apply_chart_theme(fig)
    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# MAIN SECTION RENDERER
# =============================================================================

def render_salary_analysis_section(filter_clause: str = "", category_filter_clause: str = ""):
    """Render the complete Salary Analysis section."""

    # Salary by Category
    st.subheader("Salary by Category")

    # Toggle for sorting criteria
    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption("Compare salary ranges across job categories - wider boxes mean more salary variation")
    with col2:
        sort_by = st.radio(
            "Show Top 10 by:",
            ["Most Jobs", "Highest Avg Salary", "Highest Median Salary"],
            horizontal=True,
            label_visibility="collapsed",
        )

    render_salary_distribution_by_category(category_filter_clause, sort_by)

    st.caption("What % of jobs in each category fall into each salary band? Darker = higher pay")
    render_salary_band_by_category(category_filter_clause, sort_by)

    st.divider()

    # Salary by Job Title
    st.subheader("Salary by Job Title")

    st.caption("Salary band breakdown for the most common job titles")
    render_salary_band_by_job_title(filter_clause)
