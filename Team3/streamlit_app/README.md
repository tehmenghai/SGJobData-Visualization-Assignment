# Streamlit App — Team3 Collaborative Guide

## Overview

Each team member builds their own dashboard as a **separate page** in a multi-page Streamlit app. The `main.py` serves as a landing page with an overview and links to each member's dashboard. Each dashboard appears in the sidebar for easy navigation.

---

## Folder Structure

```
streamlit_app/
├── main.py                                      # Landing page (run this)
├── pages/
│   ├── 1_Dashboard_(Lanson).py                  # Lanson's dashboard
│   ├── 2_Salary_Explorer_(Meng_Hai).py          # Meng Hai's dashboard
│   ├── 3_Job_Concierge_(Lik_Hong).py            # Lik Hong's dashboard
│   ├── 4_Job_Market_Insights_(Ben_Au).py        # Ben Au's dashboard
│   ├── 5_Top_Companies_(Huey_Ling).py           # Huey Ling's dashboard
│   └── 6_Dashboard_(Kendra_Lai).py              # Kendra Lai's dashboard
├── BenAu/                                       # Ben Au's working folder
├── HueyLing/                                    # Huey Ling's working folder
├── KendraLai/                                   # Kendra Lai's working folder
├── Lanson/                                      # Lanson's working folder
├── LikHong/                                     # Lik Hong's working folder
└── MengHai/                                     # Meng Hai's working folder
```

---

## How It Works

### 1. Multi-Page Architecture

Streamlit's **multi-page app** feature automatically picks up any `.py` file in the `pages/` folder and adds it to the sidebar. Each page runs independently with its own layout, filters, and charts.

### 2. Landing Page (`main.py`)

- Displays database stats (total jobs, companies, categories, date range)
- Shows dashboard cards for each team member with descriptions
- Links to each member's page

### 3. Each Member's Page (`pages/{N}_{Name}.py`)

Each member has a dedicated page file in `pages/`. You can either:

- **Write your code directly** in the page file, or
- **Build in your own folder** (e.g., `KendraLai/app.py`) and have the page file import it

### Database Connection

Connect to the database using a relative path from your page file:

```python
from pathlib import Path
import duckdb

DB_PATH = Path(__file__).parent.parent.parent / "data" / "raw" / "SGJobData.db"
con = duckdb.connect(str(DB_PATH), read_only=True)
```

---

## Rules for Team Members

### Must Follow

1. **Work in your own folder** (`{YourName}/`) and your own page file in `pages/` — do not modify other members' files.

2. **Use relative paths** for the database — do not hardcode absolute paths like `/home/user/...`:
   ```python
   # GOOD
   DB_PATH = Path(__file__).parent.parent.parent / "data" / "raw" / "SGJobData.db"

   # BAD — won't work on other machines
   DB_PATH = "/home/myuser/SGJobData-Visualization-Assignment/Team3/data/raw/SGJobData.db"
   ```

3. **Set page config** at the top of your page file:
   ```python
   st.set_page_config(page_title="Your Dashboard Title", page_icon="📊", layout="wide")
   ```

4. **Use `st.cache_resource`** for database connections and `st.cache_data` for queries to avoid re-running on every interaction.

### Recommended

- Use `st.sidebar` for filters — each page has its own sidebar context.
- Query from `jobs_enriched` and `jobs_categories` tables rather than raw tables.
- Cap salary at $50K in visualizations to handle outliers (consistent with EDA findings).
- Use Plotly (`plotly.express`) for interactive charts.

---

## Available Tables to Query

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
| `position_level` | VARCHAR | Fresh/entry level, Executive, Manager, etc. |
| `employment_type` | VARCHAR | Full Time, Part Time, Contract, etc. |
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

### `jobs_categories` (1 row per job-category pair)

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

### Running the Full App

```bash
cd Team3/streamlit_app
streamlit run main.py
```

The app opens at **http://localhost:8501**. All dashboards appear in the sidebar.

### Running Your Dashboard Standalone

You can run your own page file or folder app independently:

```bash
# Run your page file directly
streamlit run pages/1_Dashboard_\(Lanson\).py

# Or run from your folder
cd Team3/streamlit_app/Lanson
streamlit run app.py
```

### Git Workflow

1. **Fork** the main repo on GitHub, or ask to be added as a collaborator.
2. Work in your own folder (`streamlit_app/{YourName}/`) and your page file.
3. Commit and push to your fork.
4. Create a **Pull Request** to merge into the main repo.

---

## Adding Your Dashboard

1. Build your dashboard in your own folder (e.g., `Lanson/app.py`)
2. Update your page file in `pages/` (e.g., `1_Dashboard_(Lanson).py`) to either contain your dashboard code or import from your folder
3. Use relative paths for the database connection
4. Test by running `streamlit run main.py` from `Team3/streamlit_app/`

---

## Checklist Before Submission

- [ ] Your dashboard runs without errors
- [ ] Database path uses relative `Path(__file__)`, not hardcoded absolute paths
- [ ] Your page appears correctly in the sidebar when running `main.py`
- [ ] No modifications to other members' files
- [ ] Code is committed and pushed via Pull Request
