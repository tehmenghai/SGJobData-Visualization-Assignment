# Streamlit App — Team3 Collaborative Guide

## Overview

Each team member builds their own visualization in their individual folder. A final `main.py` compiles all members' work into a single tabbed dashboard — no copy-pasting or merging required.

---

## Folder Structure

```
streamlit_app/
├── main.py                  # Final compiled app (auto-loads all members)
├── shared/
│   └── data.py              # Shared data loader (DuckDB connection + views)
├── BenAu/
│   └── app.py               # Ben's visualization
├── HueyLing/
│   └── app.py               # HueyLing's visualization
├── KendraLai/
│   └── app.py               # Kendra's visualization
├── Lanson/
│   └── app.py               # Lanson's visualization
├── LikHong/
│   └── app.py               # LikHong's visualization
└── MengHai/
    └── app.py               # MengHai's visualization
```

---

## How It Works

### 1. Shared Data Loader (`shared/data.py`)

Loads data once and provides a DuckDB connection with all views ready:
- `jobs_base` — normalized salary, application rate, dates
- `jobs_enriched` — salary bands, experience bands, time dimensions
- `jobs_categories` — flattened category rows

All members query the **same connection** so data is consistent.

### 2. Each Member's App (`{Name}/app.py`)

Every member creates an `app.py` in their folder that follows this contract:

```python
import streamlit as st

def render(con):
    """
    Main visualization function.

    Parameters:
        con: DuckDB connection with jobs_base, jobs_enriched,
             jobs_categories views already available.
    """
    # --- YOUR FILTERS (inside your tab) ---
    col1, col2 = st.columns(2)
    with col1:
        category = st.selectbox("Category", [...], key="yourname_category")
    with col2:
        exp_band = st.selectbox("Experience", [...], key="yourname_exp")

    # --- YOUR CHARTS ---
    df = con.execute("SELECT ... FROM jobs_enriched WHERE ...").fetchdf()
    st.bar_chart(df)


# Standalone mode — for individual development/testing
if __name__ == "__page__" or __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from shared.data import get_connection

    st.set_page_config(page_title="My Visualization", layout="wide")
    con = get_connection()
    render(con)
```

### 3. Final Compiled App (`main.py`)

Imports each member's `render()` function and presents them as tabs:

```python
tabs = st.tabs(["BenAu", "HueyLing", "KendraLai", "Lanson", "LikHong", "MengHai"])

with tabs[0]:
    BenAu.app.render(con)
with tabs[1]:
    HueyLing.app.render(con)
# ... etc
```

---

## Rules for Team Members

### Must Follow

1. **Put your code in `{YourName}/app.py`** — do not modify other members' folders.

2. **Export a `render(con)` function** — this is the only function `main.py` calls.

3. **Prefix all widget keys with your name** to avoid collisions across tabs:
   ```python
   # GOOD
   st.selectbox("Category", options, key="menghai_category")
   st.slider("Salary", 0, 20000, key="menghai_salary")

   # BAD — will crash when two members use the same key
   st.selectbox("Category", options, key="category")
   ```

4. **Put your filters inside your tab**, not in `st.sidebar`. Each member's filters live within their own tab content area so switching tabs shows the right filters:
   ```python
   def render(con):
       # Filters at the top of your section
       col1, col2, col3 = st.columns(3)
       with col1:
           category = st.selectbox("Category", [...], key="yourname_cat")

       # Charts below
       st.plotly_chart(fig)
   ```

### Recommended

- Use `st.columns()` for a horizontal filter bar at the top of your section.
- Use `st.expander("Filters")` if you have many filter controls to keep it tidy.
- Query from views (`jobs_enriched`, `jobs_categories`) rather than raw tables.
- Cap salary at $50K in visualizations to handle outliers (consistent with EDA findings).

---

## Available Views to Query

All views are provided via the `con` DuckDB connection.

### `jobs_enriched` (1 row per job posting)

| Column | Type | Description |
|--------|------|-------------|
| `job_id` | VARCHAR | Unique job posting ID |
| `title` | VARCHAR | Job title |
| `company_name` | VARCHAR | Company name |
| `salary_minimum` | BIGINT | Min salary (monthly) |
| `salary_maximum` | BIGINT | Max salary (monthly) |
| `avg_salary` | DOUBLE | (min + max) / 2 |
| `salary_range` | BIGINT | max - min |
| `salary_band` | VARCHAR | < 3K, 3K-5K, 5K-8K, 8K-12K, 12K-20K, 20K+ |
| `min_experience` | BIGINT | Minimum years of experience required |
| `experience_band` | VARCHAR | Entry (0-2), Mid (3-5), Senior (6-10), Executive (10+) |
| `vacancies` | BIGINT | Number of vacancies |
| `job_status` | VARCHAR | Open / Closed |
| `posting_date` | DATE | Original posting date |
| `expiry_date` | DATE | Expiry date |
| `posting_year` | INTEGER | Year extracted |
| `posting_month` | INTEGER | Month extracted |
| `posting_quarter` | INTEGER | Quarter extracted |
| `posting_day_of_week` | INTEGER | Day of week (0=Sun, 6=Sat) |
| `days_active` | INTEGER | Duration posting was live |
| `applications` | BIGINT | Total applications received |
| `views` | BIGINT | Total views received |
| `application_rate` | FLOAT | applications / views |
| `categories` | VARCHAR | Raw JSON categories array |

### `jobs_categories` (1 row per job-category pair, ~1.7M rows)

Includes all columns from `jobs_enriched` plus:

| Column | Type | Description |
|--------|------|-------------|
| `category_id` | INTEGER | Category ID |
| `category_name` | VARCHAR | Category name (e.g., "Information Technology") |

### Common Query Examples

```sql
-- Top categories by job count
SELECT category_name, COUNT(*) as jobs
FROM jobs_categories
GROUP BY category_name
ORDER BY jobs DESC
LIMIT 10

-- Average salary by experience band
SELECT experience_band, AVG(avg_salary) as mean_salary
FROM jobs_enriched
WHERE avg_salary > 0 AND avg_salary < 50000
GROUP BY experience_band

-- Monthly posting trend
SELECT DATE_TRUNC('month', posting_date) as month, COUNT(*) as jobs
FROM jobs_enriched
GROUP BY 1 ORDER BY 1

-- Filter by category and experience
SELECT title, company_name, avg_salary, experience_band
FROM jobs_categories
WHERE category_name = 'Information Technology'
  AND experience_band = 'Entry (0-2 years)'
  AND avg_salary < 50000
ORDER BY avg_salary DESC
```

---

## Development Workflow

### Individual Development

```bash
# From your folder (e.g., streamlit_app/MengHai/)
cd streamlit_app/MengHai
streamlit run app.py
```

Your app runs standalone — you can iterate on your charts and filters independently.

### Running the Compiled App

```bash
# From streamlit_app/
cd streamlit_app
streamlit run main.py
```

This loads all team members' tabs into a single dashboard.

### Git Workflow

1. Work only in your own folder (`streamlit_app/{YourName}/`).
2. Do not modify `shared/data.py` or other members' folders without discussion.
3. Commit and push your own `app.py` when ready.
4. The `main.py` auto-imports all members — no merge step needed.

---

## Checklist Before Final Submission

- [ ] Your `app.py` has a `render(con)` function
- [ ] All widget keys are prefixed with your name
- [ ] Filters are inside your tab (not in `st.sidebar`)
- [ ] Your app runs standalone (`streamlit run app.py`)
- [ ] Your app runs in the compiled view (`streamlit run main.py`)
- [ ] No hardcoded file paths — all data comes from the `con` parameter
