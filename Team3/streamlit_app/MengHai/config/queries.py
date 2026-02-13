"""SQL query definitions for the Salary Explorer.

Data source: SGJobData.db (DuckDB) with pre-built tables:
  - jobs_raw: raw cleaned data
  - jobs_base: normalized salary, dates, application rate
  - jobs_enriched: + salary bands, experience bands, time dimensions, position_level, employment_type
  - jobs_categories: flattened category rows (1 row per job-category pair)
"""

# Filter option queries
QUERY_DISTINCT_CATEGORIES = """
SELECT DISTINCT category_name
FROM jobs_categories
WHERE category_name IS NOT NULL
ORDER BY category_name
"""

QUERY_TOP_COMPANIES = """
SELECT company_name, COUNT(*) as job_count
FROM jobs_enriched
WHERE company_name IS NOT NULL
GROUP BY company_name
ORDER BY job_count DESC
LIMIT 100
"""

QUERY_SALARY_RANGE = """
SELECT
  MIN(avg_salary) as min_salary,
  MAX(avg_salary) as max_salary
FROM jobs_enriched
WHERE avg_salary > 0 AND avg_salary < 100000
"""

QUERY_DATE_RANGE = """
SELECT
  MIN(posting_date) as min_date,
  MAX(posting_date) as max_date
FROM jobs_enriched
WHERE posting_date IS NOT NULL
"""

# KPI queries
QUERY_SALARY_SUMMARY = """
SELECT
  COUNT(*) as total_jobs,
  AVG(avg_salary) as avg_salary,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY avg_salary) as median_salary,
  PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY avg_salary) as p25_salary,
  PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY avg_salary) as p75_salary,
  MIN(avg_salary) as min_salary,
  MAX(avg_salary) as max_salary
FROM jobs_enriched
WHERE 1=1 {filters}
"""

# Chart queries
QUERY_SALARY_DISTRIBUTION = """
SELECT avg_salary
FROM jobs_enriched
WHERE avg_salary > 0 AND avg_salary < 50000 {filters}
"""

QUERY_SALARY_BY_CATEGORY = """
SELECT
  category_name,
  AVG(avg_salary) as avg_salary,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY avg_salary) as median_salary,
  COUNT(*) as job_count
FROM jobs_categories
WHERE category_name IS NOT NULL {filters}
GROUP BY category_name
ORDER BY avg_salary DESC
LIMIT 20
"""

QUERY_SALARY_BY_EXPERIENCE = """
SELECT
  experience_band,
  AVG(avg_salary) as avg_salary,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY avg_salary) as median_salary,
  COUNT(*) as job_count
FROM jobs_enriched
WHERE experience_band IS NOT NULL {filters}
GROUP BY experience_band
ORDER BY
  CASE experience_band
    WHEN 'Entry (0-2 years)' THEN 1
    WHEN 'Mid (3-5 years)' THEN 2
    WHEN 'Senior (6-10 years)' THEN 3
    WHEN 'Executive (10+ years)' THEN 4
  END
"""

QUERY_SALARY_TRENDS = """
SELECT
  DATE_TRUNC('month', posting_date) as month,
  AVG(avg_salary) as avg_salary,
  PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY avg_salary) as p25_salary,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY avg_salary) as median_salary,
  PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY avg_salary) as p75_salary,
  COUNT(*) as job_count
FROM jobs_enriched
WHERE posting_date IS NOT NULL {filters}
GROUP BY DATE_TRUNC('month', posting_date)
ORDER BY month
"""

QUERY_JOB_LISTINGS = """
SELECT
  title,
  company_name,
  avg_salary,
  experience_band,
  salary_band,
  posting_date,
  applications,
  views
FROM jobs_enriched
WHERE 1=1 {filters}
ORDER BY posting_date DESC
LIMIT 100
"""

# =============================================================================
# SEGMENT-SPECIFIC QUERIES
# =============================================================================

# Shared: KPIs for any segment
QUERY_SEGMENT_SALARY_SUMMARY = """
SELECT
  COUNT(*) as total_jobs,
  AVG(avg_salary) as avg_salary,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY avg_salary) as median_salary,
  PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY avg_salary) as p25_salary,
  PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY avg_salary) as p75_salary
FROM jobs_enriched
WHERE 1=1 {filters} {segment_filter}
"""

# Shared: Employment type breakdown
QUERY_SEGMENT_EMPLOYMENT_TYPE = """
SELECT
  employment_type,
  COUNT(*) as job_count,
  AVG(avg_salary) as avg_salary
FROM jobs_enriched
WHERE employment_type IS NOT NULL {filters} {segment_filter}
GROUP BY employment_type
ORDER BY job_count DESC
"""

# --- Fresh Graduate ---

QUERY_GRAD_TOP_HIRING_COMPANIES = """
SELECT
  company_name,
  COUNT(*) as job_count,
  AVG(avg_salary) as avg_salary
FROM jobs_enriched
WHERE company_name IS NOT NULL {filters} {segment_filter}
GROUP BY company_name
ORDER BY job_count DESC
LIMIT 10
"""

QUERY_GRAD_TOP_CATEGORIES = """
SELECT
  jc.category_name,
  COUNT(*) as job_count,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY je.avg_salary) as median_salary
FROM jobs_enriched je
JOIN jobs_categories jc ON je.job_id = jc.job_id
WHERE jc.category_name IS NOT NULL {filters} {segment_filter}
GROUP BY jc.category_name
ORDER BY job_count DESC
LIMIT 10
"""

QUERY_GRAD_SALARY_BY_EMPLOYMENT_TYPE = """
SELECT
  employment_type,
  AVG(avg_salary) as avg_salary,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY avg_salary) as median_salary,
  COUNT(*) as job_count
FROM jobs_enriched
WHERE employment_type IS NOT NULL AND avg_salary > 0 {filters} {segment_filter}
GROUP BY employment_type
ORDER BY avg_salary DESC
"""

# --- Mid-Career Switcher ---

QUERY_MID_CATEGORY_SALARY_COMPARE = """
SELECT
  jc.category_name,
  AVG(je.avg_salary) as avg_salary,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY je.avg_salary) as median_salary,
  COUNT(*) as job_count
FROM jobs_enriched je
JOIN jobs_categories jc ON je.job_id = jc.job_id
WHERE jc.category_name IS NOT NULL AND je.avg_salary > 0 {filters} {segment_filter}
GROUP BY jc.category_name
HAVING COUNT(*) >= 5
ORDER BY avg_salary DESC
LIMIT 15
"""

QUERY_MID_EXPERIENCE_PREMIUM = """
SELECT
  jc.category_name,
  je.experience_band,
  AVG(je.avg_salary) as avg_salary,
  COUNT(*) as job_count
FROM jobs_enriched je
JOIN jobs_categories jc ON je.job_id = jc.job_id
WHERE jc.category_name IS NOT NULL
  AND je.experience_band IN ('Mid (3-5 years)', 'Senior (6-10 years)')
  AND je.avg_salary > 0
  {filters}
GROUP BY jc.category_name, je.experience_band
HAVING COUNT(*) >= 3
ORDER BY jc.category_name, je.experience_band
"""

QUERY_MID_TOP_HIRING_COMPANIES = """
SELECT
  company_name,
  COUNT(*) as job_count,
  AVG(avg_salary) as avg_salary
FROM jobs_enriched
WHERE company_name IS NOT NULL {filters} {segment_filter}
GROUP BY company_name
ORDER BY job_count DESC
LIMIT 10
"""

# --- Experienced Professional ---

QUERY_EXP_POSITION_LEVEL_SALARY = """
SELECT
  position_level,
  AVG(avg_salary) as avg_salary,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY avg_salary) as median_salary,
  COUNT(*) as job_count
FROM jobs_enriched
WHERE position_level IS NOT NULL AND avg_salary > 0 {filters} {segment_filter}
GROUP BY position_level
ORDER BY avg_salary DESC
"""

QUERY_EXP_TOP_PAYING_CATEGORIES = """
SELECT
  jc.category_name,
  AVG(je.avg_salary) as avg_salary,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY je.avg_salary) as median_salary,
  COUNT(*) as job_count
FROM jobs_enriched je
JOIN jobs_categories jc ON je.job_id = jc.job_id
WHERE jc.category_name IS NOT NULL AND je.avg_salary > 0 {filters} {segment_filter}
GROUP BY jc.category_name
HAVING COUNT(*) >= 3
ORDER BY avg_salary DESC
LIMIT 10
"""

QUERY_EXP_TOP_PAYING_COMPANIES = """
SELECT
  company_name,
  AVG(avg_salary) as avg_salary,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY avg_salary) as median_salary,
  COUNT(*) as job_count
FROM jobs_enriched
WHERE company_name IS NOT NULL AND avg_salary > 0 {filters} {segment_filter}
GROUP BY company_name
HAVING COUNT(*) >= 3
ORDER BY avg_salary DESC
LIMIT 10
"""
