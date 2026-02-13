"""DuckDB connection management for the Salary Explorer."""

import duckdb
import pandas as pd
import streamlit as st

from config.settings import DB_PATH


@st.cache_resource
def get_connection():
    """
    Create and cache DuckDB connection to the pre-built SGJobData.db.

    The DB contains materialized tables: jobs_raw, jobs_base,
    jobs_enriched, jobs_categories — ready to query directly.
    """
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found at {DB_PATH}. "
            "Ensure SGJobData.db is placed in data/raw/."
        )

    conn = duckdb.connect(str(DB_PATH), read_only=True)
    return conn


def execute_query(query: str, params: dict = None) -> pd.DataFrame:
    """Execute a query and return results as DataFrame."""
    conn = get_connection()
    try:
        result = conn.execute(query).fetchdf()
        return result
    except Exception as e:
        st.error(f"Query error: {e}")
        return pd.DataFrame()


def get_company_categories(companies: list) -> pd.DataFrame:
    """Get categories for selected companies with job counts."""
    if not companies:
        return pd.DataFrame()
    conn = get_connection()
    safe_companies = ", ".join([f"'{c.replace(chr(39), chr(39)+chr(39))}'" for c in companies])
    result = conn.execute(f"""
        SELECT
            company_name as Company,
            category_name as Category,
            COUNT(*) as Jobs
        FROM jobs_categories
        WHERE company_name IN ({safe_companies})
          AND category_name IS NOT NULL
        GROUP BY company_name, category_name
        ORDER BY company_name, Jobs DESC
    """).fetchdf()
    return result


def search_companies(search_term: str, limit: int = 50) -> list:
    """Search for companies matching the search term."""
    conn = get_connection()
    safe_term = search_term.replace("'", "''")
    result = conn.execute(f"""
        SELECT DISTINCT company_name
        FROM jobs_enriched
        WHERE company_name ILIKE '%{safe_term}%'
        ORDER BY company_name
        LIMIT {limit}
    """).fetchdf()
    return result["company_name"].tolist() if not result.empty else []


def get_filter_options():
    """Get all filter options from the database."""
    conn = get_connection()

    # Get distinct categories
    categories = conn.execute("""
        SELECT DISTINCT category_name
        FROM jobs_categories
        WHERE category_name IS NOT NULL
        ORDER BY category_name
    """).fetchdf()["category_name"].tolist()

    # Get date range
    date_range = conn.execute("""
        SELECT
            MIN(posting_date) as min_date,
            MAX(posting_date) as max_date
        FROM jobs_enriched
        WHERE posting_date IS NOT NULL
    """).fetchdf().iloc[0]

    return {
        "categories": categories,
        "date_min": pd.to_datetime(date_range["min_date"]).date() if date_range["min_date"] else None,
        "date_max": pd.to_datetime(date_range["max_date"]).date() if date_range["max_date"] else None,
    }
