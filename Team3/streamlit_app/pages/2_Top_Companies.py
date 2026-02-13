"""
Top Companies mini-dashboard that shows top hiring companies with a slider to exclude companies having more than
N distinct job categories.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import duckdb

# Segment Profiles
SEGMENT_PROFILES = {
    "Everyone": {
        "icon": "👥",
        "description": "All job postings",
        "filter": "",
    },
    "Fresh Graduate": {
        "icon": "🎓",
        "description": "Entry-level roles for new graduates",
        "filter": "AND je.position_level IN ('Fresh/entry level', 'Junior Executive', 'Non-executive') AND je.experience_band = 'Entry (0-2 years)'",
    },
    "Mid-Career Switcher": {
        "icon": "🔄",
        "description": "Roles for professionals exploring new industries",
        "filter": "AND je.position_level IN ('Executive', 'Professional') AND je.experience_band IN ('Mid (3-5 years)', 'Senior (6-10 years)')",
    },
    "Experienced Professional": {
        "icon": "⭐",
        "description": "Senior and leadership positions",
        "filter": "AND je.position_level IN ('Manager', 'Senior Executive', 'Middle Management', 'Senior Management') AND je.experience_band IN ('Senior (6-10 years)', 'Executive (10+ years)')",
    },
}

st.set_page_config(page_title="Top Companies - SG Jobs", page_icon="🏢", layout="wide")

@st.cache_resource
def get_database_connection():
    db_path = Path(__file__).parent.parent.parent / "data" / "raw" / "SGJobData.db"
    if not db_path.exists():
        st.error(f"Database not found at {db_path}")
        st.stop()
    return duckdb.connect(str(db_path), read_only=True)

@st.cache_data
def fetch_query(query: str):
    con = get_database_connection()
    return con.execute(query).fetchdf()

def main():
    st.title("🏢 Top Hiring Companies")

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

    # compute maximum distinct categories per company
    try:
        max_cat_df = fetch_query("""
            SELECT MAX(category_count) as max_cat FROM (
                SELECT COUNT(DISTINCT category_name) as category_count
                FROM jobs_categories
                GROUP BY company_name
            )
        """)
        max_possible = int(max_cat_df.iloc[0, 0]) if (not max_cat_df.empty and max_cat_df.iloc[0, 0] is not None) else 1
    except Exception:
        max_possible = 50

    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Companies by Job Postings")
    with col2:
        max_categories = st.slider(
            "Max Job Categories for Company",
            min_value=1,
            max_value=max_possible,
            value=min(10, max_possible),
            step=1,
            help="Exclude companies with more than this many distinct job categories"
        )

    top_companies = fetch_query(f"""
        WITH company_categories AS (
            SELECT 
                company_name,
                COUNT(DISTINCT category_name) as category_count
            FROM jobs_categories
            GROUP BY company_name
        )
        SELECT 
            je.company_name,
            COUNT(*) as job_count,
            COUNT(DISTINCT je.title) as unique_roles,
            ROUND(AVG(je.applications), 0) as avg_applications,
            cc.category_count
        FROM jobs_enriched je
        INNER JOIN company_categories cc ON je.company_name = cc.company_name
        WHERE je.company_name IS NOT NULL AND je.company_name != '' {profile['filter']}
        AND cc.category_count <= {max_categories}
        GROUP BY je.company_name, cc.category_count
        ORDER BY job_count DESC
        LIMIT 20
    """)

    # Bar chart + details
    left, right = st.columns(2)
    with left:
        fig = px.bar(top_companies, x='company_name', y='job_count',
                     title=f'Top 20 Hiring Companies (Max {max_categories} Categories)',
                     labels={'company_name': 'Company', 'job_count': 'Job Count'},
                     text='job_count')
        fig.update_traces(textposition='outside')
        fig.update_xaxes(tickangle=-45)
        st.plotly_chart(fig, width="stretch")

    with right:
        st.subheader("Top Company Details")
        if not top_companies.empty:
            st.dataframe(
                top_companies[['company_name', 'job_count', 'unique_roles', 'category_count']],
                hide_index=True,
                column_config={
                    "company_name": "Company",
                    "job_count": "Jobs",
                    "unique_roles": "Roles",
                    "category_count": "Categories",
                },
                width="stretch",
            )
        else:
            st.info("No companies found for the selected threshold")

    # Hiring pattern heatmap for the top companies (respecting threshold)
    st.subheader("Company Hiring Patterns by Month")
    hiring_pattern = fetch_query(f"""
        WITH company_categories AS (
            SELECT 
                company_name,
                COUNT(DISTINCT category_name) as category_count
            FROM jobs_categories
            GROUP BY company_name
        )
        SELECT 
            je.company_name,
            je.posting_year,
            je.posting_month,
            COUNT(*) as job_count
        FROM jobs_enriched je
        WHERE je.company_name IN (
            SELECT je2.company_name 
            FROM jobs_enriched je2
            INNER JOIN company_categories cc2 ON je2.company_name = cc2.company_name
            WHERE je2.company_name IS NOT NULL AND je2.company_name != '' {profile['filter']}
            AND cc2.category_count <= {max_categories}
            GROUP BY je2.company_name
            ORDER BY COUNT(*) DESC LIMIT 10
        )
        GROUP BY je.company_name, je.posting_year, je.posting_month
        ORDER BY je.company_name, je.posting_year, je.posting_month
    """)

    if not hiring_pattern.empty:
        hiring_pattern['month'] = hiring_pattern['posting_year'].astype(str) + '-' + hiring_pattern['posting_month'].astype(str).str.zfill(2)
        pivot_data = hiring_pattern.pivot_table(index='company_name', columns='month', values='job_count', fill_value=0)
        fig2 = px.imshow(pivot_data, title=f'Top 10 Companies - Hiring Activity Heatmap (Max {max_categories} Categories)', labels={'x': 'Month', 'y': 'Company'}, color_continuous_scale='YlOrRd')
        st.plotly_chart(fig2, width="stretch")
    else:
        st.info("No hiring pattern data available for the selected threshold")

    st.subheader("Top Categories & Companies by Median Salary")
    category_company_bubbles = fetch_query(f"""
        WITH company_categories AS (
            SELECT
                company_name,
                COUNT(DISTINCT category_name) as category_count
            FROM jobs_categories
            GROUP BY company_name
        ),
        filtered_jobs AS (
            SELECT
                je.company_name,
                jc.category_name,
                je.avg_salary
            FROM jobs_enriched je
            INNER JOIN jobs_categories jc ON je.job_id = jc.job_id
            INNER JOIN company_categories cc ON je.company_name = cc.company_name
            WHERE je.company_name IS NOT NULL AND je.company_name != '' {profile['filter']}
            AND je.avg_salary IS NOT NULL
            AND je.avg_salary < 50000
            AND cc.category_count <= {max_categories}
        ),
        category_median AS (
            SELECT
                category_name,
                quantile_cont(avg_salary, 0.5) AS median_salary
            FROM filtered_jobs
            GROUP BY category_name
        ),
        top_categories AS (
            SELECT
                category_name,
                median_salary
            FROM category_median
            ORDER BY median_salary DESC
            LIMIT 5
        ),
        company_category AS (
            SELECT
                fj.category_name,
                fj.company_name,
                quantile_cont(fj.avg_salary, 0.5) AS median_salary,
                COUNT(*) AS job_count
            FROM filtered_jobs fj
            INNER JOIN top_categories tc ON fj.category_name = tc.category_name
            GROUP BY fj.category_name, fj.company_name
        )
        SELECT
            category_name,
            company_name,
            median_salary,
            job_count
        FROM (
            SELECT
                *,
                ROW_NUMBER() OVER (PARTITION BY category_name ORDER BY median_salary DESC) AS company_rank
            FROM company_category
        ) ranked
        WHERE company_rank <= 5
        ORDER BY category_name, median_salary DESC
    """)

    if not category_company_bubbles.empty:
        fig3 = px.scatter(
            category_company_bubbles,
            x="company_name",
            y="median_salary",
            color="category_name",
            size="job_count",
            size_max=45,
            title=f"Top 5 Categories x Top 5 Companies (Max {max_categories} Categories)",
            labels={
                "company_name": "Company",
                "median_salary": "Median Salary",
                "category_name": "Job Category",
                "job_count": "Job Count",
            },
            hover_data={
                "company_name": True,
                "category_name": True,
                "median_salary": ":,.0f",
                "job_count": True,
            },
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        fig3.update_traces(opacity=0.8)
        fig3.update_layout(
            xaxis_tickangle=-35,
            legend_title_text="Job Category",
            yaxis_tickprefix="$",
        )
        fig3.update_yaxes(dtick=5000, tickformat=",.0f")
        st.plotly_chart(fig3, width="stretch")

        st.caption("Quick Sort Table")
        table_df = category_company_bubbles.copy()
        table_df = table_df.sort_values(["category_name", "median_salary"], ascending=[True, False])
        table_df["median_salary"] = pd.to_numeric(table_df["median_salary"], errors="coerce").round(0)
        table_df["median_salary_display"] = table_df["median_salary"].apply(
            lambda v: f"${v:,.0f}" if pd.notna(v) else ""
        )
        st.dataframe(
            table_df,
            hide_index=True,
            column_order=["category_name", "company_name", "median_salary_display"],
            column_config={
                "category_name": "Job Category",
                "company_name": "Company",
                "median_salary_display": st.column_config.TextColumn("Median Salary"),
            },
            width="stretch",
        )
    else:
        st.info("No salary/category data available for the selected profile and threshold")

if __name__ == '__main__':
    main()
