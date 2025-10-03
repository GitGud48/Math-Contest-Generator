#!/usr/bin/env python3
"""
Simplified IMO Scraper - Saves raw HTML content for frontend processing
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

class RawContentIMOScraper:
    def __init__(self, database_url="sqlite:///imo.sqlite", headless=True):
        """Initialize IMO scraper that preserves raw content"""
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
        for problem_num in range(1, 7):
            url = f"https://artofproblemsolving.com/wiki/index.php/{year}_IMO_Problems/Problem_{problem_num}"
            problem_urls.append((problem_num, url))
        return problem_urls
    
    def scrape_individual_problem(self, contest_year, problem_number, problem_url):
        """Scrape individual problem preserving raw HTML"""
        try:
            self.logger.info(f"   🔍 Scraping Problem {problem_number}: {problem_url}")
            
            # Check if page exists
            response = requests.get(problem_url)
            if response.status_code != 200:
                self.logger.warning(f"   ⚠️  Problem {problem_number} page not found (404)")
                return False
            
            # Use Selenium for full page load
            self.driver.get(problem_url)
            time.sleep(3)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Extract raw HTML content
            problem_statement_html = self._extract_raw_problem_statement(soup)
            solution_html = self._extract_raw_solutions(soup)
            
            if not problem_statement_html or len(problem_statement_html.strip()) < 20:
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
            
            # Create and save the problem with raw HTML
            problem = Problem(
                contest_year_id=contest_year.id,
                problem_number=problem_number,
                problem_label=f"Problem {problem_number}",
                statement=problem_statement_html,
                statement_format='html',  # Mark as HTML format
                solution=solution_html if solution_html else "Solutions not available",
                solution_format='html',
                aops_problem_url=problem_url,
                subject_area=self._guess_subject_area(problem_statement_html)
            )
            
            self.session.add(problem)
            self.logger.info(f"   ➕ Added Problem {problem_number}")
            return True
            
        except Exception as e:
            self.logger.error(f"   ❌ Error scraping Problem {problem_number}: {e}")
            return False
    
    def _extract_raw_problem_statement(self, soup):
        """Extract raw HTML problem statement"""
        try:
            # Find h2 with span id="Problem" class="mw-headline"
            problem_header = None
            for h2 in soup.find_all('h2'):
                span = h2.find('span', {'id': 'Problem', 'class': 'mw-headline'})
                if span:
                    problem_header = h2
                    break
            
            if not problem_header:
                return ""
            
            # Collect all content until next h2
            content_html = []
            current = problem_header.find_next_sibling()
            
            while current:
                if current.name == 'h2':
                    break
                
                if current.name in ['p', 'div'] and str(current).strip():
                    content_html.append(str(current))
                
                current = current.find_next_sibling()
            
            return ''.join(content_html)
            
        except Exception as e:
            self.logger.error(f"Error extracting problem statement: {e}")
            return ""
    
    def _extract_raw_solutions(self, soup):
        """Extract raw HTML solutions"""
        try:
            # Find solutions header
            solutions_header = None
            for h2 in soup.find_all('h2'):
                span = h2.find('span', {'class': 'mw-headline'})
                if span and ('Solutions' in span.get_text() or 'Solution' in span.get_text()):
                    solutions_header = h2
                    break
            
            if not solutions_header:
                return ""
            
            # Collect all content until next major section
            content_html = []
            current = solutions_header.find_next_sibling()
            
            while current:
                if current.name == 'h2':
                    span = current.find('span', {'class': 'mw-headline'})
                    if span and any(stop_word in span.get_text().lower() 
                                  for stop_word in ['see also', 'external', 'references']):
                        break
                
                if current.name in ['p', 'div', 'h3'] and str(current).strip():
                    content_html.append(str(current))
                
                current = current.find_next_sibling()
            
            return ''.join(content_html)
            
        except Exception as e:
            self.logger.error(f"Error extracting solutions: {e}")
            return ""
    
    def _guess_subject_area(self, html_content):
        """Guess subject area from HTML content"""
        # Convert to text for analysis
        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text().lower()
        
        if any(word in text for word in 
               ['triangle', 'circle', 'angle', 'polygon', 'line', 'point']):
            return 'Geometry'
        elif any(word in text for word in 
                 ['prime', 'integer', 'divisible', 'modular', 'congruent']):
            return 'Number Theory'
        elif any(word in text for word in 
                 ['polynomial', 'equation', 'function', 'inequality']):
            return 'Algebra'
        elif any(word in text for word in 
                 ['permutation', 'combination', 'ways', 'arrangements']):
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
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
            if hasattr(self, 'session'):
                self.session.close()
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")

# Usage - Modified to loop through all years
if __name__ == "__main__":
    scraper = RawContentIMOScraper(
        database_url="sqlite:///imo.sqlite",
        headless=True
    )
    
    try:
        contest = scraper.create_imo_contest()
        
        # Loop through all IMO years from 1959 to 2024
        total_problems = 0
        for year in range(1959, 2025):  # 1959 to 2024 inclusive
            print(f"\n📊 Processing IMO {year} ({year - 1958}/{2024 - 1958})")
            
            try:
                problems_added = scraper.scrape_year_problems(contest, year)
                total_problems += problems_added
                print(f"💾 CHECKPOINT: {total_problems} total problems scraped")
                
                # Small delay between years to be respectful
                time.sleep(3)
                
            except Exception as e:
                print(f"❌ Failed processing IMO {year}: {e}")
                continue
        
        print(f"\n🎉 Complete! Scraped {total_problems} problems from {2024 - 1958} years")
        
    except KeyboardInterrupt:
        print("\n⏸️  Scraping interrupted by user")
    finally:
        scraper.cleanup()
