import os
import re
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from putnam_models import Base, Year, Problem

# Calculate the correct path to the database
script_dir = os.path.dirname(os.path.abspath(__file__))  # root/backend/putnam/
root_dir = os.path.dirname(os.path.dirname(script_dir))   # root/
databases_dir = os.path.join(root_dir, 'databases')      # root/databases/
DB_PATH = os.path.join(databases_dir, 'putnam.sqlite')   # root/databases/putnam.sqlite

# Ensure databases directory exists
os.makedirs(databases_dir, exist_ok=True)

# ----------------------------
# DB Setup
# ----------------------------
engine = create_engine(f"sqlite:///{DB_PATH}")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def fetch_tex_content(url):
    """Download tex file content"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/127.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        return ""

def parse_problems_from_tex(tex_content):
    """Parse problems from tex content using the \item[A--1] pattern"""
    # Based on the file you shared, problems use \item[A--1], \item[A--2], etc.
    pattern = re.compile(r'\\item\[(A|B)--([1-6])\]')
    parts = pattern.split(tex_content)
    
    problems = []
    for i in range(1, len(parts), 3):
        if i+2 < len(parts):
            part_letter = parts[i]
            problem_number = int(parts[i+1])
            content = parts[i+2].strip()
            
            # Clean content - stop at next problem or end
            next_problem = re.search(r'\\item\[(A|B)--[1-6]\]', content)
            if next_problem:
                content = content[:next_problem.start()].strip()
            
            problems.append({
                "part": part_letter,
                "number": problem_number, 
                "label": f"{part_letter}{problem_number}",
                "content": content
            })
    
    return problems

def process_year(sess, year):
    """Process both problem and solution files for a given year"""
    print(f"Processing {year}...")
    
    # Generate URLs - these follow the exact pattern from the website
    problems_url = f"https://kskedlaya.org/putnam-archive/{year}.tex"
    solutions_url = f"https://kskedlaya.org/putnam-archive/{year}s.tex"
    
    # Get or create year entry
    year_obj = sess.query(Year).filter_by(year=year).first()
    if not year_obj:
        year_obj = Year(
            year=year,
            pdf_url=None,
            solutions_pdf_url=None,
            problems_tex_url=problems_url,
            solutions_tex_url=solutions_url
        )
        sess.add(year_obj)
        sess.commit()
    
    problems_added = 0
    solutions_added = 0
    
    # Fetch and parse problems
    print(f"  Downloading problems: {problems_url}")
    problems_content = fetch_tex_content(problems_url)
    
    if problems_content:
        problems = parse_problems_from_tex(problems_content)
        print(f"  Found {len(problems)} problems")
        
        for prob_data in problems:
            # Check if problem already exists
            existing = sess.query(Problem).filter_by(
                year_id=year_obj.id,
                label=prob_data["label"]
            ).first()
            
            if not existing:
                problem = Problem(
                    year=year_obj,
                    label=prob_data["label"],
                    part=prob_data["part"],
                    number=prob_data["number"],
                    statement=prob_data["content"],
                    solution=None,  # Will be filled from solutions file
                    pdf_url=None
                )
                sess.add(problem)
                problems_added += 1
    else:
        print(f"  No problems found for {year}")
    
    # Fetch and parse solutions
    print(f"  Downloading solutions: {solutions_url}")
    solutions_content = fetch_tex_content(solutions_url)
    
    if solutions_content:
        solutions = parse_problems_from_tex(solutions_content)  # Same parsing format
        print(f"  Found {len(solutions)} solutions")
        
        # Match solutions to problems
        for sol_data in solutions:
            problem = sess.query(Problem).filter_by(
                year_id=year_obj.id,
                label=sol_data["label"]
            ).first()
            
            if problem:
                problem.solution = sol_data["content"]
                solutions_added += 1
    else:
        print(f"  No solutions found for {year}")
    
    sess.commit()
    print(f"  Added {problems_added} problems, {solutions_added} solutions")
    
    return problems_added, solutions_added

def main():
    print(f"Database path: {DB_PATH}")
    print("Starting simplified Putnam scraper...")
    
    sess = Session()
    
    # Years to scrape - from the website table, TEX files exist from 1985-2024
    years_to_scrape = list(range(1985, 2025))  # 1985 to 2024
    
    total_problems = 0
    total_solutions = 0
    
    for year in reversed(years_to_scrape):  # Process recent years first
        try:
            problems_added, solutions_added = process_year(sess, year)
            total_problems += problems_added
            total_solutions += solutions_added
        except Exception as e:
            print(f"Error processing {year}: {e}")
            continue
    
    # Summary
    print(f"\n{'='*50}")
    print("SCRAPING SUMMARY")
    print(f"{'='*50}")
    
    db_years = sess.query(Year).count()
    db_problems = sess.query(Problem).count()
    db_solutions = sess.query(Problem).filter(Problem.solution.isnot(None)).count()
    
    print(f"Years processed: {len(years_to_scrape)}")
    print(f"Years in database: {db_years}")
    print(f"Problems in database: {db_problems}")
    print(f"Problems with solutions: {db_solutions}")
    
    # Show sample of recent years
    print(f"\nRecent years sample:")
    recent = sess.query(Year).filter(Year.year >= 2020).order_by(Year.year.desc()).limit(5)
    for year_obj in recent:
        problem_count = len(year_obj.problems)
        solution_count = len([p for p in year_obj.problems if p.solution])
        print(f"  {year_obj.year}: {problem_count} problems, {solution_count} solutions")
    
    sess.close()
    print(f"\nDone! Database saved to: {DB_PATH}")

if __name__ == "__main__":
    main()
