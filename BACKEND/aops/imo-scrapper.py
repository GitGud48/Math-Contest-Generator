#!/usr/bin/env python3
"""
Fixed IMO Problems Scraper - Uses correct URL structure and HTML parsing
"""

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import re
import time
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from aops_models import Base, Contest, ContestYear, Problem

class IMOScraper:
    def __init__(self, database_url="sqlite:///imo_problems.db", headless=True):
        """Initialize IMO-specific scraper"""
        # Database setup
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Logging setup
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Browser setup
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            self.logger.error(f"Chrome driver error: {e}")
            raise
        
        # URLs
        self.base_url = "https://artofproblemsolving.com/wiki/index.php/"
        self.main_page = "https://artofproblemsolving.com/wiki/index.php/IMO_Problems_and_Solutions"
        
    def create_imo_contest(self):
        """Create or get the IMO contest in database"""
        contest = self.session.query(Contest).filter_by(name="IMO").first()
        if not contest:
            contest = Contest(
                name="IMO",
                full_name="International Mathematical Olympiad",
                country="International",
                organization="IMO Committee",
                contest_type="Olympiad",
                target_level="High School",
                aops_wiki_url=self.main_page
            )
            self.session.add(contest)
            self.session.commit()
            self.logger.info("✅ Created IMO contest")
        return contest
    
    def generate_problem_urls(self, year):
        """Generate the URLs for individual IMO problems for a given year"""
        problem_urls = []
        # IMO typically has 6 problems
        for problem_num in range(1, 7):
            url = f"https://artofproblemsolving.com/wiki/index.php/{year}_IMO_Problems/Problem_{problem_num}"
            problem_urls.append((problem_num, url))
        return problem_urls
    
    def scrape_individual_problem(self, contest_year, problem_number, problem_url):
        """Scrape an individual problem page using the exact HTML structure"""
        try:
            self.logger.info(f"   🔍 Scraping Problem {problem_number}: {problem_url}")
            
            # Use requests first to check if page exists
            response = requests.get(problem_url)
            if response.status_code != 200:
                self.logger.warning(f"   ⚠️  Problem {problem_number} page not found (404)")
                return False
            
            # Use Selenium for full page load
            self.driver.get(problem_url)
            time.sleep(3)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find the Problem section using exact HTML structure
            problem_statement = self._extract_problem_statement(soup)
            solution = self._extract_solutions(soup)
            
            if not problem_statement or len(problem_statement.strip()) < 20:
                self.logger.warning(f"   ⚠️  No substantial problem statement found for Problem {problem_number}")
                return False
            
            # Check if problem already exists
            existing = self.session.query(Problem).filter_by(
                contest_year_id=contest_year.id,
                problem_number=problem_number
            ).first()
            
            if existing:
                self.logger.info(f"   ✅ Problem {problem_number} already exists, skipping")
                return False
            
            # Create and save the problem
            problem = Problem(
                contest_year_id=contest_year.id,
                problem_number=problem_number,
                problem_label=f"Problem {problem_number}",
                statement=problem_statement.strip(),
                statement_format='html',
                solution=solution.strip() if solution else "Solutions not available",
                solution_format='html',
                aops_problem_url=problem_url,
                subject_area=self._guess_subject_area(problem_statement)
            )
            
            self.session.add(problem)
            self.logger.info(f"   ➕ Added Problem {problem_number}: {problem_statement[:60]}...")
            return True
            
        except Exception as e:
            self.logger.error(f"   ❌ Error scraping Problem {problem_number}: {e}")
            return False
    
    def _extract_problem_statement(self, soup):
        """Extract problem statement using the exact HTML structure"""
        try:
            # Find h2 with span id="Problem" class="mw-headline"
            problem_header = None
            for h2 in soup.find_all('h2'):
                span = h2.find('span', {'id': 'Problem', 'class': 'mw-headline'})
                if span:
                    problem_header = h2
                    break
            
            if not problem_header:
                self.logger.warning("   No problem header found with correct structure")
                return ""
            
            # Extract content after the problem header until the next h2
            content_parts = []
            current = problem_header.find_next_sibling()
            
            while current:
                # Stop if we hit another h2 (like Solutions)
                if current.name == 'h2':
                    break
                
                # Extract text content
                if hasattr(current, 'get_text'):
                    text = current.get_text().strip()
                    if text and len(text) > 5:
                        content_parts.append(text)
                
                current = current.find_next_sibling()
            
            return ' '.join(content_parts)
            
        except Exception as e:
            self.logger.error(f"Error extracting problem statement: {e}")
            return ""
    
    def _extract_solutions(self, soup):
        """Extract all solutions from the Solutions section"""
        try:
            # Find h2 with span id="Solutions" class="mw-headline"
            solutions_header = None
            for h2 in soup.find_all('h2'):
                span = h2.find('span', {'class': 'mw-headline'})
                if span and ('Solutions' in span.get_text() or 'Solution' in span.get_text()):
                    solutions_header = h2
                    break
            
            if not solutions_header:
                return ""
            
            # Extract content after the solutions header
            content_parts = []
            current = solutions_header.find_next_sibling()
            
            while current:
                # Stop if we hit "See Also" or another major section
                if current.name == 'h2':
                    span = current.find('span', {'class': 'mw-headline'})
                    if span and any(stop_word in span.get_text().lower() 
                                  for stop_word in ['see also', 'external', 'references']):
                        break
                
                # Extract text content
                if hasattr(current, 'get_text'):
                    text = current.get_text().strip()
                    if text and len(text) > 10:
                        content_parts.append(text)
                
                current = current.find_next_sibling()
            
            return ' '.join(content_parts)
            
        except Exception as e:
            self.logger.error(f"Error extracting solutions: {e}")
            return ""
    
    def _guess_subject_area(self, text):
        """Guess subject area from problem text"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in 
               ['triangle', 'circle', 'angle', 'polygon', 'line', 'point', 'perpendicular', 
                'parallel', 'inscribed', 'circumscribed', 'tangent']):
            return 'Geometry'
        elif any(word in text_lower for word in 
                 ['prime', 'integer', 'divisible', 'modular', 'congruent', 'gcd', 'lcm']):
            return 'Number Theory'
        elif any(word in text_lower for word in 
                 ['polynomial', 'equation', 'function', 'inequality', 'variable']):
            return 'Algebra'
        elif any(word in text_lower for word in 
                 ['permutation', 'combination', 'ways', 'arrangements', 'choose']):
            return 'Combinatorics'
        else:
            return 'Mixed'
    
    def scrape_year_problems(self, contest, year):
        """Scrape all problems for a specific IMO year"""
        self.logger.info(f"📖 Scraping IMO {year}...")
        
        try:
            # Get or create contest year
            contest_year = self.session.query(ContestYear).filter_by(
                contest_id=contest.id, year=year
            ).first()
            
            if not contest_year:
                contest_year = ContestYear(
                    contest_id=contest.id,
                    year=year,
                    aops_problems_url=f"https://artofproblemsolving.com/wiki/index.php/{year}_IMO"
                )
                self.session.add(contest_year)
                self.session.commit()
                self.logger.info(f"✅ Created contest year: IMO {year}")
            
            # Generate URLs for all 6 problems
            problem_urls = self.generate_problem_urls(year)
            problems_added = 0
            
            for problem_num, problem_url in problem_urls:
                try:
                    if self.scrape_individual_problem(contest_year, problem_num, problem_url):
                        problems_added += 1
                    time.sleep(2)  # Rate limiting
                except Exception as e:
                    self.logger.error(f"   ❌ Error with Problem {problem_num}: {e}")
                    continue
            
            self.session.commit()
            self.logger.info(f"✅ IMO {year}: {problems_added} problems saved")
            return problems_added
            
        except Exception as e:
            self.logger.error(f"❌ Error scraping IMO {year}: {e}")
            return 0
    
    def run_test_scrape(self, test_years=None):
        """Run a test scrape on specific years"""
        if test_years is None:
            test_years = [2023, 2022, 2021]  # Recent years for testing
        
        self.logger.info(f"🧪 Starting test scrape for years: {test_years}")
        
        try:
            contest = self.create_imo_contest()
            total_problems = 0
            
            for year in test_years:
                self.logger.info(f"\n📊 Processing: IMO {year}")
                
                try:
                    problems_added = self.scrape_year_problems(contest, year)
                    total_problems += problems_added
                    
                    self.logger.info(f"💾 CHECKPOINT: {total_problems} problems total")
                    time.sleep(2)
                    
                except Exception as e:
                    self.logger.error(f"❌ Failed processing IMO {year}: {e}")
                    continue
            
            self.logger.info(f"\n🎉 Test scraping complete! Total problems: {total_problems}")
            
        except Exception as e:
            self.logger.error(f"💥 Fatal error: {e}")
        
        finally:
            self.cleanup()
    
    def run_full_scrape(self, start_year=1959, end_year=2024):
        """Run the complete IMO scraping process"""
        self.logger.info(f"🚀 Starting full IMO scraping from {start_year} to {end_year}...")
        
        try:
            contest = self.create_imo_contest()
            total_problems = 0
            years_processed = 0
            
            for year in range(start_year, end_year + 1):
                self.logger.info(f"\n📊 Processing: IMO {year} ({year - start_year + 1}/{end_year - start_year + 1})")
                
                try:
                    problems_added = self.scrape_year_problems(contest, year)
                    total_problems += problems_added
                    years_processed += 1
                    
                    self.logger.info(f"💾 CHECKPOINT: {total_problems} problems total, {years_processed} years processed")
                    time.sleep(2)  # Rate limiting
                    
                except Exception as e:
                    self.logger.error(f"❌ Failed processing IMO {year}: {e}")
                    continue
            
            self.logger.info(f"\n🎉 IMO scraping complete! Total: {total_problems} problems from {years_processed} years")
            
        except Exception as e:
            self.logger.error(f"💥 Fatal error: {e}")
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
            if hasattr(self, 'session'):
                self.session.close()
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")

# Test with one year to verify structure
def test_single_year():
    """Test with just one year to verify everything works"""
    scraper = IMOScraper(
        database_url="sqlite:///imo_test.db",
        headless=False  # Show browser for debugging
    )
    
    try:
        scraper.run_test_scrape([1960])  # Test with 1960 since we know the structure
    except KeyboardInterrupt:
        print("\n⏸️  Testing interrupted")
    finally:
        scraper.cleanup()

# Test with recent years
def test_recent_years():
    """Test with recent years"""
    scraper = IMOScraper(
        database_url="sqlite:///imo_test.db",
        headless=True
    )
    
    try:
        scraper.run_test_scrape([2023, 2022, 2021])
    except KeyboardInterrupt:
        print("\n⏸️  Testing interrupted")
    finally:
        scraper.cleanup()

# Scrape a range of years
def scrape_year_range():
    """Scrape a specific range of years"""
    scraper = IMOScraper(
        database_url="sqlite:///imo_complete.db",
        headless=True
    )
    
    try:
        # Scrape from 1959 to 2024 (all IMO years)
        scraper.run_full_scrape(start_year=1959, end_year=2024)
    except KeyboardInterrupt:
        print("\n⏸️  Scraping interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test-single":
        test_single_year()
    elif len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_recent_years()
    elif len(sys.argv) > 1 and sys.argv[1] == "--full":
        scrape_year_range()
    else:
        # Default: test recent years
        test_recent_years()
