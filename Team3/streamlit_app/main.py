"""
SG Job Market Explorer — Team 3 Capstone Dashboard
Landing page for the multi-page Streamlit app.
"""

import streamlit as st
import duckdb
from pathlib import Path

st.set_page_config(
    page_title="SG Job Market Explorer — Team 3",
    page_icon="🇸🇬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paths ────────────────────────────────────────────────────────────────────
DB_PATH = Path(__file__).parent.parent / "data" / "raw" / "SGJobData.db"


# ── Quick DB stats (cached) ─────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def _load_db_stats():
    if not DB_PATH.exists():
        return None
    con = duckdb.connect(str(DB_PATH), read_only=True)
    stats = {}
    stats["total_jobs"] = con.execute(
        "SELECT COUNT(DISTINCT job_id) FROM jobs_enriched"
    ).fetchone()[0]
    stats["total_companies"] = con.execute(
        "SELECT COUNT(DISTINCT company_name) FROM jobs_enriched"
    ).fetchone()[0]
    stats["total_categories"] = con.execute(
        "SELECT COUNT(DISTINCT category_name) FROM jobs_categories"
    ).fetchone()[0]
    row = con.execute(
        "SELECT MIN(posting_date), MAX(posting_date) FROM jobs_enriched WHERE posting_date IS NOT NULL"
    ).fetchone()
    stats["date_min"] = str(row[0])[:10] if row[0] else "N/A"
    stats["date_max"] = str(row[1])[:10] if row[1] else "N/A"
    con.close()
    return stats


# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
    .hero-title {
        font-size: 2.6rem;
        font-weight: 800;
        line-height: 1.15;
        margin-bottom: 0.25rem;
    }
    .hero-sub {
        font-size: 1.15rem;
        color: #9CA3AF;
        margin-bottom: 2rem;
    }
    .card {
        border: 1px solid #2D3748;
        border-radius: 12px;
        padding: 1.5rem;
        height: 100%;
        transition: border-color 0.2s;
    }
    .card:hover {
        border-color: #3B82F6;
    }
    .card-title {
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
    }
    .card-author {
        font-size: 0.85rem;
        color: #60A5FA;
        margin-bottom: 0.6rem;
    }
    .card-desc {
        font-size: 0.9rem;
        color: #9CA3AF;
        line-height: 1.5;
    }
    .badge {
        display: inline-block;
        padding: 0.15rem 0.55rem;
        border-radius: 999px;
        font-size: 0.7rem;
        font-weight: 600;
        margin-right: 0.3rem;
        margin-top: 0.5rem;
    }
    .badge-blue  { background: #1E3A5F; color: #93C5FD; }
    .badge-green { background: #14532D; color: #86EFAC; }
    .badge-amber { background: #78350F; color: #FCD34D; }
    .badge-purple { background: #3B0764; color: #C4B5FD; }
    .team-section {
        margin-top: 3rem;
        padding-top: 1.5rem;
        border-top: 1px solid #2D3748;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ── Hero Section ─────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">SG Job Market Explorer</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-sub">'
    "A multi-perspective dashboard built by Team 3 — explore Singapore's job market "
    "through salary analytics, AI-powered job matching, and more."
    "</div>",
    unsafe_allow_html=True,
)

# ── Database Stats ───────────────────────────────────────────────────────────
stats = _load_db_stats()
if stats:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Job Postings", f"{stats['total_jobs']:,}")
    c2.metric("Companies", f"{stats['total_companies']:,}")
    c3.metric("Job Categories", f"{stats['total_categories']}")
    c4.metric("Date Range", f"{stats['date_min']}  to  {stats['date_max']}")

st.divider()

# ── Dashboard Cards ──────────────────────────────────────────────────────────
st.markdown("### Dashboards")
st.caption("Select a dashboard from the sidebar, or click the links below to explore.")

# Row 1 — available dashboards
col1, col2 = st.columns(2)

with col1:
    st.markdown(
        """
    <div class="card">
        <div class="card-title">Salary Explorer</div>
        <div class="card-author">by Meng Hai</div>
        <div class="card-desc">
            Market-level salary analytics with interactive filters.
            Compare salaries across categories, companies, and job titles.
            Includes job seeker profile segments (Fresh Graduate, Mid-Career, Experienced)
            that tailor KPIs and insights to your career stage.
        </div>
        <span class="badge badge-blue">Salary Analysis</span>
        <span class="badge badge-green">Profile Segments</span>
        <span class="badge badge-amber">KPI Dashboard</span>
    </div>
    """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/2_Salary_Explorer_(Meng_Hai).py", label="Open Salary Explorer", icon="📊")

with col2:
    st.markdown(
        """
    <div class="card">
        <div class="card-title">Job Concierge</div>
        <div class="card-author">by Lik Hong</div>
        <div class="card-desc">
            AI-powered personal job recommendation engine.
            Set your profile (experience, salary, industry) and get
            multi-dimensional match scores across 5 factors.
            Features radar charts, scatter analysis, and ranked job cards.
        </div>
        <span class="badge badge-purple">AI Matching</span>
        <span class="badge badge-blue">Radar Charts</span>
        <span class="badge badge-green">Job Scoring</span>
    </div>
    """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/3_Job_Concierge_(Lik_Hong).py", label="Open Job Concierge", icon="🎯")

# Row 2 — coming soon
col3, col4 = st.columns(2)

with col3:
    st.markdown(
        """
    <div class="card">
        <div class="card-title">Job Market Insights</div>
        <div class="card-author">by Ben Au</div>
        <div class="card-desc">
            Salary distribution analytics with violin plots, box & whisker charts,
            and position-level vs salary heatmaps. Features interactive filters
            for position level, category, employment type, and job status.
        </div>
        <span class="badge badge-blue">Salary Distributions</span>
        <span class="badge badge-green">Heatmaps</span>
        <span class="badge badge-purple">Violin Plots</span>
    </div>
    """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/4_Job_Market_Insights_(Ben_Au).py", label="Open Job Market Insights", icon="📈")

with col4:
    st.markdown(
        """
    <div class="card">
        <div class="card-title">Top Hiring Companies</div>
        <div class="card-author">by Huey Ling</div>
        <div class="card-desc">
            Explore the most active employers, hiring patterns by month,
            and a salary-focused bubble chart across top categories.
        </div>
        <span class="badge badge-blue">Top Companies</span>
        <span class="badge badge-green">Hiring Trends</span>
        <span class="badge badge-amber">Salary Focus</span>
    </div>
    """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/5_Top_Companies_(Huey_Ling).py", label="Open Top Companies", icon="🏢")

col5, col6 = st.columns(2)

with col5:
    st.markdown(
        """
    <div class="card">
        <div class="card-title">Dashboard 5</div>
        <div class="card-author">by Kendra Lai</div>
        <div class="card-desc">
            Coming soon — Kendra's visualization will appear here once ready.
            Check the sidebar for updates.
        </div>
        <span class="badge badge-amber">Coming Soon</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

with col6:
    st.markdown(
        """
    <div class="card">
        <div class="card-title">Dashboard 6</div>
        <div class="card-author">by Lanson</div>
        <div class="card-desc">
            Coming soon — Lanson's visualization will appear here once ready.
            Check the sidebar for updates.
        </div>
        <span class="badge badge-amber">Coming Soon</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

# ── Team Section ─────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="team-section">
    <h4>Team 3 Members</h4>
</div>
""",
    unsafe_allow_html=True,
)

team = [
    ("Ben Au", "Job Market Insights"),
    ("Huey Ling", "Top Hiring Companies"),
    ("Kendra Lai", "Dashboard 5"),
    ("Lanson", "Dashboard 6"),
    ("Lik Hong", "Job Concierge"),
    ("Meng Hai", "Salary Explorer"),
]

cols = st.columns(len(team))
for col, (name, dash) in zip(cols, team):
    with col:
        st.markdown(f"**{name}**")
        st.caption(dash)

# ── Footer ───────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<div style='text-align: center; color: #6B7280; font-size: 0.8rem;'>"
    "SCTP Data Science & AI Capstone Project | "
    "Data source: Singapore Government Job Portal | "
    "Built with Streamlit & DuckDB"
    "</div>",
    unsafe_allow_html=True,
)
