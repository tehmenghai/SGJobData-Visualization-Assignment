"""Placeholder page for Kendra Lai's dashboard."""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import seaborn as sns

st.set_page_config(page_title="Dashboard — Kendra Lai", page_icon="📋", layout="wide")

st.title("Kendra Lai's Dashboard")
#st.info("This dashboard is under development. Check back soon!")


  # Load your data using relative path
DATA_PATH = Path("KendraLai/data/").parent.parent / "KendraLai" / "data" / "jobs_cleaned.parquet"
df = pd.read_parquet(DATA_PATH)

#st.title("Kendra Lai's Dashboard")

# Define the levels of interest
levels = [
    'Executive', 'Senior Executive', 'Non-executive', 'Junior Executive',
    'Manager', 'Professional', 'Fresh/entry level',
    'Middle Management', 'Senior Management'
]

# Filter rows with relevant position levels
filtered_df = df[df['positionLevels'].isin(levels)].copy()

# Count posts per company per level
company_level_counts = (
    filtered_df.groupby(['postedCompany_name','positionLevels'])
    .size()
    .reset_index(name='post_count')
)

# Compute total posts per company
company_totals = (
    company_level_counts.groupby('postedCompany_name')['post_count']
    .sum()
    .reset_index(name='total_posts')
)

# Select top 10 companies by total posts
top10_companies = company_totals.sort_values('total_posts', ascending=False).head(10)

# Merge back to keep level breakdown only for top 10
plot_df = company_level_counts.merge(top10_companies, on='postedCompany_name')

# Plot with seaborn
fig, ax = plt.subplots(figsize=(14,7))
sns.barplot(
    data=plot_df,
    x='postedCompany_name',
    y='post_count',
    hue='positionLevels',
    palette='tab10',
    ax=ax
)

ax.set_title('Top 10 Companies by Posts (Breakdown by Position Level)')
ax.set_xlabel('Company Name')
ax.set_ylabel('Number of Posts')
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
ax.legend(title='Position Level', bbox_to_anchor=(1.05, 1), loc='upper left')

st.pyplot(fig)

#========================================

# Filter rows with relevant position levels
# filtered_df = df[df['positionLevels'].isin(levels)].copy()

# Ensure metadata_repostCount is numeric
filtered_df['metadata_repostCount'] = pd.to_numeric(
    filtered_df['metadata_repostCount'], errors='coerce'
)

# Sum repost counts per company per level
company_level_counts = (
    filtered_df.groupby(['postedCompany_name','positionLevels'])['metadata_repostCount']
    .sum()
    .reset_index(name='repost_count')
)

# Compute total repost counts per company
company_totals = (
    company_level_counts.groupby('postedCompany_name')['repost_count']
    .sum()
    .reset_index(name='total_reposts')
)

# Select top 10 companies by total repost counts
top10_companies = company_totals.sort_values('total_reposts', ascending=False).head(10)

# Merge back to keep level breakdown only for top 10
plot_df = company_level_counts.merge(top10_companies, on='postedCompany_name')

# Plot with seaborn
fig, ax = plt.subplots(figsize=(14,7))
sns.barplot(
    data=plot_df,
    x='postedCompany_name',
    y='repost_count',
    hue='positionLevels',
    palette='tab10',
    ax=ax
)

ax.set_title('Top 10 Companies by Repost Count (Breakdown by Position Level)')
ax.set_xlabel('Company Name')
ax.set_ylabel('Total Repost Count')
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
ax.legend(title='Position Level', bbox_to_anchor=(1.05, 1), loc='upper left')

# Render in Streamlit
st.pyplot(fig)

#==========================================
# Ensure job titles are strings
df['title'] = df['title'].astype(str)

# Group by company
company_stats = df.groupby('postedCompany_name').agg(
    total_posts=('metadata_jobPostId', 'count'),
    unique_titles=('title', 'nunique'),
    duplicated_posts=('metadata_jobPostId', lambda x: x.duplicated().sum())
)

# Calculate duplicated rate
company_stats['duplicated_rate'] = company_stats['duplicated_posts'] / company_stats['total_posts']

# Select top 10 companies by total posts
top10 = company_stats.sort_values('total_posts', ascending=False).head(10)

# --- First chart: counts ---
fig1, ax1 = plt.subplots(figsize=(14,7))
top10[['total_posts','unique_titles','duplicated_posts']].plot(
    kind='bar', edgecolor='black', ax=ax1
)
ax1.set_title('Top 10 Companies: Posts, Unique Titles, Duplicates')
ax1.set_xlabel('Company Name')
ax1.set_ylabel('Count')
ax1.set_xticklabels(ax1.get_xticklabels(), rotation=45, ha='right')
ax1.legend(title='Metrics')
st.pyplot(fig1)

# --- Second chart: duplicated rate ---
fig2, ax2 = plt.subplots(figsize=(14,7))
top10['duplicated_rate'].plot(kind='bar', color='orange', edgecolor='black', ax=ax2)
ax2.set_title('Duplicated Rate per Company (Top 10 by Total Posts)')
ax2.set_xlabel('Company Name')
ax2.set_ylabel('Duplicated Rate')
ax2.set_xticklabels(ax2.get_xticklabels(), rotation=45, ha='right')
st.pyplot(fig2)