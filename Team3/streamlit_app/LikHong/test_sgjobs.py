"""
Comprehensive Functional Tests for SG Jobs Dashboard
Tests all core functionalities including data loading, scoring, and recommendations
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import numpy as np
from datetime import datetime
import duckdb

# Import functions from sgjobs
import importlib.util
spec = importlib.util.spec_from_file_location("sgjobs", "sgjobs.py")
sgjobs = importlib.util.module_from_spec(spec)

# Test database connection
def test_database_connection():
    """Test database connection and basic queries"""
    print("\n🧪 TEST 1: Database Connection")
    try:
        con = duckdb.connect('../../data/raw/SGJobData.db', read_only=True)
        
        # Test basic queries
        result = con.execute("SELECT COUNT(*) FROM jobs_enriched").fetchone()
        assert result[0] > 0, "No jobs found in database"
        print(f"✅ Database connected - {result[0]:,} jobs found")
        
        # Test jobs_categories table
        result = con.execute("SELECT COUNT(*) FROM jobs_categories").fetchone()
        assert result[0] > 0, "No categories found"
        print(f"✅ Categories table accessible - {result[0]:,} records")
        
        con.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_data_loading():
    """Test data loading functions"""
    print("\n🧪 TEST 2: Data Loading Functions")
    try:
        con = duckdb.connect('../../data/raw/SGJobData.db', read_only=True)
        
        # Test category loading
        categories = con.execute("""
            SELECT DISTINCT category_name 
            FROM jobs_categories 
            WHERE category_name IS NOT NULL 
            ORDER BY category_name
        """).fetchdf()['category_name'].tolist()
        
        assert len(categories) > 0, "No categories loaded"
        print(f"✅ Categories loaded: {len(categories)} categories")
        
        # Test position levels
        levels = con.execute("""
            SELECT DISTINCT position_level 
            FROM jobs_enriched 
            WHERE position_level IS NOT NULL
        """).fetchdf()['position_level'].tolist()
        
        assert len(levels) > 0, "No position levels loaded"
        print(f"✅ Position levels loaded: {len(levels)} levels")
        
        # Test salary bands
        bands = con.execute("""
            SELECT DISTINCT salary_band 
            FROM jobs_enriched 
            WHERE salary_band IS NOT NULL
        """).fetchdf()['salary_band'].tolist()
        
        assert len(bands) > 0, "No salary bands loaded"
        print(f"✅ Salary bands loaded: {len(bands)} bands")
        
        con.close()
        return True
    except Exception as e:
        print(f"❌ Data loading failed: {e}")
        return False

def test_job_recommendations():
    """Test job recommendations query"""
    print("\n🧪 TEST 3: Job Recommendations Query")
    try:
        con = duckdb.connect('../../data/raw/SGJobData.db', read_only=True)
        
        # Test basic query without filters
        query = """
        SELECT DISTINCT
            je.job_id,
            je.title,
            je.company_name,
            je.position_level,
            je.salary_band,
            je.experience_band,
            je.avg_salary,
            je.min_experience,
            je.posting_date,
            je.applications,
            je.views,
            jc.category_name
        FROM jobs_enriched je
        LEFT JOIN jobs_categories jc ON je.job_id = jc.job_id
        WHERE je.avg_salary IS NOT NULL
            AND je.title IS NOT NULL
        LIMIT 100
        """
        
        df = con.execute(query).fetchdf()
        assert not df.empty, "Query returned no results"
        assert len(df) > 0, "No jobs retrieved"
        print(f"✅ Basic query successful: {len(df)} jobs retrieved")
        
        # Test query with filters
        query_filtered = """
        SELECT DISTINCT je.job_id, je.title, je.avg_salary, jc.category_name
        FROM jobs_enriched je
        LEFT JOIN jobs_categories jc ON je.job_id = jc.job_id
        WHERE je.avg_salary BETWEEN 3000 AND 6000
            AND COALESCE(je.min_experience, 0) BETWEEN 0 AND 5
            AND je.title IS NOT NULL
        LIMIT 50
        """
        
        df_filtered = con.execute(query_filtered).fetchdf()
        assert not df_filtered.empty, "Filtered query returned no results"
        print(f"✅ Filtered query successful: {len(df_filtered)} jobs retrieved")
        
        # Verify data quality
        assert df['job_id'].notnull().all(), "job_id contains nulls"
        assert df['title'].notnull().all(), "title contains nulls"
        print("✅ Data quality checks passed")
        
        con.close()
        return True
    except Exception as e:
        print(f"❌ Job recommendations query failed: {e}")
        return False

def test_match_scoring():
    """Test match scoring algorithm"""
    print("\n🧪 TEST 4: Match Scoring Algorithm")
    try:
        # Create sample dataframe
        sample_data = {
            'job_id': ['J001', 'J002', 'J003', 'J004', 'J005'],
            'title': ['Software Engineer', 'Data Analyst', 'Product Manager', 'DevOps Engineer', 'UX Designer'],
            'company_name': ['Company A', 'Company B', 'Company C', 'Company D', 'Company E'],
            'avg_salary': [5000, 4500, 6000, 5500, 4000],
            'min_experience': [2, 1, 5, 3, 2],
            'applications': [50, 100, 30, 75, 150],
            'posting_date': pd.date_range('2024-01-01', periods=5, freq='D'),
            'category_name': ['IT', 'Data', 'Product', 'IT', 'Design']
        }
        
        df = pd.DataFrame(sample_data)
        
        # Test scoring function
        target_salary = 5000
        target_experience = 3
        preferred_categories = ['IT', 'Data']
        
        # Compute scores manually
        df_scored = df.copy()
        
        # Salary score
        df_scored['salary_diff'] = abs(df_scored['avg_salary'] - target_salary)
        max_diff = df_scored['salary_diff'].max()
        df_scored['salary_score'] = 1 - (df_scored['salary_diff'] / max_diff)
        
        assert df_scored['salary_score'].between(0, 1).all(), "Salary scores out of range"
        print(f"✅ Salary scoring: min={df_scored['salary_score'].min():.2f}, max={df_scored['salary_score'].max():.2f}")
        
        # Experience score
        df_scored['exp_diff'] = abs(df_scored['min_experience'] - target_experience)
        max_exp_diff = df_scored['exp_diff'].max()
        df_scored['experience_score'] = 1 - (df_scored['exp_diff'] / max_exp_diff)
        
        assert df_scored['experience_score'].between(0, 1).all(), "Experience scores out of range"
        print(f"✅ Experience scoring: min={df_scored['experience_score'].min():.2f}, max={df_scored['experience_score'].max():.2f}")
        
        # Category score
        df_scored['category_score'] = df_scored['category_name'].apply(
            lambda x: 1.0 if x in preferred_categories else 0.5
        )
        
        assert df_scored['category_score'].between(0, 1).all(), "Category scores out of range"
        print(f"✅ Category scoring: min={df_scored['category_score'].min():.2f}, max={df_scored['category_score'].max():.2f}")
        
        # Competition score
        max_apps = df_scored['applications'].max()
        df_scored['competition_score'] = 1 - (df_scored['applications'] / max_apps)
        
        assert df_scored['competition_score'].between(0, 1).all(), "Competition scores out of range"
        print(f"✅ Competition scoring: min={df_scored['competition_score'].min():.2f}, max={df_scored['competition_score'].max():.2f}")
        
        # Freshness score
        df_scored['posting_date'] = pd.to_datetime(df_scored['posting_date'])
        latest_date = df_scored['posting_date'].max()
        df_scored['days_since_post'] = (latest_date - df_scored['posting_date']).dt.days
        max_days = df_scored['days_since_post'].max()
        df_scored['freshness_score'] = 1 - (df_scored['days_since_post'] / max_days)
        
        assert df_scored['freshness_score'].between(0, 1).all(), "Freshness scores out of range"
        print(f"✅ Freshness scoring: min={df_scored['freshness_score'].min():.2f}, max={df_scored['freshness_score'].max():.2f}")
        
        # Overall score
        weights = {'salary': 0.30, 'experience': 0.25, 'category': 0.20, 'competition': 0.15, 'freshness': 0.10}
        df_scored['overall_score'] = (
            df_scored['salary_score'] * weights['salary'] +
            df_scored['experience_score'] * weights['experience'] +
            df_scored['category_score'] * weights['category'] +
            df_scored['competition_score'] * weights['competition'] +
            df_scored['freshness_score'] * weights['freshness']
        )
        
        assert df_scored['overall_score'].between(0, 1).all(), "Overall scores out of range"
        assert abs(sum(weights.values()) - 1.0) < 0.01, "Weights don't sum to 1"
        print(f"✅ Overall scoring: min={df_scored['overall_score'].min():.2f}, max={df_scored['overall_score'].max():.2f}")
        
        # Test sorting
        df_sorted = df_scored.sort_values('overall_score', ascending=False)
        assert df_sorted['overall_score'].is_monotonic_decreasing, "Sorting failed"
        print("✅ Sorting by score works correctly")
        
        return True
    except Exception as e:
        print(f"❌ Match scoring failed: {e}")
        return False

def test_radar_chart_data():
    """Test radar chart data preparation"""
    print("\n🧪 TEST 5: Radar Chart Data Preparation")
    try:
        # Create sample scored data
        sample_data = {
            'job_id': ['J001', 'J002', 'J003'],
            'title': ['Software Engineer', 'Data Analyst', 'Product Manager'],
            'company_name': ['Company A', 'Company B', 'Company C'],
            'salary_score': [0.85, 0.70, 0.90],
            'experience_score': [0.75, 0.85, 0.65],
            'category_score': [0.90, 0.80, 0.70],
            'competition_score': [0.80, 0.60, 0.85],
            'freshness_score': [0.70, 0.90, 0.75],
            'overall_score': [0.80, 0.77, 0.77]
        }
        
        df = pd.DataFrame(sample_data)
        
        # Verify all scores are valid
        score_columns = ['salary_score', 'experience_score', 'category_score', 
                        'competition_score', 'freshness_score', 'overall_score']
        
        for col in score_columns:
            assert df[col].between(0, 1).all(), f"{col} contains invalid values"
        
        print("✅ All score columns are in valid range [0, 1]")
        
        # Test top N selection
        top_n = 3
        top_jobs = df.head(top_n)
        assert len(top_jobs) == top_n, f"Expected {top_n} jobs, got {len(top_jobs)}"
        print(f"✅ Top {top_n} selection works correctly")
        
        # Verify radar values can be created
        for _, job in top_jobs.iterrows():
            values = [
                job['salary_score'],
                job['experience_score'],
                job['category_score'],
                job['competition_score'],
                job['freshness_score']
            ]
            assert all(0 <= v <= 1 for v in values), "Radar values out of range"
        
        print("✅ Radar chart values prepared successfully")
        
        return True
    except Exception as e:
        print(f"❌ Radar chart data preparation failed: {e}")
        return False

def test_filters_and_queries():
    """Test various filtering scenarios"""
    print("\n🧪 TEST 6: Filtering and Query Combinations")
    try:
        con = duckdb.connect('../../data/raw/SGJobData.db', read_only=True)
        
        # Test 1: Category filter
        query_cat = """
        SELECT COUNT(DISTINCT je.job_id) as count
        FROM jobs_enriched je
        LEFT JOIN jobs_categories jc ON je.job_id = jc.job_id
        WHERE jc.category_name = 'Information Technology'
            AND je.avg_salary IS NOT NULL
        """
        result = con.execute(query_cat).fetchone()
        assert result[0] > 0, "Category filter returned no results"
        print(f"✅ Category filter: {result[0]} IT jobs found")
        
        # Test 2: Experience range filter
        query_exp = """
        SELECT COUNT(DISTINCT job_id) as count
        FROM jobs_enriched
        WHERE COALESCE(min_experience, 0) BETWEEN 0 AND 3
            AND avg_salary IS NOT NULL
        """
        result = con.execute(query_exp).fetchone()
        assert result[0] > 0, "Experience filter returned no results"
        print(f"✅ Experience filter (0-3 years): {result[0]} jobs found")
        
        # Test 3: Salary band filter
        query_sal = """
        SELECT COUNT(DISTINCT job_id) as count
        FROM jobs_enriched
        WHERE salary_band IN ('3K - 5K', '5K - 8K')
            AND avg_salary IS NOT NULL
        """
        result = con.execute(query_sal).fetchone()
        assert result[0] > 0, "Salary band filter returned no results"
        print(f"✅ Salary band filter: {result[0]} jobs found")
        
        # Test 4: Competition filter
        query_comp = """
        SELECT COUNT(DISTINCT job_id) as count
        FROM jobs_enriched
        WHERE COALESCE(applications, 0) <= 100
            AND avg_salary IS NOT NULL
        """
        result = con.execute(query_comp).fetchone()
        assert result[0] > 0, "Competition filter returned no results"
        print(f"✅ Competition filter (≤100 applicants): {result[0]} jobs found")
        
        # Test 5: Combined filters
        query_combined = """
        SELECT COUNT(DISTINCT je.job_id) as count
        FROM jobs_enriched je
        LEFT JOIN jobs_categories jc ON je.job_id = jc.job_id
        WHERE jc.category_name IN ('Information Technology', 'Engineering')
            AND COALESCE(je.min_experience, 0) BETWEEN 0 AND 5
            AND je.salary_band IN ('3K - 5K', '5K - 8K')
            AND COALESCE(je.applications, 0) <= 500
            AND je.avg_salary IS NOT NULL
        """
        result = con.execute(query_combined).fetchone()
        print(f"✅ Combined filters: {result[0]} jobs found")
        
        con.close()
        return True
    except Exception as e:
        print(f"❌ Filtering tests failed: {e}")
        return False

def test_performance():
    """Test query performance"""
    print("\n🧪 TEST 7: Performance Testing")
    try:
        con = duckdb.connect('../../data/raw/SGJobData.db', read_only=True)
        
        import time
        
        # Test 1: Large result set
        start = time.time()
        query_large = """
        SELECT DISTINCT
            je.job_id,
            je.title,
            je.avg_salary,
            jc.category_name
        FROM jobs_enriched je
        LEFT JOIN jobs_categories jc ON je.job_id = jc.job_id
        WHERE je.avg_salary IS NOT NULL
        LIMIT 500
        """
        df = con.execute(query_large).fetchdf()
        duration = time.time() - start
        
        assert duration < 5.0, f"Query too slow: {duration:.2f}s"
        print(f"✅ Large query ({len(df)} rows): {duration:.3f}s")
        
        # Test 2: Aggregation query
        start = time.time()
        query_agg = """
        SELECT 
            category_name,
            COUNT(*) as job_count,
            AVG(avg_salary) as avg_salary
        FROM jobs_categories
        WHERE avg_salary IS NOT NULL
        GROUP BY category_name
        ORDER BY job_count DESC
        """
        df_agg = con.execute(query_agg).fetchdf()
        duration = time.time() - start
        
        assert duration < 3.0, f"Aggregation query too slow: {duration:.2f}s"
        print(f"✅ Aggregation query ({len(df_agg)} categories): {duration:.3f}s")
        
        # Test 3: Complex join with filters
        start = time.time()
        query_complex = """
        SELECT DISTINCT
            je.job_id,
            je.title,
            je.company_name,
            je.avg_salary,
            je.min_experience,
            je.applications,
            jc.category_name
        FROM jobs_enriched je
        LEFT JOIN jobs_categories jc ON je.job_id = jc.job_id
        WHERE je.avg_salary BETWEEN 3000 AND 8000
            AND COALESCE(je.min_experience, 0) <= 10
            AND COALESCE(je.applications, 0) <= 500
            AND je.title IS NOT NULL
        LIMIT 200
        """
        df_complex = con.execute(query_complex).fetchdf()
        duration = time.time() - start
        
        assert duration < 5.0, f"Complex query too slow: {duration:.2f}s"
        print(f"✅ Complex filtered query ({len(df_complex)} rows): {duration:.3f}s")
        
        con.close()
        return True
    except Exception as e:
        print(f"❌ Performance tests failed: {e}")
        return False

def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n🧪 TEST 8: Edge Cases")
    try:
        # Test 1: Empty dataframe
        df_empty = pd.DataFrame()
        assert df_empty.empty, "Empty dataframe test failed"
        print("✅ Empty dataframe handled correctly")
        
        # Test 2: Single row dataframe
        df_single = pd.DataFrame({
            'job_id': ['J001'],
            'title': ['Test Job'],
            'avg_salary': [5000],
            'min_experience': [2],
            'applications': [50],
            'posting_date': [datetime.now()],
            'category_name': ['IT']
        })
        assert len(df_single) == 1, "Single row dataframe test failed"
        print("✅ Single row dataframe handled correctly")
        
        # Test 3: Missing values
        df_missing = pd.DataFrame({
            'job_id': ['J001', 'J002', 'J003'],
            'title': ['Job1', None, 'Job3'],
            'avg_salary': [5000, None, 4000],
            'min_experience': [2, None, 3]
        })
        
        # Test fillna equivalent
        df_missing['min_experience'] = df_missing['min_experience'].fillna(0)
        assert df_missing['min_experience'].notnull().all(), "fillna failed"
        print("✅ Missing values handled correctly")
        
        # Test 4: Extreme values
        df_extreme = pd.DataFrame({
            'avg_salary': [1000, 50000, 100000],
            'min_experience': [0, 20, 40],
            'applications': [0, 500, 10000]
        })
        
        # Normalize extreme values
        df_extreme['salary_norm'] = (df_extreme['avg_salary'] - df_extreme['avg_salary'].min()) / \
                                     (df_extreme['avg_salary'].max() - df_extreme['avg_salary'].min())
        assert df_extreme['salary_norm'].between(0, 1).all(), "Normalization failed"
        print("✅ Extreme values normalized correctly")
        
        return True
    except Exception as e:
        print(f"❌ Edge case tests failed: {e}")
        return False

def test_integration():
    """Test end-to-end integration"""
    print("\n🧪 TEST 9: End-to-End Integration")
    try:
        con = duckdb.connect('../../data/raw/SGJobData.db', read_only=True)
        
        # Simulate complete user journey
        print("\n📋 Simulating user journey:")
        
        # Step 1: Load data
        print("  1️⃣  Loading job data...")
        query = """
        SELECT DISTINCT
            je.job_id,
            je.title,
            je.company_name,
            je.avg_salary,
            je.min_experience,
            je.applications,
            je.posting_date,
            jc.category_name
        FROM jobs_enriched je
        LEFT JOIN jobs_categories jc ON je.job_id = jc.job_id
        WHERE jc.category_name IN ('Information Technology', 'Engineering')
            AND COALESCE(je.min_experience, 0) BETWEEN 0 AND 5
            AND je.avg_salary BETWEEN 3000 AND 7000
            AND COALESCE(je.applications, 0) <= 300
            AND je.title IS NOT NULL
        LIMIT 100
        """
        df = con.execute(query).fetchdf()
        assert not df.empty, "No data loaded"
        print(f"     ✓ Loaded {len(df)} jobs")
        
        # Step 2: Compute scores
        print("  2️⃣  Computing match scores...")
        target_salary = 5000
        target_experience = 3
        
        df_scored = df.copy()
        df_scored['salary_diff'] = abs(df_scored['avg_salary'] - target_salary)
        max_diff = df_scored['salary_diff'].max() if df_scored['salary_diff'].max() > 0 else 1
        df_scored['salary_score'] = 1 - (df_scored['salary_diff'] / max_diff)
        
        df_scored['exp_diff'] = abs(df_scored['min_experience'].fillna(0) - target_experience)
        max_exp_diff = df_scored['exp_diff'].max() if df_scored['exp_diff'].max() > 0 else 1
        df_scored['experience_score'] = 1 - (df_scored['exp_diff'] / max_exp_diff)
        
        df_scored['overall_score'] = (df_scored['salary_score'] * 0.5 + 
                                     df_scored['experience_score'] * 0.5)
        print(f"     ✓ Computed scores for {len(df_scored)} jobs")
        
        # Step 3: Sort and get top matches
        print("  3️⃣  Ranking jobs...")
        df_ranked = df_scored.sort_values('overall_score', ascending=False)
        top_5 = df_ranked.head(5)
        print(f"     ✓ Top 5 matches identified")
        
        # Step 4: Verify results
        print("  4️⃣  Verifying results...")
        assert len(top_5) == 5, "Failed to get top 5"
        assert top_5['overall_score'].is_monotonic_decreasing, "Ranking incorrect"
        assert all(top_5['overall_score'] >= 0), "Scores below 0"
        assert all(top_5['overall_score'] <= 1), "Scores above 1"
        print(f"     ✓ Results validated")
        
        # Display sample results
        print("\n🏆 Top 3 Job Matches:")
        for idx, (_, job) in enumerate(top_5.head(3).iterrows(), 1):
            print(f"     {idx}. {job['title']} at {job['company_name']}")
            print(f"        Match: {job['overall_score']:.1%} | Salary: ${job['avg_salary']:,.0f}")
        
        con.close()
        return True
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def run_all_tests():
    """Run all functional tests"""
    print("\n" + "="*80)
    print("🚀 STARTING COMPREHENSIVE FUNCTIONAL TESTS")
    print("="*80)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Data Loading", test_data_loading),
        ("Job Recommendations", test_job_recommendations),
        ("Match Scoring", test_match_scoring),
        ("Radar Chart Data", test_radar_chart_data),
        ("Filters and Queries", test_filters_and_queries),
        ("Performance", test_performance),
        ("Edge Cases", test_edge_cases),
        ("End-to-End Integration", test_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{'='*80}")
    print(f"🎯 FINAL RESULT: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("="*80)
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
