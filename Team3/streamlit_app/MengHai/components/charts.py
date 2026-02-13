"""Plotly chart components for the Salary Explorer."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from data.connection import execute_query
from config.settings import COLORS, CHART_COLORS, CHART_HEIGHT, CHART_MARGIN
from config.queries import (
    QUERY_SALARY_DISTRIBUTION,
    QUERY_SALARY_BY_CATEGORY,
    QUERY_SALARY_BY_EXPERIENCE,
    QUERY_SALARY_TRENDS,
)


def apply_chart_theme(fig):
    """Apply consistent theme to all charts."""
    fig.update_layout(
        font_family="system-ui, -apple-system, sans-serif",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=CHART_MARGIN,
        hoverlabel=dict(font_size=12),
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="#E5E7EB")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="#E5E7EB")
    return fig


def render_salary_distribution(filter_clause: str = ""):
    """Render salary distribution histogram with box plot."""
    query = QUERY_SALARY_DISTRIBUTION.format(filters=filter_clause)
    df = execute_query(query)

    if df.empty:
        st.info("No salary data available for selected filters.")
        return

    # Create subplot with histogram and box plot
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.2, 0.8],
        shared_xaxes=True,
        vertical_spacing=0.02,
    )

    # Box plot on top
    fig.add_trace(
        go.Box(
            x=df["avg_salary"],
            name="",
            marker_color=COLORS["primary"],
            boxpoints=False,
            hoverinfo="x",
        ),
        row=1, col=1,
    )

    # Histogram below
    fig.add_trace(
        go.Histogram(
            x=df["avg_salary"],
            nbinsx=50,
            marker_color=COLORS["primary"],
            opacity=0.7,
            hovertemplate="Salary: $%{x:,.0f}<br>Count: %{y}<extra></extra>",
        ),
        row=2, col=1,
    )

    fig.update_layout(
        height=CHART_HEIGHT,
        showlegend=False,
        title=dict(
            text="Salary Distribution",
            font=dict(size=16, color=COLORS["text"]),
        ),
    )

    fig.update_xaxes(title_text="Monthly Salary (SGD)", row=2, col=1)
    fig.update_yaxes(title_text="Number of Jobs", row=2, col=1)

    fig = apply_chart_theme(fig)
    st.plotly_chart(fig, use_container_width=True)


def render_salary_by_category(filter_clause: str = ""):
    """Render horizontal bar chart of salaries by category."""
    query = QUERY_SALARY_BY_CATEGORY.format(filters=filter_clause)
    df = execute_query(query)

    if df.empty:
        st.info("No category data available for selected filters.")
        return

    # Sort by average salary descending
    df = df.sort_values("avg_salary", ascending=True)

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            y=df["category_name"],
            x=df["avg_salary"],
            orientation="h",
            marker_color=COLORS["primary"],
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Avg Salary: $%{x:,.0f}<br>"
                "Jobs: %{customdata:,}<extra></extra>"
            ),
            customdata=df["job_count"],
        )
    )

    fig.update_layout(
        height=max(CHART_HEIGHT, len(df) * 25),
        title=dict(
            text="Top 20 Categories by Average Salary",
            font=dict(size=16, color=COLORS["text"]),
        ),
        xaxis_title="Average Monthly Salary (SGD)",
        yaxis_title="",
    )

    fig = apply_chart_theme(fig)
    st.plotly_chart(fig, use_container_width=True)


def render_salary_by_experience(filter_clause: str = ""):
    """Render grouped bar chart of salaries by experience level."""
    query = QUERY_SALARY_BY_EXPERIENCE.format(filters=filter_clause)
    df = execute_query(query)

    if df.empty:
        st.info("No experience data available for selected filters.")
        return

    fig = go.Figure()

    # Average salary bars
    fig.add_trace(
        go.Bar(
            x=df["experience_band"],
            y=df["avg_salary"],
            name="Average",
            marker_color=COLORS["primary"],
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Avg: $%{y:,.0f}<br>"
                "Jobs: %{customdata:,}<extra></extra>"
            ),
            customdata=df["job_count"],
        )
    )

    # Median salary bars
    fig.add_trace(
        go.Bar(
            x=df["experience_band"],
            y=df["median_salary"],
            name="Median",
            marker_color=COLORS["secondary"],
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Median: $%{y:,.0f}<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        height=CHART_HEIGHT,
        title=dict(
            text="Salary by Experience Level",
            font=dict(size=16, color=COLORS["text"]),
        ),
        xaxis_title="Experience Level",
        yaxis_title="Monthly Salary (SGD)",
        barmode="group",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )

    fig = apply_chart_theme(fig)
    st.plotly_chart(fig, use_container_width=True)


def render_salary_trends(filter_clause: str = ""):
    """Render salary trends over time with confidence band."""
    query = QUERY_SALARY_TRENDS.format(filters=filter_clause)
    df = execute_query(query)

    if df.empty or len(df) < 2:
        st.info("Not enough data to show salary trends for selected filters.")
        return

    df = df.sort_values("month")

    fig = go.Figure()

    # Add confidence band (P25-P75)
    fig.add_trace(
        go.Scatter(
            x=pd.concat([df["month"], df["month"][::-1]]),
            y=pd.concat([df["p75_salary"], df["p25_salary"][::-1]]),
            fill="toself",
            fillcolor=f"rgba(37, 99, 235, 0.1)",
            line=dict(color="rgba(255,255,255,0)"),
            hoverinfo="skip",
            name="P25-P75 Range",
        )
    )

    # Add median line
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=df["median_salary"],
            mode="lines+markers",
            name="Median Salary",
            line=dict(color=COLORS["primary"], width=2),
            marker=dict(size=6),
            hovertemplate=(
                "<b>%{x|%b %Y}</b><br>"
                "Median: $%{y:,.0f}<extra></extra>"
            ),
        )
    )

    # Add average line
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=df["avg_salary"],
            mode="lines",
            name="Average Salary",
            line=dict(color=COLORS["secondary"], width=2, dash="dash"),
            hovertemplate=(
                "<b>%{x|%b %Y}</b><br>"
                "Average: $%{y:,.0f}<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        height=CHART_HEIGHT,
        title=dict(
            text="Salary Trends Over Time",
            font=dict(size=16, color=COLORS["text"]),
        ),
        xaxis_title="Month",
        yaxis_title="Monthly Salary (SGD)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        hovermode="x unified",
    )

    fig = apply_chart_theme(fig)
    st.plotly_chart(fig, use_container_width=True)


def render_job_listings_table(filter_clause: str = ""):
    """Render detailed job listings table."""
    from config.queries import QUERY_JOB_LISTINGS

    query = QUERY_JOB_LISTINGS.format(filters=filter_clause)
    df = execute_query(query)

    if df.empty:
        st.info("No job listings available for selected filters.")
        return df

    # Format for display
    display_df = df.copy()
    if "avg_salary" in display_df.columns:
        display_df["avg_salary"] = display_df["avg_salary"].apply(
            lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A"
        )
    if "posting_date" in display_df.columns:
        display_df["posting_date"] = pd.to_datetime(display_df["posting_date"]).dt.strftime("%Y-%m-%d")

    # Rename columns for display
    display_df.columns = [
        "Title", "Company", "Avg Salary", "Experience", "Salary Band",
        "Posted", "Applications", "Views"
    ]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=400,
    )

    return df
