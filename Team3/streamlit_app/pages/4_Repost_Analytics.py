"""Kendra Lai's Repost & Company Analytics dashboard."""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import seaborn as sns

st.set_page_config(page_title="Dashboard — Kendra Lai", page_icon="📋", layout="wide")

st.title("Kendra Lai's Dashboard")

# ── Cached data loading ─────────────────────────────────────────────────────
DATA_PATH = Path(__file__).parent.parent / "KendraLai" / "data" / "jobs_cleaned.parquet"

LEVELS = [
    'Executive', 'Senior Executive', 'Non-executive', 'Junior Executive',
    'Manager', 'Professional', 'Fresh/entry level',
    'Middle Management', 'Senior Management'
]


@st.cache_data(ttl=3600)
def load_data():
    return pd.read_parquet(DATA_PATH)


@st.cache_data(ttl=3600)
def get_top10_by_posts(_df):
    filtered = _df[_df['positionLevels'].isin(LEVELS)].copy()
    counts = filtered.groupby(['postedCompany_name', 'positionLevels']).size().reset_index(name='post_count')
    totals = counts.groupby('postedCompany_name')['post_count'].sum().reset_index(name='total_posts')
    top10 = totals.sort_values('total_posts', ascending=False).head(10)
    return counts.merge(top10, on='postedCompany_name')


@st.cache_data(ttl=3600)
def get_top10_by_reposts(_df):
    filtered = _df[_df['positionLevels'].isin(LEVELS)].copy()
    filtered['metadata_repostCount'] = pd.to_numeric(filtered['metadata_repostCount'], errors='coerce')
    counts = filtered.groupby(['postedCompany_name', 'positionLevels'])['metadata_repostCount'].sum().reset_index(name='repost_count')
    totals = counts.groupby('postedCompany_name')['repost_count'].sum().reset_index(name='total_reposts')
    top10 = totals.sort_values('total_reposts', ascending=False).head(10)
    return counts.merge(top10, on='postedCompany_name')


@st.cache_data(ttl=3600)
def get_company_stats(_df):
    df_copy = _df.copy()
    df_copy['title'] = df_copy['title'].astype(str)
    stats = df_copy.groupby('postedCompany_name').agg(
        total_posts=('metadata_jobPostId', 'count'),
        unique_titles=('title', 'nunique'),
        duplicated_posts=('metadata_jobPostId', lambda x: x.duplicated().sum())
    )
    stats['duplicated_rate'] = stats['duplicated_posts'] / stats['total_posts']
    return stats.sort_values('total_posts', ascending=False).head(10)


# ── Load data (cached) ──────────────────────────────────────────────────────
df = load_data()

# ── Chart 1: Top 10 by Posts ────────────────────────────────────────────────
plot_df = get_top10_by_posts(df)

fig, ax = plt.subplots(figsize=(14, 7))
sns.barplot(data=plot_df, x='postedCompany_name', y='post_count', hue='positionLevels', palette='tab10', ax=ax)
ax.set_title('Top 10 Companies by Posts (Breakdown by Position Level)')
ax.set_xlabel('Company Name')
ax.set_ylabel('Number of Posts')
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
ax.legend(title='Position Level', bbox_to_anchor=(1.05, 1), loc='upper left')
st.pyplot(fig)

# ── Chart 2: Top 10 by Repost Count ─────────────────────────────────────────
plot_df2 = get_top10_by_reposts(df)

fig, ax = plt.subplots(figsize=(14, 7))
sns.barplot(data=plot_df2, x='postedCompany_name', y='repost_count', hue='positionLevels', palette='tab10', ax=ax)
ax.set_title('Top 10 Companies by Repost Count (Breakdown by Position Level)')
ax.set_xlabel('Company Name')
ax.set_ylabel('Total Repost Count')
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
ax.legend(title='Position Level', bbox_to_anchor=(1.05, 1), loc='upper left')
st.pyplot(fig)

# ── Chart 3 & 4: Duplicate Analysis ─────────────────────────────────────────
top10 = get_company_stats(df)

fig1, ax1 = plt.subplots(figsize=(14, 7))
top10[['total_posts', 'unique_titles', 'duplicated_posts']].plot(kind='bar', edgecolor='black', ax=ax1)
ax1.set_title('Top 10 Companies: Posts, Unique Titles, Duplicates')
ax1.set_xlabel('Company Name')
ax1.set_ylabel('Count')
ax1.set_xticklabels(ax1.get_xticklabels(), rotation=45, ha='right')
ax1.legend(title='Metrics')
st.pyplot(fig1)

fig2, ax2 = plt.subplots(figsize=(14, 7))
top10['duplicated_rate'].plot(kind='bar', color='orange', edgecolor='black', ax=ax2)
ax2.set_title('Duplicated Rate per Company (Top 10 by Total Posts)')
ax2.set_xlabel('Company Name')
ax2.set_ylabel('Duplicated Rate')
ax2.set_xticklabels(ax2.get_xticklabels(), rotation=45, ha='right')
st.pyplot(fig2)
