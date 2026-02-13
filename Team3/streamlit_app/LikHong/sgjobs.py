import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Page configuration
st.set_page_config(
    page_title="SG Jobs - Your Personal Job Concierge",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .job-card {
        border-left: 4px solid #667eea;
        padding: 1rem;
        margin: 0.5rem 0;
        background: #1e1e1e;
        border-radius: 5px;
        color: #e0e0e0;
    }
    .job-card h4 {
        color: #ffffff;
    }
    .job-card p {
        color: #b0b0b0;
    }
    .job-card strong {
        color: #e0e0e0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0 24px;
        font-size: 16px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Database connection
@st.cache_resource
def get_db_connection():
    return duckdb.connect('../../data/raw/SGJobData.db', read_only=True)

con = get_db_connection()

# Cache data loading
@st.cache_data(ttl=3600)
def load_categories():
    query = """
    SELECT DISTINCT category_name 
    FROM jobs_categories 
    WHERE category_name IS NOT NULL 
    ORDER BY category_name
    """
    return con.execute(query).fetchdf()['category_name'].tolist()

@st.cache_data(ttl=3600)
def load_position_levels():
    query = """
    SELECT DISTINCT position_level 
    FROM jobs_enriched 
    WHERE position_level IS NOT NULL 
    ORDER BY position_level
    """
    return con.execute(query).fetchdf()['position_level'].tolist()

@st.cache_data(ttl=3600)
def load_salary_bands():
    query = """
    SELECT DISTINCT salary_band 
    FROM jobs_enriched 
    WHERE salary_band IS NOT NULL 
    ORDER BY CASE 
        WHEN salary_band LIKE '< %' THEN 1
        WHEN salary_band LIKE '%-%' THEN 2
        WHEN salary_band LIKE '> %' THEN 3
        ELSE 4
    END, salary_band
    """
    return con.execute(query).fetchdf()['salary_band'].tolist()

@st.cache_data(ttl=3600)
def get_job_recommendations(categories=None, salary_bands=None, position_levels=None, 
                            min_exp=0, max_exp=40, max_competition=1000, limit=500):
    """Get personalized job recommendations based on user profile"""
    
    filters = ["1=1"]
    
    if categories and len(categories) > 0:
        cat_list = "', '".join(categories)
        filters.append(f"jc.category_name IN ('{cat_list}')")
    
    if salary_bands and len(salary_bands) > 0:
        band_list = "', '".join(salary_bands)
        filters.append(f"je.salary_band IN ('{band_list}')")
    
    if position_levels and len(position_levels) > 0:
        level_list = "', '".join(position_levels)
        filters.append(f"je.position_level IN ('{level_list}')")
    
    filters.append(f"COALESCE(je.min_experience, 0) BETWEEN {min_exp} AND {max_exp}")
    filters.append(f"COALESCE(je.applications, 0) <= {max_competition}")
    
    where_clause = " AND ".join(filters)
    
    query = f"""
    SELECT DISTINCT
        je.job_id,
        je.title,
        je.company_name,
        je.position_level,
        je.salary_band,
        je.experience_band,
        je.avg_salary,
        je.min_experience,
        je.salary_minimum,
        je.salary_maximum,
        je.posting_date,
        je.expiry_date,
        je.applications,
        je.views,
        je.application_rate,
        je.days_active,
        jc.category_name,
        jc.category_id,
        (je.title || ' ' || COALESCE(je.company_name, '') || ' ' || 
         COALESCE(jc.category_name, '') || ' ' || COALESCE(je.position_level, '')) as search_text
    FROM jobs_enriched je
    LEFT JOIN jobs_categories jc ON je.job_id = jc.job_id
    WHERE {where_clause}
        AND je.avg_salary IS NOT NULL
        AND je.title IS NOT NULL
    ORDER BY je.posting_date DESC
    LIMIT {limit}
    """
    
    return con.execute(query).fetchdf()

def compute_match_scores(df, target_salary, target_experience, preferred_categories=None):
    """Compute multi-dimensional match scores for jobs"""
    
    if df.empty:
        return df
    
    df_scored = df.copy()
    
    # 1. Salary Match Score (0-1)
    df_scored['salary_diff'] = abs(df_scored['avg_salary'].fillna(target_salary) - target_salary)
    max_diff = df_scored['salary_diff'].max() if df_scored['salary_diff'].max() > 0 else 1
    df_scored['salary_score'] = 1 - (df_scored['salary_diff'] / max_diff)
    
    # 2. Experience Match Score (0-1)
    df_scored['exp_diff'] = abs(df_scored['min_experience'].fillna(0) - target_experience)
    max_exp_diff = df_scored['exp_diff'].max() if df_scored['exp_diff'].max() > 0 else 1
    df_scored['experience_score'] = 1 - (df_scored['exp_diff'] / max_exp_diff)
    
    # 3. Category Match Score (0-1)
    if preferred_categories and len(preferred_categories) > 0:
        df_scored['category_score'] = df_scored['category_name'].apply(
            lambda x: 1.0 if x in preferred_categories else 0.5
        )
    else:
        df_scored['category_score'] = 0.75
    
    # 4. Competition Score (0-1) - lower competition is better
    max_apps = df_scored['applications'].max() if df_scored['applications'].max() > 0 else 1
    df_scored['competition_score'] = 1 - (df_scored['applications'].fillna(0) / max_apps)
    
    # 5. Freshness Score (0-1) - newer postings are better
    df_scored['posting_date'] = pd.to_datetime(df_scored['posting_date'])
    latest_date = df_scored['posting_date'].max()
    df_scored['days_since_post'] = (latest_date - df_scored['posting_date']).dt.days
    max_days = df_scored['days_since_post'].max() if df_scored['days_since_post'].max() > 0 else 1
    df_scored['freshness_score'] = 1 - (df_scored['days_since_post'] / max_days)
    
    # Overall Match Score (weighted average)
    weights = {
        'salary': 0.30,
        'experience': 0.25,
        'category': 0.20,
        'competition': 0.15,
        'freshness': 0.10
    }
    
    df_scored['overall_score'] = (
        df_scored['salary_score'] * weights['salary'] +
        df_scored['experience_score'] * weights['experience'] +
        df_scored['category_score'] * weights['category'] +
        df_scored['competition_score'] * weights['competition'] +
        df_scored['freshness_score'] * weights['freshness']
    )
    
    return df_scored.sort_values('overall_score', ascending=False)

def create_radar_chart(df_scored, top_n=10):
    """Create interactive radar chart showing match scores"""
    
    if df_scored.empty:
        return None
    
    top_jobs = df_scored.head(top_n)
    
    fig = go.Figure()
    
    categories_radar = ['Salary Match', 'Experience Match', 'Industry Fit', 
                        'Low Competition', 'Fresh Posting']
    
    colors = px.colors.qualitative.Set3
    
    for idx, (_, job) in enumerate(top_jobs.iterrows()):
        values = [
            job['salary_score'],
            job['experience_score'],
            job['category_score'],
            job['competition_score'],
            job['freshness_score']
        ]
        
        # Close the radar chart
        values_closed = values + [values[0]]
        categories_closed = categories_radar + [categories_radar[0]]
        
        job_label = f"{job['title'][:40]}... - {job['company_name'][:25]}"
        
        fig.add_trace(go.Scatterpolar(
            r=values_closed,
            theta=categories_closed,
            fill='toself',
            name=job_label,
            hovertemplate=(
                f"<b>{job_label}</b><br>" +
                "Score: %{r:.2f}<br>" +
                "<extra></extra>"
            ),
            line=dict(color=colors[idx % len(colors)], width=2),
            fillcolor=colors[idx % len(colors)],
            opacity=0.6,
            customdata=[job['job_id']] * len(values_closed)
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                showticklabels=True,
                ticks='outside',
                tickfont=dict(size=10)
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color='#667eea')
            )
        ),
        showlegend=True,
        title={
            'text': f"🎯 Top {top_n} Job Matches - Multi-Dimensional Analysis",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': '#667eea'}
        },
        height=600,
        hovermode='closest',
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.1,
            font=dict(size=10)
        )
    )
    
    return fig

def create_scatter_analysis(df_scored):
    """Create interactive scatter plot for job analysis"""
    
    if df_scored.empty:
        return None
    
    # Add jitter for better visualization
    df_plot = df_scored.copy()
    df_plot['salary_plot'] = df_plot['avg_salary'] + np.random.normal(0, 50, len(df_plot))
    df_plot['exp_plot'] = df_plot['min_experience'] + np.random.normal(0, 0.1, len(df_plot))
    
    fig = px.scatter(
        df_plot,
        x='exp_plot',
        y='salary_plot',
        size='overall_score',
        color='category_name',
        hover_data={
            'title': True,
            'company_name': True,
            'overall_score': ':.2%',
            'applications': True,
            'exp_plot': False,
            'salary_plot': False
        },
        labels={
            'exp_plot': 'Years of Experience Required',
            'salary_plot': 'Average Salary (SGD)',
            'overall_score': 'Match Score'
        },
        title="📊 Job Opportunities Landscape - Experience vs Salary"
    )
    
    fig.update_traces(marker=dict(line=dict(width=1, color='white')))
    fig.update_layout(
        height=500,
        hovermode='closest',
        showlegend=True,
        xaxis_title="Years of Experience Required",
        yaxis_title="Average Salary (SGD)"
    )
    
    return fig

# Main App
def main():
    # Header
    st.markdown('<h1 class="main-header">🎯 SG Jobs - Your Personal Job Concierge</h1>', unsafe_allow_html=True)
    st.markdown("### Find your perfect job match with AI-powered recommendations")
    
    # Sidebar - User Profile
    with st.sidebar:
        st.header("👤 Your Job Profile")
        st.markdown("---")
        
        # Experience
        st.subheader("💼 Experience")
        target_experience = st.slider(
            "Years of Experience",
            min_value=0,
            max_value=40,
            value=3,
            help="Your total years of professional experience"
        )
        
        exp_range = st.slider(
            "Acceptable Experience Range",
            min_value=0,
            max_value=40,
            value=(max(0, target_experience-2), min(40, target_experience+3)),
            help="Range of job experience requirements you're open to"
        )
        
        st.markdown("---")
        
        # Salary
        st.subheader("💰 Salary Expectations")
        salary_bands_all = load_salary_bands()
        selected_salary_bands = st.multiselect(
            "Preferred Salary Bands",
            options=salary_bands_all,
            default=salary_bands_all[:3] if len(salary_bands_all) >= 3 else salary_bands_all,
            help="Select one or more salary ranges"
        )
        
        target_salary = st.number_input(
            "Target Salary (SGD)",
            min_value=1000,
            max_value=30000,
            value=5000,
            step=500,
            help="Your desired monthly salary"
        )
        
        st.markdown("---")
        
        # Industry Preferences
        st.subheader("🏢 Industry Preferences")
        categories_all = load_categories()
        selected_categories = st.multiselect(
            "Preferred Industries",
            options=categories_all,
            default=[],
            help="Select industries you're interested in (leave empty for all)"
        )
        
        st.markdown("---")
        
        # Position Level
        st.subheader("📊 Position Level")
        position_levels_all = load_position_levels()
        selected_positions = st.multiselect(
            "Preferred Position Levels",
            options=position_levels_all,
            default=[],
            help="Select position levels (leave empty for all)"
        )
        
        st.markdown("---")
        
        # Competition Filter
        st.subheader("🎯 Competition")
        max_competition = st.slider(
            "Maximum Applicants",
            min_value=0,
            max_value=1000,
            value=500,
            help="Filter out jobs with too many applicants"
        )
        
        st.markdown("---")
        
        # Number of recommendations
        num_recommendations = st.slider(
            "📋 Number of Jobs to Analyze",
            min_value=50,
            max_value=500,
            value=200,
            step=50
        )
        
        st.markdown("---")
        
        # Generate button
        generate_btn = st.button("🚀 Find My Perfect Matches!", type="primary", use_container_width=True)
    
    # Main Content
    if generate_btn or 'recommendations_df' in st.session_state:
        
        if generate_btn:
            with st.spinner("🔍 Analyzing job market and finding your perfect matches..."):
                # Load job data
                df = get_job_recommendations(
                    categories=selected_categories if selected_categories else None,
                    salary_bands=selected_salary_bands if selected_salary_bands else None,
                    position_levels=selected_positions if selected_positions else None,
                    min_exp=exp_range[0],
                    max_exp=exp_range[1],
                    max_competition=max_competition,
                    limit=num_recommendations
                )
                
                if df.empty:
                    st.error("😔 No jobs found matching your criteria. Try adjusting your filters.")
                    return
                
                # Compute match scores
                df_scored = compute_match_scores(
                    df,
                    target_salary=target_salary,
                    target_experience=target_experience,
                    preferred_categories=selected_categories if selected_categories else None
                )
                
                # Store in session state
                st.session_state['recommendations_df'] = df_scored
                st.session_state['profile'] = {
                    'experience': target_experience,
                    'salary': target_salary,
                    'categories': selected_categories,
                    'positions': selected_positions
                }
        
        df_scored = st.session_state.get('recommendations_df')
        
        if df_scored is None or df_scored.empty:
            st.error("No recommendations available. Please generate matches first.")
            return
        
        # Key Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "🎯 Jobs Analyzed",
                f"{len(df_scored):,}",
                help="Total number of jobs matching your criteria"
            )
        
        with col2:
            avg_match = df_scored['overall_score'].mean()
            st.metric(
                "📊 Avg Match Score",
                f"{avg_match:.1%}",
                help="Average match score across all jobs"
            )
        
        with col3:
            top_match = df_scored.iloc[0]['overall_score']
            st.metric(
                "⭐ Best Match",
                f"{top_match:.1%}",
                help="Your highest match score"
            )
        
        with col4:
            avg_salary = df_scored['avg_salary'].mean()
            st.metric(
                "💰 Avg Salary",
                f"${avg_salary:,.0f}",
                help="Average salary across matched jobs"
            )
        
        st.markdown("---")
        
        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs([
            "🎯 Radar Match Analysis",
            "📊 Job Landscape",
            "🏆 Top Recommendations",
            "📋 Full Job List"
        ])
        
        with tab1:
            st.markdown("### 🎯 Multi-Dimensional Job Match Analysis")
            st.info("👆 **Click on any line in the legend to highlight that job. Click on a job area to see details below.**")
            
            # Radar chart controls
            col_r1, col_r2 = st.columns([1, 3])
            
            with col_r1:
                top_n = st.slider(
                    "Number of jobs to display",
                    min_value=5,
                    max_value=20,
                    value=10,
                    key="radar_top_n"
                )
            
            with col_r2:
                sort_by = st.selectbox(
                    "Sort jobs by",
                    options=[
                        'Overall Match',
                        'Salary Match',
                        'Experience Match',
                        'Industry Fit',
                        'Low Competition',
                        'Fresh Posting'
                    ],
                    key="radar_sort"
                )
            
            # Sort based on selection
            sort_map = {
                'Overall Match': 'overall_score',
                'Salary Match': 'salary_score',
                'Experience Match': 'experience_score',
                'Industry Fit': 'category_score',
                'Low Competition': 'competition_score',
                'Fresh Posting': 'freshness_score'
            }
            
            df_display = df_scored.sort_values(sort_map[sort_by], ascending=False).head(top_n)
            
            # Create and display radar chart
            radar_fig = create_radar_chart(df_display, top_n=top_n)
            if radar_fig:
                st.plotly_chart(radar_fig, use_container_width=True)
            
            # Detailed job cards for top matches
            st.markdown("---")
            st.markdown(f"### 🏆 Top {min(5, len(df_display))} Best Matches - Detailed View")
            
            for idx, (_, job) in enumerate(df_display.head(5).iterrows(), 1):
                with st.expander(
                    f"**#{idx} - {job['title']}** at **{job['company_name']}** "
                    f"(Match: {job['overall_score']:.1%})",
                    expanded=(idx <= 2)
                ):
                    col_j1, col_j2, col_j3 = st.columns(3)
                    
                    with col_j1:
                        st.markdown("**💰 Compensation**")
                        st.write(f"Salary: ${job['avg_salary']:,.0f}/month")
                        st.write(f"Range: ${job['salary_minimum']:,.0f} - ${job['salary_maximum']:,.0f}")
                        st.write(f"Band: {job['salary_band']}")
                    
                    with col_j2:
                        st.markdown("**💼 Requirements**")
                        st.write(f"Experience: {job['experience_band']}")
                        st.write(f"Min Years: {job['min_experience']:.0f}")
                        st.write(f"Level: {job['position_level']}")
                    
                    with col_j3:
                        st.markdown("**📊 Competition**")
                        st.write(f"Industry: {job['category_name']}")
                        st.write(f"Applicants: {int(job['applications'])}")
                        st.write(f"Views: {int(job['views'])}")
                    
                    # Match scores breakdown
                    st.markdown("**🎯 Match Score Breakdown**")
                    score_cols = st.columns(5)
                    
                    scores = [
                        ('Salary', job['salary_score'], '💰'),
                        ('Experience', job['experience_score'], '💼'),
                        ('Industry', job['category_score'], '🏢'),
                        ('Competition', job['competition_score'], '🎯'),
                        ('Freshness', job['freshness_score'], '🆕')
                    ]
                    
                    for col_idx, (col, (name, score, emoji)) in enumerate(zip(score_cols, scores)):
                        with col:
                            st.metric(
                                f"{emoji} {name}",
                                f"{score:.0%}",
                                delta=None
                            )
                    
                    # Posting info
                    st.markdown("**📅 Posting Information**")
                    st.write(f"Posted: {job['posting_date'].strftime('%B %d, %Y')}")
                    st.write(f"Days Active: {int(job['days_active'])}")
                    if pd.notna(job['expiry_date']):
                        st.write(f"Expires: {job['expiry_date'].strftime('%B %d, %Y')}")
        
        with tab2:
            st.markdown("### 📊 Job Opportunities Landscape")
            st.info("🔍 **Explore the relationship between experience requirements and salary. Bubble size indicates match score.**")
            
            scatter_fig = create_scatter_analysis(df_scored)
            if scatter_fig:
                st.plotly_chart(scatter_fig, use_container_width=True)
            
            # Industry breakdown
            st.markdown("---")
            col_s1, col_s2 = st.columns(2)
            
            with col_s1:
                st.markdown("#### 🏢 Top Industries")
                industry_counts = df_scored['category_name'].value_counts().head(10)
                fig_industry = px.bar(
                    x=industry_counts.values,
                    y=industry_counts.index,
                    orientation='h',
                    labels={'x': 'Number of Jobs', 'y': 'Industry'},
                    title="Top 10 Industries in Your Matches"
                )
                fig_industry.update_traces(marker_color='#667eea')
                st.plotly_chart(fig_industry, use_container_width=True)
            
            with col_s2:
                st.markdown("#### 📊 Position Level Distribution")
                level_counts = df_scored['position_level'].value_counts()
                fig_level = px.pie(
                    values=level_counts.values,
                    names=level_counts.index,
                    title="Position Levels Distribution"
                )
                st.plotly_chart(fig_level, use_container_width=True)
        
        with tab3:
            st.markdown("### 🏆 Your Top Job Recommendations")
            
            # Filters for top recommendations
            col_f1, col_f2, col_f3 = st.columns(3)
            
            with col_f1:
                filter_industry = st.multiselect(
                    "Filter by Industry",
                    options=sorted(df_scored['category_name'].unique()),
                    default=[],
                    key="top_filter_industry"
                )
            
            with col_f2:
                filter_level = st.multiselect(
                    "Filter by Position Level",
                    options=sorted(df_scored['position_level'].unique()),
                    default=[],
                    key="top_filter_level"
                )
            
            with col_f3:
                min_match_score = st.slider(
                    "Minimum Match Score",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.5,
                    step=0.05,
                    format="%.0f%%",
                    key="min_match"
                )
            
            # Apply filters
            df_filtered = df_scored.copy()
            if filter_industry:
                df_filtered = df_filtered[df_filtered['category_name'].isin(filter_industry)]
            if filter_level:
                df_filtered = df_filtered[df_filtered['position_level'].isin(filter_level)]
            df_filtered = df_filtered[df_filtered['overall_score'] >= min_match_score]
            
            st.markdown(f"**Showing {len(df_filtered)} jobs** (sorted by match score)")
            
            # Add visualizations for filtered results
            if len(df_filtered) > 0:
                st.markdown("---")
                
                # Top 10 Match Scores Chart
                col_chart1, col_chart2 = st.columns(2)
                
                with col_chart1:
                    st.markdown("#### 📊 Top 10 Match Scores")
                    top_10_filtered = df_filtered.head(10)
                    
                    # Create horizontal bar chart for match scores
                    fig_matches = px.bar(
                        top_10_filtered,
                        y=top_10_filtered['title'].str[:40] + '...',
                        x='overall_score',
                        orientation='h',
                        labels={'overall_score': 'Match Score', 'y': 'Job Title'},
                        color='overall_score',
                        color_continuous_scale='RdYlGn',
                        range_color=[0, 1]
                    )
                    fig_matches.update_layout(
                        height=400,
                        showlegend=False,
                        yaxis={'categoryorder': 'total ascending'}
                    )
                    fig_matches.update_traces(
                        hovertemplate='<b>%{y}</b><br>Match: %{x:.1%}<extra></extra>'
                    )
                    st.plotly_chart(fig_matches, use_container_width=True)
                
                with col_chart2:
                    st.markdown("#### 💰 Salary Distribution")
                    
                    # Salary histogram
                    fig_salary = px.histogram(
                        df_filtered,
                        x='avg_salary',
                        nbins=20,
                        labels={'avg_salary': 'Average Salary (SGD)', 'count': 'Number of Jobs'},
                        color_discrete_sequence=['#667eea']
                    )
                    fig_salary.update_layout(
                        height=400,
                        showlegend=False,
                        bargap=0.1
                    )
                    fig_salary.update_traces(
                        hovertemplate='Salary: $%{x:,.0f}<br>Jobs: %{y}<extra></extra>'
                    )
                    st.plotly_chart(fig_salary, use_container_width=True)
                
                # Additional insights
                col_insight1, col_insight2, col_insight3 = st.columns(3)
                
                with col_insight1:
                    avg_match = df_filtered['overall_score'].mean()
                    st.metric(
                        "Average Match Score",
                        f"{avg_match:.1%}",
                        help="Average match score across filtered jobs"
                    )
                
                with col_insight2:
                    median_salary = df_filtered['avg_salary'].median()
                    st.metric(
                        "Median Salary",
                        f"${median_salary:,.0f}",
                        help="Median salary of filtered jobs"
                    )
                
                with col_insight3:
                    avg_competition = df_filtered['applications'].mean()
                    st.metric(
                        "Avg Competition",
                        f"{int(avg_competition)} apps",
                        help="Average number of applicants"
                    )
                
                st.markdown("---")
            
            # Display top recommendations
            for idx, (_, job) in enumerate(df_filtered.head(20).iterrows(), 1):
                col_c1, col_c2 = st.columns([3, 1])
                
                with col_c1:
                    st.markdown(f"""
                    <div class="job-card">
                        <h4>#{idx} {job['title']}</h4>
                        <p><strong>🏢 {job['company_name']}</strong> | 
                           🏭 {job['category_name']} | 
                           📊 {job['position_level']}</p>
                        <p>💰 ${job['avg_salary']:,.0f}/month | 
                           💼 {job['experience_band']} | 
                           👥 {int(job['applications'])} applicants</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_c2:
                    st.metric(
                        "Match Score",
                        f"{job['overall_score']:.0%}",
                        delta=None
                    )
                    st.caption(f"Posted: {job['posting_date'].strftime('%b %d, %Y')}")
        
        with tab4:
            st.markdown("### 📋 Complete Job List")
            
            # Download button
            csv = df_scored.to_csv(index=False)
            st.download_button(
                label="📥 Download Full Job List (CSV)",
                data=csv,
                file_name=f"job_recommendations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
            # Column selector
            all_columns = [
                'title', 'company_name', 'category_name', 'position_level',
                'avg_salary', 'salary_band', 'experience_band', 'min_experience',
                'applications', 'views', 'overall_score', 'posting_date'
            ]
            
            selected_columns = st.multiselect(
                "Select columns to display",
                options=all_columns,
                default=['title', 'company_name', 'avg_salary', 'overall_score', 
                        'category_name', 'applications'],
                key="column_selector"
            )
            
            if selected_columns:
                # Format display dataframe
                display_df = df_scored[selected_columns].copy()
                
                # Format specific columns
                if 'avg_salary' in selected_columns:
                    display_df['avg_salary'] = display_df['avg_salary'].apply(
                        lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A"
                    )
                
                if 'overall_score' in selected_columns:
                    display_df['overall_score'] = display_df['overall_score'].apply(
                        lambda x: f"{x:.1%}" if pd.notna(x) else "N/A"
                    )
                
                if 'posting_date' in selected_columns:
                    display_df['posting_date'] = pd.to_datetime(
                        display_df['posting_date']
                    ).dt.strftime('%Y-%m-%d')
                
                # Display dataframe
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    height=600
                )
                
                st.caption(f"Showing all {len(display_df)} matched jobs")
    
    else:
        # Welcome screen
        st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 3rem; border-radius: 15px; text-align: center; color: white;'>
            <h2>👋 Welcome to Your Personal Job Concierge!</h2>
            <p style='font-size: 1.3rem; margin-top: 1rem;'>
                Let's find your perfect job match using AI-powered recommendations
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        col_w1, col_w2, col_w3 = st.columns(3)
        
        with col_w1:
            st.markdown("""
            ### 1️⃣ Set Your Profile
            Tell us about your:
            - Years of experience
            - Salary expectations
            - Industry preferences
            - Position level
            """)
        
        with col_w2:
            st.markdown("""
            ### 2️⃣ Get AI Matches
            Our algorithm analyzes:
            - Salary alignment
            - Experience fit
            - Industry relevance
            - Competition level
            - Job freshness
            """)
        
        with col_w3:
            st.markdown("""
            ### 3️⃣ Explore Results
            Interactive views:
            - Radar match analysis
            - Job landscape
            - Top recommendations
            - Full job list
            """)
        
        st.markdown("---")
        
        st.info("👈 **Get started by filling in your job profile in the sidebar and clicking 'Find My Perfect Matches!'**")
        
        # Quick stats
        st.markdown("### 📊 Database Overview")
        
        col_q1, col_q2, col_q3, col_q4 = st.columns(4)
        
        with col_q1:
            total_jobs = con.execute("SELECT COUNT(DISTINCT job_id) FROM jobs_enriched").fetchone()[0]
            st.metric("Total Jobs", f"{total_jobs:,}")
        
        with col_q2:
            total_companies = con.execute("SELECT COUNT(DISTINCT company_name) FROM jobs_enriched").fetchone()[0]
            st.metric("Companies", f"{total_companies:,}")
        
        with col_q3:
            total_categories = con.execute("SELECT COUNT(DISTINCT category_name) FROM jobs_categories").fetchone()[0]
            st.metric("Industries", f"{total_categories}")
        
        with col_q4:
            avg_salary_db = con.execute("SELECT AVG(avg_salary) FROM jobs_enriched WHERE avg_salary IS NOT NULL").fetchone()[0]
            st.metric("Avg Salary", f"${avg_salary_db:,.0f}")

if __name__ == "__main__":
    main()
