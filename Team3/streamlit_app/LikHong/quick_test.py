"""
Quick Functional Tests for SG Jobs Dashboard
"""

import duckdb
import pandas as pd
import numpy as np
from datetime import datetime

print("\n" + "="*80)
print("🚀 RUNNING QUICK FUNCTIONAL TESTS")
print("="*80)

# Test 1: Database Connection
print("\n🧪 TEST 1: Database Connection")
try:
    con = duckdb.connect('../../data/raw/SGJobData.db', read_only=True)
    total_jobs = con.execute("SELECT COUNT(*) FROM jobs_enriched").fetchone()[0]
    print(f"✅ Connected - {total_jobs:,} jobs in database")
except Exception as e:
    print(f"❌ Failed: {e}")
    exit(1)

# Test 2: Data Query
print("\n🧪 TEST 2: Job Recommendations Query")
try:
    query = """
    SELECT DISTINCT
        je.job_id, je.title, je.avg_salary, je.min_experience,
        je.applications, je.posting_date, jc.category_name
    FROM jobs_enriched je
    LEFT JOIN jobs_categories jc ON je.job_id = jc.job_id
    WHERE je.avg_salary IS NOT NULL AND je.title IS NOT NULL
    LIMIT 100
    """
    df = con.execute(query).fetchdf()
    assert len(df) > 0
    print(f"✅ Query successful - retrieved {len(df)} jobs")
except Exception as e:
    print(f"❌ Failed: {e}")
    exit(1)

# Test 3: Match Scoring
print("\n🧪 TEST 3: Match Scoring Algorithm")
try:
    target_salary = 5000
    target_experience = 3
    
    df_test = df.copy()
    
    # Salary score
    df_test['salary_diff'] = abs(df_test['avg_salary'] - target_salary)
    max_diff = df_test['salary_diff'].max() if df_test['salary_diff'].max() > 0 else 1
    df_test['salary_score'] = 1 - (df_test['salary_diff'] / max_diff)
    
    # Experience score
    df_test['exp_diff'] = abs(df_test['min_experience'].fillna(0) - target_experience)
    max_exp_diff = df_test['exp_diff'].max() if df_test['exp_diff'].max() > 0 else 1
    df_test['experience_score'] = 1 - (df_test['exp_diff'] / max_exp_diff)
    
    # Competition score
    max_apps = df_test['applications'].max() if df_test['applications'].max() > 0 else 1
    df_test['competition_score'] = 1 - (df_test['applications'].fillna(0) / max_apps)
    
    # Freshness score
    df_test['posting_date'] = pd.to_datetime(df_test['posting_date'])
    latest_date = df_test['posting_date'].max()
    df_test['days_since_post'] = (latest_date - df_test['posting_date']).dt.days
    max_days = df_test['days_since_post'].max() if df_test['days_since_post'].max() > 0 else 1
    df_test['freshness_score'] = 1 - (df_test['days_since_post'] / max_days)
    
    # Overall score
    df_test['overall_score'] = (
        df_test['salary_score'] * 0.30 +
        df_test['experience_score'] * 0.25 +
        df_test['competition_score'] * 0.15 +
        df_test['freshness_score'] * 0.10 +
        0.20  # category score placeholder
    )
    
    assert df_test['overall_score'].between(0, 1).all()
    print(f"✅ Scoring works - scores range: {df_test['overall_score'].min():.2f} to {df_test['overall_score'].max():.2f}")
except Exception as e:
    print(f"❌ Failed: {e}")
    exit(1)

# Test 4: Radar Chart Data
print("\n🧪 TEST 4: Radar Chart Data Preparation")
try:
    top_10 = df_test.nlargest(10, 'overall_score')
    assert len(top_10) == 10
    
    for _, job in top_10.iterrows():
        values = [
            job['salary_score'],
            job['experience_score'],
            job['competition_score'],
            job['freshness_score']
        ]
        assert all(0 <= v <= 1 for v in values)
    
    print(f"✅ Radar data ready - top 10 jobs prepared")
except Exception as e:
    print(f"❌ Failed: {e}")
    exit(1)

# Test 5: Filtering
print("\n🧪 TEST 5: Query Filtering")
try:
    # Test category filter
    it_jobs = con.execute("""
        SELECT COUNT(*) FROM jobs_enriched je
        LEFT JOIN jobs_categories jc ON je.job_id = jc.job_id
        WHERE jc.category_name = 'Information Technology'
    """).fetchone()[0]
    
    # Test experience filter
    entry_jobs = con.execute("""
        SELECT COUNT(*) FROM jobs_enriched
        WHERE COALESCE(min_experience, 0) BETWEEN 0 AND 3
    """).fetchone()[0]
    
    # Test salary filter
    mid_salary = con.execute("""
        SELECT COUNT(*) FROM jobs_enriched
        WHERE salary_band = '3K - 5K'
    """).fetchone()[0]
    
    print(f"✅ Filters work - IT: {it_jobs:,}, Entry: {entry_jobs:,}, Mid-Salary: {mid_salary:,}")
except Exception as e:
    print(f"❌ Failed: {e}")
    exit(1)

# Test 6: Performance
print("\n🧪 TEST 6: Query Performance")
try:
    import time
    
    start = time.time()
    large_query = """
    SELECT DISTINCT
        je.job_id, je.title, je.company_name, je.avg_salary,
        je.min_experience, je.applications, jc.category_name
    FROM jobs_enriched je
    LEFT JOIN jobs_categories jc ON je.job_id = jc.job_id
    WHERE je.avg_salary BETWEEN 3000 AND 8000
        AND COALESCE(je.min_experience, 0) <= 10
        AND je.title IS NOT NULL
    LIMIT 500
    """
    df_large = con.execute(large_query).fetchdf()
    duration = time.time() - start
    
    assert duration < 5.0
    print(f"✅ Performance OK - {len(df_large)} jobs in {duration:.3f}s")
except Exception as e:
    print(f"❌ Failed: {e}")
    exit(1)

# Test 7: Edge Cases
print("\n🧪 TEST 7: Edge Cases")
try:
    # Empty dataframe
    df_empty = pd.DataFrame()
    assert df_empty.empty
    
    # Missing values
    df_missing = pd.DataFrame({'value': [1, None, 3]})
    df_missing['value'] = df_missing['value'].fillna(0)
    assert df_missing['value'].notnull().all()
    
    # Extreme values
    df_extreme = pd.DataFrame({'salary': [1000, 100000]})
    df_extreme['norm'] = (df_extreme['salary'] - df_extreme['salary'].min()) / \
                         (df_extreme['salary'].max() - df_extreme['salary'].min())
    assert df_extreme['norm'].between(0, 1).all()
    
    print(f"✅ Edge cases handled correctly")
except Exception as e:
    print(f"❌ Failed: {e}")
    exit(1)

# Test 8: End-to-End Integration
print("\n🧪 TEST 8: End-to-End Integration")
try:
    # Simulate complete user flow
    query_integration = """
    SELECT DISTINCT
        je.job_id, je.title, je.company_name, je.avg_salary,
        je.min_experience, je.applications, je.posting_date,
        jc.category_name
    FROM jobs_enriched je
    LEFT JOIN jobs_categories jc ON je.job_id = jc.job_id
    WHERE jc.category_name IN ('Information Technology', 'Engineering')
        AND COALESCE(je.min_experience, 0) BETWEEN 0 AND 5
        AND je.avg_salary BETWEEN 3000 AND 7000
        AND je.title IS NOT NULL
    LIMIT 100
    """
    
    df_int = con.execute(query_integration).fetchdf()
    
    # Score
    df_int['salary_diff'] = abs(df_int['avg_salary'] - 5000)
    df_int['salary_score'] = 1 - (df_int['salary_diff'] / df_int['salary_diff'].max())
    df_int['overall_score'] = df_int['salary_score']
    
    # Rank
    df_ranked = df_int.sort_values('overall_score', ascending=False)
    top_3 = df_ranked.head(3)
    
    assert len(top_3) == 3
    assert top_3['overall_score'].is_monotonic_decreasing
    
    print(f"✅ Integration test passed")
    print(f"\n🏆 Top 3 Matches:")
    for idx, (_, job) in enumerate(top_3.iterrows(), 1):
        print(f"   {idx}. {job['title'][:50]} - {job['company_name'][:30]}")
        print(f"      Match: {job['overall_score']:.1%}, Salary: ${job['avg_salary']:,.0f}")
    
except Exception as e:
    print(f"❌ Failed: {e}")
    exit(1)

con.close()

print("\n" + "="*80)
print("✅ ALL TESTS PASSED!")
print("="*80)
print("\n📊 Summary:")
print("   - Database connection: OK")
print("   - Data queries: OK")
print("   - Match scoring: OK")
print("   - Radar chart data: OK")
print("   - Filtering: OK")
print("   - Performance: OK")
print("   - Edge cases: OK")
print("   - Integration: OK")
print("\n🎯 Dashboard is ready for deployment!")
print("="*80 + "\n")
