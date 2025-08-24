#!/usr/bin/env python3
"""
Test script for imo.sqlite database
Verifies database structure, content, and data integrity
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.aops.aops_models import Base, Contest, ContestYear, Problem

def test_imo_database():
    """Test the IMO database structure and content"""
    
    DB_PATH = 'databases/imo.sqlite'
    os.path
    print("🧪 Testing IMO Database")
    print("=" * 50)
    
    # Check if database file exists
    if not os.path.exists(DB_PATH):
        print(f"❌ ERROR: Database file '{DB_PATH}' not found!")
        print("   Please run the IMO scraper first to create the database.")
        return False
    
    try:
        # Connect to database
        engine = create_engine(f'sqlite:///{DB_PATH}')
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print(f"✅ Connected to database: {DB_PATH}")
        
        # Test 1: Check table structure
        print("\n📋 Database Structure:")
        with engine.connect() as conn:
            tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
            table_names = [table[0] for table in tables]
            
            expected_tables = ['contests', 'contest_years', 'problems']
            for table in expected_tables:
                if table in table_names:
                    print(f"   ✅ Table '{table}' exists")
                else:
                    print(f"   ❌ Table '{table}' missing")
        
        # Test 2: Count records
        print("\n📊 Record Counts:")
        contest_count = session.query(Contest).count()
        year_count = session.query(ContestYear).count()
        problem_count = session.query(Problem).count()
        
        print(f"   Contests: {contest_count}")
        print(f"   Contest Years: {year_count}")
        print(f"   Problems: {problem_count}")
        
        if problem_count == 0:
            print("   ⚠️  WARNING: No problems found in database!")
            return False
        
        # Test 3: Check IMO contest
        print("\n🏆 Contest Details:")
        imo_contest = session.query(Contest).filter_by(name="IMO").first()
        if imo_contest:
            print(f"   ✅ IMO Contest found")
            print(f"      Full Name: {imo_contest.full_name}")
            print(f"      Country: {imo_contest.country}")
            print(f"      Contest Type: {imo_contest.contest_type}")
            print(f"      Target Level: {imo_contest.target_level}")
        else:
            print("   ❌ IMO Contest not found!")
            return False
        
        # Test 4: Check year range
        print("\n📅 Year Coverage:")
        years = session.query(ContestYear.year).distinct().order_by(ContestYear.year).all()
        year_list = [year[0] for year in years]
        
        if year_list:
            print(f"   Years: {min(year_list)} - {max(year_list)}")
            print(f"   Total years: {len(year_list)}")
            print(f"   Sample years: {year_list[:5]}{'...' if len(year_list) > 5 else ''}")
        else:
            print("   ❌ No years found!")
        
        # Test 5: Sample problems
        print("\n📝 Sample Problems:")
        sample_problems = session.query(Problem).limit(3).all()
        
        for i, problem in enumerate(sample_problems, 1):
            print(f"\n   Problem {i}:")
            print(f"      Label: {problem.problem_label}")
            print(f"      Year: {problem.contest_year.year}")
            print(f"      Number: {problem.problem_number}")
            print(f"      Subject: {problem.subject_area}")
            print(f"      Statement length: {len(problem.statement) if problem.statement else 0} chars")
            print(f"      Solution length: {len(problem.solution) if problem.solution else 0} chars")
            print(f"      AoPS URL: {problem.aops_problem_url[:50]}..." if problem.aops_problem_url else "      No URL")
        
        # Test 6: Subject area distribution
        print("\n🔬 Subject Area Distribution:")
        subjects = session.query(Problem.subject_area, session.query(Problem).filter_by(subject_area=Problem.subject_area).count()).distinct().all()
        
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT subject_area, COUNT(*) as count 
                FROM problems 
                GROUP BY subject_area 
                ORDER BY count DESC
            """))
            
            for subject, count in result:
                print(f"   {subject or 'Unknown'}: {count} problems")
        
        # Test 7: Recent problems
        print("\n🆕 Recent Problems (last 3 years):")
        recent_years = sorted(year_list, reverse=True)[:3]
        
        for year in recent_years:
            year_problems = session.query(Problem).join(ContestYear).filter(ContestYear.year == year).count()
            print(f"   {year}: {year_problems} problems")
        
        # Test 8: Data quality checks
        print("\n🔍 Data Quality Checks:")
        
        # Check for empty statements
        empty_statements = session.query(Problem).filter(
            (Problem.statement == "") | (Problem.statement == None)
        ).count()
        print(f"   Problems with empty statements: {empty_statements}")
        
        # Check for empty solutions
        empty_solutions = session.query(Problem).filter(
            (Problem.solution == "") | (Problem.solution == None)
        ).count()
        print(f"   Problems with empty solutions: {empty_solutions}")
        
        # Check for duplicate problems
        duplicates = session.execute(text("""
            SELECT contest_year_id, problem_number, COUNT(*) as count
            FROM problems 
            GROUP BY contest_year_id, problem_number 
            HAVING count > 1
        """)).fetchall()
        
        print(f"   Duplicate problems: {len(duplicates)}")
        
        # Test 9: Database file size
        file_size = os.path.getsize(DB_PATH)
        file_size_mb = file_size / (1024 * 1024)
        print(f"\n💾 Database File:")
        print(f"   Size: {file_size_mb:.2f} MB")
        print(f"   Path: {os.path.abspath(DB_PATH)}")
        
        session.close()
        
        # Final summary
        print("\n🎉 Test Summary:")
        if problem_count > 0 and contest_count > 0:
            print("   ✅ Database appears to be working correctly!")
            print(f"   📈 Ready to serve {problem_count} problems from {len(year_list)} years")
            return True
        else:
            print("   ❌ Database has issues - check the warnings above")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Failed to test database: {e}")
        return False

def test_api_compatibility():
    """Test if database is compatible with Flask API"""
    print("\n🌐 API Compatibility Test:")
    
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        engine = create_engine("sqlite:///imo.sqlite")
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Test the exact query the API uses
        problems = (session.query(Problem)
                   .join(ContestYear)
                   .join(Contest)
                   .limit(5)
                   .all())
        
        print(f"   ✅ API query test passed - {len(problems)} problems retrieved")
        
        # Test data format
        if problems:
            p = problems[0]
            api_format = {
                "label": p.problem_label or f"Problem {p.problem_number}",
                "statement": p.statement or "Statement not available",
                "solution": p.solution or "Solution not available",
                "year": p.contest_year.year,
                "contest": p.contest_year.contest.full_name or p.contest_year.contest.name,
                "subject": p.subject_area or "Unknown",
                "source": "imo"
            }
            print("   ✅ API data format test passed")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"   ❌ API compatibility test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧮 IMO Database Test Suite")
    print("=" * 60)
    
    # Run tests
    db_test_passed = test_imo_database()
    api_test_passed = test_api_compatibility()
    
    print("\n" + "=" * 60)
    if db_test_passed and api_test_passed:
        print("🎊 ALL TESTS PASSED! Database is ready to use.")
        sys.exit(0)
    else:
        print("💥 SOME TESTS FAILED! Please check the issues above.")
        sys.exit(1)
