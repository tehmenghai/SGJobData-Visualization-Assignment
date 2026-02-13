import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import numpy as np
from pathlib import Path

# --- 1. CONFIGURATION & CONNECTION  ---
# set_page_config MUST be the first Streamlit command
st.set_page_config(page_title="SG Gems Explorer", layout="wide")

# --- CSS FIX: KILL SIDE MARGINS ---
st.markdown("""
    <style>
        /* This forces the main content area to take up 95% of the screen */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            padding-left: 2rem;
            padding-right: 2rem;
            max-width: 95% !important;
        }
    </style>
""", unsafe_allow_html=True)

# Database path logic using pathlib
DB_PATH = Path(__file__).parent.parent.parent / "data" / "raw" / "SGJobData.db"

@st.cache_resource
def get_db_connection():
    if not DB_PATH.exists():
        st.error(f"### ❌ Database Not Found\nCould not find database at: `{DB_PATH}`")
        st.stop()
    return duckdb.connect(str(DB_PATH), read_only=True)

con = get_db_connection()

# --- 2. SIDEBAR: FILTERS & SETTINGS ---
st.sidebar.markdown("# 🥬 Fresh!")
with st.sidebar.expander("Timing is Everything", expanded=True):
    max_days = st.slider("Jobs posted within last (days):", 1, 60, 14)

st.sidebar.markdown("# 🔍 Hunt")
with st.sidebar.expander("💼 Career Match", expanded=True):
    industries = con.execute("SELECT DISTINCT category_name FROM jobs_categories ORDER BY 1").fetchdf()['category_name'].tolist()
    selected_ind = st.selectbox("Industry Category", options=["All Categories"] + industries)

    exp_query = """
    SELECT DISTINCT experience_band FROM jobs_enriched 
    WHERE experience_band IS NOT NULL
    ORDER BY CASE 
        WHEN experience_band LIKE 'Entry%' THEN 1
        WHEN experience_band LIKE 'Mid%' THEN 2
        WHEN experience_band LIKE 'Senior%' THEN 3
        WHEN experience_band LIKE 'Executive%' THEN 4
        ELSE 5 END
    """
    exp_bands = con.execute(exp_query).fetchdf()['experience_band'].tolist()
    selected_exp = st.selectbox("Experience Band", options=["All Levels"] + exp_bands)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Settings")
min_views = st.sidebar.number_input("Min View Threshold", value=20, step=10)
max_comp_limit = st.sidebar.slider(
    "Max Competition Ratio \n (Applications per 100 view)", 
    1, 100, 5
)
result_limit = st.sidebar.slider("Max Results on Chart", 20, 500, 150)

# --- 3. MAIN DASHBOARD AREA ---
st.title("💎 Gems Explorer")
st.markdown(f"### Hunting for gems in: {selected_ind} | {selected_exp}")

# --- 4. DATA PROCESSING & SQL QUERY ---
filters = [f"je.days_active <= {max_days}", f"je.views >= {min_views}", "je.avg_salary <= 50000"]

if selected_exp != "All Levels":
    filters.append(f"je.experience_band = '{selected_exp}'")
if selected_ind != "All Categories":
    filters.append(f"jc.category_name = '{selected_ind}'")

where_clause = " AND ".join(filters)

query = f"""
SELECT 
    je.title as job_title, je.company_name, je.avg_salary, je.salary_minimum, je.salary_maximum,
    je.applications, je.views, je.days_active, jc.category_name as primary_category,
    (CAST(je.applications AS FLOAT) * 100.0 / NULLIF(CAST(je.views AS FLOAT), 0)) as competition_ratio
FROM jobs_enriched je
JOIN jobs_categories jc ON je.job_id = jc.job_id
WHERE {where_clause}
AND competition_ratio <= {max_comp_limit}
ORDER BY je.avg_salary DESC
LIMIT {result_limit}
"""

df_gems = con.execute(query).fetchdf()

# --- 5. VISUALIZATION ---
if not df_gems.empty:
    high_exposure_mark = df_gems['views'].quantile(0.75)

    def classify_gem(row):
        if row['competition_ratio'] <= 5 and row['views'] >= high_exposure_mark:
            return "🏆 Niche Gem (High Exposure)"
        elif row['applications'] <= 5 and row['days_active'] <= 7:
            return "🥬 First Mover (Fresh & Low Apps)"
        else:
            return "Standard Job"

    df_gems['gem_type'] = df_gems.apply(classify_gem, axis=1)

    # JITTER TOOLKIT
    df_gems['inverted_comp'] = 1 / (df_gems['competition_ratio'] + 0.1) 
    df_gems['views_jitter'] = df_gems['views'] + np.random.uniform(-0.4, 0.4, len(df_gems))
    df_gems['salary_jitter'] = df_gems['avg_salary'] + np.random.uniform(-40, 40, len(df_gems))
    df_gems = df_gems.sort_values(by='inverted_comp', ascending=True)

    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    m1.metric("Gems Found", len(df_gems))
    m2.metric("Median Salary", f"${df_gems['avg_salary'].median():,.0f}")
    priority_count = len(df_gems[df_gems['gem_type'] != "Standard Job"])
    m3.metric("Priority Targets", priority_count, delta="High-Value Leads")

    fig = px.scatter(
        df_gems, x="views_jitter", y="salary_jitter", size="inverted_comp", color="gem_type",
        color_discrete_map={
            "🥬 First Mover (Fresh & Low Apps)": "#00CC96", 
            "🏆 Niche Gem (High Exposure)": "#FFD700",
            "Standard Job": "#636EFA"
        },
        opacity=0.6, hover_name="company_name", template="plotly_white", height=750, size_max=40,
        hover_data={"job_title": True, "views": True, "avg_salary": ":$,.0f", "applications": True, "competition_ratio": ":.2f", "days_active": True},
        labels={"views_jitter": "Market Exposure", "salary_jitter": "Estimated Salary (SGD)", "gem_type": "Strategy"}
    )

    fig.add_vline(x=high_exposure_mark, line_dash="dash", line_color="gray", annotation_text="Market High-Proof Zone")
    fig.update_traces(marker=dict(line=dict(width=1, color='white'))) 
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    
    # use_container_width=True ensures the chart expands to the CSS-defined width
    st.plotly_chart(fig, use_container_width=True)

    # --- 6. SPLIT DATA TABLES WITH CASUAL HEADERS ---
    CASUAL_HEADERS = {
        'job_title': 'The Gig',
        'company_name': 'Who Dis?',
        'avg_salary': 'The Moolah',
        'applications': 'The Rivals',
        'views': 'Eyekalls',
        'days_active': 'Days Since Birth',
        'competition_ratio': 'Sweat Factor',
        'primary_category': 'The Hood'
    }

    st.markdown("---")
    
    st.subheader("🚀 Grab 'Em Before They're Famous (Early Leads)")
    df_first = df_gems[df_gems['gem_type'] == "🥬 First Mover (Fresh & Low Apps)"].sort_values(by=['days_active', 'views'], ascending=[True, True])
    if not df_first.empty:
        st.dataframe(df_first[['job_title', 'company_name', 'avg_salary', 'applications', 'views', 'days_active']].rename(columns=CASUAL_HEADERS), use_container_width=True)

    st.subheader("💡 The Hidden Loot (Strategic Leads)")
    df_niche = df_gems[df_gems['gem_type'] == "🏆 Niche Gem (High Exposure)"].sort_values(by=['competition_ratio', 'views'], ascending=[True, True])
    if not df_niche.empty:
        st.dataframe(df_niche[['job_title', 'company_name', 'avg_salary', 'applications', 'views', 'competition_ratio']].rename(columns=CASUAL_HEADERS), use_container_width=True)

    st.subheader("✅ The Daily Grind (Standard Leads)")
    df_standard = df_gems[df_gems['gem_type'] == "Standard Job"].sort_values(by=['avg_salary', 'competition_ratio'], ascending=[False, True])
    if not df_standard.empty:
        st.dataframe(df_standard[['job_title', 'company_name', 'avg_salary', 'applications', 'views', 'primary_category']].rename(columns=CASUAL_HEADERS), use_container_width=True)
else:
    st.info("No gems found. Adjust your criteria in the sidebar to widen the hunt.")